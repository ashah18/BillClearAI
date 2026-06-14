# BillClear AI

**Understand, audit, and dispute your medical bills with AI.**

🌐 **[Live Demo → https://billclearai.app](https://billclearai.app)**

BillClear AI is a consumer-facing web app that helps patients make sense of confusing medical bills and EOBs (Explanation of Benefits). Upload a bill, and the platform parses every line item, translates billing codes into plain English, flags likely errors and overcharges, compares charges against regional fair-market (Medicare) pricing, and generates ready-to-send dispute letters.

## What It Does

- **Bill upload & AI parsing** — Upload a photo or PDF of a medical bill or EOB. Claude's vision API reads it and extracts each line item (procedure code, description, charge).
- **Plain-English explanations** — CPT, HCPCS, and CDT billing codes are translated into language anyone can understand.
- **Error & overcharge detection** — Line items are color-coded by risk, with flags for duplicate charges, upcoding, and other common billing errors.
- **Fair-price comparison** — Charges are benchmarked against the CMS Physician Fee Schedule (RVUs, GPCIs, ZIP-to-locality mapping, and the Medicare payment formula) to estimate what a fair price would be.
- **AI chat** — Ask follow-up questions about your specific bill in a contextual chat.
- **Dispute letter generation** — Auto-generates professionally formatted Word/PDF dispute letters with your details filled in.
- **Dispute tracking** — Track each dispute's status (draft → sent → resolved/denied) and record confirmed savings.
- **Accounts & billing** — Email/password and Google OAuth sign-in, JWT auth, password reset, and email verification.
- **Freemium plans (Stripe)** — A public landing page presents the product, with limits enforced server-side:
  - **Free** — 3 bill analyses/month, 5 chat messages per bill, fair-price comparison included, but no dispute letter generation.
  - **Pro ($9.99/mo)** — unlimited analyses and chat, plus dispute letter generation and full dispute tracking.

> AI-generated analyses are informational estimates to help you understand your bill — not legal, medical, or financial advice. Uploaded documents are never used to train AI models.

## Tech Stack

### Frontend (`/frontend`)
- React 18 (JavaScript, not TypeScript)
- Vite (build tool & dev server)
- Tailwind CSS for all styling
- React Router for routing
- Axios for API calls
- react-markdown for rendering AI chat responses

### Backend (`/backend`)
- Django 5 + Django REST Framework
- PostgreSQL (via Docker for local development)
- djangorestframework-simplejwt for JWT auth
- django-allauth for Google OAuth
- django-cors-headers for CORS
- Anthropic Claude Python SDK for AI parsing, analysis, and chat
- python-docx for dispute letter generation
- Pillow for image/PDF handling for the Claude vision API
- CMS pricing data models (ProcedureRVU, LocalityGPCI, ZipToLocality)
- django-storages + boto3 (S3 storage in production), whitenoise (static files)
- django-axes for brute-force login protection, DRF throttling for rate limits
- Stripe SDK for subscriptions, SendGrid for transactional email

### Architecture
A two-service monorepo. The React frontend talks to the Django backend exclusively over a JSON REST API. Authentication uses JWT (access token in memory, refresh token in an httpOnly cookie). The root route (`/`) is a public landing page; the authenticated app lives at `/dashboard`, with logged-in users redirected there automatically.

```
BillClearAI/
├── frontend/          # React + Vite + Tailwind
├── backend/           # Django + DRF
│   ├── config/        # Django project settings & URLs
│   ├── users/         # Auth, profiles, subscriptions
│   ├── bills/         # Bill upload, AI parsing & analysis, chat
│   ├── pricing/       # CMS fair-price comparison engine
│   └── disputes/      # Dispute letter generation & tracking
└── docker-compose.yml # Local PostgreSQL
```

## Running It Locally

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Docker Desktop (for PostgreSQL)
- An Anthropic API key (required for AI features)

### 1. Start PostgreSQL

From the project root:

```bash
docker-compose up -d
```

This runs Postgres 16 in a container (database `billclear`, user/password `billclear`, exposed on host port **5433**).

### 2. Backend (Django)

```bash
cd backend

# Create & activate a virtualenv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Then edit .env — at minimum set SECRET_KEY and ANTHROPIC_API_KEY,
# and point DATABASE_URL at the Docker Postgres on port 5433:
#   DATABASE_URL=postgres://billclear:billclear@localhost:5433/billclear

# Run migrations
python manage.py migrate

# Import CMS pricing data (powers the fair-price comparison)
python manage.py import_cms_data

# (Optional) create an admin user
python manage.py createsuperuser

# Start the dev server
python manage.py runserver
```

The backend runs at **http://localhost:8000** (admin at `/admin/`, API under `/api/`).

### 3. Frontend (React)

In a new terminal:

```bash
cd frontend
npm install

# Configure environment
echo "VITE_API_URL=http://localhost:8000/api" > .env

npm run dev
```

The frontend runs at **http://localhost:5173**.

### Quick start (all-in-one)

A helper script starts Postgres, the backend, and the frontend together (assumes the venv and dependencies are already set up):

```bash
./start.sh
```

## Environment Variables

### Frontend (`frontend/.env`)
| Variable | Description |
| --- | --- |
| `VITE_API_URL` | Backend API base URL (e.g. `http://localhost:8000/api`) |

### Backend (`backend/.env`)
| Variable | Description |
| --- | --- |
| `SECRET_KEY` | Django secret key |
| `DATABASE_URL` | PostgreSQL connection string |
| `ANTHROPIC_API_KEY` | Claude API key (required for AI features) |
| `DEBUG` | `True` for development, `False` for production |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts |
| `CORS_ALLOWED_ORIGINS` | Allowed frontend origin(s) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REDIRECT_URI` | Google OAuth config |
| `EMAIL_BACKEND` / `SENDGRID_API_KEY` / `DEFAULT_FROM_EMAIL` | Email (console backend in dev, SendGrid in prod) |
| `USE_S3` / `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_STORAGE_BUCKET_NAME` / `AWS_S3_REGION_NAME` | S3 file storage (production) |
| `STRIPE_SECRET_KEY` / `STRIPE_PUBLISHABLE_KEY` / `STRIPE_WEBHOOK_SECRET` / `STRIPE_PRO_PRICE_ID` | Stripe subscriptions |

See `backend/.env.example` for a complete template.

> **Never commit `.env` files.** Secrets and API keys belong only in environment variables.
