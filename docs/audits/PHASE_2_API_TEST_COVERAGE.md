# Phase 2 API Test Coverage Matrix

**Audited commit:** `66dfc5ac25ec03826c7bb8c61cdd5c5c586e023f` (`main`)  
**Total discovered API routes:** 16  
**Test result:** 55 collected; 8 pure Mongo unit tests passed; the other 47 database-backed tests errored during PostgreSQL test DB setup because local authentication failed.
**Coverage note:** The matrix below is the historical baseline. The current remediation suite and final results are recorded at the end of this document.

## Coverage matrix

Legend:

- **Present**: a test is in the repository; not necessarily executed successfully in this environment.
- **Passed**: executed successfully in the audit environment.
- **Blocked**: test setup errored before reaching the assertion.
- **Missing**: no relevant test found.
- **Partial**: covers shape/basic path but not the stated business edge cases.

| Endpoint / behavior | Success path | Validation / boundary | Error path | Security | Integration | Existing coverage and audit result | Recommended regression tests |
|---|---|---|---|---|---|---|---|
| `POST /api/bookings/create/` | Present, Blocked | Present for missing/invalid email, name, past date, zero/negative count; malformed/empty JSON; today accepted. Missing content-type, non-object JSON, wrong types, whitespace email, inactive site, and oversized payload not covered. | Partial: malformed and serializer errors; database outage mapping not covered. | Missing: anonymous vs authenticated identity binding, rate-limit response behavior, abuse controls. | Present, Blocked | `test_api.py::TestBookingEndpoint`; service creation in `test_transactions.py`. | Authenticated body cannot override account identity if policy is account-bound; inactive/nonexistent site; invalid JSON shapes/content types; database error is sanitized 5xx; visitor rollback assertion; email normalization policy; rate limit. |
| `PATCH /api/bookings/<id>/cancel/` | Missing | Missing for wrong method, cancelled, past, current/future dates. | Missing for missing booking and unexpected DB failure. | Missing: anonymous denial, owner-only cancellation, staff path. | Missing | No cancellation test found; not executed. | Owner may cancel own valid booking; other owner/anonymous denied; unknown ID 404; past/repeated transition; wrong verb 405 with `Allow`; state fields update together. |
| `/api/reports/bookings-per-site/` | Present, Blocked | Partial: no exact counts, equal site names in different provinces, cancellations, empty case. | Missing database outage behavior. | Missing endpoint access policy tests (aggregate is public by design unless changed). | Present, Blocked | `test_api.py::TestReportingEndpoints::test_bookings_per_site_*`; `test_reporting.py` only checks non-`None`. | Exact grouped totals keyed by site ID; same-name/different-province sites remain distinct; cancellation policy. |
| `/api/reports/average-group-size/` | Present, Blocked | Partial: empty and one booking only; no rounding/mixed/cancelled fixture. | Missing DB error behavior. | Missing. | Present, Blocked | `test_average_group_size_*` in `test_api.py`. | Exact mean across multiple sizes, rounding, empty, cancelled booking policy. |
| `/api/reports/monthly-stats/` | Present, Blocked | Partial: row shape only; no month boundary/timezone or exact counts. | Missing DB error behavior. | Missing. | Present, Blocked | `test_monthly_stats_*` in `test_api.py`. | Exact booking-date grouping across month/year boundary; empty; cancellation policy; stable month serialization. |
| `/api/reports/sites/` | Present, Blocked | Partial: list and keys; inactive site filtering not asserted. | Missing. | Missing. | Present, Blocked | `test_sites_with_provinces_*` in `test_api.py`. | Include active, exclude inactive; confirm response contract and decimals/null fee. |
| `/api/reports/province-counts/` | Present, Blocked | Partial: one fixture shape only; no exact multi-province or empty count. | Missing. | Missing. | Present, Blocked | `test_province_counts_shape` in `test_api.py`. | Exact counts across active/inactive sites and empty table. |
| `/api/reports/category-counts/` | Present, Blocked | Partial: response fields only. | Missing. | Missing. | Present, Blocked | `test_category_counts_shape` in `test_api.py`. | Exact counts and inactive/empty behavior. |
| `/api/reports/featured/` | Present, Blocked | Partial: nonempty fixture/keys; no upper bound, duplicates, empty, or active-only assertions. | Missing. | Missing. | Present, Blocked | `test_featured_sites_shape` in `test_api.py`. | Empty; no inactive rows; no more than 3 unique IDs; deterministic injection of sampling for tests. |
| `/api/reports/export/bookings/` | Missing | Missing: headers/order, empty output, Unicode, commas/newlines, date format, formula-leading text. | Missing. | Missing: anonymous denial and staff access tests. | Missing | No CSV tests found; route source inspected only. | Anonymous denied; staff permitted; exact content-type/disposition/header/order; UTF-8; formula neutralization; cancelled rows policy; empty export. |
| `/api/sites/<id>/` | Missing | Missing: invalid ID/inactive site. | Missing 404 assertion. | Missing. | Missing | No test found. | Active site fields/fee/null; inactive and missing 404; invalid path ID; unsupported method. |
| `/api/mongo/sites/` | Present, Blocked | Partial: seeded, empty, `_id` projection; no pagination, inactive filtering, serialization edge, or method checks. | Missing Mongo outage tests. | Missing. | Present, Blocked | Mongo route tests in `test_mongo.py::TestMongoSitesEndpoints`; PostgreSQL setup blocks before body. | Page/page_size validation and stable page envelope; active-only behavior; BSON-safe serialization; Mongo unavailable controlled response; unsupported method. |
| `/api/mongo/sites/province/<province>/` | Present, Blocked | Partial: match/no match; no Unicode/case policy/inactive docs. | Missing Mongo outage tests. | Missing. | Present, Blocked | Province match/no-match tests in `TestMongoSitesEndpoints`; Blocked. | Unicode/path encoding, no results, active-only filtering, error response, method restriction. |
| `/api/mongo/sites/<name>/` | Present, Blocked | Partial: match and absent returns `{}`/200; no malformed/unicode document tests. | Missing: expected 404 contract and DB failure. | Missing. | Present, Blocked | Detail tests in `TestMongoSitesEndpoints`; Blocked. | Matching document; absent 404; Unicode; unexpected BSON; controlled outage. |
| `/api/mongo/analytics/sites-per-province/` | Present, Blocked; aggregation unit Passed | Partial: grouping/order/empty unit cases; no inactive filtering or connection errors. | Missing endpoint DB failure. | Missing. | Present, Blocked | `TestSitesPerProvince` unit cases: **4 passed**; HTTP route tests Blocked. | Active/inactive policy, non-string/missing province, endpoint serialization, outage response. |
| `/api/mongo/analytics/average-fee/` | Present, Blocked; aggregation unit Passed | Partial: empty/null/single/two-value unit cases; no active filtering or invalid fee types. | Missing endpoint DB failure. | Missing. | Present, Blocked | `TestAverageEntryFee` unit cases: **4 passed**; HTTP route tests Blocked. | Inactive-site policy, malformed fee data, endpoint JSON contract, outage response. |
| Booking rollback on invalid site | Present, Blocked | Partial: test asserts zero bookings but does not assert Visitor rollback. | Present only as broad exception swallowed by test. | N/A | Present, Blocked | `test_transactions.py::test_booking_rollback_on_invalid_site`; blocked. | Assert no visitor persists; assert exception type and transaction state. |
| Mongo aggregation helpers | Passed | Present for empty/null/single/multiple/count/order cases. | Not applicable to mocked database outage. | N/A | Unit only, not live integration. | `TestAverageEntryFee` and `TestSitesPerProvince`: **8 passed** in 2.73s. | Keep unit tests; add helper validation for malformed projected documents if that state is supported. |
| Frontend/admin route access | Present, Blocked | Partial. | Partial redirect test. | Partial: staff dashboard anonymous redirect; no export API permission test. | Present, Blocked | `TestPublicDiscoverPage`; DB test setup blocked. | Staff/nonstaff dashboard; independently enforce and test report/export endpoint permissions. |
| URL/method contract | Partial, Blocked | One `GET` to booking-create returns 405. No consistent GET-only tests for reads. | Missing for unsupported methods on other endpoints. | Missing. | Partial | `test_get_request_returns_405`; blocked. | Resolve every registered route; assert allowed methods and `Allow` header; unexpected method never executes business query. |

## Existing test execution evidence

| Command | Result |
|---|---|
| `python manage.py check` | Passed; no system-check issues. |
| `python -m pytest -v` | Collected 55; 8 passed, 47 setup errors, 1 warning. Errors were PostgreSQL password authentication failures while creating/accessing the local Django test database, before test assertions. |
| `python -m pytest -q heritage_backend/tests/test_mongo.py::TestAverageEntryFee heritage_backend/tests/test_mongo.py::TestSitesPerProvince` | 8 passed using mongomock, no PostgreSQL writes. |
| `python manage.py makemigrations --check --dry-run` | Exit 0, no model changes detected; migration history check warned because local PostgreSQL authentication failed. |

The CI workflow configures its own disposable services and runs pytest, but no remote workflow execution was performed. No coverage percentage was generated; existing tests are too shallow to establish report arithmetic, cancellation authorization, export safety, or live database outage behavior.

## Current Phase 2 regression coverage

The following results supersede the baseline execution table above. The full test run used Python 3.11.9 with dedicated local PostgreSQL 17 and MongoDB 8 services; no production URL or production service was used.

| Requirement / regression | Current automated evidence |
|---|---|
| CSV authorization and compatibility | Anonymous/non-staff denial, staff allow, exact response headers/filename/column order, empty export, formula-leading name/email/site values, comma/newline quoting. |
| Cancellation containment | PATCH returns 503 without calling the cancellation service; other methods return 405. |
| PostgreSQL report arithmetic | Exact counts/averages, cancelled-row exclusion, duplicate site names across provinces, and `booking_date` grouping distinct from `visit_date`. |
| Mongo report semantics | Cancelled-row exclusion, stable site identity, exact month totals, empty/null aggregate results, and PostgreSQL/Mongo parity. |
| Active-site visibility | Public PostgreSQL and Mongo catalogue/detail/count/fee routes exclude inactive sites; inactive-only province/category/site behavior is asserted. |
| Mongo pagination | Default page and size, page-size maximum 100, stable ordering, multi-page results, invalid and negative values, and an offset exceeding signed 64-bit bounds. Existing bare-array response is asserted by route tests. |
| Error and method handling | Database/service errors return sanitized 503, unexpected API errors return sanitized 500, missing active sites return 404/400 as contracted, and public read routes reject POST with 405. |
| ETL refresh safety | Live isolated MongoDB verifies staging and pointer publication, new index creation, old projection and indexes retained after source failure, and active staging collections retained after an ambiguous pointer-write acknowledgement. |
| Test-environment isolation | Subprocess regressions verify database URL variables, non-local PostgreSQL hosts, and non-local Mongo URIs are rejected before tests can connect. |
| Production secret-key validation | Missing, blank, built-in development, and documented template values are rejected when debug is disabled, without including values in errors. |

### Final verification results

| Command / check | Result |
|---|---|
| Python 3.11.9 `python -m pytest -q` | **104 passed in 186.16s** on the final code state. |
| `python manage.py check` with `DJANGO_SETTINGS_MODULE=test_settings` | Passed; no system-check issues. |
| `python manage.py makemigrations --check --dry-run` with test settings | Passed; no model changes detected. |
| `python manage.py migrate --noinput` with test settings | Passed against the isolated `heritage_phase2_test` database. |
| `python manage.py collectstatic --noinput` with test settings | Passed; 152 files copied. |
| GitHub Actions | Not run remotely. The local CI-equivalent sequence passed using PostgreSQL 17/MongoDB 8; CI workflow services are PostgreSQL 15/MongoDB 6. |
| Coverage percentage | Not collected. |

The per-file collected counts are 2 `test_transactions.py`, 1 `test_reporting.py`, 33 `test_api.py`, 40 `test_mongo.py`, 25 `test_phase2_remediation.py`, and 3 `test_etl.py` (104 total).
