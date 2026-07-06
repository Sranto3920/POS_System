"""
End-to-end workflow tests for the POS system.
Run: python -m pytest tests/test_workflow.py -v
Or:  python tests/test_workflow.py
"""

import os
import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app, db, ensure_schema
from flask_login import login_user
from models.category import Category
from models.customer import Customer
from models.platform_user import PlatformUser
from models.product import Product
from models.shop import Shop
from models.supplier import Supplier
from models.user import User
from services.payment_service import PaymentService
from services.purchase_service import PurchaseService
from services.sale_service import SaleService, MIN_PRICE_ERROR


class WorkflowTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app
        cls.app.config["TESTING"] = True
        cls.app.config["WTF_CSRF_ENABLED"] = False
        cls.client = cls.app.test_client()
        cls.ctx = cls.app.app_context()
        cls.ctx.push()
        ensure_schema()

    @classmethod
    def tearDownClass(cls):
        cls.ctx.pop()

    def _get_shop_admin(self):
        user = User.query.filter_by(role="Admin").first()
        if user is None:
            user = User.query.first()
        self.assertIsNotNone(user, "No shop user found. Run: flask init-db --seed")
        return user

    def _login_shop(self, user):
        with self.app.test_request_context():
            login_user(user)
            with self.client.session_transaction() as sess:
                sess["_user_id"] = user.get_id()
                sess["_fresh"] = True

    def test_01_login_page_loads(self):
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"auth-card", response.data)

    def test_02_platform_login_page_loads(self):
        response = self.client.get("/owner/login")
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/platform/login")
        self.assertEqual(response.status_code, 302)

    def test_03_dashboard_requires_auth(self):
        response = self.client.get("/", follow_redirects=False)
        self.assertEqual(response.status_code, 302)

    def test_04_dashboard_authenticated(self):
        user = self._get_shop_admin()
        self._login_shop(user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_05_product_search_api(self):
        user = self._get_shop_admin()
        self._login_shop(user)
        response = self.client.get("/sales/api/products/search?q=a")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json(), list)

    def test_06_new_sale_page(self):
        user = self._get_shop_admin()
        self._login_shop(user)
        response = self.client.get("/sales/new")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Search Product", response.data)

    def test_07_minimum_price_validation(self):
        user = self._get_shop_admin()
        shop_id = user.shop_id
        product = Product.query.filter_by(shop_id=shop_id).first()
        customer = Customer.query.filter(
            Customer.shop_id == shop_id,
            Customer.name != "Walk-in Customer",
        ).first()
        self.assertIsNotNone(product)
        self.assertIsNotNone(customer)

        product.minimum_selling_price = Decimal("80")
        product.market_price = Decimal("100")
        db.session.commit()

        service = SaleService(shop_id)
        with self.assertRaises(ValueError) as ctx:
            service.create_sale(
                shop_id,
                user.id,
                customer.id,
                [
                    {
                        "product_id": product.id,
                        "quantity": 1,
                        "selling_price": Decimal("50"),
                        "discount": Decimal("0"),
                    }
                ],
                "Cash",
                Decimal("50"),
            )
        self.assertIn(MIN_PRICE_ERROR, str(ctx.exception))

    def test_08_partial_payment_sale(self):
        user = self._get_shop_admin()
        shop_id = user.shop_id
        product = Product.query.filter_by(shop_id=shop_id).filter(
            Product.stock_quantity > 0
        ).first()
        customer = Customer.query.filter(
            Customer.shop_id == shop_id,
            Customer.name != "Walk-in Customer",
        ).first()
        self.assertIsNotNone(product)
        self.assertIsNotNone(customer)

        stock_before = product.stock_quantity
        product.minimum_selling_price = Decimal("1")
        db.session.commit()

        service = SaleService(shop_id)
        sale = service.create_sale(
            shop_id,
            user.id,
            customer.id,
            [
                {
                    "product_id": product.id,
                    "quantity": 1,
                    "selling_price": product.effective_market_price,
                    "discount": Decimal("0"),
                }
            ],
            "Cash",
            Decimal("1"),
        )
        self.assertEqual(sale.payment_status, "Partially Paid")
        self.assertGreater(Decimal(str(sale.due_amount)), 0)

        db.session.refresh(product)
        self.assertEqual(product.stock_quantity, stock_before - 1)

    def test_09_collect_due_page(self):
        user = self._get_shop_admin()
        self._login_shop(user)
        response = self.client.get("/payments/collect-due")
        self.assertEqual(response.status_code, 200)

    def test_10_reports_index(self):
        user = self._get_shop_admin()
        self._login_shop(user)
        response = self.client.get("/reports/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Due Customers", response.data)

    def test_11_invalid_sale_rejected(self):
        user = self._get_shop_admin()
        shop_id = user.shop_id
        walkin = SaleService(shop_id).get_or_create_walkin_customer(shop_id)
        product = Product.query.filter_by(shop_id=shop_id).first()
        service = SaleService(shop_id)

        with self.assertRaises(ValueError) as ctx:
            service.create_sale(
                shop_id,
                user.id,
                walkin.id,
                [
                    {
                        "product_id": product.id,
                        "quantity": 1,
                        "selling_price": Decimal("100"),
                        "discount": Decimal("0"),
                    }
                ],
                "Cash",
                Decimal("50"),
            )
        self.assertIn("registered customer", str(ctx.exception).lower())

    def test_12_paid_exceeds_total_rejected(self):
        user = self._get_shop_admin()
        shop_id = user.shop_id
        customer = Customer.query.filter(
            Customer.shop_id == shop_id,
            Customer.name != "Walk-in Customer",
        ).first()
        product = Product.query.filter_by(shop_id=shop_id).filter(
            Product.stock_quantity > 0
        ).first()
        service = SaleService(shop_id)

        with self.assertRaises(ValueError):
            service.create_sale(
                shop_id,
                user.id,
                customer.id,
                [
                    {
                        "product_id": product.id,
                        "quantity": 1,
                        "selling_price": Decimal("10"),
                        "discount": Decimal("0"),
                    }
                ],
                "Cash",
                Decimal("99999"),
            )


if __name__ == "__main__":
    unittest.main()
