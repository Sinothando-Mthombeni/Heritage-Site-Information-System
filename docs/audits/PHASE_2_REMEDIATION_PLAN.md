# Phase 2 API Remediation Plan

**Prepared against:** `main` at `66dfc5ac25ec03826c7bb8c61cdd5c5c586e023f`  
**Execution status:** Authorized and implemented in the working tree based on `main` at `2a33901f09809a3df5e4b7639202f8ad8eec1d37`. Final verification and dispositions are recorded below.

Tasks are ordered by risk. “Phase 2 mandatory” means required to safely complete or accurately claim the currently documented API behavior. Tasks that depend on the authentication phase are marked so that an interim protection can be implemented without creating a new authentication architecture.

## Ordered tasks

### P0 — Restrict public booking export

- **Priority:** P0 / High, deployment-blocking while exposed.
- **Finding IDs:** SEC-01, SEC-03.
- **Required changes:** Add a server-side staff/admin permission check to the export view, before queryset construction/streaming. If no usable auth policy is active, temporarily disable the route rather than relying on the dashboard being staff-only. Escape/neutralize spreadsheet formula-leading untrusted cell values without changing existing column names/order.
- **Likely files:** `backend/api/views_reports.py`, `backend/api/urls_reports.py`, `backend/heritage_backend/tests/test_api.py` or a focused export test module.
- **Test cases:** Anonymous request denied; staff request receives CSV; exact headers/order and response headers; empty export; visitor/site text with formula markers; Unicode/commas/newlines; cancelled rows according to the agreed export policy.
- **Dependencies:** Confirm whether staff-only is the intended policy. Existing Django staff/session authentication is available through middleware; no new auth system is required for staff protection.
- **Acceptance criteria:** Anonymous callers cannot receive any visitor name/email; authorized staff can export; CSV values are safe for spreadsheet consumers; tests do not query production.
- **Risks/compatibility:** This intentionally changes public route behavior. The dashboard already requires staff; ensure its session credentials are sent same-origin. Keep CSV headers, row order, and filename unless an explicit compatibility update is approved.

### P1 — Protect booking cancellation from unauthorized callers

- **Priority:** P1 / Medium, access-control and booking-integrity issue.
- **Finding IDs:** SEC-02.
- **Required changes:** Introduce a verified caller identity/ownership rule at the service/query boundary before changing booking state. Until Phase 3 user ownership is implemented, restrict cancellation to an existing trusted staff path or disable public cancellation; do not trust a submitted visitor email as ownership proof.
- **Likely files:** `backend/api/views_pg.py`, `backend/heritage_backend/services/booking_service.py`, related tests, and later Phase 3 auth modules if approved.
- **Test cases:** Anonymous denied; owner can cancel their eligible booking after identity is established; another visitor cannot; staff policy; missing ID 404; past/repeated cancellation behavior; wrong method 405; cancellation fields update as one state transition.
- **Dependencies:** Product owner must select interim policy for public/anonymous bookings; full member ownership depends on Phase 3.
- **Acceptance criteria:** A caller cannot cancel another visitor's record by knowing/guessing its integer ID. Ownership is verified server-side and tests cover both allow/deny paths.
- **Risks/compatibility:** Current README says registered members cancel bookings, while auth is deferred. Do not invent a client-supplied identity workaround; document any temporary restriction.

### P2 — Complete Mongo list pagination contract

- **Priority:** P2 / Medium; documented Phase 2 gap.
- **Finding IDs:** API-F01.
- **Required changes:** Implement the documented `page` and `page_size` behavior in `/api/mongo/sites/`, with bounded limits, invalid-input handling, deterministic ordering, and a response shape compatible with any current frontend consumer. Or, if product owner rejects pagination for this phase, remove the promise from README/roadmap and explicitly retain unbounded behavior as a known limit.
- **Likely files:** `backend/api/views_mongo.py`, `backend/mongo/heritage_sites.py`, `backend/heritage_backend/tests/test_mongo.py`, `README.md`.
- **Test cases:** Default page, page-size override, maximum, invalid/negative values, empty page, stable order, no duplicate/missing rows across pages.
- **Dependencies:** Confirm desired response envelope and max page size before changing response shape. No frontend `/api/mongo/sites/` pagination consumer was found in inspected templates.
- **Acceptance criteria:** Runtime behavior matches documented query parameters and is bounded; tests verify response shape and boundaries.
- **Risks/compatibility:** Returning an envelope instead of the current array can break consumers; inspect/update all consumers or retain a compatible response contract.

### P3 — Align active-site visibility across API routes

- **Priority:** P2 / Medium.
- **Finding IDs:** API-F02.
- **Required changes:** Apply the existing soft-delete visibility policy consistently to public PostgreSQL `/api/reports/sites/`, Mongo all/province site reads, and Mongo analytics (if the desired analytics are active-only). Explicitly distinguish public catalogue reads from administrative/all-record views.
- **Likely files:** `backend/api/views_reports.py`, `backend/heritage_backend/services/reporting_service.py`, `backend/api/views_mongo.py`, `backend/mongo/heritage_sites.py`, `backend/mongo/analytics.py`, `backend/heritage_backend/tests/test_api.py`, `backend/heritage_backend/tests/test_mongo.py`.
- **Test cases:** Include active and inactive sites in PostgreSQL and Mongo fixtures; verify public list/detail/count/average consistency against the approved active-site rule.
- **Dependencies:** Confirm whether Mongo analytics should count all catalog records or only active sites. The home page and several PostgreSQL reports already use active-only behavior.
- **Acceptance criteria:** Each route's visibility policy is documented and tested; inactive records are not exposed through public catalogue routes unless explicitly intended.
- **Risks/compatibility:** Analytics totals may change; avoid filtering historical booking reports by site activity unless a separate business rule says so.

### P4 — Correct per-site aggregation identity

- **Priority:** P2 / Medium.
- **Finding IDs:** API-F03.
- **Required changes:** Group booking totals by stable `heritage_site_id` (and include the site name/province in the response as needed), rather than by a name that is only unique within a province.
- **Likely files:** `backend/heritage_backend/services/reporting_service.py`, `backend/api/views_reports.py`, `backend/heritage_backend/tests/test_api.py`, dashboard templates if they assume current keys.
- **Test cases:** Two different provinces with same-named sites produce two rows; exact count and ordering; zero bookings.
- **Dependencies:** Confirm response key compatibility with `admin_dashboard.html` and `dashboard.html` before replacing `heritage_site__name`.
- **Acceptance criteria:** Report counts each model site exactly once and has deterministic ordering; frontend rendering works with the documented response.
- **Risks/compatibility:** Response shape changes can affect charts; keep the existing name field and add a stable ID if possible.

### P5 — Sanitize unexpected API errors and correct status classes

- **Priority:** P2 / Medium.
- **Finding IDs:** API-F04.
- **Required changes:** Catch expected validation/not-found/integrity errors specifically. Log unexpected failures server-side with context; return generic 5xx (or a deliberate controlled 503 for dependency outage) without exception text. Do not map database outages to 400.
- **Likely files:** `backend/api/views_pg.py`, possibly a small shared response helper only if it follows existing project patterns; tests.
- **Test cases:** Invalid serializer data remains 400; missing site/bookings use appropriate 404/400; mocked database failure returns sanitized 5xx; response contains no exception/connection detail.
- **Dependencies:** Decide whether API errors retain current object shapes or adopt a minimal common envelope; avoid unrelated contract redesign.
- **Acceptance criteria:** Client errors remain actionable; server failures are not success-shaped or classified as client errors; internal exception text does not appear in response.
- **Risks/compatibility:** Consumers may currently inspect exception `message`; update frontend/tests if needed. No secrets or DB details should be exposed.

### P6 — Normalize read methods and Mongo missing-record response

- **Priority:** P3 / Low-to-Medium.
- **Finding IDs:** API-F05.
- **Required changes:** Explicitly allow GET on read-only views, return 405 for unsupported methods, and align missing Mongo detail with the approved 404 response contract.
- **Likely files:** `backend/api/views_mongo.py`, `backend/api/views_reports.py`, `backend/heritage_backend/tests/test_api.py`, `backend/heritage_backend/tests/test_mongo.py`.
- **Test cases:** Every read route rejects POST/PATCH with 405 and appropriate `Allow`; Mongo missing detail returns the approved 404; current successful JSON shapes remain unchanged.
- **Dependencies:** Confirm whether API clients depend on empty-object 200 for missing Mongo site.
- **Acceptance criteria:** Method behavior is predictable and resource-not-found is distinguishable from success.
- **Risks/compatibility:** Some undocumented clients may use non-GET methods on reads; no such frontend use was found.

### P7 — Make ETL refresh safe and retire legacy script

- **Priority:** P3 / Medium reliability; no direct API write.
- **Finding IDs:** API-F06.
- **Required changes:** Avoid exposing empty/partial Mongo projections during refresh (for example stage then replace collections only after successful load), retain PostgreSQL as source of truth, and document that freshness depends on `manage.py run_etl`. Separately review and remove/deprecate the legacy `backend/etl.py` only after confirming no workflow uses it and its connection literals are handled safely.
- **Likely files:** `backend/heritage_backend/core/management/commands/run_etl.py`, `backend/etl.py`, ETL tests/documentation.
- **Test cases:** Successful projection refresh; failure before publish leaves old projection intact; empty PostgreSQL source correctly produces empty projection; command closes connections; legacy path is not a CI/deployment entrypoint.
- **Dependencies:** Safe isolated Mongo test database and PostgreSQL test fixtures; no Atlas credentials needed for unit tests.
- **Acceptance criteria:** Failed refresh does not erase the last successful projection; no route treats Mongo as authoritative; active status and cancellation policy are explicit.
- **Risks/compatibility:** Collection staging/rename semantics and index preservation should be confirmed for target Mongo deployment before implementation. Do not run the legacy script.

### P8 — Reduce unbounded CSV memory use

- **Priority:** P4 / Medium performance, after access control.
- **Finding IDs:** API-F07.
- **Required changes:** Iterate using Django's streaming queryset iterator or a bounded export mechanism; preserve `select_related` and existing CSV columns.
- **Likely files:** `backend/api/views_reports.py`, export tests.
- **Test cases:** Export correct rows over multiple iterator batches; query count remains bounded; no accidental full queryset cache; large fixture behavior tested without production data.
- **Dependencies:** SEC-01 must be addressed before export behavior is broadened.
- **Acceptance criteria:** Response remains streamed and memory does not grow by caching all model instances in one QuerySet evaluation.
- **Risks/compatibility:** Iterator chunk size and server/database cursor behavior require validation on the supported PostgreSQL deployment.

### P9 — Add endpoint-focused regression coverage and restore local testability

- **Priority:** P4 / Medium quality gate.
- **Finding IDs:** Cross-cutting test gap.
- **Required changes:** Provide documented non-production local PostgreSQL test credentials/service or a safe test setup, then add missing API tests per [PHASE_2_API_TEST_COVERAGE.md](./PHASE_2_API_TEST_COVERAGE.md). Keep CI isolated and ensure tests never inherit production `DATABASE_URL`/Neon settings.
- **Likely files:** `backend/heritage_backend/tests/`, `backend/pytest.ini`, `.github/workflows/ci.yml`, setup documentation.
- **Test cases:** Cancellation; export authorization/content; PostgreSQL detail; exact report aggregation/date boundaries; pagination; Mongo failure paths; method restrictions; cross-database ETL failure.
- **Dependencies:** The local PostgreSQL service must have a known test-only user/password; this audit intentionally did not read `.env` or use unknown credentials.
- **Acceptance criteria:** Full `python -m pytest -v` passes against disposable/test-only stores on Python 3.11 CI and a documented local environment. A failed service setup is reported as an error, not mistaken for passing tests.
- **Risks/compatibility:** Do not change assertions merely to green the suite; preserve failing evidence and investigate behavior.

### P10 — Align public API documentation and policy

- **Priority:** P5 / Low; after contract decisions.
- **Finding IDs:** API-F01 through API-F09, documentation observations.
- **Required changes:** Correct “13 REST endpoints” to actual route count; align pagination documentation to shipped behavior; accurately label public/member/admin access; state whether cancelled bookings are included in each report; document booking-date vs visit-date semantics and missing-record/status behavior.
- **Likely files:** `README.md`, `docs/architecture.md`, API inventory/report docs.
- **Test cases:** Documentation-only; add assertions only if repository adds a documentation validation job.
- **Dependencies:** Complete API behavior and authorization decisions first.
- **Acceptance criteria:** README endpoint count, route contracts, role expectations, and actual implementation agree.
- **Risks/compatibility:** Do not document speculative auth, pagination, or data semantics as already shipped.

## Deferred or conditional work

| Work item | Classification | Reason |
|---|---|---|
| Full member authentication and user-tier model | Phase 3 | README roadmap defers register/login/account and anonymous/member/admin tiers. Interim route protection remains mandatory for sensitive actions. |
| Formal OpenAPI/Swagger documentation | Phase 4 | Explicitly deferred; current audit inventory is not a replacement for a generated public API schema. |
| Broader caching, indexing, Celery, large-scale tuning | Phase 5 | Not required unless later measurement shows a current reliability problem. Explicit Mongo pagination is kept in Phase 2 because the README already promises it. |
| Reviews/ratings | Phase 6 | `docs/requirements.md` mentions reviews, but README roadmap explicitly schedules them in Phase 6 and there is no model/route. |
| Change behavior for cancelled-booking report inclusion | Fixed and verified | User confirmed cancelled bookings are excluded from PostgreSQL and Mongo booking-count, monthly, and average-group-size reports; month grouping remains `booking_date`. |
| Require a non-development `SECRET_KEY` in production | Fixed and verified in source | Missing, blank, built-in development, and documented template values are rejected when `DEBUG=False`; deployed environment values were not accessed. |

## Remediation execution and disposition

| Work item | Final status | Result |
|---|---|---|
| P0 — Booking export and CSV safety | Fixed and verified | Server-side staff permission is checked before data access; non-staff is 403; CSV contract is preserved and formula-leading strings are neutralized. |
| P1 — Booking cancellation | Fixed and verified (temporary containment) | PATCH remains method-restricted but returns 503 without accessing the booking until Phase 3 ownership is implemented. |
| P2 — Mongo pagination | Fixed and verified | Positive `page`, default page 1, default `page_size` 10, maximum size 100, stable site-ID order, array response retained, invalid/overflow values return 400. |
| P3 — Active-site visibility | Fixed and verified | Public PostgreSQL and Mongo catalogue/report paths follow active-only policy; inactive rows remain stored. |
| P4 — Site aggregation identity | Fixed and verified | PostgreSQL/Mongo per-site totals group by stable site ID and retain existing display fields. |
| P5 — API error/method contract | Fixed and verified | GET-only read routes return 405 for unsupported methods; missing details return 404; dependency errors return generic 503, unexpected errors generic 500. |
| P6 — ETL refresh reliability | Fixed and verified | Generation-specific staging, indexes before publication, one-document pointer switch, and safe handling of source/index/pointer-write failures are covered against isolated MongoDB. |
| P7 — CSV iteration | Fixed and verified | Export query uses `QuerySet.iterator(chunk_size=2000)`. |
| P8 — Isolated tests and regression coverage | Fixed and verified | Tests use Python 3.11.9, dedicated PostgreSQL/Mongo test names, local-only service hosts, and URL guards; 104 full-suite tests passed. |
| P9 — Secret and legacy ETL review | Fixed in current tree; potential historical credential outstanding | Production key validation is implemented; unreferenced `backend/etl.py` was removed after inspection. Its prior tracked source contained a literal-looking database password under `password`; validity and remote exposure remain uncertain and rotation/history cleanup require separate approval. |
| P10 — Documentation | Fixed and verified by source comparison | README and endpoint inventory reflect 16 routes, methods, permissions, pagination, report semantics, date fields, and manual ETL freshness. |

Authentication/user tiers and permanent booking ownership remain **Deferred, with justification** to Phase 3. OpenAPI, broad scalability work, and reviews remain Phase 4, Phase 5, and Phase 6 respectively. No production service, data, deployment secret, or production configuration was accessed or changed.

The complete final status table, exact test commands, commit hashes, and remaining risk are in [PHASE_2_REMEDIATION_REPORT.md](./PHASE_2_REMEDIATION_REPORT.md).
