# Local Lead Prospector

A multi-tenant SaaS platform for automated B2B lead generation, website auditing, and AI-driven outreach — targeting web development and local SEO service providers.

---

## Overview

Local Lead Prospector automates the entire top-of-funnel sales process: discovering local businesses via Google Places, auditing their digital presence, generating AI-personalized outreach emails, and tracking prospects through a built-in Kanban CRM pipeline — all scoped per authenticated user.

---

## Key Features

### Lead Discovery
- Map-based search powered by the **Google Places API (New)**
- Configurable keyword, radius, and result limit per scan
- Per-user deduplication — the same business is never imported twice for the same account

### Website Auditor
Automated technical analysis of each prospect's website:
- SSL/HTTPS detection (including redirect chain inspection)
- Responsive design check (viewport meta tag)
- Page load time measurement
- SEO tag audit: `<title>`, `<h1>`, `<meta description>`
- CMS fingerprinting (WordPress, Next.js, Shopify)
- Email address extraction (mailto links + HTML text scan)
- Social media presence detection (Facebook, Instagram, LinkedIn)

### AI Analysis (Gemini 2.5 Flash)
- Sends raw audit data to Google Gemini
- Returns 2–3 structured selling points tailored to the specific business
- Generates a ready-to-send, non-aggressive Polish sales email draft

### Email Delivery (Resend)
- One-click email dispatch directly from the UI
- Powered by the **Resend** transactional email API
- Automatically moves the lead to `contacted` status on send

### CRM Pipeline (Kanban)
- Drag-and-drop board with five stages: `New`, `To Contact`, `Contacted`, `Rejected`, `Closed`
- Status persisted to the database via `PATCH /api/leads/{id}`

### Authentication & Multi-Tenancy
- JWT-based authentication (HS256, 7-day tokens)
- bcrypt password hashing
- All lead data is scoped to the authenticated user — complete data isolation between accounts
- Role field on user model (`user` / `admin`) for future access control

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Docker Network                    │
│                                                      │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────┐ │
│  │   Frontend   │   │   Backend    │   │   DB     │ │
│  │  Nuxt 4 +    │──▶│  FastAPI +   │──▶│ Postgres │ │
│  │  Nginx :80   │   │  Uvicorn     │   │ :5432    │ │
│  └──────────────┘   │  :8000       │   └──────────┘ │
│                     └──────────────┘                 │
└─────────────────────────────────────────────────────┘
```

The three services communicate over an isolated Docker bridge network (`app-network`). The backend waits for a PostgreSQL healthcheck before starting.

---

## Tech Stack

### Frontend
| Technology | Role |
|---|---|
| **Nuxt 4** (Vue 3 + Composition API) | SSR-capable SPA framework |
| **TypeScript** | Type safety across composables and pages |
| **Tailwind CSS** | Utility-first styling |
| **shadcn-vue** (Reka UI) | Accessible, unstyled component primitives |
| **Nuxt middleware** | Client-side route protection via JWT cookie |

### Backend
| Technology | Role |
|---|---|
| **FastAPI** | Async REST API with automatic OpenAPI docs |
| **SQLAlchemy** | ORM with declarative models |
| **PostgreSQL 15** | Production-grade relational database |
| **python-jose** | JWT creation and verification |
| **passlib + bcrypt** | Secure password hashing |
| **httpx + BeautifulSoup4** | Async website scraping and HTML parsing |
| **google-generativeai** | Gemini 2.5 Flash AI integration |
| **Resend** | Transactional email delivery |

### DevOps
| Technology | Role |
|---|---|
| **Docker & Docker Compose** | Containerised, reproducible environment |
| **Nginx** | Static file serving + reverse proxy for frontend |
| **PostgreSQL named volume** | Persistent database storage across restarts |

---

## API Reference

All endpoints except `/api/auth/*` require a `Bearer <token>` header.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Create account, returns JWT |
| `POST` | `/api/auth/login` | Authenticate, returns JWT |
| `GET` | `/api/auth/me` | Get current user profile |
| `GET` | `/api/leads` | List authenticated user's leads |
| `PATCH` | `/api/leads/{id}` | Update lead status |
| `POST` | `/api/scan` | Discover leads via Google Places |
| `POST` | `/api/leads/{id}/audit` | Run website audit + AI analysis |
| `POST` | `/api/leads/{id}/send-email` | Send outreach email via Resend |

Interactive API docs: `http://localhost:8000/docs`

---

## Data Model

### User
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `email` | String (unique) | Login identifier |
| `hashed_password` | String | bcrypt hash |
| `role` | String | `user` \| `admin` |
| `created_at` | DateTime | UTC |

### Lead
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `place_id` | String (unique) | Google Places ID |
| `company_name` | String | — |
| `phone` | String | — |
| `address` | String | — |
| `rating` | Float | Google rating |
| `reviews_count` | Integer | — |
| `website_uri` | String | — |
| `email` | String | Extracted during audit |
| `has_ssl` | Boolean | — |
| `audited` | Boolean | — |
| `audit_report` | JSON | Full raw + AI analysis |
| `status` | String | Pipeline stage |
| `user_id` | Integer | Owner (no FK constraint) |
| `created_at` | DateTime | UTC |

---

## Environment Variables

Create `backend/.env` based on the following:

```env
# Database (auto-configured by Docker Compose)
DATABASE_URL=postgresql://llp_user:llp_password@db:5432/llp_db

# Google Places API (New)
GOOGLE_PLACES_API_KEY=your_key_here

# Gemini AI
GEMINI_API_KEY=your_key_here

# Resend email delivery
RESEND_API_KEY=your_key_here

# JWT signing secret — change in production
SECRET_KEY=change-this-in-production
ACCESS_TOKEN_EXPIRE_DAYS=7
```

---

## Getting Started

### Docker (Recommended)

Requires Docker and Docker Compose.

```bash
# 1. Configure environment
cp backend/.env.example backend/.env
# edit backend/.env with your API keys

# 2. Build and start all services
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost |
| Backend API docs | http://localhost:8000/docs |

---

### Manual (Development)

#### Backend

```bash
cd backend
python -m venv venv

# Linux/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Requires a running PostgreSQL instance. Set `DATABASE_URL` in `backend/.env` accordingly.

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend dev server runs on `http://localhost:3000` by default.

---

## Project Structure

```
local-lead-prospector/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, all lead endpoints
│   │   ├── models.py            # SQLAlchemy ORM models (User, Lead)
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   ├── database.py          # SQLAlchemy engine + session factory
│   │   ├── dependencies.py      # JWT auth, password hashing
│   │   ├── business_auditor.py  # Async website scraper
│   │   ├── ai_analyzer.py       # Gemini integration
│   │   ├── audit_service.py     # Orchestrates audit + AI pipeline
│   │   └── routers/
│   │       └── auth.py          # /api/auth/* endpoints
│   ├── scraper.py               # Google Places scan logic
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── app/
│       ├── pages/               # Nuxt file-based routing
│       │   ├── index.vue        # Landing page
│       │   ├── login.vue
│       │   ├── register.vue
│       │   └── app/index.vue    # Main dashboard (protected)
│       ├── components/
│       │   ├── KanbanBoard.vue
│       │   ├── KanbanCard.vue
│       │   └── ui/              # shadcn-vue component library
│       ├── composables/
│       │   └── useAuth.ts       # JWT cookie management + auth state
│       ├── middleware/
│       │   └── auth.ts          # Route guard
│       ├── layouts/
│       │   ├── default.vue
│       │   └── dashboard.vue
│       └── services/
│           └── api.js           # Axios instance with auth interceptors
├── docker-compose.yml
└── README.md
```

---

## License & Self-Hosting

This project is open-source and available under the **AGPL-3.0 License**. 

You are free to self-host this application for your own use (requires your own Google Places and AI API keys). However, if you want a ready-to-use, hassle-free solution with premium features, check out the hosted version at [znajdzfirmy.pl](https://www.znajdzfirmy.pl).
