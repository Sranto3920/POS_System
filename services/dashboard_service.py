from sqlalchemy import text

from extensions import db
from utils.formatters import LOW_STOCK_THRESHOLD


class DashboardService:
    """Shop-scoped dashboard queries. Every method filters by shop_id."""

    def __init__(self, shop_id):
        self.shop_id = shop_id

    def get_stats(self):
        return {
            "total_products": self._scalar(
                "SELECT COUNT(*) FROM Products WHERE shop_id = :shop_id",
            ),
            "total_categories": self._scalar(
                "SELECT COUNT(*) FROM Categories WHERE shop_id = :shop_id",
            ),
            "total_customers": self._scalar(
                "SELECT COUNT(*) FROM Customers WHERE shop_id = :shop_id",
            ),
            "total_suppliers": self._scalar(
                "SELECT COUNT(*) FROM Suppliers WHERE shop_id = :shop_id",
            ),
            "today_sales_count": self._scalar(
                """
                SELECT COUNT(*) FROM Sales
                WHERE shop_id = :shop_id AND DATE(sale_date) = CURDATE()
                """,
            ),
            "today_sales_amount": self._scalar(
                """
                SELECT COALESCE(SUM(total_amount), 0) FROM Sales
                WHERE shop_id = :shop_id AND DATE(sale_date) = CURDATE()
                """,
            ),
            "monthly_revenue": self._scalar(
                """
                SELECT COALESCE(SUM(total_amount), 0) FROM Sales
                WHERE shop_id = :shop_id
                  AND YEAR(sale_date) = YEAR(CURDATE())
                  AND MONTH(sale_date) = MONTH(CURDATE())
                """,
            ),
            "low_stock_count": self._scalar(
                """
                SELECT COUNT(*) FROM Products
                WHERE shop_id = :shop_id AND stock_quantity <= :threshold
                """,
                threshold=LOW_STOCK_THRESHOLD,
            ),
        }

    def get_recent_sales(self, limit=10):
        rows = db.session.execute(
            text(
                """
                SELECT
                  s.sale_id,
                  s.sale_date,
                  s.total_amount,
                  COALESCE(c.customer_name, 'Walk-in Customer') AS customer_name,
                  u.name AS cashier_name
                FROM Sales s
                LEFT JOIN Customers c
                  ON s.customer_id = c.customer_id AND c.shop_id = :shop_id
                LEFT JOIN Users u
                  ON s.user_id = u.user_id AND u.shop_id = :shop_id
                WHERE s.shop_id = :shop_id
                ORDER BY s.sale_date DESC, s.sale_id DESC
                LIMIT :limit
                """
            ),
            {"shop_id": self.shop_id, "limit": limit},
        ).mappings()

        return [dict(row) for row in rows]

    def get_low_stock_products(self, limit=10):
        rows = db.session.execute(
            text(
                """
                SELECT
                  p.product_id,
                  p.product_name,
                  p.stock_quantity,
                  c.category_name
                FROM Products p
                LEFT JOIN Categories c
                  ON p.category_id = c.category_id AND c.shop_id = :shop_id
                WHERE p.shop_id = :shop_id
                  AND p.stock_quantity <= :threshold
                ORDER BY p.stock_quantity ASC, p.product_name ASC
                LIMIT :limit
                """
            ),
            {
                "shop_id": self.shop_id,
                "threshold": LOW_STOCK_THRESHOLD,
                "limit": limit,
            },
        ).mappings()

        return [dict(row) for row in rows]

    def _scalar(self, query, **extra):
        params = {"shop_id": self.shop_id, **extra}
        return db.session.execute(text(query), params).scalar() or 0
