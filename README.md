# POS Inventory Management System

A multi-tenant **Point of Sale (POS)** web application for small shops and retail businesses. Built with Flask and MySQL, it supports inventory, sales, purchases, customer due tracking (Halkhata), and business reports.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)

## Demo

> **Live URL:** _Add after deployment, e.g. `https://your-pos-app.onrender.com`_

| Portal | URL | Role |
|--------|-----|------|
| Platform Owner | `/platform/login` | Creates & manages shops |
| Shop Staff | `/login` | Admin, Manager, Cashier |

## Features

### Platform (Multi-tenant)
- Platform owner dashboard to create and manage shops
- Each shop is fully isolated by `shop_id`

### Inventory
- Categories, products (barcode, SKU), suppliers
- Stock tracking with low-stock alerts
- Purchase orders that increase stock

### Sales (POS)
- Product search by name, barcode, or SKU
- Editable market price and line discounts
- Hidden minimum selling price (admin only, enforced at checkout)
- Partial payments / Halkhata (due) support
- Walk-in and registered customers

### Payments & Ledger
- Collect due payments per invoice
- Customer ledger and profile with due history
- Payment status: Paid / Partially Paid / Due

### Reports & Export
- Daily & monthly sales
- Stock, purchases, customers, suppliers
- Due customers, outstanding due, due collection, paid vs due
- Excel export

### Roles
| Role | Access |
|------|--------|
| **Admin** | Full access, minimum price, user management |
| **Manager** | Inventory, sales, reports, ledger |
| **Cashier** | Sales, collect due, no minimum price visibility |

## Tech Stack

- **Backend:** Python, Flask, SQLAlchemy, Flask-Login, Flask-WTF
- **Database:** MySQL 8+
- **Frontend:** Jinja2, Bootstrap 5, vanilla JavaScript
- **Production:** Gunicorn, Render / Railway ready

## Project Structure

```
POS_System/
├── app.py              # Application factory & CLI
├── wsgi.py             # Production WSGI entry
├── config.py           # Environment-based config
├── models/             # SQLAlchemy models
├── routes/             # Flask blueprints
├── services/           # Business logic
├── forms/              # WTForms
├── templates/          # Jinja2 HTML
├── static/             # CSS, JS
├── database/           # DB setup docs
├── tests/              # Workflow tests
├── requirements.txt
├── .env.example        # Environment template (copy to .env)
└── Procfile            # Render/Heroku start command
```

## Installation (Local)

### Prerequisites
- Python 3.11+
- MySQL 8+

### 1. Clone & virtual environment

```bash
git clone https://github.com/YOUR_USERNAME/POS_System.git
cd POS_System
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
SECRET_KEY=your-long-random-secret-key
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=pos_inventory_db
FLASK_ENV=development
FLASK_DEBUG=1
```

### 3. Database setup

```sql
CREATE DATABASE pos_inventory_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

```bash
export FLASK_APP=app.py
flask init-db
```

Optional seed accounts (set passwords in `.env` first):

```bash
flask init-db --seed-platform
flask init-db --seed
```

### 4. Run the app

```bash
python app.py
```

Open **http://127.0.0.1:5000**

## Running Tests

```bash
source venv/bin/activate
python -m pytest tests/test_workflow.py -v
# or
python tests/test_workflow.py
```

## Deployment (Render)

1. Push this repo to GitHub (do **not** commit `.env`).
2. Create a [Render](https://render.com) account → **New Blueprint** → connect repo (`render.yaml` included).
3. Or manually:
   - **Web Service:** Python, build `pip install -r requirements.txt`, start `gunicorn wsgi:application --bind 0.0.0.0:$PORT`
   - **MySQL:** Render MySQL or external provider (PlanetScale, Railway)
4. Set environment variables in Render dashboard:

| Variable | Value |
|----------|-------|
| `SECRET_KEY` | Long random string |
| `FLASK_ENV` | `production` |
| `DATABASE_URL` | `mysql+pymysql://user:pass@host:3306/dbname` |

5. Open Render shell and run once: `flask init-db --seed-platform`

## Screenshots

_Add screenshots after deployment:_

1. Dashboard  
2. New Sale with product search  
3. Collect Due  
4. Reports  

## Security Notes

- Never commit `.env` or real passwords to GitHub
- Change all default passwords before production
- Use `FLASK_ENV=production` and HTTPS in production
- Rotate `SECRET_KEY` if ever exposed

## License

MIT — suitable for portfolio and educational use.

## Author

Your Name — [GitHub](https://github.com/YOUR_USERNAME)
