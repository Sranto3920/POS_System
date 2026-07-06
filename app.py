from datetime import datetime

import os

import click
from flask import Flask, redirect, render_template, request, url_for
from sqlalchemy import inspect, text

from config import Config
from extensions import csrf, db, login_manager
from models.platform_user import PlatformUser
from models.shop import Shop
from models.user import User
from routes.auth import auth_bp
from routes.categories import categories_bp
from routes.customers import customers_bp
from routes.dashboard import dashboard_bp
from routes.exports import exports_bp
from routes.language import language_bp
from routes.ledger import ledger_bp
from routes.manager import manager_bp
from routes.payments import payments_bp
from routes.platform import platform_bp
from routes.owner_auth import owner_auth_bp
from routes.platform_auth import platform_auth_bp
from routes.pos import pos_bp
from routes.products import products_bp
from routes.profile import profile_bp
from routes.purchases import purchases_bp
from routes.reports import reports_bp
from routes.sales import sales_bp
from routes.suppliers import suppliers_bp
from routes.users import users_bp
from utils.formatters import format_currency
from utils.roles import Role


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    app.register_blueprint(platform_auth_bp)
    app.register_blueprint(owner_auth_bp)
    app.register_blueprint(platform_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(manager_bp)
    app.register_blueprint(pos_bp)
    app.register_blueprint(purchases_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(ledger_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(exports_bp)
    app.register_blueprint(language_bp)

    register_user_loader()
    register_language_handler(app)
    register_unauthorized_handler(app)
    register_error_handlers(app)
    register_cli(app)
    register_context_processors(app)

    return app


def register_language_handler(app):
    from flask import g

    from utils.i18n import get_lang, normalize_lang

    @app.before_request
    def set_request_language():
        g.lang = get_lang()

    @app.context_processor
    def inject_language():
        from utils.i18n import (
            format_date_locale,
            format_weekday_locale,
            get_all_packs,
            get_lang,
            t,
            translate_payment_method,
            translate_payment_status,
            translate_stock_status,
        )

        lang = get_lang()
        return {
            "t": t,
            "current_lang": lang,
            "i18n_packs": get_all_packs(),
            "format_date_locale": format_date_locale,
            "format_weekday_locale": format_weekday_locale,
            "translate_payment_method": translate_payment_method,
            "translate_payment_status": translate_payment_status,
            "translate_stock_status": translate_stock_status,
        }


def register_context_processors(app):
    @app.context_processor
    def inject_globals():
        from flask_login import current_user

        from models.platform_user import PlatformUser

        current_shop = None
        if current_user.is_authenticated and not isinstance(current_user, PlatformUser):
            current_shop = db.session.get(Shop, current_user.shop_id)

        return {
            "format_currency": format_currency,
            "now": datetime.now,
            "current_shop": current_shop,
            "shop_display_name": app.config.get("SHOP_DISPLAY_NAME", "POS System"),
        }


def register_user_loader():
    @login_manager.user_loader
    def load_user(user_id):
        if not user_id:
            return None

        user_id = str(user_id)

        if user_id.startswith("p:"):
            return db.session.get(PlatformUser, int(user_id[2:]))

        if user_id.startswith("s:"):
            return db.session.get(User, int(user_id[2:]))

        # Backward compatibility for sessions created before prefixed IDs.
        return db.session.get(User, int(user_id))


def register_unauthorized_handler(app):
    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith("/platform"):
            return redirect(url_for("owner_auth.login", next=request.url))
        return redirect(url_for("auth.login", next=request.url))


def register_error_handlers(app):
    @app.errorhandler(401)
    def unauthorized(error):
        return render_template("errors/401.html"), 401

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("errors/500.html"), 500


def ensure_schema():
    """Create new tables and add missing columns for multi-tenant platform support."""
    db.create_all()
    ensure_user_columns()
    ensure_shop_columns()
    ensure_product_columns()
    ensure_sale_columns()
    ensure_sale_detail_columns()
    ensure_payment_columns()
    ensure_daily_cash_columns()


def ensure_user_columns():
    inspector = inspect(db.engine)
    if "Users" not in inspector.get_table_names():
        return

    columns = {column["name"].lower() for column in inspector.get_columns("Users")}

    if "is_active" not in columns:
        db.session.execute(
            text(
                "ALTER TABLE Users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE"
            )
        )

    if "last_login" not in columns:
        db.session.execute(text("ALTER TABLE Users ADD COLUMN last_login DATETIME NULL"))

    if "preferred_language" not in columns:
        db.session.execute(
            text(
                "ALTER TABLE Users ADD COLUMN preferred_language VARCHAR(5) NOT NULL DEFAULT 'bn'"
            )
        )

    if "login_password" not in columns:
        db.session.execute(
            text("ALTER TABLE Users ADD COLUMN login_password VARCHAR(255) NULL")
        )
        db.session.commit()

    from models.user import User
    from sqlalchemy import func
    from utils.roles import Role

    users_missing_password = User.query.filter(User.login_password.is_(None)).all()
    for user in users_missing_password:
        stored = user.password_hash or ""
        if stored and not stored.startswith(("pbkdf2:", "scrypt:")):
            user.login_password = stored
    db.session.commit()


def ensure_shop_columns():
    inspector = inspect(db.engine)
    if "Shops" not in inspector.get_table_names():
        return

    columns = {column["name"].lower() for column in inspector.get_columns("Shops")}

    if "is_active" not in columns:
        db.session.execute(
            text("ALTER TABLE Shops ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE")
        )
        db.session.commit()


def ensure_product_columns():
    inspector = inspect(db.engine)
    if "Products" not in inspector.get_table_names():
        return

    columns = {column["name"].lower() for column in inspector.get_columns("Products")}

    if "barcode" not in columns:
        db.session.execute(text("ALTER TABLE Products ADD COLUMN barcode VARCHAR(50) NULL"))

    if "sku" not in columns:
        db.session.execute(text("ALTER TABLE Products ADD COLUMN sku VARCHAR(50) NULL"))

    if "minimum_selling_price" not in columns:
        db.session.execute(
            text("ALTER TABLE Products ADD COLUMN minimum_selling_price DECIMAL(10,2) NULL")
        )

    if "market_price" not in columns:
        db.session.execute(
            text("ALTER TABLE Products ADD COLUMN market_price DECIMAL(10,2) NULL")
        )

    db.session.execute(
        text(
            """
            UPDATE Products
            SET market_price = default_selling_price
            WHERE market_price IS NULL
            """
        )
    )
    db.session.execute(
        text(
            """
            UPDATE Products
            SET minimum_selling_price = cost_price
            WHERE minimum_selling_price IS NULL
            """
        )
    )
    db.session.commit()


def ensure_sale_columns():
    inspector = inspect(db.engine)
    if "Sales" not in inspector.get_table_names():
        return

    columns = {column["name"].lower() for column in inspector.get_columns("Sales")}

    if "paid_amount" not in columns:
        db.session.execute(
            text("ALTER TABLE Sales ADD COLUMN paid_amount DECIMAL(10,2) NOT NULL DEFAULT 0")
        )

    if "due_amount" not in columns:
        db.session.execute(
            text("ALTER TABLE Sales ADD COLUMN due_amount DECIMAL(10,2) NOT NULL DEFAULT 0")
        )

    if "payment_status" not in columns:
        db.session.execute(
            text(
                "ALTER TABLE Sales ADD COLUMN payment_status VARCHAR(20) NOT NULL DEFAULT 'Paid'"
            )
        )

    db.session.execute(
        text(
            """
            UPDATE Sales s
            LEFT JOIN (
                SELECT sale_id, COALESCE(SUM(paid_amount), 0) AS total_paid
                FROM Payments
                GROUP BY sale_id
            ) p ON p.sale_id = s.sale_id
            SET
              s.paid_amount = COALESCE(p.total_paid, s.total_amount),
              s.due_amount = GREATEST(s.total_amount - COALESCE(p.total_paid, s.total_amount), 0),
              s.payment_status = CASE
                WHEN COALESCE(p.total_paid, s.total_amount) >= s.total_amount THEN 'Paid'
                WHEN COALESCE(p.total_paid, 0) <= 0 THEN 'Due'
                ELSE 'Partially Paid'
              END
            WHERE s.paid_amount = 0 AND s.due_amount = 0
            """
        )
    )
    db.session.commit()


def ensure_sale_detail_columns():
    inspector = inspect(db.engine)
    if "Sale_Details" not in inspector.get_table_names():
        return

    columns = {column["name"].lower() for column in inspector.get_columns("Sale_Details")}

    if "discount" not in columns:
        db.session.execute(
            text(
                "ALTER TABLE Sale_Details ADD COLUMN discount DECIMAL(10,2) NOT NULL DEFAULT 0"
            )
        )
        db.session.commit()

    subtotal_col = next(
        (col for col in inspector.get_columns("Sale_Details") if col["name"].lower() == "subtotal"),
        None,
    )
    if subtotal_col and "discount" in {
        column["name"].lower() for column in inspector.get_columns("Sale_Details")
    }:
        generation = (subtotal_col.get("computed") or {}).get("sqltext", "")
        if "discount" not in str(generation).lower():
            db.session.execute(
                text(
                    """
                    ALTER TABLE Sale_Details
                    MODIFY subtotal DECIMAL(10,2)
                    GENERATED ALWAYS AS ((quantity * selling_price) - discount) STORED
                    """
                )
            )
            db.session.commit()


def ensure_payment_columns():
    inspector = inspect(db.engine)
    if "Payments" not in inspector.get_table_names():
        return

    columns = {column["name"].lower() for column in inspector.get_columns("Payments")}

    if "shop_id" not in columns:
        db.session.execute(
            text("ALTER TABLE Payments ADD COLUMN shop_id INT NULL")
        )

    if "user_id" not in columns:
        db.session.execute(
            text("ALTER TABLE Payments ADD COLUMN user_id INT NULL")
        )

    if "payment_type" not in columns:
        db.session.execute(
            text(
                "ALTER TABLE Payments ADD COLUMN payment_type VARCHAR(20) NOT NULL DEFAULT 'sale'"
            )
        )

    db.session.commit()


def ensure_daily_cash_columns():
    inspector = inspect(db.engine)
    if "DailyCash" not in inspector.get_table_names():
        return

    columns = {column["name"].lower() for column in inspector.get_columns("DailyCash")}

    if "carry_forward_cash" not in columns:
        db.session.execute(
            text(
                "ALTER TABLE DailyCash ADD COLUMN carry_forward_cash DECIMAL(10,2) NOT NULL DEFAULT 0"
            )
        )
        db.session.commit()


def register_cli(app):
    @app.cli.command("init-db")
    @click.option("--seed", is_flag=True, help="Seed demo shop users.")
    @click.option(
        "--seed-platform",
        is_flag=True,
        help="Create the platform owner account.",
    )
    @click.option("--hash-passwords", is_flag=True, help="Hash legacy plaintext passwords.")
    def init_db(seed, seed_platform, hash_passwords):
        """Create tables and apply schema updates."""
        ensure_schema()
        click.echo("Database ready.")

        if hash_passwords:
            hash_legacy_passwords()

        if seed_platform:
            seed_platform_owner()

        if seed:
            seed_users()

    @app.cli.command("set-password")
    @click.argument("email")
    @click.argument("password")
    def set_password(email, password):
        """Set a hashed password for a shop user."""
        user = User.query.filter_by(email=email.strip().lower()).first()
        if user is None:
            click.echo(f"User not found: {email}")
            return

        user.set_password(password)
        db.session.commit()
        click.echo(f"Password updated for {user.email}.")


def seed_platform_owner():
    import os

    email = os.getenv("PLATFORM_OWNER_EMAIL", "owner@posplatform.com").strip().lower()
    password = os.getenv("PLATFORM_OWNER_PASSWORD")
    if not password:
        click.echo("Set PLATFORM_OWNER_PASSWORD in .env before seeding platform owner.")
        return
    name = os.getenv("PLATFORM_OWNER_NAME", "Platform Owner")

    if PlatformUser.query.filter_by(email=email).first():
        click.echo("Platform owner already exists — skipped.")
        return

    owner = PlatformUser(full_name=name, email=email, is_active=True)
    owner.set_password(password)
    db.session.add(owner)
    db.session.commit()
    click.echo(f"Platform owner created: {email}")


def hash_legacy_passwords():
    upgraded = 0
    for user in User.query.all():
        stored = user.password_hash or ""
        if stored.startswith(("pbkdf2:", "scrypt:")):
            continue
        user.set_password(stored)
        upgraded += 1

    if upgraded:
        db.session.commit()
        click.echo(f"Hashed {upgraded} legacy password(s).")
    else:
        click.echo("No legacy plaintext passwords found.")


def seed_users():
    import os

    defaults = [
        {
            "email": os.getenv("ADMIN_EMAIL", "admin@pos.local"),
            "password": os.getenv("ADMIN_PASSWORD"),
            "full_name": "System Administrator",
            "role": "Admin",
        },
        {
            "email": os.getenv("MANAGER_EMAIL", "manager@pos.local"),
            "password": os.getenv("MANAGER_PASSWORD"),
            "full_name": "Store Manager",
            "role": "Manager",
        },
        {
            "email": os.getenv("CASHIER_EMAIL", "cashier@pos.local"),
            "password": os.getenv("CASHIER_PASSWORD"),
            "full_name": "Front Desk Cashier",
            "role": "Cashier",
        },
    ]

    created = 0
    for entry in defaults:
        if not entry["password"]:
            click.echo(f'Skip {entry["email"]}: set password env var before --seed.')
            continue
        email = entry["email"].strip().lower()
        if User.query.filter_by(email=email).first():
            continue

        user = User(
            email=email,
            full_name=entry["full_name"],
            role=entry["role"],
            shop_id=1,
        )
        user.set_password(entry["password"])
        db.session.add(user)
        created += 1

    if created:
        db.session.commit()
        click.echo(f"Seeded {created} user(s).")
    else:
        click.echo("Seed users already exist — skipped.")


app = create_app()

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=debug)
