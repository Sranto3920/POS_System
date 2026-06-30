from decimal import Decimal

from models.customer import Customer
from models.ledger import CustomerLedger
from utils.pagination import PER_PAGE_DEFAULT


class LedgerService:
    """Shop-scoped customer ledger operations."""

    def __init__(self, shop_id):
        self.shop_id = shop_id

    def list_by_customer(self, customer_id, page=1, per_page=PER_PAGE_DEFAULT):
        return (
            CustomerLedger.query.filter_by(
                shop_id=self.shop_id, customer_id=customer_id
            )
            .order_by(
                CustomerLedger.transaction_date.desc(), CustomerLedger.id.desc()
            )
            .paginate(page=page, per_page=per_page, error_out=False)
        )

    def get_customer_balance(self, customer_id):
        entry = (
            CustomerLedger.query.filter_by(
                shop_id=self.shop_id, customer_id=customer_id
            )
            .order_by(
                CustomerLedger.transaction_date.desc(), CustomerLedger.id.desc()
            )
            .first()
        )
        if entry is None:
            return Decimal("0")
        return Decimal(str(entry.balance))

    def list_all(self, page=1, per_page=PER_PAGE_DEFAULT, customer_id=None, search=""):
        query = CustomerLedger.query.filter_by(shop_id=self.shop_id).order_by(
            CustomerLedger.transaction_date.desc(), CustomerLedger.id.desc()
        )

        if customer_id:
            query = query.filter_by(customer_id=customer_id)

        if search:
            like = f"%{search}%"
            query = query.join(Customer).filter(Customer.name.ilike(like))

        return query.paginate(page=page, per_page=per_page, error_out=False)

    def get_customer(self, customer_id):
        return Customer.query.filter_by(id=customer_id, shop_id=self.shop_id).first()

    def list_customers_with_balance(self):
        customers = (
            Customer.query.filter_by(shop_id=self.shop_id)
            .order_by(Customer.name.asc())
            .all()
        )
        results = []
        for customer in customers:
            balance = self.get_customer_balance(customer.id)
            results.append({"customer": customer, "balance": balance})
        return results
