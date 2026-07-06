# Complete Deploy Guide — Free MySQL + Online Website

Read this **from top to bottom**. Do not skip steps.

---

## What you are building

```
┌─────────────────┐         ┌─────────────────┐
│   TiDB Cloud    │         │     Render      │
│  (MySQL online) │ ◄────── │  (your website) │
│     FREE        │         │      FREE       │
└─────────────────┘         └─────────────────┘
        ▲                           │
        │                           ▼
   DATABASE_URL              https://your-app.onrender.com
   (connection string)        (public link for everyone)
```

- **Your Mac MySQL** = only works on your computer (`localhost`)
- **TiDB Cloud** = MySQL on the internet (free)
- **Render** = hosts your Flask app (free)

**Total cost: $0**

---

## PART 0 — Before you start (5 minutes)

### 0.1 Check GitHub has your code

1. Open browser: **https://github.com/Sranto3920/POS_System**
2. You should see your project files (`app.py`, `README.md`, etc.)

If code is not there, run on your Mac Terminal:

```bash
cd /Users/asmaulhasabsranto/POS_System
git add .
git commit -m "Prepare for deploy"
git push origin main
```

### 0.2 Delete old failed Render project (important)

Your first deploy failed because Render created **PostgreSQL**, not MySQL.

1. Go to **https://dashboard.render.com**
2. If you see a **POS** blueprint or **pos-mysql** database → delete them
3. Delete failed **pos-system** web service if it exists

You will create everything fresh below.

---

# PART 1 — DATABASE (TiDB Cloud) — Do this FIRST

TiDB Cloud = **free online MySQL** (works like MySQL on your Mac).

---

### Step 1.1 — Create TiDB account

1. Open: **https://tidbcloud.com**
2. Click **Get Started for Free** (or **Sign Up**)
3. Sign up with **Google** or **Email**
4. Verify email if asked
5. You land on TiDB Cloud dashboard

---

### Step 1.2 — Create a free cluster

1. Click **Create Cluster** (or **New Cluster**)
2. Select **TiDB Cloud Serverless** (must say **Serverless** = free)
3. Fill in:
   - **Cluster Name:** `pos-cluster`
   - **Region:** `AWS - Singapore` (or closest to Bangladesh)
   - **Encryption:** leave default
4. Click **Create**
5. Wait 1–3 minutes until status shows **Active** (green)

---

### Step 1.3 — Create the database name

1. Click your cluster name **`pos-cluster`**
2. Left menu → click **SQL Editor** (or **Chat2Query**)
3. In the SQL box, type exactly:

```sql
CREATE DATABASE pos_inventory_db;
```

4. Click **Run** (or press Ctrl+Enter)
5. You should see success message

---

### Step 1.4 — Get username, password, host

1. Go back to cluster page
2. Click **Connect** button (top area)
3. Select **Public** (not VPC)
4. You may need to click **Create Password** or **Generate Password** for the user
5. Write down these 4 values in Notepad:

| What to copy | Where you see it | Example |
|--------------|------------------|---------|
| **Host** | Endpoint / Host | `gateway01.ap-southeast-1.prod.aws.tidbcloud.com` |
| **Port** | Port | `4000` |
| **User** | Username | `2abc123.root` |
| **Password** | Password | `xxxxxxxx` |
| **Database** | You created this | `pos_inventory_db` |

> **Important:** Port is **4000** (NOT 3306)

---

### Step 1.5 — Build DATABASE_URL (copy-paste formula)

Open Notepad. Replace the CAPITAL words with YOUR values from Step 1.4:

```
mysql+pymysql://USER:PASSWORD@HOST:4000/pos_inventory_db
```

**Filled example** (yours will look similar but different values):

```
mysql+pymysql://2abc123.root:MyTiDBpass99@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/pos_inventory_db
```

**Password has special characters?** Replace before pasting in Render:

| Character | Replace with |
|-----------|--------------|
| `@` | `%40` |
| `#` | `%23` |
| `!` | `%21` |
| `$` | `%24` |
| `&` | `%26` |

**Save this full line.** You need it in Part 2.

**Test:** Your URL must:
- Start with `mysql+pymysql://`
- Contain `@` before the host
- End with `/pos_inventory_db`
- Have port `:4000` before `/pos_inventory_db`

---

# PART 2 — WEBSITE (Render) — Do this SECOND

---

### Step 2.1 — Create Render account

1. Open: **https://render.com**
2. Click **Get Started**
3. Sign up with **GitHub** (easiest — connects your repo)
4. Allow Render to access GitHub when asked

---

### Step 2.2 — Create Web Service

1. On Render dashboard, click **New +** (top right)
2. Click **Web Service**
3. Under **Connect a repository**, find **`Sranto3920/POS_System`**
   - If not listed: click **Configure account** → give Render access to the repo
4. Click **Connect** next to your repo

---

### Step 2.3 — Fill service settings

Copy each value exactly:

| Setting | Value |
|---------|--------|
| **Name** | `pos-system` |
| **Region** | Singapore (or closest) |
| **Branch** | `main` |
| **Root Directory** | *(leave empty)* |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120` |
| **Instance Type** | **Free** |

Scroll down to **Environment Variables**.

---

### Step 2.4 — Add environment variables

Click **Add Environment Variable** for each row:

| Key | Value |
|-----|--------|
| `PYTHON_VERSION` | `3.11.9` |
| `FLASK_APP` | `app.py` |
| `FLASK_ENV` | `production` |
| `FLASK_DEBUG` | `0` |
| `SECRET_KEY` | Click **Generate** button, or type 50 random letters |
| `DATABASE_URL` | Paste your full URL from **Step 1.5** |
| `PLATFORM_OWNER_EMAIL` | `owner@posplatform.com` |
| `PLATFORM_OWNER_PASSWORD` | Pick a password you will remember (e.g. `BhaiBhai2026!`) |

Double-check `DATABASE_URL` — no spaces at start or end.

---

### Step 2.5 — Deploy

1. Click **Create Web Service** (bottom)
2. Render starts building (you see logs scrolling)
3. Wait 3–8 minutes
4. When successful, top shows **Live** with green dot
5. Your URL is at the top, like:

```
https://pos-system-abcd.onrender.com
```

Copy and save this URL.

---

### Step 2.6 — If deploy FAILED (red)

1. Click **Logs** tab
2. Read the last 10–20 lines

| Error in logs | What to do |
|---------------|------------|
| `PostgreSQL` / `requires MySQL` | Wrong `DATABASE_URL` — must be `mysql+pymysql://...` |
| `Can't connect` / `Connection refused` | TiDB cluster not Active, or wrong host/port |
| `Access denied` | Wrong password in `DATABASE_URL` |
| `ModuleNotFoundError` | Build failed — check Build logs |

Fix the problem → **Manual Deploy** → **Deploy latest commit**

---

# PART 3 — CREATE TABLES (one time, after Live)

Your cloud database is empty. You must create tables once.

### Step 3.1 — Open Render Shell

1. Render dashboard → click your **`pos-system`** service
2. Top menu → click **Shell**
3. Wait for terminal to open inside browser

### Step 3.2 — Run commands (one at a time)

Type command 1, press Enter, wait for finish:

```bash
flask init-db
```

You should see: `Database ready.`

Type command 2, press Enter:

```bash
flask init-db --seed-platform
```

You should see: `Platform owner created: owner@posplatform.com`

If you see `Platform owner already exists` — that is OK.

---

# PART 4 — USE YOUR ONLINE APP

### Step 4.1 — Platform Owner login

1. Open browser: `https://YOUR-APP-URL.onrender.com/platform/login`
2. Email: `owner@posplatform.com`
3. Password: your `PLATFORM_OWNER_PASSWORD` from Step 2.4

### Step 4.2 — Create your shop

1. After login → **Create Shop** (or Shops → Create)
2. Fill in:
   - Shop name: e.g. `M/S Bhai Bhai Enterprise`
   - Admin name, email, password for shop staff
3. Save

### Step 4.3 — Shop staff login

1. Logout from platform
2. Go to: `https://YOUR-APP-URL.onrender.com/login`
3. Login with the **shop admin** email/password you just created

### Step 4.4 — Test the app

Do this once to confirm everything works:

1. Add **Supplier**
2. Add **Customer**
3. Add **Product**
4. **Purchase** (stock increases)
5. **New Sale** (stock decreases)
6. Try **partial payment** (due/halkhata)

---

# PART 5 — Local vs Online (do not confuse)

| | Local (your Mac) | Online (Render) |
|--|------------------|-----------------|
| Run app | `PORT=5001 python app.py` | Automatic on Render |
| Open app | `http://127.0.0.1:5001` | `https://pos-system-xxxx.onrender.com` |
| Database | MySQL on Mac (`.env` file) | TiDB (`DATABASE_URL` on Render) |
| Data | Separate | Separate |

Changes on local **do not** appear online. They use different databases.

---

# Quick checklist — tick when done

**Database (TiDB)**
- [ ] TiDB account created
- [ ] Serverless cluster **Active**
- [ ] `CREATE DATABASE pos_inventory_db` ran successfully
- [ ] `DATABASE_URL` saved in Notepad

**Website (Render)**
- [ ] Old failed blueprint deleted
- [ ] Web service created from GitHub repo
- [ ] All 8 environment variables set
- [ ] Status is **Live**
- [ ] `flask init-db` ran in Shell
- [ ] `flask init-db --seed-platform` ran in Shell

**Test**
- [ ] Platform login works
- [ ] Shop created
- [ ] Shop login works
- [ ] Sale completed

---

# Still stuck?

Send these 3 things:

1. Screenshot of Render **Logs** (last 20 lines)
2. Screenshot of TiDB cluster page (showing **Active**)
3. First 30 characters of your `DATABASE_URL` only (hide password), e.g. `mysql+pymysql://2abc123.root:****@gate...`

---

# One-line summary

```
TiDB (free MySQL) → copy DATABASE_URL → Render (paste env vars) → Shell: flask init-db → open URL → login
```

That is everything. Follow Part 1, then Part 2, then Part 3, then Part 4.
