# Deploy POS System on Render (Step 4 & 5)

## Why your first deploy failed

Your `render.yaml` had this block:

```yaml
databases:
  - name: pos-mysql
```

**On Render, `databases:` always creates PostgreSQL — not MySQL.**

Your Flask app uses **MySQL** (`PyMySQL`). Render linked a `postgresql://...` URL to `DATABASE_URL`, so the web service crashed on startup.

The database step showed green, but the web service failed because the wrong database type was connected.

---

## Fix your current Render project

### 1. Clean up the wrong resources

In [Render Dashboard](https://dashboard.render.com):

1. Open your **POS** Blueprint → **Settings** → **Delete Blueprint** (or delete resources manually).
2. Delete the **`pos-mysql`** database (it is PostgreSQL, not MySQL).
3. Delete the failed **`pos-system`** web service if it still exists.

### 2. Push the fixed code

```bash
cd /Users/asmaulhasabsranto/POS_System
git add render.yaml config.py scripts/ DEPLOY_RENDER.md runtime.txt
git commit -m "Fix Render deploy: MySQL via external DATABASE_URL"
git push origin main
```

---

## Step 5: Create a production MySQL database

You need a **hosted MySQL** URL. Pick one option:

### Option A — PlanetScale (recommended, free tier)

1. Go to [planetscale.com](https://planetscale.com) → Sign up.
2. **Create database** → name: `pos_inventory_db`.
3. Click **Connect** → choose **General** → copy the connection string.
4. It looks like:
   ```
   mysql://xxxx:pscale_pw_xxxx@aws.connect.psdb.cloud/pos_inventory_db?ssl={"rejectUnauthorized":true}
   ```
5. For SQLAlchemy, use this format in Render:
   ```
   mysql+pymysql://USER:PASSWORD@HOST/pos_inventory_db?ssl_ca=/etc/ssl/certs/ca-certificates.crt
   ```
   Or simpler (PlanetScale often works with):
   ```
   mysql+pymysql://USER:PASSWORD@aws.connect.psdb.cloud/pos_inventory_db?ssl_verify_cert=true
   ```

   **Tip:** In PlanetScale → Connect → "SQLAlchemy" if available, copy that URL directly.

### Option B — Railway MySQL

1. [railway.app](https://railway.app) → New Project → **Add MySQL**.
2. Open MySQL service → **Variables** → copy `MYSQL_URL` or individual `MYSQLHOST`, `MYSQLUSER`, etc.
3. Build URL:
   ```
   mysql+pymysql://USER:PASS@HOST:PORT/railway
   ```

### Option C — Aiven MySQL (free trial)

1. [aiven.io](https://aiven.io) → Create MySQL service.
2. Copy **Service URI** and change `mysql://` to `mysql+pymysql://`.

---

## Step 4: Deploy web service on Render

### Method 1 — Blueprint (updated repo)

1. Render Dashboard → **New +** → **Blueprint**.
2. Connect repo: `Sranto3920/POS_System` → branch `main`.
3. Render reads the new `render.yaml` (web service only).
4. When prompted for **`DATABASE_URL`**, paste your **MySQL** URL from Step 5.
5. Click **Apply**.

### Method 2 — Manual web service (easiest to debug)

1. **New +** → **Web Service**.
2. Connect GitHub → `Sranto3920/POS_System`.
3. Settings:

| Setting | Value |
|---------|--------|
| Name | `pos-system` |
| Region | Singapore (or nearest) |
| Branch | `main` |
| Runtime | Python 3 |
| Build Command | `./scripts/render_build.sh` |
| Start Command | `gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120` |
| Plan | Free |

4. **Environment variables:**

| Key | Value |
|-----|--------|
| `PYTHON_VERSION` | `3.11.9` |
| `FLASK_APP` | `app.py` |
| `FLASK_ENV` | `production` |
| `FLASK_DEBUG` | `0` |
| `SECRET_KEY` | *(Generate — click Generate)* |
| `DATABASE_URL` | `mysql+pymysql://user:pass@host:3306/pos_inventory_db` |
| `PLATFORM_OWNER_PASSWORD` | *(your strong password)* |

5. Click **Create Web Service**.

---

## Initialize the production database (once)

After the web service is **Live**:

1. Open the service → **Shell** tab.
2. Run:

```bash
flask init-db
flask init-db --seed-platform
```

3. Optional demo shop users (set passwords in env first):

```bash
flask init-db --seed
```

4. Open your app URL: `https://pos-system-xxxx.onrender.com`

| Portal | URL |
|--------|-----|
| Platform Owner | `/platform/login` |
| Shop Login | `/login` |

---

## Create your first shop (production)

1. Login at `/platform/login` with platform owner credentials.
2. **Create Shop** → fill shop name + first admin email/password.
3. Logout → login at `/login` with the shop admin you created.
4. Add supplier → customer → product → purchase → sale.

---

## Troubleshooting

### Deploy still fails — check Logs

Render → your service → **Logs** → look for:

| Error | Fix |
|-------|-----|
| `PostgreSQL, but this app requires MySQL` | Wrong `DATABASE_URL` — use MySQL URL |
| `Can't connect to MySQL server` | Wrong host/password; check SSL params for PlanetScale |
| `ModuleNotFoundError: gunicorn` | Build failed — check Build logs |
| `Permission denied: ./scripts/render_build.sh` | Fixed in repo; or use `pip install -r requirements.txt` as build command |
| `SECRET_KEY` warning | Set `SECRET_KEY` env var |

### Make build script executable (if needed)

Locally:

```bash
chmod +x scripts/render_build.sh
git add scripts/render_build.sh
git commit -m "Make render build script executable"
git push
```

### Free tier notes

- Render free web services **sleep after 15 min** — first visit may take ~30 seconds.
- Free MySQL on Render does **not** exist as managed DB — use PlanetScale/Railway.
- Change all passwords after first login.

---

## Quick checklist

- [ ] Deleted old PostgreSQL `pos-mysql` from failed blueprint
- [ ] Created hosted **MySQL** (PlanetScale / Railway / Aiven)
- [ ] Deployed web service with `mysql+pymysql://...` in `DATABASE_URL`
- [ ] Ran `flask init-db` and `flask init-db --seed-platform` in Render Shell
- [ ] Created shop via Platform Owner portal
- [ ] Tested login, sale, and collect due
- [ ] Updated README with live demo URL

---

## Your URLs (fill in after deploy)

| Item | URL |
|------|-----|
| Live app | `https://________________.onrender.com` |
| GitHub | `https://github.com/Sranto3920/POS_System` |
| PlanetScale DB | *(dashboard link)* |
