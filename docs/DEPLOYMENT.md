# LostLink Production Deployment Guide

This guide is a complete, step-by-step walkthrough for deploying LostLink to **Render** as a single-service container (FastAPI serving the built React 19 PWA with a single Uvicorn worker), backed by managed PostgreSQL, Supabase Object Storage, and Resend transactional email.

---

## Architecture Overview

```
                      ┌────────────────────────────────────────┐
                      │              User Browser              │
                      │       (PWA / Mobile / Desktop)         │
                      └──────────────────┬─────────────────────┘
                                         │ HTTPS / WSS
                                         ▼
                      ┌────────────────────────────────────────┐
                      │          Render Web Service            │
                      │  ┌──────────────────────────────────┐  │
                      │  │       FastAPI (Single Worker)     │  │
                      │  │  - Static SPA & PWA Shell (/ )   │  │
                      │  │  - JSON API (/api/*)             │  │
                      │  │  - In-Memory Type-Partitioned    │  │
                      │  │    DSA Matching Index (RAM)      │  │
                      │  └──────────────────┬───────────────┘  │
                      └──────────────┬──────┴─────────┬────────┘
                                     │                │
            ┌────────────────────────┼────────────────┼────────────────────────┐
            ▼                        ▼                ▼                        ▼
┌───────────────────────┐ ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐
│   Managed Postgres    │ │  Supabase Storage  │ │   Resend Email     │ │ Local Temp Disk    │
│ (Render/Neon/Supabase)│ │ (Sanitized Images) │ │ (Notifications)    │ │ (/tmp uploads)     │
└───────────────────────┘ └────────────────────┘ └────────────────────┘ └────────────────────┘
```

> [!IMPORTANT]
> **Single-Worker Requirement**: LostLink maintains an in-memory, type-partitioned inverted index and bounded priority queue for $O(1)$ candidate retrieval and sub-millisecond matching. The production container runs with **exactly 1 Uvicorn worker** (`--workers 1`). Do not scale horizontally without externalizing the index to Redis or a dedicated index service.

---

## Step-by-Step Deployment Instructions

### Step 1: Provision Managed PostgreSQL Database

You can use **Render PostgreSQL**, **Neon**, or **Supabase Database**.

#### Option A: Render Managed PostgreSQL (Recommended for simplicity)
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** $\to$ **PostgreSQL**.
3. Fill in the parameters:
   - **Name**: `lostlink-postgres`
   - **Database**: `lostlink`
   - **User**: `lostlink_user`
   - **Region**: Choose the region closest to your users (e.g., `Oregon (US West)` or `Frankfurt (EU Central)`).
   - **Plan**: Free or Starter.
4. Click **Create Database**.
5. Once provisioned, locate the **Internal Database URL** (e.g., `postgres://lostlink_user:...@dpg-...:5432/lostlink`).
6. *Note*: LostLink automatically handles the `postgres://` $\to$ `postgresql+psycopg2://` dialect conversion on startup.

---

### Step 2: Configure Supabase Object Storage

LostLink stores sanitized user photo uploads (with stripped EXIF and GPS metadata) in an S3-compatible Supabase Storage bucket.

1. Log in to your [Supabase Dashboard](https://app.supabase.com).
2. Select your project (or create one: **New project** $\to$ name: `LostLink` $\to$ select region $\to$ set strong database password).
3. In the left navigation menu, click **Storage** (bucket icon).
4. Click **New bucket**:
   - **Name**: `lostlink-images`
   - **Public bucket**: Toggle **ON** (Report images are publicly visible to logged-in users; individual files are served via CDN URLs).
   - Click **Save bucket**.
5. Navigate to **Project Settings** (gear icon) $\to$ **API**:
   - Copy **Project URL** (e.g. `https://xyzcompany.supabase.co`).
   - Copy **anon / public key** (`sb_publishable_...`).
   - Copy **service_role secret** (`sb_secret_...`).

---

### Step 3: Configure Resend Transactional Email

LostLink uses [Resend](https://resend.com) to deliver double-blind contact notifications, password reset links, and high-confidence match alerts asynchronously.

1. Sign in to [Resend Dashboard](https://resend.com).
2. Navigate to **API Keys** $\to$ click **Create API Key**:
   - **Name**: `LostLink Production`
   - **Permission**: Full access
   - Copy the generated API key (format: `re_...`).
3. For custom domains:
   - Go to **Domains** $\to$ **Add Domain** $\to$ enter your domain (e.g. `mail.lostlink.org`).
   - Add the specified DKIM, SPF, and MX records to your DNS provider.
   - Set `EMAIL_FROM=notifications@yourdomain.com`.
4. For quick initial testing without a custom domain:
   - Use `EMAIL_FROM=onboarding@resend.dev` (can deliver only to the email address registered with your Resend account).

---

### Step 4: Deploy Single-Service Docker to Render

LostLink includes a multi-stage `Dockerfile` that:
1. Installs Node 20 dependencies and builds the React 19 frontend into optimized static PWA bundles.
2. Sets up Python 3.11 with `libpq5` and backend requirements.
3. Copies the built frontend assets into the Python image.
4. On container boot (`docker-entrypoint.sh`), safely runs `alembic upgrade head` before starting Uvicorn with `--workers 1`.

#### Deploying via Render Web Dashboard:
1. In Render Dashboard, click **New +** $\to$ **Web Service**.
2. Connect your GitHub repository (`LostLink`).
3. Configure settings:
   - **Name**: `lostlink`
   - **Region**: Same region as your database.
   - **Branch**: `main`
   - **Runtime**: **Docker**
   - **Dockerfile Path**: `Dockerfile`
   - **Docker Context**: `.` (root directory)
   - **Instance Type**: Starter ($7/mo recommended for persistent memory; Free tier sleeps after inactivity).
4. Expand **Advanced** $\to$ click **Add Environment Variable** and configure the following:

| Variable | Recommended Production Value | Description |
| :--- | :--- | :--- |
| `ENV` | `production` | Enables production security features |
| `DEBUG` | `false` | Disables debug stack traces in API errors |
| `DATABASE_URL` | *(Render internal URL or Neon connection string)* | PostgreSQL connection string |
| `SECRET_KEY` | *(Generate via `openssl rand -hex 32`)* | Min 32-byte secret for PyJWT auth cookies |
| `PORT` | `8000` | Port exposed by the container |
| `COOKIE_SECURE` | `true` | Ensures cookies transmit only over HTTPS |
| `COOKIE_DOMAIN` | *(Leave empty or your domain, e.g. `lostlink.onrender.com`)* | Scope for auth cookies |
| `ALLOWED_ORIGINS` | `https://<your-render-subdomain>.onrender.com` | Allowed CORS and CSRF origins |
| `APP_BASE_URL` | `https://<your-render-subdomain>.onrender.com` | Base URL used in password reset links |
| `STORAGE_PROVIDER` | `supabase` | Pluggable storage adapter |
| `SUPABASE_URL` | `https://<your-project-ref>.supabase.co` | Supabase API endpoint |
| `SUPABASE_PUBLISHABLE_KEY` | `sb_publishable_...` | Supabase publishable key |
| `SUPABASE_SERVICE_ROLE_KEY` | `sb_secret_...` | Supabase service role secret |
| `SUPABASE_STORAGE_BUCKET` | `lostlink-images` | Storage bucket name |
| `EMAIL_PROVIDER` | `resend` | Transactional email provider |
| `RESEND_API_KEY` | `re_...` | Resend API key |
| `EMAIL_FROM` | `notifications@lostlink.org` or `onboarding@resend.dev` | Sender address |

5. Under **Health Check Path**, enter: `/api/health`.
6. Click **Create Web Service**.
7. Render will pull the repository, run the multi-stage Docker build, execute `alembic upgrade head`, and boot the app.

---

### Step 5: Configure Custom Domain & Automatic SSL/TLS

1. In your Render service, click **Settings** $\to$ **Custom Domains**.
2. Click **Add Custom Domain** (e.g. `lostlink.yourdomain.com` or `yourdomain.com`).
3. Add the DNS records provided by Render to your domain registrar (e.g., Cloudflare, Namecheap, GoDaddy):
   - For subdomains: `CNAME` pointing to `lostlink.onrender.com`.
   - For apex domains: `ANAME`/`ALIAS` record pointing to Render's IP.
4. Render will verify DNS propagation and issue a free Let's Encrypt SSL/TLS certificate with automatic renewal.
5. Update `ALLOWED_ORIGINS` and `APP_BASE_URL` in your Render Environment Variables to your custom domain.

---

### Step 6: Database Backup and Restore Procedures

#### Automated Backups
If using Render PostgreSQL Starter or higher, automated daily backups are retained for 7 days.

#### Manual On-Demand Backup (`pg_dump`)
Run from any terminal with PostgreSQL client tools installed:
```bash
# Set your production database URL
export DATABASE_URL="postgresql://lostlink_user:password@hostname:5432/lostlink"

# Create a compressed SQL dump with timestamp
pg_dump --no-owner --clean --if-exists --format=custom "$DATABASE_URL" > "lostlink_backup_$(date +%Y%m%d_%H%M%S).dump"
```

#### Database Restoration (`pg_restore`)
To restore a snapshot to a new or existing database instance:
```bash
# WARNING: This overwrites target tables
pg_restore --clean --if-exists --no-owner -d "$DATABASE_URL" lostlink_backup_YYYYMMDD_HHMMSS.dump

# After restore, restart the LostLink web service to re-index active reports in RAM:
# (Triggered via Render Dashboard -> Manual Deploy -> Clear build cache & deploy)
```

---

### Step 7: Post-Deployment Verification Checklist

Once deployed, verify the installation by checking:

- [ ] **Health Endpoint**: Visit `https://your-domain/api/health`. Verify JSON output:
  ```json
  {
    "status": "healthy",
    "database": "connected",
    "dialect": "postgresql",
    "indexed_reports": 0
  }
  ```
- [ ] **SPA Client Routing**: Visit `https://your-domain/` and directly visit `https://your-domain/reports` and `https://your-domain/privacy`. Confirm the React app loads without 404 errors.
- [ ] **PWA Manifest & Service Worker**: Open DevTools $\to$ Application $\to$ Manifest. Verify manifest name, teal `#527C76` theme color, and registered service worker.
- [ ] **User Registration & Cookie Test**: Register an account. Inspect `Application` $\to$ `Cookies`. Confirm `access_token` and `refresh_token` are set with `HttpOnly`, `SameSite=Lax`, and `Secure`.
- [ ] **Photo Upload**: Create a Lost/Found report and upload a photo. Verify the image appears on the card and detail view.
- [ ] **Double-Blind Contact Flow**: Using a second browser/incognito session, submit a contact request. Verify owner receives it in "My Reports", and contact details are masked until "Accept" is clicked.

---

## Exhaustive List of Manual Steps Required by You

Because API accounts, billing, and domains require your personal credentials, you must complete the following external actions:

1. **Supabase**:
   - Log into [Supabase](https://supabase.com).
   - Note your **Project URL** (format: `https://<project-ref>.supabase.co`).
   - Create the bucket named `lostlink-images` and mark it **Public**.
2. **Resend**:
   - If sending emails to arbitrary external users, verify your domain in [Resend](https://resend.com/domains) by adding DKIM DNS records.
3. **Render**:
   - Create a Render account at [render.com](https://render.com).
   - Create the PostgreSQL database service.
   - Create the Web Service using the Docker runtime and configure the environment variables as shown above.
4. **Custom Domain (Optional)**:
   - Add CNAME records at your DNS registrar pointing to your Render service address.

