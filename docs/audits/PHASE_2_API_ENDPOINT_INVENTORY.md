# Phase 2 API Endpoint Inventory

**Audit date:** 2026-10-27  
**Repository:** `Sinothando-Mthombeni/Heritage-Site-Information-System`  
**Branch / commit:** `main` / `66dfc5ac25ec03826c7bb8c61cdd5c5c586e023f`  
**Scope:** All URL patterns included under `/api/` by `backend/heritage_backend/urls.py`.
**Inventory note:** The first table records behavior at the audited baseline. The current post-remediation contracts are recorded at the end of this document.

## Route discovery and interpretation

`backend/heritage_backend/urls.py` includes `api.urls_mongo`, `api.urls_pg`, and `api.urls_reports` under `/api/`. Those modules register **16 API URL patterns**: 5 MongoDB, 2 booking, and 9 reporting/site-detail patterns. No DRF router or additional API URL include was found.

The root page, `/discover/`, `/admin-dashboard/`, and Django's `/admin/` are registered web/admin routes, not API routes. `/admin-dashboard/` is protected by `staff_member_required`; Django admin uses Django's admin authentication. API permission checks are not globally configured for the plain Django `JsonResponse` views.

At the audited baseline, most read endpoints lacked explicit HTTP method decorators and Mongo pagination was absent. The effective methods and contracts after remediation are listed below.

## API route inventory

| ID | Registered method / URL | Handler and source | Purpose / data source | Request contract and validation | Response contract / errors | Access control | Existing tests / status |
|---|---|---|---|---|---|---|---|
| API-01 | `POST /api/bookings/create/` | `create_booking_view` — `backend/api/views_pg.py:24-68` | Create visitor and booking in PostgreSQL through `BookingSerializer` and `create_booking`. | JSON object: `visitor_email`, `visitor_name`, positive `site_id`, `visit_date` (today or later), positive `number_of_people`. Malformed JSON returns 400. | 201: `status`, `booking_id`, `site`, `visit_date`, `number_of_people`; validation 400 with `errors`; malformed JSON 400 with `message`; broad service exception 400 with raw exception text; rate-limited 429. | Public; CSRF-exempt; POST rate limit 10/minute per IP. Authenticated user values are defaults only because request values are applied with `setdefault`. | `test_api.py::TestBookingEndpoint` exercises success and several validation paths; blocked by local PostgreSQL authentication in this run. **Implemented, needs correction** (error handling and identity policy); broader runtime evidence unverified. |
| API-02 | `PATCH /api/bookings/<int:booking_id>/cancel/` | `cancel_booking_view` — `backend/api/views_pg.py:70-83`; `cancel_booking` — `backend/heritage_backend/services/booking_service.py:35-47` | Soft-cancel a PostgreSQL booking. | Positive integer path ID; no body contract; view manually rejects non-PATCH with 405. Service rejects missing, already-cancelled, or past-visit bookings. | Success: `{"status":"cancelled","booking_id":...}`; missing 404; invalid state 400; unexpected error 400 with raw exception text. | Public; no authentication, ownership check, or staff check. | No cancellation tests found. **Implemented, needs correction** (authorization); runtime behavior unverified. |
| API-03 | `GET` intended: `/api/reports/bookings-per-site/` | `bookings_per_site_view` — `backend/api/views_reports.py:24-30`; service — `backend/heritage_backend/services/reporting_service.py:12-18` | Count PostgreSQL bookings grouped by `heritage_site__name`, descending by count. | No query parameters or body; no explicit method guard. | 200 JSON array of `{"heritage_site__name": string, "total": integer}`; empty data is `[]`. No endpoint-specific error handling. | Public. | `test_api.py::TestReportingEndpoints` checks list shape and presence after a booking, but not exact counts or duplicate site names; blocked in this run. **Implemented, needs correction** (group by site identity). |
| API-04 | `GET` intended: `/api/reports/average-group-size/` | `average_group_size_view` — `backend/api/views_reports.py:32-41`; service — `backend/heritage_backend/services/reporting_service.py:20-22` | Average `number_of_people` over all PostgreSQL bookings. | No parameters/body; no method guard. | 200 `{"average_group_size": number}`; empty booking table is represented as `0`. | Public. | Tests check empty result and one-booking result; blocked in this run. **Implemented, insufficiently tested** (mixed/cancelled booking semantics not specified or tested). |
| API-05 | `GET` intended: `/api/reports/monthly-stats/` | `monthly_booking_stats_view` — `backend/api/views_reports.py:44-55`; service — `backend/heritage_backend/services/reporting_service.py:24-35` | PostgreSQL raw SQL groups `booking.booking_date` by month. | No parameters/body; no method guard. | 200 JSON array of `{"month":"YYYY-MM","total_bookings": integer}`; empty data is `[]`. | Public. | Tests check list/row shape only, not exact boundary totals or cancellation policy; blocked in this run. **Implemented, insufficiently tested**. |
| API-06 | `GET` intended: `/api/reports/sites/` | `sites_with_provinces_view` — `backend/api/views_reports.py:58-67`; service — `backend/heritage_backend/services/reporting_service.py:9-10` | List PostgreSQL sites with province, fee, and active flag. | No parameters/body; no method guard. | 200 JSON array with `site_id`, `name`, `province__name`, `entry_fee`, `is_active`. The view's docstring says active sites, but the queryset currently includes inactive sites. | Public. | Tests check list and key shape only; blocked in this run. **Implemented, needs correction** (inactive rows contradict the stated contract). |
| API-07 | `GET` intended: `/api/reports/province-counts/` | `sites_by_province_count` — `backend/api/views_reports.py:70-73` | Count active PostgreSQL heritage sites per province. | No parameters/body; no method guard. | 200 JSON array with `province__name` and `count`; empty data is `[]`. | Public. | Test checks response shape with one fixture; blocked in this run. **Implemented, insufficiently tested** (aggregate correctness and empty case). |
| API-08 | `GET` intended: `/api/reports/category-counts/` | `sites_by_category_count` — `backend/api/views_reports.py:75-78` | Count active PostgreSQL sites per category. | No parameters/body; no method guard. | 200 JSON array with `category__name` and `count`; empty data is `[]`. | Public. | Test checks shape only; blocked in this run. **Implemented, insufficiently tested**. |
| API-09 | `GET` intended: `/api/reports/featured/` | `featured_sites_view` — `backend/api/views_reports.py:80-85` | Randomly select up to three active PostgreSQL sites. | No parameters/body; no method guard. | 200 JSON array with IDs, name, description, province, category, and numeric/null fee; empty data is `[]`. | Public. | Test checks nonempty fixture and keys; blocked in this run. **Implemented, insufficiently tested** (selection distribution, stable expectations, and empty case). |
| API-10 | `GET` intended: `/api/reports/export/bookings/` | `export_bookings_csv` — `backend/api/views_reports.py:94-107` | Stream all PostgreSQL bookings and visitor contact details as CSV. | No parameters/body; no method guard. | `text/csv`, attachment name `bookings.csv`; header order: `booking_id`, `visitor_name`, `visitor_email`, `site_name`, `visit_date`, `number_of_people`, `booking_date`, `is_cancelled`. No endpoint-specific error response. | **Public**, despite README describing export as an administrator function. | No CSV tests. **Implemented, needs correction** (access control, spreadsheet formula risk, and query memory behavior). |
| API-11 | `GET` intended: `/api/sites/<int:site_id>/` | `site_detail_view` — `backend/api/views_reports.py:87-92` | Read one active PostgreSQL site with province/category. | Integer path ID; no query/body validation; no method guard. | 200 object with `site_id`, `name`, `description`, `entry_fee`, `province`, `category`; inactive or nonexistent site returns 404 `status`/`message`. | Public. | No test found. **Implemented, insufficiently tested**. |
| API-12 | `GET` intended: `/api/mongo/sites/` | `all_heritage_sites` — `backend/api/views_mongo.py:12-13`; helper — `backend/mongo/heritage_sites.py:5-11` | Return all MongoDB `heritage_sites` documents excluding top-level `_id`. | No parameters/body validation; no method guard. README advertises `page`/`page_size`, but implementation ignores them. | 200 JSON array of documents; empty collection is `[]`. BSON values outside JSON-compatible types can fail serialization. | Public. | Endpoint tests exist but were blocked by PostgreSQL test DB setup; unit query tests do not cover pagination. **Implemented, needs correction** (documented pagination is absent; unbounded result). |
| API-13 | `GET` intended: `/api/mongo/sites/province/<str:province>/` | `heritage_sites_by_province` — `backend/api/views_mongo.py:15-16`; helper — `backend/mongo/heritage_sites.py:13-19` | Exact-match MongoDB filter by province. | Province in path; no normalization/validation; no query parameters or method guard. | 200 JSON array; no matches return `[]`. | Public. | Endpoint tests exist for match/no-match but were blocked by PostgreSQL test DB setup. **Implemented, insufficiently tested** (inactive-site and error behavior). |
| API-14 | `GET` intended: `/api/mongo/sites/<str:name>/` | `heritage_site_detail` — `backend/api/views_mongo.py:18-20`; helper — `backend/mongo/heritage_sites.py:21-25` | Exact-match MongoDB site lookup by name. | Name in path; no validation or method guard. | 200 matching object; absent name returns `{}` with 200, unlike PostgreSQL detail's 404. | Public. | Endpoint tests exist for match and absent name but were blocked by PostgreSQL test DB setup. **Implemented, needs correction** (ambiguous missing-record contract). |
| API-15 | `GET` intended: `/api/mongo/analytics/sites-per-province/` | `analytics_sites_per_province` — `backend/api/views_mongo.py:22-23`; aggregation — `backend/mongo/analytics.py:5-10` | MongoDB `$group` and `$sort` across all site documents. | No parameters/body; no method guard. | 200 array of `{"_id": province, "count": integer}`; empty collection is `[]`. | Public. | Unit aggregation tests pass; HTTP tests exist but were blocked by PostgreSQL test DB setup. **Implemented, insufficiently tested** (active/inactive semantics and Mongo outage). |
| API-16 | `GET` intended: `/api/mongo/analytics/average-fee/` | `analytics_average_fee` — `backend/api/views_mongo.py:25-26`; aggregation — `backend/mongo/analytics.py:12-23` | MongoDB average of non-null `entry_fee` values across all site documents. | No parameters/body; no method guard. | 200 `{"average_fee": number}`; no matching fees returns `0`. | Public. | Unit tests pass for empty, null, and numeric data; HTTP tests exist but were blocked by PostgreSQL test DB setup. **Implemented, insufficiently tested** (active/inactive policy and Mongo outage). |

## Related registered non-API routes

| Method / URL | Handler | Access / note |
|---|---|---|
| `GET /` | `home_view` — `backend/heritage_backend/views_frontend.py:6-12` | Public HTML; PostgreSQL; filters active sites before rendering. |
| `GET /discover/` | `discover_view` — `backend/heritage_backend/views_frontend.py:15-20` | Public HTML; PostgreSQL counts. |
| `GET /admin-dashboard/` | `admin_dashboard_view` — `backend/heritage_backend/views_frontend.py:23-25` | Staff-only HTML; its browser JavaScript fetches public reports, including the unprotected CSV route. |
| `/admin/` | Django admin site — `backend/heritage_backend/urls.py:9` | Django admin authentication/permissions; not counted among the 16 API patterns. |

## Baseline contract and requirements notes

- At the audited baseline, the root README enumerated 16 paths but said there were “13 REST endpoints” (`README.md:123`); the current README now reports 16 API routes.
- The baseline README/roadmap promised MongoDB list pagination (`README.md:209-210, 464-465`); pagination is implemented and its current contract is recorded below.
- `REST_FRAMEWORK` sets a default paginator and page size in `backend/settings.py:129-132`, but these function-based views return `JsonResponse` and do not use DRF pagination.
- `docs/requirements.md:8` states reviews may follow a booking. No Review model or review route exists; the README explicitly defers reviews to Phase 6 (`README.md:468`). Treat this as a deferred requirement, not a Phase 2 API omission.
- At the baseline, API documentation described cancellation and CSV export as member/admin functionality, but those API routes had no equivalent permission check.

## Current inventory after Phase 2 remediation

The 16 registered routes remain unchanged. The method, permission, and response details below describe the current working tree and supersede baseline behavior above.

| Route | Current behavior, visibility, and response contract |
|---|---|
| `POST /api/bookings/create/` | Public, rate-limited to 10/minute/IP. Requires a JSON object; invalid or non-object JSON returns 400, a non-empty unsupported media type returns 415, serializer/missing-site errors return sanitized 400, data-store failures return 503, and unexpected failures return generic 500. Success remains 201. |
| `PATCH /api/bookings/<id>/cancel/` | Temporarily disabled: returns 503 without querying or modifying a booking. Other methods return 405. No submitted email or booking ID establishes ownership. |
| `GET /api/reports/bookings-per-site/` | PostgreSQL aggregation returns `heritage_site_id`, the existing site name/province fields, and `total`; groups by stable site ID, orders by count then ID, excludes cancelled bookings. |
| `GET /api/reports/average-group-size/` | Returns `{"average_group_size": number}` over non-cancelled bookings; empty data returns zero. |
| `GET /api/reports/monthly-stats/` | Returns monthly non-cancelled booking totals grouped by `booking_date` (booking creation date), not `visit_date`. |
| `GET /api/reports/sites/` | Returns active PostgreSQL sites only, preserving existing fields. |
| `GET /api/reports/province-counts/` | Counts active PostgreSQL sites by province. |
| `GET /api/reports/category-counts/` | Counts active PostgreSQL sites by category. |
| `GET /api/reports/featured/` | Returns up to three randomly selected active PostgreSQL sites. |
| `GET /api/reports/export/bookings/` | Requires authenticated staff; anonymous/non-staff callers receive 403 before querying. CSV filename and original column order are retained; formula-leading text values are neutralized; rows are streamed using `QuerySet.iterator()`. |
| `GET /api/sites/<int:site_id>/` | Returns an active PostgreSQL site; inactive or missing IDs return 404. |
| `GET /api/mongo/sites/` | Active Mongo projection sites only, ordered by `site_id`; accepts positive `page` (default 1) and `page_size` (default 10, maximum 100). Invalid values or a skip offset outside signed 64-bit bounds return 400. Existing bare JSON-array response is retained. |
| `GET /api/mongo/sites/province/<province>/` | Returns active Mongo projection sites matching the province; stable site-ID order. |
| `GET /api/mongo/sites/<name>/` | Returns the first active Mongo projection site by name in stable site-ID order; missing name returns 404. |
| `GET /api/mongo/analytics/sites-per-province/` | Counts active Mongo projection sites only; provinces without active sites do not appear. |
| `GET /api/mongo/analytics/average-fee/` | Averages non-null fees for active Mongo projection sites only; empty data returns zero. |

All reporting and Mongo read routes are GET-only; unsupported methods return 405. Expected PostgreSQL/Mongo service failures return sanitized 503 responses, and unexpected API errors return generic 500 responses without exception details. PostgreSQL remains the authoritative source; Mongo output reflects the most recently successful manual ETL refresh.

### Remediation evidence and dispositions

| Finding | Final status | Evidence |
|---|---|---|
| SEC-01 | Fixed and verified | Anonymous and authenticated non-staff exports return 403; staff CSV contract and content are tested. |
| SEC-02 | Fixed and verified | Cancellation returns 503 before service access; non-PATCH methods return 405. Permanent owner linkage is deferred to Phase 3. |
| SEC-03 | Fixed and verified | Formula-leading name, email, and site text are neutralized in parsed CSV output. |
| API-F01 | Fixed and verified | Default, maximum, multiple-page, invalid, and oversized pagination inputs are covered. |
| API-F02 | Fixed and verified | Public PostgreSQL and Mongo catalogue/report paths exclude inactive sites under the confirmed policy. |
| API-F03 | Fixed and verified | PostgreSQL and Mongo reports group by site ID and retain existing display fields. |
| API-F04 | Fixed and verified | Tests confirm missing-site validation and sanitized 503/500 responses. |
| API-F05 | Fixed and verified | Read routes return 405 for unsupported methods; Mongo and PostgreSQL missing-site details return 404. |
| API-F06 | Fixed and verified | Live isolated Mongo tests cover staged publication, index setup/preservation, source failure, and ambiguous pointer-write failure. |
| API-F07 | Fixed and verified | CSV export uses `.iterator(chunk_size=2000)` and CSV output is regression-tested. |
| API-F08 | Fixed and verified | Production settings reject absent, blank, and known development/template keys without displaying values. |
| API-F09 | Not applicable, with evidence | No Review model or endpoint exists; requirements and README place reviews/ratings in Phase 6. |

The report policy was explicitly confirmed for this remediation: cancelled bookings are excluded from PostgreSQL and Mongo booking-count, monthly, and average-group-size reports; monthly grouping remains `booking_date`. Inactive Mongo sites remain stored but do not contribute to public catalogue, province-count, or average-fee output.
