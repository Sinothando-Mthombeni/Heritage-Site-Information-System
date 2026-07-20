# Heritage Site Information System

A full-stack web application for managing and analysing cultural heritage site data across South Africa's nine provinces. Built as a portfolio project demonstrating polyglot persistence, REST API design, ETL pipeline engineering, containerised deployment, and CI/CD.

[![CI](https://github.com/Sinothando-Mthombeni/Heritage-Site-Information-
System/actions/workflows/ci.yml/badge.svg)](https://github.com/Sinothando-
Mthombeni/Heritage-Site-Information-System/actions/workflows/ci.yml)


---

## Architecture

```
Client (Browser / Postman / curl)
          │
          ▼
   Django Application
   ┌──────────────────────────────────────────┐
   │  urls.py (routing)                       │
   │     │                      │             │
   │  views_pg.py          views_mongo.py     │
   │  (transactional)      (analytical)       │
   │     │                      │             │
   │  services/            mongo/client.py    │
   │  booking_service      analytics.py       │
   │  reporting_service         │             │
   │     │                      │             │
   │  core/models.py         pymongo          │
   └──────│──────────────────────│────────────┘
          │ ORM/SQL              │
          ▼                      ▼
    PostgreSQL              MongoDB
   (transactional)         (analytical)
   source of truth    ◄── ETL ──► sync
```

**PostgreSQL** is the source of truth for all transactional data (sites, bookings, visitors). **MongoDB** holds a denormalised, read-optimised copy for analytics and reporting queries. A one-directional ETL pipeline (`manage.py run_etl`) syncs Postgres → Mongo. Mongo is never written to directly by the application.

This is an intentional implementation of the OLTP/OLAP separation pattern — the same architectural split used in production systems between an application's primary database and its data warehouse.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | Django 4.2, Django REST Framework |
| Transactional database | PostgreSQL 15 |
| Analytical database | MongoDB 6 |
| ETL | Custom Python pipeline (psycopg2 + pymongo) |
| Testing | pytest, pytest-django |
| Containerisation | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| Language | Python 3.11 |

---

## Data Model

Five entities in PostgreSQL:

```
Province ──< HeritageSite >── Category
                  │
              Booking
                  │
              Visitor
```

- **Province** — South Africa's nine provinces (lookup table)
- **Category** — Site type: UNESCO WHS, Museum, Natural Reserve, Archaeological Site, Historical Monument, Cultural Village
- **HeritageSite** — Core entity. Normalised FK references to province and category; `entry_fee` is nullable (free sites stored as NULL, not zero); `is_active` is a soft-delete flag to preserve booking history
- **Visitor** — Identified by email, created on first booking (`get_or_create` pattern)
- **Booking** — Links a visitor to a site for a specific visit date

MongoDB stores denormalised documents in two collections:

- **heritage_sites** — site data with province/category names inlined (no joins needed for read)
- **bookings** — booking data with site name, province, and visitor details inlined

---

## Seed Data

29 curated real South African heritage sites covering all nine provinces:

| Category | Count | Examples |
|---|---|---|
| UNESCO World Heritage Site | 11 | Robben Island, Cradle of Humankind, iSimangaliso Wetland Park |
| Museum & Memorial | 7 | Apartheid Museum, Constitution Hill, District Six Museum |
| Historical Monument | 4 | Castle of Good Hope, Voortrekker Monument, Pilgrim's Rest |
| Natural Reserve | 3 | Blyde River Canyon, Addo Elephant Park, Pilanesberg |
| Cultural Village | 3 | Shakaland, Botshabelo Ndebele Village, Mapoch Ndebele Village |
| Archaeological Site | 1 | Sterkfontein Caves |

An optional Wikidata enrichment script (`scripts/enrich_from_wikidata.py`) queries Wikidata's SPARQL endpoint by QID for each site and adds English descriptions, GPS coordinates, and Wikimedia Commons image URLs.

---

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Git

### 1. Clone the repository

```bash
git clone https://github.com/Sinothando-Mthombeni/Heritage-Site-Information-System.git
cd Heritage-Site-Information-System/backend
```

### 2. Start the stack

```bash
docker compose up --build
```

This starts three containers: `web` (Django on port 8000), `postgres` (port 5432), and `mongo` (port 27017). Django runs migrations and collects static files automatically on startup via `entrypoint.sh`.

### 3. Load seed data

In a second terminal:

```bash
docker compose exec web python manage.py load_seed
```

Options:
```bash
python manage.py load_seed              # load base seed (29 sites)
python manage.py load_seed --enriched   # load Wikidata-enriched version (if generated)
python manage.py load_seed --flush      # wipe existing data then reload
```

### 4. Run the ETL (Postgres → MongoDB)

```bash
docker compose exec web python manage.py run_etl
```

This syncs all heritage sites and bookings from PostgreSQL into MongoDB. Run after any data change to keep analytics endpoints current.

### 5. Verify

```bash
# Check record counts
docker compose exec web python manage.py shell -c "
from heritage_backend.core.models import HeritageSite, Province, Category, Booking
print('Sites:', HeritageSite.objects.count())
print('Provinces:', Province.objects.count())
print('Categories:', Category.objects.count())
print('Bookings:', Booking.objects.count())
"

# Hit the API
curl http://localhost:8000/api/mongo/sites/
```

---

## API Reference

All endpoints served at `http://localhost:8000`.

### Transactional endpoints (PostgreSQL-backed)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/bookings/create/` | Create a booking |

**Example — create a booking:**
```bash
curl -X POST http://localhost:8000/api/bookings/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "visitor_email": "jane@example.com",
    "visitor_name": "Jane Doe",
    "site_id": 1,
    "visit_date": "2026-09-15",
    "number_of_people": 2
  }'
```

**Success response (201):**
```json
{
  "status": "success",
  "booking_id": 1,
  "site": "Cradle of Humankind",
  "visit_date": "2026-09-15",
  "number_of_people": 2
}
```

### Analytical endpoints (MongoDB-backed)

> Requires `manage.py run_etl` to have been run first.

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/mongo/sites/` | All heritage sites |
| `GET` | `/api/mongo/sites/<province>/` | Sites filtered by province |

**Example:**
```bash
curl "http://localhost:8000/api/mongo/sites/Mpumalanga/"
```

### Reporting endpoints (PostgreSQL-backed)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/reports/bookings-per-site/` | Booking count grouped by site |
| `GET` | `/api/reports/average-group-size/` | Average number of people per booking |
| `GET` | `/api/reports/monthly-stats/` | Booking counts grouped by month |
| `GET` | `/api/reports/sites/` | All sites with province names |

### Admin

```bash
# Create a superuser first
docker compose exec web python manage.py createsuperuser

# Then visit
http://localhost:8000/admin/
```

---

## Running Tests

```bash
docker compose exec web pytest -v
```

Current coverage: booking creation, booking rollback on invalid site, reporting service queries.

---

## Optional: Wikidata Enrichment

Run once on your local machine (not inside Docker) to add GPS coordinates, descriptions, and image URLs from Wikidata:

```bash
cd backend
python scripts/enrich_from_wikidata.py
# Takes ~30 seconds — queries Wikidata SPARQL by QID for each of the 29 sites

docker compose exec web python manage.py load_seed --enriched --flush
docker compose exec web python manage.py run_etl
```

---

## Project Structure

```
Heritage-Site-Information-System/
└── backend/
    ├── settings.py
    ├── manage.py
    ├── Dockerfile
    ├── docker-compose.yml
    ├── entrypoint.sh
    ├── requirements.txt
    ├── requirements-dev.txt
    ├── pytest.ini
    ├── scripts/
    │   └── enrich_from_wikidata.py
    ├── api/
    │   ├── views_pg.py
    │   ├── views_mongo.py
    │   ├── views_reports.py
    │   ├── urls_pg.py
    │   ├── urls_mongo.py
    │   └── urls_reports.py
    ├── heritage_backend/
    │   ├── urls.py
    │   ├── core/
    │   │   ├── models.py
    │   │   ├── fixtures/
    │   │   │   ├── seed_data.json
    │   │   │   └── seed_data_enriched.json
    │   │   ├── management/commands/
    │   │   │   ├── load_seed.py
    │   │   │   └── run_etl.py
    │   │   └── migrations/
    │   ├── services/
    │   │   ├── booking_service.py
    │   │   └── reporting_service.py
    │   └── tests/
    │       ├── conftest.py
    │       ├── test_transactions.py
    │       └── test_reporting.py
    └── mongo/
        ├── client.py
        └── analytics.py
```

---

## Environment Variables

| Variable | Description | Docker default |
|---|---|---|
| `SECRET_KEY` | Django secret key | — |
| `DEBUG` | Debug mode | `False` |
| `DB_NAME` | PostgreSQL database name | `*******` |
| `DB_USER` | PostgreSQL user | `*******` |
| `DB_PASSWORD` | PostgreSQL password | `******` |
| `DB_HOST` | PostgreSQL host | `postgres` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `MONGO_URI` | MongoDB connection URI | `mongodb://mongo:27017/` |
| `MONGO_DB_NAME` | MongoDB database name | `heritage_phase3` |

> **Local dev (Django outside Docker):** create `backend/.env.local` with `DB_HOST=localhost` and `MONGO_URI=mongodb://localhost:27017/`. Add `load_dotenv(BASE_DIR / ".env.local", override=True)` to `settings.py` after the base `load_dotenv` call.

---

## Known Limitations

Intentional omissions appropriate for portfolio scope, documented here rather than left as silent gaps:

- **No authentication** — all API endpoints are publicly accessible. Production would use DRF Token Authentication or JWT.
- **No rate limiting** — no throttling on write endpoints.
- **ETL is manual** — sync is triggered manually. Production would schedule via cron, Celery Beat, or a cloud scheduler.
- **No pagination** on list endpoints — acceptable at 29-site seed scale.
- **MongoDB test coverage** — the test suite covers the PostgreSQL/booking path only; MongoDB analytics are not yet unit-tested.
- **No CORS configuration** — a frontend on a different origin would need `django-cors-headers`.

---

## Development Workflow

```bash
docker compose up --build             # start the stack
docker compose exec web pytest -v     # run tests
docker compose exec web python manage.py check   # check configuration
docker compose logs web --tail=50 -f  # follow logs
```

---

## Author

**Sinothando Mthombeni**
BSc Information Technology — North-West University (2025)
IT Support Technician Intern — Mpumalanga Economic Growth Agency (MEGA)

- GitHub: [github.com/Sinothando-Mthombeni](https://github.com/Sinothando-Mthombeni)
- LinkedIn: [linkedin.com/in/sinothando-mthombeni-211166363](https://linkedin.com/in/sinothando-mthombeni-211166363)
- Portfolio: [sinothando-mthombeni.github.io/myportfolio](https://sinothando-mthombeni.github.io/myportfolio)
- Email: sinopapi7@gmail.com
