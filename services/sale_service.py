from decimal import Decimal

from extensions import db
from models.customer import Customer
from models.ledger import CustomerLedger
from models.payment import PAYMENT_METHODS, Payment
from models.product import Product
from models.sale import (
    PAYMENT_STATUS_DUE,
    PAYMENT_STATUS_PAID,
    PAYMENT_STATUS_PARTIAL,
    Sale,
    SaleDetail,
)
from utils.pagination import PER_PAGE_DEFAULT

WALKIN_CUSTOMER_NAME = "Walk-in Customer"
MIN_PRICE_ERROR = "This product cannot be sold below the minimum allowed price."


def compute_payment_status(paid_amount, total_amount):
    paid_amount = Decimal(str(paid_amount or 0))
    total_amount = Decimal(str(total_amount or 0))
    if paid_amount >= total_amount:
        return PAYMENT_STATUS_PAID
    if paid_amount <= 0:
        return PAYMENT_STATUS_DUE
    return PAYMENT_STATUS_PARTIAL


class SaleService:
    """Shop-scoped sale operations."""

    def __init__(self, shop_id):
        self.shop_id = shop_id

    def get_or_create_walkin_customer(self, shop_id):
        customer = Customer.query.filter_by(
            shop_id=shop_id, name=WALKIN_CUSTOMER_NAME
        ).first()
        if customer is None:
            customer = Customer(shop_id=shop_id, name=WALKIN_CUSTOMER_NAME)
            db.session.add(customer)
            db.session.commit()
        return customer

    def validate_stock(self, shop_id, items):
        errors = []
        for item in items:
            product_id = int(item["product_id"])
            quantity = int(item["quantity"])
            product = Product.query.filter_by(id=product_id, shop_id=shop_id).first()

            if product is None:
                errors.append(f"Product #{product_id} not found.")
                continue

            available = product.stock_quantity or 0
            if quantity <= 0:
                errors.append(f"{product.name}: quantity must be greater than zero.")
            elif quantity > available:
                errors.append(
                    f"{product.name}: requested {quantity}, only {available} in stock."
                )
        return errors

    def validate_minimum_prices(self, shop_id, items):
        errors = []
        for item in items:
            product_id = int(item["product_id"])
            selling_price = Decimal(str(item["selling_price"]))
            product = Product.query.filter_by(id=product_id, shop_id=shop_id).first()
            if product is None:
                continue

            minimum_price = Decimal(str(product.effective_minimum_price))
            if selling_price < minimum_price:
                errors.append(f"{product.name}: {MIN_PRICE_ERROR}")
        return errors

    def create_sale(
        self, shop_id, user_id, customer_id, items, payment_method, paid_amount
    ):
        if not items:
            raise ValueError("At least one product line is required.")

        if payment_method not in PAYMENT_METHODS:
            raise ValueError("Invalid payment method.")

        customer = Customer.query.filter_by(id=customer_id, shop_id=shop_id).first()
        if customer is None:
            raise ValueError("Customer not found.")

        stock_errors = self.validate_stock(shop_id, items)
        if stock_errors:
            raise ValueError("; ".join(stock_errors))

        price_errors = self.validate_minimum_prices(shop_id, items)
        if price_errors:
            raise ValueError("; ".join(price_errors))

        paid_amount = Decimal(str(paid_amount or 0))
        if paid_amount < 0:
            raise ValueError("Paid amount cannot be negative.")

        sale = Sale(
            shop_id=shop_id,
            customer_id=customer_id,
            user_id=user_id,
            total_amount=Decimal("0"),
            paid_amount=Decimal("0"),
            due_amount=Decimal("0"),
            payment_status=PAYMENT_STATUS_PAID,
        )
        db.session.add(sale)

        total = Decimal("0")

        try:
            for item in items:
                product_id = int(item["product_id"])
                quantity = int(item["quantity"])
                selling_price = Decimal(str(item["selling_price"]))
                discount = Decimal(str(item.get("discount") or 0))

                if selling_price < 0:
                    raise ValueError("Selling price cannot be negative.")
                if discount < 0:
                    raise ValueError("Discount cannot be negative.")

                product = (
                    Product.query.filter_by(id=product_id, shop_id=shop_id)
                    .with_for_update()
                    .first()
                )
                if product is None:
                    raise ValueError(f"Product #{product_id} not found.")

                minimum_price = Decimal(str(product.effective_minimum_price))
                if selling_price < minimum_price:
                    raise ValueError(f"{product.name}: {MIN_PRICE_ERROR}")

                available = product.stock_quantity or 0
                if quantity > available:
                    raise ValueError(
                        f"{product.name}: insufficient stock ({available} available)."
                    )

                line_total = (selling_price * quantity) - discount
                if line_total < 0:
                    raise ValueError(
                        f"{product.name}: discount cannot exceed line total."
                    )
                total += line_total

                detail = SaleDetail(
                    sale=sale,
                    product_id=product_id,
                    quantity=quantity,
                    selling_price=selling_price,
                    discount=discount,
                )
                db.session.add(detail)

                product.stock_quantity = available - quantity

            sale.total_amount = total

            if paid_amount > total:
                raise ValueError("Paid amount cannot exceed sale total.")

            if paid_amount == 0 and total > 0:
                paid_amount = total

            due_amount = total - paid_amount
            if due_amount > 0 and customer.name == WALKIN_CUSTOMER_NAME:
                raise ValueError(
                    "Select a registered customer to record a due amount."
                )

            sale.paid_amount = paid_amount
            sale.due_amount = due_amount
            sale.payment_status = compute_payment_status(paid_amount, total)

            db.session.flush()

            if paid_amount > 0:
                payment = Payment(
                    sale_id=sale.id,
                    payment_method=payment_method,
                    paid_amount=paid_amount,
                )
                db.session.add(payment)

            if due_amount > 0:
                previous_balance = self._get_customer_balance(shop_id, customer_id)
                new_balance = previous_balance + due_amount
                ledger_entry = CustomerLedger(
                    shop_id=shop_id,
                    customer_id=customer_id,
                    sale_id=sale.id,
                    debit=due_amount,
                    credit=Decimal("0"),
                    balance=new_balance,
                    remarks=f"Due on sale #{sale.id}",
                )
                db.session.add(ledger_entry)

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return sale

    def list_sales(self, page=1, per_page=PER_PAGE_DEFAULT, search=""):
        query = Sale.query.filter_by(shop_id=self.shop_id).order_by(
            Sale.sale_date.desc(), Sale.id.desc()
        )

        if search:
            like = f"%{search}%"
            query = query.join(Customer).filter(Customer.name.ilike(like))

        return query.paginate(page=page, per_page=per_page, error_out=False)

    def get_sale(self, sale_id):
        return Sale.query.filter_by(id=sale_id, shop_id=self.shop_id).first()

    def get_sale_paid_total(self, sale):
        payments = sale.payments.all()
        return sum(
            (Decimal(str(p.paid_amount)) for p in payments),
            Decimal("0"),
        )

    def get_sale_balance_due(self, sale):
        return Decimal(str(sale.total_amount)) - self.get_sale_paid_total(sale)

    def sync_sale_payment_fields(self, sale):
        paid_total = self.get_sale_paid_total(sale)
        total = Decimal(str(sale.total_amount))
        due = total - paid_total
        if due < 0:
            due = Decimal("0")

        sale.paid_amount = paid_total
        sale.due_amount = due
        sale.payment_status = compute_payment_status(paid_total, total)
        return sale

    def get_unpaid_sales_for_customer(self, customer_id):
        sales = (
            Sale.query.filter_by(shop_id=self.shop_id, customer_id=customer_id)
            .order_by(Sale.sale_date.desc(), Sale.id.desc())
            .all()
        )
        unpaid = []
        for sale in sales:
            balance = self.get_sale_balance_due(sale)
            if balance > 0:
                unpaid.append(
                    {
                        "sale": sale,
                        "paid_total": self.get_sale_paid_total(sale),
                        "balance_due": balance,
                    }
                )
        return unpaid

    def _get_customer_balance(self, shop_id, customer_id):
        entry = (
            CustomerLedger.query.filter_by(shop_id=shop_id, customer_id=customer_id)
            .order_by(CustomerLedger.transaction_date.desc(), CustomerLedger.id.desc())
            .first()
        )
        if entry is None:
            return Decimal("0")
        return Decimal(str(entry.balance))
