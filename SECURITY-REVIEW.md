# HeritageSA API Security Review

**Reviewed branch and commit:** `main` / `66dfc5ac25ec03826c7bb8c61cdd5c5c586e023f`
**Review date:** 2026-10-27
**Scope:** Static review of the 16 API patterns included from the three API URL modules. No production services, records, or destructive requests were used.

## Summary

| ID | Severity | Component | Finding |
|---|---|---|---|
| SEC-01 | High | Booking CSV export | Public endpoint discloses every booking's visitor name and email. |
| SEC-02 | Medium | Booking cancellation | No authentication or ownership check; an eligible booking can be cancelled by ID. |
| SEC-03 | Medium, potential | CSV spreadsheet handling | Caller-controlled visitor names may be interpreted as spreadsheet formulas. |
| SEC-04 | Low, conditional | Django settings | A known development fallback is used if `SECRET_KEY` is absent; the live environment was not verified. |

## Findings

### SEC-01 — Public booking export exposes visitor contact data

- **Severity:** High
- **Affected route:** `GET /api/reports/export/bookings/`
- **Evidence:** `backend/api/urls_reports.py:17` registers the route. `backend/api/views_reports.py:94-107` implements it without a login, staff, or permission check. Lines 100-101 select every booking and include `bk.visitor.full_name` and `bk.visitor.email`.
- **Preconditions:** The route is reachable by the caller. No account or booking ID is needed.
- **Impact:** Any caller can retrieve visitor names and email addresses for all bookings.
- **Reproduction:** Confirmed by source inspection only. No HTTP request or booking data was accessed.
- **Remediation:** Require server-side staff authorization before accessing or streaming the queryset. If a safe permission policy is not available, disable the route until it is. Review access logs and incident-response requirements if this route has been deployed publicly.
- **Deployment guidance:** Treat the endpoint as deployment-blocking while reachable without authorization.

### SEC-02 — Unauthenticated caller can cancel another visitor's booking

- **Severity:** Medium
- **Affected route:** `PATCH /api/bookings/<booking_id>/cancel/`
- **Evidence:** `backend/api/urls_pg.py:6` registers the route. `backend/api/views_pg.py:70-83` checks only the HTTP method and passes the path ID to the cancellation service. `backend/heritage_backend/services/booking_service.py:35-47` loads the record by primary key without caller identity or ownership validation.
- **Preconditions:** A caller can reach the endpoint and knows or guesses the sequential integer ID of a booking that is not already cancelled and is not for a past visit.
- **Impact:** Unauthorized cancellation of another visitor's booking.
- **Reproduction:** Confirmed by static inspection only. No booking was modified.
- **Remediation:** Require an authenticated identity and verify ownership (or staff authorization) server-side before changing state. Until the Phase 3 ownership design is implemented, apply an interim trusted policy or disable public cancellation. Non-enumerable IDs are not a substitute for authorization.
- **Deployment guidance:** Block public/member-only cancellation exposure until the authorization rule is enforced.

### SEC-03 — Potential spreadsheet formula injection in CSV export

- **Severity:** Medium, potential
- **Affected route:** `GET /api/reports/export/bookings/`; input originates at `POST /api/bookings/create/`
- **Evidence:** `backend/api/serializers.py:13-14` accepts ordinary visitor-name strings. `backend/api/views_reports.py:99-101` writes visitor names into CSV cells without spreadsheet-specific neutralization. CSV quoting does not prevent spreadsheet applications from interpreting formula-leading cell values.
- **Preconditions:** A caller submits a visitor name beginning with a formula marker, the value is stored, and an administrator opens the resulting export in spreadsheet software that evaluates the cell.
- **Impact:** Depending on the spreadsheet application and its settings, opening the export may evaluate attacker-controlled cell content.
- **Reproduction:** The source data path is evident; no CSV was generated or opened in a spreadsheet.
- **Remediation:** Neutralize formula-leading untrusted values when generating the export. Add a test that asserts the exact exported bytes for formula-marker values. Preserve existing CSV column names and order.
- **Deployment guidance:** Fix before administrators use the export in spreadsheet software. This is separate from the public PII disclosure in SEC-01.

### SEC-04 — Known fallback Django secret if deployment omits configuration

- **Severity:** Low, conditional; deployment configuration not verified
- **Affected component:** `backend/settings.py:23`
- **Evidence:** `SECRET_KEY` uses a known development fallback when the environment variable is absent. `render.yaml` configures a generated value, but no deployed environment was inspected.
- **Preconditions:** A deployment omits `SECRET_KEY` and uses the fallback.
- **Impact:** Django signatures and session-related protections would rely on a publicly known key. The deployed state and actual impact were not verified.
- **Reproduction:** Not attempted; no deployment configuration was accessed.
- **Remediation:** Fail fast when `SECRET_KEY` is missing or equals a development fallback in production settings. Do not log or copy the configured value.

## Review limitations

- Static inspection covered the 16 API patterns registered through `backend/heritage_backend/urls.py`.
- No live production request, database query, booking mutation, spreadsheet execution, or denial-of-service test was performed.
- The local full test run was blocked before database-backed assertions by PostgreSQL authentication failure. Eight isolated Mongo aggregation unit tests passed; they do not exercise these access-control findings.
- Actual deployment exposure, proxy rules, logs, and runtime secrets were not verified.
