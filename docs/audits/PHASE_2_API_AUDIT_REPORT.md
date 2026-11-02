# Phase 2 API Completeness Audit — HeritageSA

**Audit date:** 2026-10-27  
**Repository:** `https://github.com/Sinothando-Mthombeni/Heritage-Site-Information-System`  
**Branch audited:** `main`  
**Audited commit:** `66dfc5ac25ec03826c7bb8c61cdd5c5c586e023f`  
**Working tree at start:** clean  
**Audit scope:** Read-only source, documentation, tests, CI and deployment-configuration assessment; no application or infrastructure fixes applied.

## Executive summary — audited baseline

The API is **partially complete** for the documented Phase 2 scope. The three included URL modules register 16 API patterns, and all 16 were traced through their handlers and backing services/helpers. PostgreSQL is the transactional source of truth; MongoDB is populated by a one-way management-command ETL and is read by the Mongo site and analytics routes.

The most important verified issue is a **high-severity public disclosure of every booking's visitor name and email** through the CSV export. The cancellation route also accepts a public booking ID without owner verification, allowing cancellation of another visitor's eligible booking. These endpoints should not be treated as administrator/member-protected merely because their links or UI are shown on a staff page.

Additional Phase 2 gaps include missing Mongo pagination despite explicit README/roadmap promises, inactive site exposure on list routes, a per-site report grouped by non-unique site name, weak exception/status handling, and no tests for cancellation, PostgreSQL site detail, or CSV output. No numerical report was proven incorrect for an established policy: booking reports currently include cancelled bookings, but the intended cancellation policy for those totals is undocumented.

**Route counts:** 16 API patterns discovered; 16 source-assessed.  
**Security findings:** 0 Critical, 1 High, 2 Medium (one Medium is a potential spreadsheet-formula risk rather than a reproduced exploit).  
**Data-integrity highlights:** create is transaction-wrapped and validates active site/date/group size; cancellation checks state/date but not caller ownership; no DB constraint enforces the paired `is_cancelled`/`cancelled_at` values.  
**Tests:** 55 collected; the full run yielded 8 passed and 47 setup errors because the local PostgreSQL service rejected the explicitly supplied non-production password. Eight isolated Mongo aggregation unit tests passed. Django system checks passed.  
**Limitations:** No database-backed tests or live Mongo/API integration tests could be completed; deployed secrets, services, and production behavior were not inspected.

**Recommended first remediation:** make `/api/reports/export/bookings/` unavailable to anonymous callers or require an authenticated staff permission check before data access/streaming, then add a regression test proving anonymous denial and authorized access. Do not use the current route as a public endpoint.

## Scope and methodology

The audit followed the actual URL include chain from `backend/heritage_backend/urls.py` into `api/urls_mongo.py`, `api/urls_pg.py`, and `api/urls_reports.py`. Each registered API route was traced through its view into serializers, services, ORM/raw SQL, or Mongo helpers. Model definitions and both core migrations were reviewed. Existing tests, fixtures, settings, requirements, root/backend configuration, CI, frontend call sites, README, and Phase 2 requirements were inspected.

No live production database or Atlas endpoint was contacted. Test commands used process-local environment overrides for a local PostgreSQL address and a dedicated audit database name. No secret values were copied into this report. Source-level security findings were reviewed separately by the read-only security reviewer; safe exploit attempts and production mutations were not performed.

Implementation-status vocabulary follows the audit request: **Implemented and verified**, **Implemented, needs correction**, **Implemented, insufficiently tested**, **Missing**, **Not applicable**, and **Unverified**. Severity is Critical/High/Medium/Low/Informational and reflects demonstrated impact, not theoretical severity alone.

## Baseline and configuration

| Item | Observed baseline |
|---|---|
| Branch / commit | `main` / `66dfc5ac25ec03826c7bb8c61cdd5c5c586e023f` |
| Python | Repository README and CI target Python 3.11; audit runtime was Python 3.10.4. No `requires-python` declaration was found. |
| Django | Installed Django 4.2.30; `requirements.txt` allows `Django>=4.2,<5.0` without a lockfile. |
| Other relevant packages | pytest 9.1.1, pytest-django 4.14.0, mongomock 4.3.0, psycopg2-binary 2.9.10 were installed. Manifests use minimum/range constraints rather than fully locked versions. |
| Transactional store | PostgreSQL Django backend; connection values read from environment with local defaults in `backend/settings.py:85-99`. |
| Analytical store | PyMongo `MongoClient` created in `backend/mongo/client.py:1-7`; URI and database name come from environment/settings with local defaults. |
| Test framework | pytest + pytest-django; `backend/pytest.ini`; database-backed tests require PostgreSQL. Mongo tests use mongomock. |
| CI | `.github/workflows/ci.yml` uses disposable PostgreSQL 15 and MongoDB 6 services, Python 3.11, migrations, collectstatic, and pytest. The workflow was inspected, not run remotely. |
| Runtime/deployment | Docker image uses Python 3.11; entrypoint migrates and collects static files before starting Gunicorn or runserver. Render blueprint provisions a web service/PostgreSQL and requires Mongo URI configuration. No live deployment was inspected. |

`manage.py check` returned “System check identified no issues”. `makemigrations --check --dry-run` reported “No changes detected”; Django emitted a warning that migration-history consistency could not be checked because the local PostgreSQL connection was rejected. This is not a verified production migration state.

## Architecture and data ownership

The actual request flow is:

`URL include -> plain Django view -> (BookingSerializer for create only) -> booking/reporting service or direct ORM/raw SQL/Mongo helper -> JSON/CSV response`

- `backend/api/views_pg.py` implements booking creation/cancellation. Creation validates through `api/serializers.py`, then calls `heritage_backend/services/booking_service.py`.
- `backend/heritage_backend/services/booking_service.py` performs visitor/site lookup and booking insertion. Creation is inside `transaction.atomic`; cancellation is a direct model read/update without a transaction decorator.
- `backend/api/views_reports.py` delegates some aggregates to `services/reporting_service.py`, but also contains direct ORM reports, site detail, featured-site selection, and CSV export.
- `backend/mongo/client.py`, `mongo/heritage_sites.py`, and `mongo/analytics.py` hold module-level Mongo client/collection access and query logic. Mongo views directly return helper results.
- `backend/heritage_backend/core/models.py` defines Province, Category, HeritageSite, Visitor, and Booking. Both core migrations are present; `makemigrations --check --dry-run` found no model drift.

PostgreSQL is authoritative for sites, visitors, and bookings. `backend/heritage_backend/core/management/commands/run_etl.py` reads PostgreSQL site and booking tables and replaces Mongo `heritage_sites` and `bookings` collections. It is an explicit/manual sync; no automatic API-triggered or scheduled synchronization was found. Mongo analytics therefore reflect the latest successful ETL run, not necessarily current PostgreSQL state. Mongo writes do not participate in PostgreSQL transactions.

The management command deletes and repopulates each Mongo collection (`run_etl.py:51-59, 89-107`). A failure after deletion can leave an empty or partially refreshed projection. Separately, a top-level legacy `backend/etl.py` contains connection literals, references older table/column names, and performs destructive collection replacement; the documented current path is `manage.py run_etl`. Do not run that legacy script without a separate validation and credential review.

## Endpoint inventory summary

| Route group | Count | Summary |
|---|---:|---|
| Booking API | 2 | Create and cancel PostgreSQL bookings |
| PostgreSQL reporting/site routes | 9 | Seven JSON reporting/list routes, one CSV export, one site detail |
| MongoDB site/analytics routes | 5 | All sites, province filter, name detail, two aggregate endpoints |
| **Total API URL patterns** | **16** | Complete route-by-route table in [PHASE_2_API_ENDPOINT_INVENTORY.md](./PHASE_2_API_ENDPOINT_INVENTORY.md) |

The separate web/admin routes are `/`, `/discover/`, `/admin-dashboard/`, and `/admin/`. `/admin-dashboard/` is staff-only, but the report and export APIs called from it do not inherit that protection.

## Findings register

| Finding ID | Severity | Classification | Evidence summary | Phase |
|---|---|---|---|---|
| SEC-01 | High | Demonstrated security issue | Public CSV route exports every visitor name/email without authorization. | Immediate mitigation; API/Phase 2 |
| SEC-02 | Medium | Demonstrated security issue | Public cancellation looks up a booking by sequential ID and does not check identity/ownership. | Immediate interim mitigation; Phase 3 ownership design |
| SEC-03 | Medium, potential | Potential security risk | Caller-controlled visitor name can reach spreadsheet formula cells without neutralization. | Phase 2 |
| API-F01 | Medium | Documented contract gap | Mongo all-sites route ignores README-promised page/page_size parameters. | Phase 2 |
| API-F02 | Medium | Demonstrated behavior defect | PostgreSQL sites report and Mongo site reads/aggregations include inactive records, unlike active-only paths. | Phase 2 |
| API-F03 | Medium | Demonstrated calculation defect | Per-site booking report groups by name although names may repeat across provinces. | Phase 2 |
| API-F04 | Medium | Demonstrated error-contract defect | Unexpected booking service exceptions become raw-text HTTP 400 responses. | Phase 2 |
| API-F05 | Low | Contract inconsistency | Read routes accept unsupported methods; missing Mongo detail is `{}`/200 unlike PostgreSQL 404. | Phase 2 |
| API-F06 | Medium | Reliability risk | Manual ETL deletes Mongo collections before re-inserting, permitting partial/empty projection on failure. | Reliability; Phase 2/5 boundary |
| API-F07 | Low | Code-level performance risk | CSV queryset iteration can cache all booking rows despite streaming response. | Phase 5, after access control |
| API-F08 | Low, conditional | Configuration risk | `SECRET_KEY` has a known fallback if deployment omits the environment variable; Render blueprint generates a key, live env unverified. | Deployment hardening |
| API-F09 | Informational | Deferred requirement | Review requirement exists in `docs/requirements.md`, while README schedules reviews for Phase 6; no model/route exists. | Phase 6 |

## PostgreSQL API assessment

### Booking creation

`BookingSerializer` requires a syntactically valid email, non-whitespace name, positive integer site ID/group size, and a date not earlier than `date.today()` (`backend/api/serializers.py:12-33`). The service obtains/reuses a Visitor by exact email, requires an active site, and inserts the booking inside `transaction.atomic()` (`booking_service.py:4-33`). This avoids a partial Visitor row if later site lookup/booking creation fails. Existing same-case repeat-visitor behavior is tested in source, but DB-backed tests could not run here.

Observed constraints/gaps:

- The create view's final `except Exception` turns database/service outages and unexpected defects into HTTP 400 and returns `str(e)` to the client (`api/views_pg.py:63-68`). A server failure is not a malformed client request; the response can expose internal exception detail and prevents clients/monitoring from distinguishing 4xx from 5xx.
- Visitor identity is caller-supplied for anonymous requests. If a user is authenticated, `setdefault` still permits submitted visitor name/email to override their account values (`views_pg.py:31-37`). Whether anonymous self-attribution is intended is supported by the existing email-based Visitor model; whether authenticated requests must be bound to the account is a Phase 3 policy and must be enforced before claiming ownership.
- `date.today()` uses the host's local date rather than Django's configured timezone-aware local date. A request at the SA/UTC date boundary can be evaluated against the wrong calendar date if the host runs UTC; this is a low-risk edge case requiring a timezone boundary test.
- Email is used as the unique visitor key without canonicalization. Case variants can be separate records in a case-sensitive PostgreSQL unique constraint. Existing tests only verify exact-case reuse.
- No booking capacity, duplicate booking, or idempotency rule is documented; no such rule is assumed missing.

### Booking cancellation

The service selects a booking by primary key only, rejects already-cancelled and past-visit records, then saves `is_cancelled=True` and `cancelled_at=now()` together (`booking_service.py:35-47`). The single `save()` updates both columns, but there is no model/database constraint requiring their consistency and no endpoint test covers valid, missing, past, repeat, or concurrent cancellation.

More importantly, the view does not authenticate the request or verify visitor ownership. Booking IDs are sequential integers. An unauthenticated caller who knows/guesses an eligible ID can cancel another visitor's booking. This is an access-control finding even though account ownership belongs to Phase 3; the endpoint needs an interim protection before exposure if cancellation is meant to be member-owned.

### Reports, queries, and response contracts

- `bookings_per_site()` groups by `heritage_site__name`, but the model permits the same name in different provinces (`unique_together` is `(name, province)`). Equal-named sites therefore merge into one reported row. Group by stable site ID (and return the documented name) to preserve per-site meaning.
- `/api/reports/sites/` is documented in its view as active sites, but `sites_with_provinces()` returns `.all()` and the view does not filter `is_active`; inactive sites are included. `/api/sites/<id>/` and the province/category/featured PostgreSQL reports do filter active rows.
- `monthly_booking_stats()` uses fixed, non-user-controlled SQL `DATE_TRUNC('month', booking_date)` grouped across all rows. It is not vulnerable to query-string SQL injection. Its tests only check shape, not exact month totals or boundaries.
- Booking reports currently include cancelled bookings. Neither requirements nor README defines whether cancellations should be excluded, so this is documented behavior and a policy question, not a proven arithmetic defect.
- All reports are unpaginated and most materialize full result lists. The `REST_FRAMEWORK` paginator setting does not apply to these plain Django `JsonResponse` views.
- Views do not consistently restrict HTTP methods. Unexpected methods can execute read queries and return a success response rather than 405. No report view has endpoint-specific database failure handling.

## MongoDB API assessment

The code confirms MongoDB is a derived/read-optimized projection, not the transactional source of truth. Current APIs read only `heritage_sites`; the ETL also writes `bookings`, but no Mongo booking endpoint was found. `run_etl` includes `is_active`, fee, category/province names, descriptions, and booking fields in its projections.

Observed behavior and risks:

- All-site and province queries return entire Mongo result sets as Python lists (`mongo/heritage_sites.py:5-19`) with no limit, sort, or pagination. The README documents `?page=1&page_size=10` and the roadmap lists Mongo pagination as Phase 2; those parameters are ignored.
- The ETL preserves `is_active`, but all-site/province queries and both analytics pipelines do not filter it. Inactive sites can appear in the public Mongo catalog and affect province counts/average fee, unlike active-only PostgreSQL reports.
- Missing Mongo name detail returns `{}` with 200, while PostgreSQL site detail returns 404. This makes absence ambiguous and differs between data stores.
- Queries have no route-level validation, explicit timeout policy, or controlled handling for Mongo connection/server-selection failures. An exception will use Django's generic error path; deployment response behavior was not verified. PyMongo's default server-selection timeout remains implicit.
- `JsonResponse` cannot encode arbitrary BSON/Python types. The ETL's current fields are mostly scalar JSON-compatible values and dates are converted to strings for bookings, but unexpected external/manual document shapes are unverified.
- Mongo client creation is lazy; no network request was made by the passing mongomock unit tests.

The ETL is one-way and manually triggered. It uses delete-then-insert, not an atomic Mongo collection swap. There is no outbox, retry scheduler, or automatic freshness guarantee. PostgreSQL writes remain authoritative; a successful booking does not update Mongo until ETL runs.

## Booking, reporting, and CSV assessment

PostgreSQL model fields and migrations support site, province, category, visitor, and booking records. There is no Review model or review endpoint; `docs/requirements.md:8` mentions reviews, while the README places reviews and ratings in Phase 6. This is treated as explicitly deferred, not a Phase 2 defect.

Reports are structurally plausible but not comprehensively validated:

- The average group-size conversion rounds to two decimals and represents empty data as zero.
- Monthly reporting groups booking creation dates, not visit dates. This follows the SQL field selected (`booking_date`) but should remain explicit in client-facing docs.
- Booking totals and averages include cancelled bookings; intended semantics are not stated.
- Per-site aggregation can merge same-named sites across provinces.
- Inactive-site behavior is inconsistent between PostgreSQL list and Mongo list/report paths.

CSV details are recorded in the endpoint inventory. The route exports every booking's visitor name/email and lacks authorization. The caller-supplied visitor name can reach a CSV cell without neutralization; values beginning with spreadsheet formula markers may be interpreted if an administrator opens the file in spreadsheet software. This is a potential formula-injection risk, not a reproduced spreadsheet exploit. `csv.writer` correctly handles CSV quoting, but quoting alone does not prevent spreadsheet formula evaluation.

The `StreamingHttpResponse` iterator reduces response-body buffering, but iterating a regular Django `QuerySet` uses its caching iterator; it can cache the full selected booking set in memory. Use `QuerySet.iterator()` or a bounded/export job strategy if this export is expected to grow. No benchmark was run.

## Security assessment

Security findings below are source-demonstrated unless marked potential. No production request, mutation, or live-data test was performed.

| ID | Severity | Affected route/component | Evidence and preconditions | Impact / recommendation | Safe reproduction |
|---|---|---|---|---|---|
| SEC-01 | High | `GET /api/reports/export/bookings/` — `backend/api/views_reports.py:94-107`; registration `backend/api/urls_reports.py:17` | Public view has no auth/permission guard and returns every booking's visitor full name/email (`views_reports.py:100-101`). Any network caller can request it while route is reachable. README presents export as an administrator feature (`README.md:116-118`). | Visitor contact data disclosure. Deployment-blocking while public. Restrict to authenticated staff/administrators or disable the route until a permission check is in place; test anonymous denial and authorized export. If already deployed, assess access logs and incident-response obligations. | Confirmed by static inspection; no HTTP export request was made. |
| SEC-02 | Medium | `PATCH /api/bookings/<id>/cancel/` — `backend/api/views_pg.py:70-83`; `backend/heritage_backend/services/booking_service.py:35-47` | View checks method and forwards caller-provided integer ID; service loads by primary key with no identity/ownership check. Caller must know/guess an eligible booking ID. | Unauthorized cancellation of another visitor's booking. Require identity and verify ownership (or staff role) at the service/query boundary. Avoid relying on sequential IDs as authorization. | Confirmed by static inspection; no booking was modified. |
| SEC-03 | Medium, potential | CSV cells generated by `/api/reports/export/bookings/` — `backend/api/views_reports.py:99-101`; input `backend/api/serializers.py:13-14` | A caller can submit a visitor name beginning with spreadsheet formula markers; exporter sends the value into a CSV cell without spreadsheet-specific neutralization. Impact depends on how an administrator opens the export. | Formula execution may occur in spreadsheet software. Neutralize formula-leading text in untrusted cells and test the actual exported bytes with marker-prefixed text. Treat this separately from SEC-01. | Data path evident statically; CSV/spreadsheet was not generated or opened. |

Additional security/configuration observations:

- `create_booking_view` is `csrf_exempt` (`views_pg.py:24`), but it is a public, anonymous-capable endpoint and the repository does not establish an active session-authenticated API flow. The decorator alone is not claimed exploitable. If authenticated session identities are later bound to booking creation, remove/replace the exemption or use a correctly designed token/API auth flow.
- Booking create rate-limits POST by IP at 10/minute; no rate limits were found on read/report/export/Mongo routes.
- CORS lists local origins and adds the Render hostname when supplied (`settings.py:135-140`). External production frontend origins and deployed settings were unavailable; no wildcard origin was found in source.
- `SECRET_KEY` falls back to a known development literal (`settings.py:23`). Render blueprint sets a generated key, but deployment configuration was not inspected. Require a non-default secret in production; do not assume the deployed environment uses the fallback.
- API views do not set a global access policy. The public booking form may be intentional, but the CSV and cancel routes contradict the README's administrator/member descriptions.

## API contract and error-handling consistency

- Booking create uses 201 on success, 400 on serializer errors, 400 for malformed JSON, and 429 for rate limiting.
- Cancellation uses 404 for absent bookings and 400 for state errors, but unexpected failures are also returned as 400 and raw exception text is exposed.
- Mongo detail absence is `{}`/200, while PostgreSQL detail absence is an error object/404.
- Reporting and Mongo list views return bare arrays, while other endpoints return objects. This may be an intentional small API contract, but error structures are not centralized.
- Reports and Mongo read views do not enforce GET. A non-GET caller can receive a success-shaped response; this is inconsistent with the documented HTTP method.
- No endpoint has an API-wide exception contract. Database outages on unguarded report/Mongo routes are not translated to a controlled service-unavailable response.
- Error-format consolidation is a later compatibility decision; preserve existing successful shapes unless frontend call sites and tests are updated together.

## Test suite and results

### Existing tests

The repository contains four test modules: `test_api.py`, `test_mongo.py`, `test_reporting.py`, and `test_transactions.py`. `test_api.py` covers booking create input and several report/page response shapes; `test_mongo.py` covers two aggregation helpers and Mongo route behavior with mongomock; `test_reporting.py` asserts only that an aggregate is not `None`; `test_transactions.py` covers create and invalid site rollback. There are no tests found for cancellation, CSV bytes/headers/permissions/formula safety, PostgreSQL site detail, report exact totals across boundary cases, Mongo failure handling, or booking ownership.

The 8 pure Mongo aggregation unit tests ran and passed. Many HTTP tests are marked `django_db`; despite Mongo collection mocking, pytest-django still requires the PostgreSQL test database before those tests can run.

### Executed checks

| Command | Environment | Result |
|---|---|---|
| `python manage.py check` | Windows; Python 3.10.4; Django 4.2.30; process-local non-production key and local DB/Mongo settings | Exit 0; “System check identified no issues (0 silenced).” |
| `python -m pytest -v` | `backend/`; explicitly local `127.0.0.1` PostgreSQL, dedicated audit DB name, never Neon; system collected 55 tests | Exit 1; **8 passed, 47 errors, 1 warning** in 18.33s. Database-backed test setup failed with PostgreSQL password authentication failure before assertions. No assertion failure was observed; DB-backed behavior is unverified. |
| `python -m pytest -q heritage_backend/tests/test_mongo.py::TestAverageEntryFee heritage_backend/tests/test_mongo.py::TestSitesPerProvince` | Same local-only process settings; mongomock fixtures | Exit 0; **8 passed** in 2.73s. |
| `python manage.py makemigrations --check --dry-run` | Same local-only process settings | Exit 0; “No changes detected.” A warning says Django could not check migration history because PostgreSQL authentication failed. |

The full suite failure was reproducible as an authentication/setup error from the single run; it is not evidence that the endpoint assertions pass or fail. No dependency installation, production connection, migration against a real database, or live Atlas request was performed.

## Performance and reliability observations

1. Mongo site routes and multiple PostgreSQL report endpoints return unbounded result sets. Mongo pagination is explicitly listed in the Phase 2 roadmap; CSV exports all rows.
2. The CSV's regular queryset iteration can cache all selected rows despite a streaming response. This is a code-level memory risk; no measurement was made.
3. `featured_sites_view` materializes every active site ID and then samples three, which scales with catalogue size. Current README describes 29 sites, so no current impact was measured.
4. Mongo has no explicit server-selection timeout/retry or API-level controlled outage behavior.
5. ETL fully deletes each projection collection before reinserting, so interrupted runs can leave incomplete data. It is manually executed and no freshness SLA exists.
6. `bookings_per_site()` can merge distinct site rows with equal names; correctness, not a benchmark, is the primary concern.

No performance benchmark, load test, live query plan, or production telemetry was available. These are risks inferred from code paths, not measured latency claims.

## Documentation and deployment compatibility

- README currently says 13 REST endpoints although its own endpoint table and registered URL patterns contain 16.
- README documents `page` and `page_size` for Mongo all-sites while the implementation ignores both. Pagination also remains listed as a planned Phase 2 task.
- README says export is administrator functionality and booking cancellation is for registered members; the endpoints themselves are public and do not enforce those roles.
- README shows account/history features although Phase 3 auth routes are commented out; this audit treats identity/account functionality as deferred, but the mismatch should be corrected or clearly labeled.
- `docs/requirements.md` requires an optional review-after-booking capability; the README defers reviews to Phase 6. There is no Review model or route.
- CI provisions disposable PostgreSQL/Mongo and executes system checks, migrations, collectstatic, and pytest. It does not show separate lint/type-check commands.
- Render blueprint provisions PostgreSQL and expects Mongo URI to be set manually. Actual deployment environment variables, Atlas connection health, Sentry DSN, and API exposure were not verified.
- The Docker entrypoint applies migrations at startup. This is operationally relevant but not changed by this API audit.

## Limitations

- Production database, MongoDB Atlas, Sentry, and Render settings were not accessed.
- Local PostgreSQL was listening, but the supplied test-only credentials were rejected. Existing `.env` values were not used; no attempt was made to discover or reuse any production credential.
- Mongo HTTP tests could not run because their test classes request the PostgreSQL test DB. Mongo query-unit tests used mongomock only.
- Findings about access-control reachability are based on registered source routes; no deployed reverse-proxy/network configuration was validated.
- No production data was queried; no destructive test, live exploit, stress test, or spreadsheet execution was performed.

## Prioritized recommendations

1. **SEC-01 / SEC-02:** Close public booking PII export and unauthorized cancellation paths before exposing these routes. This is the first remediation batch; add permission/ownership regression tests.
2. **SEC-03:** Neutralize formula-leading untrusted values in CSV output and test the exact CSV content.
3. **API-01:** Implement the already-documented Mongo pagination contract with validation and stable response shape, or remove the promise only after updating all documentation and consumers.
4. **API-02 / API-03:** Make active-site visibility consistent across PostgreSQL and Mongo read/report routes, and group bookings by stable site identity.
5. **API-04:** Return sanitized server errors for unexpected DB/service failures; keep validation errors as 4xx and do not send exception text to clients.
6. **API-05 / API-06:** Add explicit GET-only behavior, consistent not-found responses for Mongo detail, and tests for each route.
7. **API-07:** Decide and document whether cancelled bookings count in each report before changing aggregate filters.
8. **API-08:** Make the ETL replacement robust against interrupted refreshes, document manual freshness, and retire or clearly isolate the legacy script after credential/schema review.
9. **Testing:** Provide safe local PostgreSQL test credentials/service, then rerun the full suite and add missing tests for cancellation, CSV, site detail, exact report totals, Mongo endpoint errors, and access control.
10. **Deferred phases:** Authentication/user tiers belong to Phase 3; formal OpenAPI docs to Phase 4; broader pagination/performance tuning to Phase 5, except the README-promised Mongo pagination needed to complete the current Phase 2 plan; reviews are explicitly Phase 6.

The findings and recommendations above describe the audited baseline only. Remediation outcomes and current verification are recorded below and supersede baseline behavior where noted.

## Phase 2 remediation outcome

**Starting commit for remediation:** `2a33901f09809a3df5e4b7639202f8ad8eec1d37` on `main`  
**Final commit:** `2a33901f09809a3df5e4b7639202f8ad8eec1d37` (changes remain in the working tree; no remediation commit was created)  
**Baseline audited commit:** `66dfc5ac25ec03826c7bb8c61cdd5c5c586e023f`

| Finding | Final status | Evidence / disposition |
|---|---|---|
| SEC-01 | Fixed and verified | Anonymous and authenticated non-staff callers receive 403 before export data access; staff CSV output is regression-tested. |
| SEC-02 | Fixed and verified (temporary containment) | Cancellation returns 503 without calling the cancellation service; non-PATCH methods return 405. Permanent owner verification is deferred to Phase 3. |
| SEC-03 | Fixed and verified | CSV tests verify formula-leading visitor name, email, and site text are neutralized while headers, order, filename, and CSV parsing are preserved. |
| API-F01 | Fixed and verified | Mongo pagination defaults, maximum page size, deterministic order, multiple pages, invalid values, and skip overflow are tested. |
| API-F02 | Fixed and verified | Active-only visibility is enforced and tested for public PostgreSQL/Mongo catalogues and Mongo site analytics; inactive documents remain stored. |
| API-F03 | Fixed and verified | Both reporting helpers group bookings by stable site ID and retain existing display fields; duplicate-name rows are tested. |
| API-F04 | Fixed and verified | Missing/inactive site validation is sanitized; database failures return generic 503, and unexpected failures generic 500. |
| API-F05 | Fixed and verified | Read routes are GET-only; missing active Mongo/PostgreSQL site detail returns 404. |
| API-F06 | Fixed and verified | Isolated Mongo integration tests cover staged collection/index creation, pointer publication, source failure, index preservation, and an ambiguous publication acknowledgement. |
| API-F07 | Fixed and verified | CSV rows use `QuerySet.iterator(chunk_size=2000)`. |
| API-F08 | Fixed and verified in source | Production settings reject missing, blank, built-in development, and documented template secret-key values without printing them; the deployed key was not inspected. |
| API-F09 | Not applicable, with evidence | No Review model or endpoint is present; reviews and ratings remain a Phase 6 requirement. |

### Verification

- Python 3.11.9 full test suite: `python -m pytest -q` — **104 passed in 186.16s** on the final code state.
- Focused API/Mongo regressions: **58 passed**; isolated ETL integration tests: **3 passed** before the final test additions; all are included in the passing full suite.
- `python manage.py check` — passed; no system-check issues.
- `python manage.py makemigrations --check --dry-run` — passed; no model changes detected.
- `python manage.py migrate --noinput` — passed against the dedicated local test database.
- `python manage.py collectstatic --noinput` — passed; 152 files copied.
- GitHub Actions was not run remotely. The local CI command sequence passed using isolated native PostgreSQL 17 and MongoDB 8 services; workflow service images remain PostgreSQL 15 and MongoDB 6.
- No coverage percentage was collected. Frontend chart consumers still read the existing `heritage_site__name` and `total` fields; the stable site ID is additive.

### Remaining issue and scope boundary

During the authorized legacy ETL review, `backend/etl.py` was found to contain a literal-looking database password under the variable `password`; the legacy script had no in-repository execution references and stale schema usage, so it was removed from the current tree. The literal's validity and remote/public exposure are uncertain, and its prior source remains in local Git history. No value is reproduced, no credential was rotated, and no history rewrite or deployment-secret change was attempted. This potential historical credential requires owner follow-up under separate authorization; it is **Outstanding, with explanation** and prevents an environment-wide claim that all credential risk has been cleared.

The user-confirmed report policies are implemented: cancelled bookings are excluded from PostgreSQL and Mongo booking-count, monthly, and average-group-size reports, with monthly grouping by `booking_date`; inactive Mongo sites remain stored but are excluded from public catalogue, province-count, and average-fee output. No production service, database, deployment secret, or production configuration was accessed or changed.

See [PHASE_2_REMEDIATION_REPORT.md](./PHASE_2_REMEDIATION_REPORT.md) for the consolidated changed-file list and final completion assessment.
