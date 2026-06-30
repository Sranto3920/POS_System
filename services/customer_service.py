from decimal import Decimal

from sqlalchemy import or_

from extensions import db
from models.customer import Customer
from models.ledger import CustomerLedger
from models.sale import Sale
from services.sale_service import SaleService
from utils.pagination import PER_PAGE_DEFAULT


class CustomerService:
    @staticmethod
    def list(shop_id, search="", page=1, per_page=PER_PAGE_DEFAULT):
        query = Customer.query.filter_by(shop_id=shop_id)

        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    Customer.name.ilike(term),
                    Customer.phone.ilike(term),
                    Customer.email.ilike(term),
                    Customer.address.ilike(term),
                )
            )

        return query.order_by(Customer.name.asc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def get(shop_id, customer_id):
        return Customer.query.filter_by(shop_id=shop_id, id=customer_id).first()

    @staticmethod
    def get_profile_stats(shop_id, customer_id):
        customer = Customer.query.filter_by(shop_id=shop_id, id=customer_id).first()
        if customer is None:
            return None

        sale_service = SaleService(shop_id)
        sales = Sale.query.filter_by(shop_id=shop_id, customer_id=customer_id).all()

        total_purchases = sum(Decimal(str(s.total_amount or 0)) for s in sales)
        total_paid = Decimal("0")
        total_due = Decimal("0")
        due_invoice_count = 0

        for sale in sales:
            paid = sale_service.get_sale_paid_total(sale)
            due = sale_service.get_sale_balance_due(sale)
            total_paid += paid
            total_due += due
            if due > 0:
                due_invoice_count += 1

        ledger_entry = (
            CustomerLedger.query.filter_by(shop_id=shop_id, customer_id=customer_id)
            .order_by(CustomerLedger.transaction_date.desc(), CustomerLedger.id.desc())
            .first()
        )
        ledger_balance = (
            Decimal(str(ledger_entry.balance)) if ledger_entry else Decimal("0")
        )

        return {
            "customer": customer,
            "total_purchases": total_purchases,
            "total_paid": total_paid,
            "total_due": total_due,
            "due_invoice_count": due_invoice_count,
            "ledger_balance": ledger_balance,
            "sales": sales,
            "sale_service": sale_service,
        }

    @staticmethod
    def create(shop_id, form):
        customer = Customer(
            shop_id=shop_id,
            name=form.name.data.strip(),
            phone=(form.phone.data or "").strip() or None,
            email=(form.email.data or "").strip().lower() or None,
            address=(form.address.data or "").strip() or None,
        )
        db.session.add(customer)
        db.session.commit()
        return customer

    @staticmethod
    def update(customer, form):
        customer.name = form.name.data.strip()
        customer.phone = (form.phone.data or "").strip() or None
        customer.email = (form.email.data or "").strip().lower() or None
        customer.address = (form.address.data or "").strip() or None
        db.session.commit()
        return customer

    @staticmethod
    def delete(customer):
        if Sale.query.filter_by(customer_id=customer.id).first():
            return False, "Cannot delete customer with existing sales."

        db.session.delete(customer)
        db.session.commit()
        return True, f'Customer "{customer.name}" deleted successfully.'
