# Heritage Site Information System

**HeritageSA** is a full-stack web application for discovering, exploring, and booking visits to South African cultural and natural heritage sites. Built as a portfolio project demonstrating professional-grade Django development, polyglot persistence, REST API design, ETL pipeline engineering, containerised deployment, and CI/CD.

[![CI](https://github.com/Sinothando-Mthombeni/Heritage-Site-Information-System/actions/workflows/ci.yml/badge.svg)](https://github.com/Sinothando-Mthombeni/Heritage-Site-Information-System/actions/workflows/ci.yml)
![Tests](https://img.shields.io/badge/tests-55%20passing-brightgreen)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Django](https://img.shields.io/badge/django-4.2-green)
![PostgreSQL](https://img.shields.io/badge/postgresql-15-336791)
![MongoDB](https://img.shields.io/badge/mongodb-6-47A248)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Data Model](#data-model)
- [API Endpoints](#api-endpoints)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Running Tests](#running-tests)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [Roadmap](#roadmap)

---

## Overview

HeritageSA catalogues **29 real South African heritage sites** spanning all 9 provinces and 6 categories — from UNESCO World Heritage Sites like Robben Island and the Cradle of Humankind, to museums, historical monuments, cultural villages, and natural reserves.

The system deliberately uses **two databases** for different purposes:

- **PostgreSQL** — transactional source of truth (bookings, site data, visitors)
- **MongoDB** — read-optimised analytical store (populated from PostgreSQL via a one-directional ETL pipeline)

This separation mirrors production analytics architectures and is a deliberate design choice, not accidental complexity.

---

## Architecture

```
Browser / API Client
        │
        ▼
Django Application (Gunicorn in production)
        │
   ┌────┴────────────────────────────────┐
   │              View Layer             │
   │  Template views (home, discover,   │
   │  admin dashboard)                  │
   │  API views (booking, reporting,    │
   │  MongoDB analytics)                │
   └────┬────────────────────────────────┘
        │
   ┌────┴────────────────────────────────┐
   │           Service Layer             │
   │  booking_service.py                │
   │  reporting_service.py              │
   └────┬────────────────────────────────┘
        │
   ┌────┴──────────────┐   ┌───────────────────┐
   │   PostgreSQL 15   │   │    MongoDB 6       │
   │   Source of truth │   │    Read-optimised  │
   │   Transactional   │   │    Analytics       │
   └────────┬──────────┘   └────────▲───────────┘
            │                       │
            └──── manage.py run_etl ┘
                  (one-directional sync)
```

**Architectural invariants:**
- PostgreSQL is always the source of truth — all writes go here first
- MongoDB is never written to directly by the application
- ETL is one-directional: `PostgreSQL → MongoDB`
- If MongoDB is lost, it can be fully rebuilt from PostgreSQL via `run_etl`

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Web framework** | Django 4.2 |
| **API** | Django REST Framework (serializers), plain `JsonResponse` views |
| **Production server** | Gunicorn |
| **Transactional database** | PostgreSQL 15 |
| **Analytical database** | MongoDB 6 / MongoDB Atlas M0 |
| **Frontend** | Bootstrap 5, Chart.js 4 |
| **Static files** | WhiteNoise |
| **Containerisation** | Docker, Docker Compose |
| **CI/CD** | GitHub Actions |
| **Testing** | pytest, pytest-django ≥4.9, mongomock |
| **Security** | django-cors-headers, django-ratelimit, Sentry SDK |
| **Application hosting** | Render.com |

---

## Features

### Public (no login required)
- Browse 29 heritage sites with live search and province/category filters
- View site descriptions, entry fees, provinces, and categories
- Discover page — province and category breakdowns, featured sites, heritage facts
- MongoDB-backed analytical endpoints (average entry fee, sites per province)

### Registered members
- Create bookings with full input validation (email format, future dates, group size)
- Cancel upcoming bookings
- View booking history and upcoming visits in account page

### Administrators
- Protected analytics dashboard — booking statistics, monthly trends, site activity
- Export all booking data as CSV
- Full Django admin panel for managing sites, provinces, categories, and bookings
- Soft-delete sites (is_active flag) without losing booking history

### API
- 13 REST endpoints across booking, reporting, and MongoDB analytics layers
- DRF serializer validation on booking creation with per-field error messages
- Rate limiting: 10 POST requests per minute per IP on the booking endpoint
- CORS configured for cross-origin frontend access

---

## Data Model

```
Province ──────────┐
                   │
Category ──────────┤
                   │
             HeritageSite (site_id, name, description,
                   │        entry_fee, is_active)
                   │
                Booking ──── Visitor (visitor_id,
            (booking_id,              full_name,
             visit_date,              email UNIQUE)
             number_of_people,
             is_cancelled,
             cancelled_at)
```

**Key design decisions:**

| Decision | Rationale |
|---|---|
| `is_active` on HeritageSite (not hard delete) | Bookings reference sites by FK — deleting a site would orphan booking history |
| `entry_fee` nullable (not zero) | NULL means explicitly free; zero would be ambiguous |
| Province and Category as lookup tables | Prevents typo fragmentation in reporting queries |
| Visitor identified by email via `get_or_create` | Repeat visitors accumulate history without requiring an account |
| `is_cancelled` + `cancelled_at` (soft cancel) | Historical booking records are preserved for reporting |

---

## API Endpoints

### Frontend pages
| Method | Path | Description |
|---|---|---|
| GET | `/` | Heritage site catalogue with search and filters |
| GET | `/discover/` | Public discovery page — province/category charts, featured sites |
| GET | `/admin-dashboard/` | Staff-only analytics dashboard |
| GET | `/admin/` | Django admin panel |

### Booking API
| Method | Path | Description |
|---|---|---|
| POST | `/api/bookings/create/` | Create a booking — DRF validated, rate limited 10/min per IP |
| PATCH | `/api/bookings/<id>/cancel/` | Cancel a booking (soft cancel) |

### Reporting API (PostgreSQL-backed)
| Method | Path | Description |
|---|---|---|
| GET | `/api/reports/bookings-per-site/` | Booking count per site |
| GET | `/api/reports/average-group-size/` | Average number of people per booking |
| GET | `/api/reports/monthly-stats/` | Booking totals by calendar month |
| GET | `/api/reports/sites/` | All active sites with province names |
| GET | `/api/reports/province-counts/` | Site count per province (no booking data) |
| GET | `/api/reports/category-counts/` | Site count per category (no booking data) |
| GET | `/api/reports/featured/` | 3 randomly selected active sites |
| GET | `/api/reports/export/bookings/` | Download all bookings as CSV |
| GET | `/api/sites/<site_id>/` | Full site detail by ID |

### MongoDB analytical API
| Method | Path | Description |
|---|---|---|
| GET | `/api/mongo/sites/` | All sites from MongoDB (paginated: `?page=1&page_size=10`) |
| GET | `/api/mongo/sites/province/<name>/` | Sites filtered by province name |
| GET | `/api/mongo/sites/<name>/` | Single site document by name |
| GET | `/api/mongo/analytics/average-fee/` | Average entry fee across all sites |
| GET | `/api/mongo/analytics/sites-per-province/` | Site count grouped by province |

### Booking request body
```json
{
  "visitor_email":    "visitor@example.com",
  "visitor_name":     "Jane Doe",
  "site_id":          1,
  "visit_date":       "2026-10-15",
  "number_of_people": 2
}
```

### Booking success response (201)
```json
{
  "status":           "success",
  "booking_id":       42,
  "site":             "Cradle of Humankind",
  "visit_date":       "2026-10-15",
  "number_of_people": 2
}
```

---

## Getting Started

### Prerequisites
- Docker Desktop
- Git

### 1. Clone the repository
```bash
git clone https://github.com/Sinothando-Mthombeni/Heritage-Site-Information-System.git
cd Heritage-Site-Information-System/backend
```

### 2. Create your environment file
```bash
cp .env.example .env
```
Edit `.env` and fill in your values. For local Docker development, the defaults in `.env.example` work without changes.

### 3. Start the full stack
```bash
docker compose up --build -d
```
This starts three services: `web` (Django on port 8000), `postgres` (PostgreSQL 15), and `mongo` (MongoDB 6).

### 4. Run migrations
```bash
docker compose exec web python manage.py migrate
```

### 5. Load seed data
```bash
# 29 real South African heritage sites
docker compose exec web python manage.py load_seed

# Or with Wikidata-enriched descriptions and coordinates
docker compose exec web python manage.py load_seed --enriched
```

### 6. Sync to MongoDB
```bash
docker compose exec web python manage.py run_etl
```

### 7. Create an admin user
```bash
docker compose exec web python manage.py createsuperuser
```

### 8. Open the application
| URL | What you see |
|---|---|
| http://localhost:8000 | Heritage site catalogue |
| http://localhost:8000/discover/ | Public analytics and discovery |
| http://localhost:8000/admin/ | Django admin panel |
| http://localhost:8000/admin-dashboard/ | Staff analytics dashboard (requires superuser) |

---

## Environment Variables

| Variable | Description | Local Docker value |
|---|---|---|
| `SECRET_KEY` | Django secret key | Any long random string |
| `DEBUG` | Debug mode | `False` |
| `DB_NAME` | PostgreSQL database name | `heritage_db` |
| `DB_USER` | PostgreSQL username | `postgres` |
| `DB_PASSWORD` | PostgreSQL password | Set in `.env` |
| `DB_HOST` | PostgreSQL host | `postgres` (service name) |
| `DB_PORT` | PostgreSQL port | `5432` |
| `MONGO_URI` | MongoDB connection string | `mongodb://mongo:27017/` |
| `MONGO_DB_NAME` | MongoDB database name | `heritage_phase3` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1` |
| `SENTRY_DSN` | Sentry error monitoring DSN | Leave blank to disable |

> **Important:** `DB_HOST` must be `localhost` in GitHub Actions CI and when running Django locally outside Docker. It is only `postgres` when Django runs inside the Docker Compose network.

---

## Running Tests

```bash
# Run the full test suite (55 tests)
docker compose exec web python -m pytest -v

# Run a specific test file
docker compose exec web python -m pytest heritage_backend/tests/test_api.py -v

# Run a specific test class
docker compose exec web python -m pytest heritage_backend/tests/test_mongo.py::TestAverageEntryFee -v
```

### Test suite breakdown

| File | Tests | What is covered |
|---|---|---|
| `test_transactions.py` | 3 | Booking creation, rollback on invalid site, repeat visitor identity |
| `test_reporting.py` | 1 | Reporting service executes without error |
| `test_api.py` | 32 | Booking endpoint (positive + all negative paths), CORS headers, public page access, province/category/featured endpoints, reporting endpoints, model `__str__`, DB indexes |
| `test_mongo.py` | 19 | `average_entry_fee` (4), `sites_per_province` (4), Mongo API endpoints (7), analytics API endpoints (4) |

**Test design decisions:**
- MongoDB tests use `mongomock` — no live MongoDB instance required in test runs
- Rate limiting is disabled in tests via an autouse fixture (`settings.RATELIMIT_ENABLE = False`) — production rate limiting remains fully active
- CI uses disposable PostgreSQL 15 and MongoDB 6 service containers, never the production database

---

## Project Structure

```
Heritage-Site-Information-System/
├── .github/workflows/ci.yml          # GitHub Actions CI pipeline
├── render.yaml                        # Render deployment blueprint
├── README.md
└── backend/
    ├── Dockerfile
    ├── docker-compose.yml             # web + postgres + mongo
    ├── entrypoint.sh                  # migrate → collectstatic → gunicorn/runserver
    ├── settings.py                    # Django settings (reads from .env)
    ├── manage.py
    ├── requirements.txt               # Production dependencies
    ├── requirements-dev.txt           # pytest, pytest-django, mongomock
    ├── pytest.ini
    ├── .env.example                   # Environment variable template
    │
    ├── api/
    │   ├── serializers.py             # BookingSerializer (DRF)
    │   ├── views_pg.py                # Booking + cancel endpoints
    │   ├── views_mongo.py             # MongoDB read endpoints
    │   ├── views_reports.py           # Reporting + public aggregate endpoints
    │   ├── urls_pg.py
    │   ├── urls_mongo.py
    │   └── urls_reports.py
    │
    ├── heritage_backend/
    │   ├── urls.py                    # Root URL configuration
    │   ├── views_frontend.py          # Template views (home, discover, admin dashboard)
    │   ├── wsgi.py / asgi.py
    │   │
    │   ├── core/
    │   │   ├── models.py              # Province, Category, HeritageSite, Visitor, Booking
    │   │   ├── admin.py
    │   │   ├── migrations/
    │   │   │   ├── 0001_initial.py
    │   │   │   └── 0002_alter_category_options_...py  # Phase 1 schema changes
    │   │   ├── fixtures/
    │   │   │   ├── seed_data.json             # 29 SA heritage sites
    │   │   │   └── seed_data_enriched.json    # + Wikidata coordinates/descriptions
    │   │   └── management/commands/
    │   │       ├── load_seed.py       # manage.py load_seed [--enriched] [--flush]
    │   │       └── run_etl.py         # manage.py run_etl (Postgres → MongoDB)
    │   │
    │   ├── services/
    │   │   ├── booking_service.py     # create_booking(), cancel_booking()
    │   │   └── reporting_service.py   # bookings_per_site(), average_group_size(), etc.
    │   │
    │   ├── templates/heritage_backend/
    │   │   ├── base.html              # Navbar, booking modal, footer
    │   │   ├── home.html              # Site cards, search, filters
    │   │   ├── discover.html          # Public analytics and discovery
    │   │   └── admin_dashboard.html   # Staff-only operational analytics
    │   │
    │   └── tests/
    │       ├── conftest.py            # Fixtures: active_site, disable_rate_limiting
    │       ├── test_transactions.py
    │       ├── test_reporting.py
    │       ├── test_api.py
    │       └── test_mongo.py
    │
    ├── mongo/
    │   ├── client.py                  # MongoClient connection
    │   ├── analytics.py               # Aggregation pipelines
    │   └── heritage_sites.py          # Site query helpers
    │
    └── scripts/
        └── enrich_from_wikidata.py    # One-shot Wikidata SPARQL enrichment
```

---

## Deployment

### Current architecture

```
GitHub Actions CI          Render (application host)
    │                              │
    ├── Disposable PostgreSQL      ├── Django / Gunicorn
    ├── Disposable MongoDB         │
    └── pytest (55 tests)          ├── External PostgreSQL (source of truth)
                                   │
                                   └── MongoDB Atlas M0 (analytics)
```

The application host (Render) and database host are deliberately **separate** — application hosting and data persistence should not form a single failure domain.

### Local development

```bash
docker compose up --build -d     # Start all services
docker compose logs web -f       # Follow application logs
docker compose exec web python manage.py check  # Verify configuration
```

### Applying migrations to a hosted database

```powershell
# Set environment variables to point at the hosted database
$env:DB_HOST = "your-db-host.example.com"
$env:DB_NAME = "heritage_db"
$env:DB_USER = "heritage_user"
$env:DB_PASSWORD = "your-password"
$env:DB_PORT = "5432"
$env:SECRET_KEY = "any-value"
$env:DEBUG = "False"

# Run management commands locally against the hosted database
python manage.py migrate
python manage.py load_seed
python manage.py run_etl
python manage.py createsuperuser
```

---

## Roadmap

### Completed

| Phase | Description | Status |
|---|---|---|
| Foundation | Django setup, models, migrations, Docker, CI | ✅ Done |
| Data | 29 real SA heritage sites, Wikidata enrichment, seed commands | ✅ Done |
| API | Booking, cancellation, reporting, MongoDB analytics endpoints | ✅ Done |
| Frontend | Home page, discover page, admin dashboard, booking modal | ✅ Done |
| Phase 1 | CORS, rate limiting, Sentry, `__str__`, DB indexes, logging, UX cleanup | ✅ Done |
| Infrastructure | External PostgreSQL + portable backups + restore drill | 🔄 In progress |

### Planned

| Phase | Description | Effort |
|---|---|---|
| Phase 2 | MongoDB pagination, site detail page, CSV export completion | 3–4 days |
| Phase 3 | Authentication — register/login/account, user tiering (anonymous / member / admin) | 5–6 days |
| Phase 4 | API documentation — Swagger UI via drf-spectacular | 0.5 days |
| Phase 5 | Redis caching, PostgreSQL full-text search, Celery scheduled ETL | 3–4 days |
| Phase 6 | Site reviews and ratings, real-time WebSocket booking notifications | 5–7 days |
| Frontend redesign | Image-rich UI, site detail pages, responsive chart improvements | TBD |

---

## What This Project Demonstrates

This is a portfolio project intentionally designed to demonstrate engineering breadth beyond a basic CRUD application:

| Concept | How it's demonstrated |
|---|---|
| **Relational modelling** | Normalised PostgreSQL schema with FK constraints, soft delete, nullable fields with clear semantics |
| **Document modelling** | MongoDB denormalised documents with inlined province/category names for query performance |
| **Polyglot persistence** | Two databases with clearly defined roles — OLTP vs OLAP — and a one-directional ETL pipeline |
| **Service layer pattern** | Business logic in `services/` files, not in views or models — directly testable without HTTP |
| **REST API design** | POST for writes, correct HTTP status codes (201/400/401/405), per-field DRF error messages |
| **Input validation** | DRF BookingSerializer with field-level validators and a custom `validate_visit_date` |
| **Test engineering** | 55 tests across unit, integration, and API layers — including mongomock for offline MongoDB testing |
| **Test isolation** | Rate limiting disabled via autouse fixture, not by weakening production configuration |
| **CI/CD** | GitHub Actions pipeline with PostgreSQL and MongoDB service containers, matching the production stack |
| **Docker** | Multi-service Compose stack, `.dockerignore`, gunicorn/runserver switching in entrypoint |
| **Security** | CORS, rate limiting (10/min per IP), environment variables, `DEBUG=False` in production |
| **Data engineering** | ETL pipeline from SAHRIS/UNESCO source data, Wikidata SPARQL enrichment script |
| **Operational awareness** | Structured logging, Sentry error monitoring, WhiteNoise static serving, collectstatic in CI |
| **Database resilience** | Application host ≠ database host, `pg_dump` portable backups, documented restore procedure |

---

## Developer

**Sinothando Mthombeni**
IT Support Technician
BSc Information Technology, North-West University, 2025

- GitHub: [github.com/Sinothando-Mthombeni](https://github.com/Sinothando-Mthombeni)
- Portfolio: [sinothando-mthombeni.github.io/myportfolio](https://sinothando-mthombeni.github.io/myportfolio)
- LinkedIn: [linkedin.com/in/sinothando-mthombeni-211166363](https://linkedin.com/in/sinothando-mthombeni-211166363)

---

*HeritageSA is a solo portfolio project. All architectural decisions are intentional and documented. The system is designed to be understandable, maintainable, and progressively extensible — not to demonstrate enterprise scale.*
