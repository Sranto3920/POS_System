# Database Setup

This project uses **MySQL** with SQLAlchemy. Schema is managed via Flask CLI (no Alembic migrations).

## Local setup

1. Install MySQL 8+ and create the database:

```sql
CREATE DATABASE pos_inventory_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. Copy environment file and set credentials:

```bash
cp .env.example .env
# Edit .env with your MySQL user, password, and SECRET_KEY
```

3. Initialize tables and optional seed data:

```bash
source venv/bin/activate
export FLASK_APP=app.py
flask init-db
flask init-db --seed-platform   # Platform owner account
flask init-db --seed            # Demo shop users (shop_id=1)
```

## Production (hosted MySQL)

Use a managed MySQL provider (PlanetScale, Railway, AWS RDS, etc.) and set:

```env
DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:3306/pos_inventory_db
FLASK_ENV=production
SECRET_KEY=<long-random-secret>
```

Then run `flask init-db` once against the production database (via Render shell or Railway CLI).

## Schema updates

`flask init-db` runs `ensure_schema()` which:

- Creates missing tables via `db.create_all()`
- Adds new columns safely with `ALTER TABLE` (products, sales, users, shops)

Safe to re-run after pulling new code.
