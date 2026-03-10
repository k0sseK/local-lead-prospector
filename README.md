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
- Dockerized — three services (frontend, backend, PostgreSQL) wired together with a single `docker compose up`

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
```

---

## License

Licensed under the [GNU Affero General Public License v3.0 (AGPL-3.0)](./LICENSE).

You are free to self-host this application for personal use. If you modify and run it over a network, you must make your source code available under the same license. For a ready-to-use hosted solution, visit [znajdzfirmy.pl](https://www.znajdzfirmy.pl).
