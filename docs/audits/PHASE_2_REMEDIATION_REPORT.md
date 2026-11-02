# Phase 2 API Remediation Report — HeritageSA

## Executive outcome

Phase 2 API remediations are implemented and the full isolated Python 3.11 test suite passes. The API-level high-priority exposure is contained, cancellation remains disabled pending Phase 3 ownership, and the documented pagination, reporting, method, and error contracts are covered by regression tests.

**Formal overall sign-off is withheld** because a potential database-password literal was found in the pre-existing legacy ETL source. The file is removed from the current working tree, but its validity and remote exposure are uncertain and its history remains. No credential rotation or Git-history rewrite was authorized or attempted. This outstanding item and the required separate owner follow-up are detailed below.

## Repository and commit record

| Item | Value |
|---|---|
| Repository | `Sinothando-Mthombeni/Heritage-Site-Information-System` |
| Branch | `main` |
| Baseline audit commit | `66dfc5ac25ec03826c7bb8c61cdd5c5c586e023f` |
| Starting commit for remediation | `2a33901f09809a3df5e4b7639202f8ad8eec1d37` |
| Final commit | `2a33901f09809a3df5e4b7639202f8ad8eec1d37` |
| Commit state | Remediation changes are uncommitted in the working tree; no new commit was created. |

The four baseline audit documents were reconciled with the repository at the starting commit before application changes. The implementation uses the approved policy decisions: cancelled bookings are excluded from PostgreSQL and Mongo booking-count, monthly, and average-group-size reports; monthly reports continue grouping on `booking_date`; inactive Mongo site documents remain stored but are excluded from public catalogue, province-count, and average-fee output.

## Findings and final status

| Finding | Final status | Evidence / result |
|---|---|---|
| SEC-01 — Public CSV exposes visitor contact data | **Fixed and verified** | Export checks authenticated staff status before data access. Anonymous and authenticated non-staff tests assert 403; staff tests assert the allowed CSV output. |
| SEC-02 — Public cancellation has no ownership check | **Fixed and verified (temporary containment)** | PATCH returns 503 without calling the cancellation service or looking up the booking. Other methods return 405. Permanent owner verification is deferred to Phase 3. |
| SEC-03 — CSV formula injection | **Fixed and verified** | Formula-leading visitor names, emails, and site names are neutralized. Tests verify parsed CSV, original columns/order, filename, empty export, and quoting of commas/newlines. |
| SEC-04 — Known development secret-key fallback | **Fixed and verified in source** | Production settings reject missing/blank keys and known development/template values without printing them. Deployed settings were not accessed. |
| API-F01 — Mongo pagination absent | **Fixed and verified** | Default page 1/page size 10, maximum page size 100, stable site-ID order, valid multiple-page results, invalid input, and skip overflow are tested. The bare-array response is retained. |
| API-F02 — Active-site visibility inconsistent | **Fixed and verified** | Public PostgreSQL and Mongo site/report paths use active-only visibility. Inactive records are preserved; active-only analytics behavior follows the user-approved policy. |
| API-F03 — Per-site aggregation uses non-unique name | **Fixed and verified** | PostgreSQL and Mongo booking aggregates group on stable site ID and retain existing display fields. Duplicate-name sites in different provinces are tested. |
| API-F04 — Raw or incorrect API errors | **Fixed and verified** | Missing-site validation returns a controlled 400; database/service failures return generic 503; unexpected errors return generic 500. Regression tests assert exception details are absent from responses and invalid-site visitor creation rolls back. |
| API-F05 — Method and missing-record contracts inconsistent | **Fixed and verified** | Read-only routes reject unsupported methods with 405. Mongo and PostgreSQL active-site detail routes return 404 for missing/inactive records. |
| API-F06 — ETL could destroy last good projection | **Fixed and verified** | Isolated live Mongo tests verify generation staging, named indexes, single-document pointer publication, prior-data/index preservation after source failure, and safe retention after an ambiguous pointer-write acknowledgement. |
| API-F07 — CSV queryset can cache all rows | **Fixed and verified** | CSV uses `QuerySet.iterator(chunk_size=2000)`. |
| API-F08 — Production secret-key fallback | **Fixed and verified in source** | The same production key validation addresses this conditional configuration finding. |
| API-F09 — Review endpoint/model absent | **Not applicable, with evidence** | No Review model or route exists; reviews/ratings remain explicitly scheduled for Phase 6. |
| Full member authentication and booking ownership | **Deferred, with justification** | These are Phase 3 architecture items. Until then, cancellation remains disabled; no client-supplied visitor email or booking ID is accepted as proof of ownership. |
| Potential historical database password | **Outstanding, with explanation** | The pre-existing tracked `backend/etl.py` contained a literal-looking database password under variable `password`. The legacy script had no in-repository execution references and stale schema usage, and was removed from the current tree. Literal presence in source is confirmed; validity and remote/public exposure are uncertain. The value is not reproduced. Historical Git content remains; rotation and history cleanup require separate approval. |

## Tests and checks

The complete suite was run with **Python 3.11.9** against disposable local PostgreSQL 17 and MongoDB 8 services. The test settings enforce the dedicated `heritage_phase2_test` database name and loopback-only service hosts, reject inherited database URL variables, and reject non-local test Mongo URIs. ETL integration tests use separate disposable Mongo databases and clean them up.

| Command/check | Result |
|---|---|
| `python -m pytest -q` | **104 passed in 186.16s** on the final code state. |
| Focused Phase 2 API/Mongo regression run | 58 passed (earlier focused run; full final suite includes subsequent additions). |
| `python manage.py check` with `DJANGO_SETTINGS_MODULE=test_settings` | Passed; no system-check issues. |
| `python manage.py makemigrations --check --dry-run` with test settings | Passed; no model changes detected. |
| `python manage.py migrate --noinput` with test settings | Passed against the isolated test database. |
| `python manage.py collectstatic --noinput` with test settings | Passed; 152 files copied. |
| `git diff --check` | Passed. |
| GitHub Actions | Not run remotely. The local CI command sequence passed; local database versions were PostgreSQL 17/MongoDB 8, while the workflow service images are PostgreSQL 15/MongoDB 6. |
| Coverage | No coverage percentage was collected. |

The full suite covers allowed and denied export access; CSV headers, filename, formula safety, empty output, and quoting; cancellation containment and method restrictions; exact booking report calculations and cross-store parity; duplicate site names; active/inactive visibility; pagination boundaries; sanitized errors; secret-key validation; test-environment guards; and ETL success/failure/index behavior.

## Files changed and purpose

### Application and test infrastructure

| File | Purpose |
|---|---|
| `.github/workflows/ci.yml` | Configure CI to use the isolated test settings and dedicated PostgreSQL/Mongo service endpoints. |
| `backend/api/decorators.py` | Add shared sanitized 503/500 JSON error handling without returning exception details. |
| `backend/api/views_pg.py` | Validate booking request content, sanitize service failures, and disable cancellation until ownership exists. |
| `backend/api/views_reports.py` | Restrict reports to GET, require staff for CSV, neutralize formula-leading strings, and stream with queryset iteration. |
| `backend/api/views_mongo.py` | Add validated/bounded pagination and GET-only behavior while retaining the existing array response. |
| `backend/heritage_backend/services/reporting_service.py` | Align active catalogue visibility, exclude cancelled bookings, and group per-site reports by stable ID. |
| `backend/mongo/client.py` | Resolve the active site/booking projection through the ETL state pointer. |
| `backend/mongo/heritage_sites.py` | Add stable bounded pagination and active-only catalogue queries. |
| `backend/mongo/analytics.py` | Apply active-site and cancellation policies and align Mongo booking report calculations with PostgreSQL. |
| `backend/heritage_backend/core/management/commands/run_etl.py` | Stage generation-specific projections, create indexes before publication, atomically switch pointers, preserve active collections on failure, and close resources safely. |
| `backend/settings.py` | Reject missing, blank, built-in development, and documented template secret keys in production mode. |
| `backend/test_settings.py` | Isolate tests to the named local-only PostgreSQL/Mongo services and reject inherited production URLs. |
| `backend/pytest.ini` | Select the dedicated test settings by default for pytest. |
| `backend/docker-compose.test.yml` | Provide disposable test-only PostgreSQL and MongoDB services on ports 55432 and 27018. |
| `backend/heritage_backend/tests/test_mongo.py` | Extend pagination, active visibility, report parity, missing-detail, error, and method regression coverage. |
| `backend/heritage_backend/tests/test_phase2_remediation.py` | Add API security, CSV, report semantics, request/error, and secret/test-settings regression tests. |
| `backend/heritage_backend/tests/test_etl.py` | Add isolated Mongo ETL publication, index preservation, and failure-safety integration tests. |
| `backend/etl.py` | Remove the unreferenced legacy ETL script after confirming stale schema usage and inspecting its credential-like literal. |

### Documentation and audit artifacts

| File | Purpose |
|---|---|
| `README.md` | Correct the 16-route inventory and document methods, permissions, pagination, report semantics, manual ETL freshness, isolated tests, and current Phase 2 status. |
| `SECURITY-REVIEW.md` | Record remediation evidence and the outstanding historical credential uncertainty without exposing values. |
| `docs/audits/PHASE_2_API_AUDIT_REPORT.md` | Preserve baseline findings and append current remediation statuses, verification, and limitations. |
| `docs/audits/PHASE_2_REMEDIATION_PLAN.md` | Record execution results, deferred phases, and finding dispositions. |
| `docs/audits/PHASE_2_API_TEST_COVERAGE.md` | Preserve baseline matrix and add current regression coverage and test results. |
| `docs/audits/PHASE_2_API_ENDPOINT_INVENTORY.md` | Preserve the baseline inventory and append the current contracts for all 16 routes. |
| `docs/audits/PHASE_2_REMEDIATION_REPORT.md` | Provide this consolidated completion report. |

## Compatibility, deployment, and remaining risks

- The CSV route now returns 403 to anonymous and non-staff callers. The staff dashboard's existing same-origin session flow is compatible; no CSV columns, order, or filename changed.
- Existing dashboard charts still consume `heritage_site__name` and `total`; the new stable site ID is additive.
- Mongo list pagination preserves the previous bare-array envelope. Callers must now handle 400 for invalid values.
- Booking cancellation is intentionally unavailable (503) until Phase 3 server-side ownership is implemented.
- Mongo-backed catalogue and analytics freshness remains manual: run `manage.py run_etl` after PostgreSQL changes when an updated projection is required. Old successful generations are retained; automated cleanup is deferred.
- CI has not run on GitHub Actions, and local validation used newer database versions than the workflow images. The workflow service versions should be confirmed by CI before deployment.
- The legacy database-password literal's validity and remote exposure remain unverified. No credential rotation, production database access, deployment-secret changes, or Git-history rewrite occurred.

**Production-data/configuration confirmation:** No production database, MongoDB Atlas service, deployed secret, or production configuration was accessed or modified. All migrations and ETL tests used isolated local test infrastructure.

## Completion decision

The approved Phase 2 API behavior is implemented and verified by the passing full test suite. No critical/high API route exposure remains uncontained. However, due the **Outstanding, with explanation** historical credential issue, this report does **not** make an environment-wide security sign-off or unconditional completion declaration. Resolve that credential's validity/exposure through separate owner authorization before treating the overall security posture as fully cleared.
