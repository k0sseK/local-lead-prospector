<img width="1581" height="393" alt="llp-banner" src="https://github.com/user-attachments/assets/abfdafd9-687f-402a-8cbb-bec5262472a8" />

# Local Lead Prospector

**Find local businesses, audit their websites, and close deals — automated.**

Local Lead Prospector is an open-source B2B lead generation platform. Search for local businesses via Google Places, automatically audit their web presence, let AI write personalized outreach emails, and track every prospect through a built-in CRM — all scoped per user account.

A hosted version is available at [znajdzfirmy.pl](https://www.znajdzfirmy.pl).

---

## Features

**Lead Discovery**

- Search businesses by keyword and radius using Google Places API (New)
- Interactive map view of discovered leads
- Per-user deduplication — the same business is never imported twice
- CSV export for any lead selection

**Website Auditor**

- SSL/HTTPS status, responsive design check, page load time
- SEO audit: `<title>`, `<h1>`, `<meta description>`
- CMS fingerprinting (WordPress, Next.js, Shopify, and others)
- Email address extraction, social media presence detection
- Playwright fallback — headless Chromium renders SPA sites (React, Vue, Angular) that return empty HTML via httpx

**AI-Powered Outreach**

- Gemini 2.5 Flash generates personalized cold emails and selling points per lead
- Configurable sender persona: name, company, offer description, tone of voice
- One-click send directly from the CRM

**Email Delivery**

- Resend API or custom SMTP — your choice, configured per account
- Lead automatically moves to `Contacted` on send

**CRM Pipeline**

- Kanban board with 5 stages and drag-and-drop
- Bulk status updates and bulk delete
- Per-lead notes, audit results, and AI output in one view

**Plans & Payments**

- Free and Pro tiers with monthly quotas (scans, AI audits, emails sent)
- LemonSqueezy subscription integration with webhook-based plan sync
- Quota enforcement with graceful in-app messaging

**Authentication**

- JWT-based auth with bcrypt password hashing
- Password reset via email
- Complete data isolation per user account

**Admin Panel**

- User management and manual plan assignment
- Per-user usage stats, quota monitoring, and cost tracking

**Infrastructure**

- Per-IP rate limiting (30 req/min, configurable)
- Interactive API docs at `/api/docs`
- Dockerized — four services (frontend, backend, PostgreSQL, Playwright scraper) wired together with a single `docker compose up`

---

## Tech Stack

**Backend:** FastAPI, SQLAlchemy, PostgreSQL, Google Gemini (`gemini-2.5-flash`), httpx, BeautifulSoup4, Resend

**Frontend:** Nuxt 4, Vue 3, Tailwind CSS, shadcn-vue, vue3-google-map, vuedraggable

**Payments:** LemonSqueezy

**Infrastructure:** Docker, Nginx, Docker Compose

---

## Self-Hosting

### Prerequisites

- Docker and Docker Compose
- [Google Cloud project](https://console.cloud.google.com/) with Places API (New) enabled
- [Google AI Studio](https://aistudio.google.com/apikey) API key (Gemini)
- [Resend](https://resend.com) account or custom SMTP credentials
- LemonSqueezy account (optional — required only for paid plan integration)

### Quick Start

```bash
git clone https://github.com/marcellocodes/local-lead-prospector
cd local-lead-prospector
cp backend/.env.example backend/.env
# Fill in your values in backend/.env
docker compose up --build
```

Frontend: `http://localhost` · API docs: `http://localhost:8000/docs`

### Environment Variables

```env
# Database (pre-configured for Docker Compose)
DATABASE_URL=postgresql://llp_user:llp_password@db:5432/llp_db

# Google Places API (New)
GOOGLE_PLACES_API_KEY=your_key_here

# Gemini AI
GEMINI_API_KEY=your_key_here

# Resend email delivery
RESEND_API_KEY=your_key_here
RESEND_FROM_EMAIL=you@yourdomain.com

# JWT signing secret — generate with: openssl rand -hex 32
SECRET_KEY=change-this-in-production
ACCESS_TOKEN_EXPIRE_DAYS=7

# CORS — comma-separated allowed frontend origins
ALLOWED_ORIGINS=http://localhost,http://localhost:3000

# Password reset links (set to your public frontend URL in production)
FRONTEND_URL=http://localhost:3000

# LemonSqueezy (optional)
LEMONSQUEEZY_WEBHOOK_SECRET=your_webhook_secret

# Admin cost alerts (optional)
ADMIN_EMAIL=you@yourdomain.com
ADMIN_COST_ALERT_USD=2.0

# Playwright scraper microservice (optional — SPA fallback)
# Leave empty to disable; backend uses httpx-only scraping
PLAYWRIGHT_SERVICE_URL=http://playwright-service:8001
PLAYWRIGHT_API_SECRET=your-internal-secret
```

### Playwright Scraper Service (Railway)

The Playwright microservice renders JavaScript-heavy sites (React, Vue, Angular SPAs) that return empty HTML to httpx. It runs as a separate container with its own Chromium instance (~500 MB RAM).

**Adding to Railway:**

1. **New Service** → select your GitHub repo → set **Root Directory** to `playwright-service`
2. Add environment variable `API_SECRET` — use the same value as `PLAYWRIGHT_API_SECRET` in the backend
3. In the backend service, add:
   - `PLAYWRIGHT_SERVICE_URL=http://${{playwright-service.RAILWAY_PRIVATE_DOMAIN}}:8001`
   - `PLAYWRIGHT_API_SECRET=<your shared secret>`
4. Railway private networking routes traffic between services in the same project — no public URL needed

The backend gracefully degrades if the Playwright service is unavailable — audits fall back to httpx-only scraping.

---

## Testing

The project uses a two-layer testing strategy: **pytest** for backend business logic (fast, no external services) and **Playwright** for frontend end-to-end tests (black-box, runs against a live app).

### Backend — pytest

Tests use an in-memory SQLite database — no PostgreSQL, no API keys, no Docker required.

```bash
# One-time setup (adds pytest to your local venv)
cd backend
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/ -v
```

> `requirements-dev.txt` is for local development only. Railway and Docker use `requirements.txt` which does not include test tools.

### Frontend — Playwright (E2E, black-box)

Playwright clicks through the real app. Both servers must be running before you start tests.

**One-time setup:**

```bash
cd frontend
pnpm install                              # installs @playwright/test from devDependencies
pnpm exec playwright install chromium    # downloads ~280 MB Chromium browser (once)
```

**Set test account credentials** (must exist in your local database — register via `/register`):

```powershell
# PowerShell
$env:E2E_TEST_EMAIL    = "tester@example.com"
$env:E2E_TEST_PASSWORD = "YourPassword123"
```

```bash
# bash / zsh
export E2E_TEST_EMAIL="tester@example.com"
export E2E_TEST_PASSWORD="YourPassword123"
```

Optional (useful in CI):

```bash
# Explicit API base used by E2E auth precheck
export E2E_API_BASE_URL="http://localhost:8000/api"

# Explicit backend health endpoint used before tests start
export E2E_BACKEND_HEALTH_URL="http://localhost:8000/health"
```

Playwright auth tests now run a precheck before UI interactions:

- verify frontend URL is reachable,
- verify backend health endpoint is reachable,
- verify login credentials are valid and account is already verified.

If any of these checks fail, tests stop early with a clear diagnostic instead of timing out on redirect to `/app`.

**Run tests** (start both servers first — `start_dev.bat` or manually):

```bash
pnpm test:e2e:ui      # interactive UI mode — recommended, shows every click live
pnpm test:e2e         # headless, results in terminal
pnpm test:e2e:debug   # headed + Playwright Inspector for debugging
```

Each `test:e2e*` command now runs an automatic precheck first (`frontend/scripts/e2e-precheck.mjs`):

- waits for frontend URL,
- waits for backend `/health`,
- validates E2E login credentials.

This prevents flaky "waitForURL(/app) timeout" failures by failing early with a specific reason.

> Playwright is a `devDependency`. The frontend Docker image (`nginx:alpine`) is built from static files only — Playwright never ends up in the production image.

### Pre-push checklist

Before every `git push`:

```bash
# 1. Start the app (if not already running)
start_dev.bat

# 2. Backend tests — takes ~0.3s
cd backend
python -m pytest tests/ -v

# 3. E2E tests — takes ~15–30s
cd frontend
pnpm test:e2e:ui
```

Railway deploys automatically after a successful push. GitHub Actions workflows (`.github/workflows/`) are included for future CI automation but are not required today.

---

## License

Licensed under the [GNU Affero General Public License v3.0 (AGPL-3.0)](./LICENSE).

You are free to self-host this application for personal use. If you modify and run it over a network, you must make your source code available under the same license. For a ready-to-use hosted solution, visit [znajdzfirmy.pl](https://www.znajdzfirmy.pl).
