from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import text

from extensions import db
from models.daily_cash import DailyCash
from models.due_payment import DuePayment
from models.expense import Expense
from models.sale import Sale
from services.sale_service import SaleService


class CashService:
    """Today's cash drawer calculations for a shop."""

    def __init__(self, shop_id):
        self.shop_id = shop_id

    def get_today_summary(self):
        today = date.today()
        daily = self._get_or_create_daily_cash(today)
        self._apply_carry_forward_opening(today, daily)

        opening = Decimal(str(daily.opening_cash or 0))
        carry_forward = Decimal(str(daily.carry_forward_cash or 0))
        new_sales_cash = self._cash_from_new_sales(today)
        due_collected_cash = self._cash_from_due_collections(today)
        expenses = self._today_expenses(today)
        supplier_payments = self._supplier_payments(today)
        withdrawals = self._cash_withdrawals(today)

        total_received = new_sales_cash + due_collected_cash
        expected = (
            opening
            + new_sales_cash
            + due_collected_cash
            - expenses
            - supplier_payments
            - withdrawals
        )

        actual = (
            Decimal(str(daily.actual_cash))
            if daily.actual_cash is not None
            else None
        )
        difference = None
        cash_status = "unknown"
        if actual is not None:
            difference = actual - expected
            if difference == 0:
                cash_status = "ok"
            elif difference < 0:
                cash_status = "shortage"
            else:
                cash_status = "extra"

        return {
            "date": today,
            "opening_cash": opening,
            "carry_forward_cash": carry_forward,
            "new_sales_cash": new_sales_cash,
            "due_collected_cash": due_collected_cash,
            "total_received": total_received,
            "expenses": expenses,
            "supplier_payments": supplier_payments,
            "withdrawals": withdrawals,
            "expected_cash": expected,
            "actual_cash": actual,
            "difference": difference,
            "cash_status": cash_status,
            "daily_record": daily,
        }

    def get_total_customer_due(self):
        service = SaleService(self.shop_id)
        sales = Sale.query.filter_by(shop_id=self.shop_id).all()
        total = Decimal("0")
        for sale in sales:
            balance = service.get_sale_balance_due(sale)
            if balance > 0:
                total += balance
        return total

    def get_recent_due_collections(self, limit=8):
        return (
            DuePayment.query.filter_by(shop_id=self.shop_id)
            .order_by(DuePayment.collected_at.desc(), DuePayment.id.desc())
            .limit(limit)
            .all()
        )

    def get_today_expenses(self, limit=10):
        today = date.today()
        return (
            Expense.query.filter_by(shop_id=self.shop_id)
            .filter(db.func.date(Expense.expense_date) == today)
            .order_by(Expense.expense_date.desc())
            .limit(limit)
            .all()
        )

    def save_daily_cash(
        self,
        user_id,
        opening_cash=None,
        carry_forward_cash=None,
        actual_cash=None,
        supplier_payments=None,
        cash_withdrawals=None,
        notes=None,
    ):
        today = date.today()
        daily = self._get_or_create_daily_cash(today)

        if opening_cash is not None:
            daily.opening_cash = Decimal(str(opening_cash))
        if carry_forward_cash is not None:
            daily.carry_forward_cash = Decimal(str(carry_forward_cash))
        if supplier_payments is not None:
            daily.supplier_payments = Decimal(str(supplier_payments))
        if cash_withdrawals is not None:
            daily.cash_withdrawals = Decimal(str(cash_withdrawals))
        if actual_cash is not None:
            daily.actual_cash = Decimal(str(actual_cash))
            daily.recorded_by = user_id
            daily.recorded_at = datetime.now(timezone.utc)
        if notes is not None:
            daily.notes = notes

        db.session.commit()
        return daily

    def add_expense(self, user_id, amount, description, category=None):
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError("Expense amount must be greater than zero.")
        description = (description or "").strip()
        if not description:
            raise ValueError("Expense description is required.")

        expense = Expense(
            shop_id=self.shop_id,
            user_id=user_id,
            amount=amount,
            description=description,
            category=category,
        )
        db.session.add(expense)
        db.session.commit()
        return expense

    def delete_expense(self, expense_id):
        expense = Expense.query.filter_by(
            shop_id=self.shop_id, id=expense_id
        ).first()
        if expense is None:
            raise ValueError("Expense not found.")
        db.session.delete(expense)
        db.session.commit()

    def _apply_carry_forward_opening(self, cash_date, daily):
        """If today has no opening set, use yesterday's carry forward."""
        if Decimal(str(daily.opening_cash or 0)) > 0:
            return
        yesterday = cash_date - timedelta(days=1)
        prev = DailyCash.query.filter_by(
            shop_id=self.shop_id, cash_date=yesterday
        ).first()
        if prev and Decimal(str(prev.carry_forward_cash or 0)) > 0:
            daily.opening_cash = prev.carry_forward_cash
            db.session.commit()

    def _get_or_create_daily_cash(self, cash_date):
        daily = DailyCash.query.filter_by(
            shop_id=self.shop_id, cash_date=cash_date
        ).first()
        if daily is None:
            daily = DailyCash(shop_id=self.shop_id, cash_date=cash_date)
            db.session.add(daily)
            db.session.commit()
        return daily

    def _supplier_payments(self, cash_date):
        daily = DailyCash.query.filter_by(
            shop_id=self.shop_id, cash_date=cash_date
        ).first()
        if daily:
            return Decimal(str(daily.supplier_payments or 0))
        return Decimal("0")

    def _cash_withdrawals(self, cash_date):
        daily = DailyCash.query.filter_by(
            shop_id=self.shop_id, cash_date=cash_date
        ).first()
        if daily:
            return Decimal(str(daily.cash_withdrawals or 0))
        return Decimal("0")

    def _cash_from_new_sales(self, cash_date):
        result = db.session.execute(
            text(
                """
                SELECT COALESCE(SUM(p.paid_amount), 0)
                FROM Payments p
                JOIN Sales s ON p.sale_id = s.sale_id
                WHERE s.shop_id = :shop_id
                  AND DATE(s.sale_date) = :cash_date
                  AND DATE(p.payment_date) = :cash_date
                  AND (p.payment_type = 'sale' OR p.payment_type IS NULL)
                  AND p.payment_method = 'Cash'
                """
            ),
            {"shop_id": self.shop_id, "cash_date": cash_date},
        ).scalar()
        return Decimal(str(result or 0))

    def _cash_from_due_collections(self, cash_date):
        result = db.session.execute(
            text(
                """
                SELECT COALESCE(SUM(paid_amount), 0)
                FROM DuePayments
                WHERE shop_id = :shop_id
                  AND DATE(collected_at) = :cash_date
                  AND payment_method = 'Cash'
                """
            ),
            {"shop_id": self.shop_id, "cash_date": cash_date},
        ).scalar()
        return Decimal(str(result or 0))

    def _today_expenses(self, cash_date):
        result = db.session.execute(
            text(
                """
                SELECT COALESCE(SUM(amount), 0)
                FROM Expenses
                WHERE shop_id = :shop_id
                  AND DATE(expense_date) = :cash_date
                """
            ),
            {"shop_id": self.shop_id, "cash_date": cash_date},
        ).scalar()
        return Decimal(str(result or 0))
