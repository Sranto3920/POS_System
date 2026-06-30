from decimal import Decimal

from extensions import db
from models.ledger import CustomerLedger
from models.payment import PAYMENT_METHODS, Payment
from models.sale import Sale
from services.sale_service import SaleService
from utils.pagination import PER_PAGE_DEFAULT


class PaymentService:
    """Shop-scoped payment operations."""

    def __init__(self, shop_id):
        self.shop_id = shop_id
        self._sale_service = SaleService(shop_id)

    def list_payments(self, page=1, per_page=PER_PAGE_DEFAULT, search=""):
        query = (
            Payment.query.join(Sale)
            .filter(Sale.shop_id == self.shop_id)
            .order_by(Payment.payment_date.desc(), Payment.id.desc())
        )

        if search:
            like = f"%{search}%"
            query = query.filter(Payment.payment_method.ilike(like))

        return query.paginate(page=page, per_page=per_page, error_out=False)

    def record_payment(self, sale_id, payment_method, paid_amount, remarks=None):
        if payment_method not in PAYMENT_METHODS:
            raise ValueError("Invalid payment method.")

        paid_amount = Decimal(str(paid_amount or 0))
        if paid_amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")

        sale = Sale.query.filter_by(id=sale_id, shop_id=self.shop_id).first()
        if sale is None:
            raise ValueError("Sale not found.")

        balance_due = self._sale_service.get_sale_balance_due(sale)
        if paid_amount > balance_due:
            raise ValueError(
                f"Payment exceeds balance due ({balance_due:.2f})."
            )

        try:
            payment = Payment(
                sale_id=sale.id,
                payment_method=payment_method,
                paid_amount=paid_amount,
            )
            db.session.add(payment)

            if balance_due > 0:
                previous_balance = self._get_customer_balance(
                    self.shop_id, sale.customer_id
                )
                new_balance = previous_balance - paid_amount
                if new_balance < 0:
                    new_balance = Decimal("0")

                ledger_entry = CustomerLedger(
                    shop_id=self.shop_id,
                    customer_id=sale.customer_id,
                    sale_id=sale.id,
                    debit=Decimal("0"),
                    credit=paid_amount,
                    balance=new_balance,
                    remarks=remarks or f"Payment on sale #{sale.id}",
                )
                db.session.add(ledger_entry)

            self._sale_service.sync_sale_payment_fields(sale)

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return payment

    def get_unpaid_sales(self):
        sales = (
            Sale.query.filter_by(shop_id=self.shop_id)
            .order_by(Sale.sale_date.desc(), Sale.id.desc())
            .all()
        )
        unpaid = []
        for sale in sales:
            balance = self._sale_service.get_sale_balance_due(sale)
            if balance > 0:
                unpaid.append({"sale": sale, "balance_due": balance})
        return unpaid

    def get_customers_with_due(self, search=""):
        from models.customer import Customer

        customers = (
            Customer.query.filter_by(shop_id=self.shop_id)
            .order_by(Customer.name.asc())
            .all()
        )
        results = []
        for customer in customers:
            unpaid = self._sale_service.get_unpaid_sales_for_customer(customer.id)
            if not unpaid:
                continue
            if search:
                term = search.lower()
                haystack = " ".join(
                    filter(
                        None,
                        [customer.name, customer.phone or "", customer.email or ""],
                    )
                ).lower()
                if term not in haystack:
                    continue
            total_due = sum(item["balance_due"] for item in unpaid)
            results.append(
                {
                    "customer": customer,
                    "unpaid_sales": unpaid,
                    "total_due": total_due,
                }
            )
        return results

    def _get_customer_balance(self, shop_id, customer_id):
        entry = (
            CustomerLedger.query.filter_by(shop_id=shop_id, customer_id=customer_id)
            .order_by(CustomerLedger.transaction_date.desc(), CustomerLedger.id.desc())
            .first()
        )
        if entry is None:
            return Decimal("0")
        return Decimal(str(entry.balance))
