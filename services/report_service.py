"""
ReportService — shop-scoped business reports.
"""

from sqlalchemy import text

from extensions import db
from utils.formatters import LOW_STOCK_THRESHOLD


class ReportService:
    @staticmethod
    def daily_sales(shop_id, date):
        rows = db.session.execute(
            text(
                """
                SELECT
                  s.sale_id,
                  s.sale_date,
                  s.total_amount,
                  COALESCE(c.customer_name, 'Walk-in') AS customer_name,
                  u.name AS cashier_name
                FROM Sales s
                LEFT JOIN Customers c
                  ON s.customer_id = c.customer_id AND c.shop_id = :shop_id
                LEFT JOIN Users u
                  ON s.user_id = u.user_id AND u.shop_id = :shop_id
                WHERE s.shop_id = :shop_id
                  AND DATE(s.sale_date) = :report_date
                ORDER BY s.sale_date DESC, s.sale_id DESC
                """
            ),
            {"shop_id": shop_id, "report_date": date},
        ).mappings()

        items = [dict(row) for row in rows]
        total_amount = sum(float(row["total_amount"] or 0) for row in items)

        return {
            "date": date,
            "sale_count": len(items),
            "total_amount": total_amount,
            "rows": items,
        }

    @staticmethod
    def monthly_sales(shop_id, year, month):
        summary_rows = db.session.execute(
            text(
                """
                SELECT
                  DATE(s.sale_date) AS sale_day,
                  COUNT(*) AS sale_count,
                  COALESCE(SUM(s.total_amount), 0) AS day_total
                FROM Sales s
                WHERE s.shop_id = :shop_id
                  AND YEAR(s.sale_date) = :year
                  AND MONTH(s.sale_date) = :month
                GROUP BY DATE(s.sale_date)
                ORDER BY sale_day ASC
                """
            ),
            {"shop_id": shop_id, "year": year, "month": month},
        ).mappings()

        daily = [dict(row) for row in summary_rows]

        detail_rows = db.session.execute(
            text(
                """
                SELECT
                  s.sale_id,
                  s.sale_date,
                  s.total_amount,
                  COALESCE(c.customer_name, 'Walk-in') AS customer_name,
                  u.name AS cashier_name
                FROM Sales s
                LEFT JOIN Customers c
                  ON s.customer_id = c.customer_id AND c.shop_id = :shop_id
                LEFT JOIN Users u
                  ON s.user_id = u.user_id AND u.shop_id = :shop_id
                WHERE s.shop_id = :shop_id
                  AND YEAR(s.sale_date) = :year
                  AND MONTH(s.sale_date) = :month
                ORDER BY s.sale_date DESC, s.sale_id DESC
                """
            ),
            {"shop_id": shop_id, "year": year, "month": month},
        ).mappings()

        sales = [dict(row) for row in detail_rows]
        total_amount = sum(float(row["total_amount"] or 0) for row in sales)

        return {
            "year": year,
            "month": month,
            "sale_count": len(sales),
            "total_amount": total_amount,
            "daily": daily,
            "rows": sales,
        }

    @staticmethod
    def purchase_report(shop_id, date_from=None, date_to=None):
        query = """
            SELECT
              p.purchase_id,
              p.purchase_date,
              p.total_amount,
              s.supplier_name,
              u.name AS recorded_by
            FROM Purchases p
            LEFT JOIN Suppliers s
              ON p.supplier_id = s.supplier_id AND s.shop_id = :shop_id
            LEFT JOIN Users u
              ON p.user_id = u.user_id AND u.shop_id = :shop_id
            WHERE p.shop_id = :shop_id
        """
        params = {"shop_id": shop_id}

        if date_from:
            query += " AND DATE(p.purchase_date) >= :date_from"
            params["date_from"] = date_from
        if date_to:
            query += " AND DATE(p.purchase_date) <= :date_to"
            params["date_to"] = date_to

        query += " ORDER BY p.purchase_date DESC, p.purchase_id DESC"

        rows = db.session.execute(text(query), params).mappings()
        items = [dict(row) for row in rows]
        total_amount = sum(float(row["total_amount"] or 0) for row in items)

        return {
            "date_from": date_from,
            "date_to": date_to,
            "purchase_count": len(items),
            "total_amount": total_amount,
            "rows": items,
        }

    @staticmethod
    def customer_report(shop_id):
        rows = db.session.execute(
            text(
                """
                SELECT
                  c.customer_id,
                  c.customer_name,
                  c.phone,
                  c.email,
                  COUNT(s.sale_id) AS sale_count,
                  COALESCE(SUM(s.total_amount), 0) AS total_spent
                FROM Customers c
                LEFT JOIN Sales s
                  ON s.customer_id = c.customer_id AND s.shop_id = :shop_id
                WHERE c.shop_id = :shop_id
                GROUP BY c.customer_id, c.customer_name, c.phone, c.email
                ORDER BY total_spent DESC, c.customer_name ASC
                """
            ),
            {"shop_id": shop_id},
        ).mappings()

        items = [dict(row) for row in rows]
        return {
            "customer_count": len(items),
            "total_spent": sum(float(row["total_spent"] or 0) for row in items),
            "rows": items,
        }

    @staticmethod
    def supplier_report(shop_id):
        rows = db.session.execute(
            text(
                """
                SELECT
                  s.supplier_id,
                  s.supplier_name,
                  s.phone,
                  s.email,
                  COUNT(p.purchase_id) AS purchase_count,
                  COALESCE(SUM(p.total_amount), 0) AS total_purchased
                FROM Suppliers s
                LEFT JOIN Purchases p
                  ON p.supplier_id = s.supplier_id AND p.shop_id = :shop_id
                WHERE s.shop_id = :shop_id
                GROUP BY s.supplier_id, s.supplier_name, s.phone, s.email
                ORDER BY total_purchased DESC, s.supplier_name ASC
                """
            ),
            {"shop_id": shop_id},
        ).mappings()

        items = [dict(row) for row in rows]
        return {
            "supplier_count": len(items),
            "total_purchased": sum(float(row["total_purchased"] or 0) for row in items),
            "rows": items,
        }

    @staticmethod
    def product_report(shop_id):
        rows = db.session.execute(
            text(
                """
                SELECT
                  p.product_id,
                  p.product_name,
                  c.category_name,
                  sup.supplier_name,
                  p.cost_price,
                  p.default_selling_price,
                  p.stock_quantity,
                  p.expiry_date
                FROM Products p
                LEFT JOIN Categories c
                  ON p.category_id = c.category_id AND c.shop_id = :shop_id
                LEFT JOIN Suppliers sup
                  ON p.supplier_id = sup.supplier_id AND sup.shop_id = :shop_id
                WHERE p.shop_id = :shop_id
                ORDER BY p.product_name ASC
                """
            ),
            {"shop_id": shop_id},
        ).mappings()

        items = [dict(row) for row in rows]
        return {
            "product_count": len(items),
            "rows": items,
        }

    @staticmethod
    def stock_report(shop_id):
        rows = db.session.execute(
            text(
                """
                SELECT
                  p.product_id,
                  p.product_name,
                  c.category_name,
                  p.stock_quantity,
                  p.cost_price,
                  p.default_selling_price,
                  (p.stock_quantity * p.cost_price) AS stock_value
                FROM Products p
                LEFT JOIN Categories c
                  ON p.category_id = c.category_id AND c.shop_id = :shop_id
                WHERE p.shop_id = :shop_id
                ORDER BY p.product_name ASC
                """
            ),
            {"shop_id": shop_id},
        ).mappings()

        items = [dict(row) for row in rows]
        total_value = sum(float(row["stock_value"] or 0) for row in items)
        total_units = sum(int(row["stock_quantity"] or 0) for row in items)

        return {
            "product_count": len(items),
            "total_units": total_units,
            "total_value": total_value,
            "rows": items,
        }

    @staticmethod
    def low_stock_report(shop_id):
        rows = db.session.execute(
            text(
                """
                SELECT
                  p.product_id,
                  p.product_name,
                  c.category_name,
                  p.stock_quantity,
                  p.default_selling_price
                FROM Products p
                LEFT JOIN Categories c
                  ON p.category_id = c.category_id AND c.shop_id = :shop_id
                WHERE p.shop_id = :shop_id
                  AND p.stock_quantity <= :threshold
                ORDER BY p.stock_quantity ASC, p.product_name ASC
                """
            ),
            {"shop_id": shop_id, "threshold": LOW_STOCK_THRESHOLD},
        ).mappings()

        items = [dict(row) for row in rows]
        return {
            "threshold": LOW_STOCK_THRESHOLD,
            "product_count": len(items),
            "rows": items,
        }

    @staticmethod
    def due_customers_report(shop_id):
        rows = db.session.execute(
            text(
                """
                SELECT
                  c.customer_id,
                  c.customer_name,
                  c.phone,
                  COUNT(s.sale_id) AS due_invoice_count,
                  COALESCE(SUM(s.due_amount), 0) AS total_due
                FROM Customers c
                INNER JOIN Sales s
                  ON s.customer_id = c.customer_id
                 AND s.shop_id = :shop_id
                 AND s.due_amount > 0
                WHERE c.shop_id = :shop_id
                GROUP BY c.customer_id, c.customer_name, c.phone
                ORDER BY total_due DESC, c.customer_name ASC
                """
            ),
            {"shop_id": shop_id},
        ).mappings()

        items = [dict(row) for row in rows]
        return {
            "customer_count": len(items),
            "total_due": sum(float(row["total_due"] or 0) for row in items),
            "rows": items,
        }

    @staticmethod
    def outstanding_due_report(shop_id):
        rows = db.session.execute(
            text(
                """
                SELECT
                  s.sale_id,
                  s.sale_date,
                  c.customer_name,
                  s.total_amount,
                  s.paid_amount,
                  s.due_amount,
                  s.payment_status
                FROM Sales s
                INNER JOIN Customers c
                  ON s.customer_id = c.customer_id AND c.shop_id = :shop_id
                WHERE s.shop_id = :shop_id
                  AND s.due_amount > 0
                ORDER BY s.sale_date DESC, s.sale_id DESC
                """
            ),
            {"shop_id": shop_id},
        ).mappings()

        items = [dict(row) for row in rows]
        return {
            "invoice_count": len(items),
            "total_due": sum(float(row["due_amount"] or 0) for row in items),
            "rows": items,
        }

    @staticmethod
    def due_collection_report(shop_id, date_from=None, date_to=None):
        query = """
            SELECT
              p.payment_id,
              p.payment_date,
              s.sale_id,
              c.customer_name,
              p.payment_method,
              p.paid_amount
            FROM Payments p
            INNER JOIN Sales s ON p.sale_id = s.sale_id AND s.shop_id = :shop_id
            INNER JOIN Customers c ON s.customer_id = c.customer_id AND c.shop_id = :shop_id
            WHERE p.payment_id > (
              SELECT MIN(p2.payment_id)
              FROM Payments p2
              WHERE p2.sale_id = s.sale_id
            )
        """
        params = {"shop_id": shop_id}

        if date_from:
            query += " AND DATE(p.payment_date) >= :date_from"
            params["date_from"] = date_from
        if date_to:
            query += " AND DATE(p.payment_date) <= :date_to"
            params["date_to"] = date_to

        query += " ORDER BY p.payment_date DESC, p.payment_id DESC"

        rows = db.session.execute(text(query), params).mappings()
        items = [dict(row) for row in rows]
        return {
            "payment_count": len(items),
            "total_collected": sum(float(row["paid_amount"] or 0) for row in items),
            "rows": items,
        }

    @staticmethod
    def paid_vs_due_sales_report(shop_id, date_from=None, date_to=None):
        query = """
            SELECT
              s.sale_id,
              s.sale_date,
              c.customer_name,
              s.total_amount,
              s.paid_amount,
              s.due_amount,
              s.payment_status
            FROM Sales s
            LEFT JOIN Customers c
              ON s.customer_id = c.customer_id AND c.shop_id = :shop_id
            WHERE s.shop_id = :shop_id
        """
        params = {"shop_id": shop_id}

        if date_from:
            query += " AND DATE(s.sale_date) >= :date_from"
            params["date_from"] = date_from
        if date_to:
            query += " AND DATE(s.sale_date) <= :date_to"
            params["date_to"] = date_to

        query += " ORDER BY s.sale_date DESC, s.sale_id DESC"

        rows = db.session.execute(text(query), params).mappings()
        items = [dict(row) for row in rows]
        paid_total = sum(float(row["paid_amount"] or 0) for row in items)
        due_total = sum(float(row["due_amount"] or 0) for row in items)

        return {
            "sale_count": len(items),
            "paid_total": paid_total,
            "due_total": due_total,
            "rows": items,
        }
