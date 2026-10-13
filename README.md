# GetYourGuide → Airtable Booking Automation
## Project Blueprint & Implementation Specification

**Status:** Planning / discovery  
**Primary language:** Python  
**Browser automation:** Playwright (authorized supplier-account UI access only)  
**Destination:** Airtable API  
**UI reference:** Screenshot supplied by the user showing `https://supplier.getyourguide.com/bookings`

> This document is the source of truth for the coding AI. Read it before changing code. Update `PROJECT_MEMORY.md` after every meaningful step. Do not claim a feature works until it has been tested and the test result is recorded.

---

## 1. Project objective

Build two separate, reliable automations that read booking information from the company's GetYourGuide Supplier Portal and synchronize it into the appropriate Airtable table.

### Automation A — Recent 50 bookings
- Open the Bookings page.
- Read the most recent 50 bookings.
- The visible UI currently appears to show 10 bookings per page; verify pagination behavior before implementation.
- Process 5 pages × 10 bookings, if the portal's actual pagination supports this.
- For each booking, extract the available fields, open `Show details` if necessary, normalize the values, then upsert the record in Airtable.
- If a record already exists, update it instead of creating a duplicate.
- Do not assume the visible ordering is newest-first until confirmed from the page and a test run.

### Automation B — Upcoming activity dates
- Apply the portal's **Activity date** filter dynamically from the current date through the next 7 days, using the portal/account's intended timezone.
- Read every result page matching the date range; do not hard-code five pages for this automation.
- Upsert each result to Airtable, including updates to records already stored.
- Run repeatedly so changes to bookings that remain in the date window are picked up on the next run.
- This filter alone cannot guarantee discovery of edits to bookings outside the next-7-days window. If detecting every edit is required, investigate an official modified-since feed/API, booking-update notifications, or a broader periodic reconciliation.

### Shared requirements
- Idempotent sync: rerunning a job must not create duplicate records.
- Stable identity: use the booking reference shown by the portal (for example, a reference resembling `GYG...`) as the external unique key.
- Logs, retries, error reporting, safe handling of partial failures, and a clear dry-run mode.
- No credentials or tokens committed to Git.
- No silent deletion of Airtable records when a booking disappears from a filtered result.
- The system should be deployable on a server/scheduler so the user's laptop does not need to stay on.

---

## 2. Screenshot observations (verify in the live portal)

The provided screenshot shows:
- URL path: `/bookings`
- Search field: **Name or Reference**
- **Product** selector
- **Purchase date** range
- **Activity date** range
- **Download bookings** button with dropdown
- A visible sort label **Purchase date** with a downward arrow
- Booking cards containing product title, activity date/time, participant count, booking reference, purchase date, and `Show details`
- Some cards show operational states such as `Urgent` or `Missing` and actions such as `Specify pickup time`

These are observations from one screenshot, not a confirmed DOM contract. Inspect the page and detail panel before choosing selectors or assuming what each label means.

### Important filter distinction
- Use **Activity date** for Automation B, because the stated requirement is based on when the experience takes place.
- **Purchase date** means when the booking was purchased; it is not interchangeable with activity date.
- Sorting by purchase date does not necessarily mean the portal is sorted by last modification time.

---

## 3. Proposed architecture

```text
                 Scheduler / Hosted Runner
                           |
             +-------------+-------------+
             |                           |
     recent_bookings job          upcoming_bookings job
     latest 50 records            activity date: today..today+7
             |                           |
             +-------------+-------------+
                           |
                    Portal Adapter
              Playwright login/session
              search, filters, pagination
              booking list + detail parser
                           |
                    Normalization Layer
            dates, currency, participants, status
                           |
                    Sync / Upsert Service
              lookup by external booking reference
              compare normalized fields / hash
              create or update Airtable record
                           |
             +-------------+-------------+
             |                           |
       Airtable table              Run/event logs
       configured mapping          success/fail/change
```

### Suggested project structure

```text
getyourguide-airtable-sync/
├── README.md
├── PROJECT_MEMORY.md
├── .env.example
├── .gitignore
├── pyproject.toml                 # or requirements.txt; choose one
├── src/
│   └── booking_sync/
│       ├── config.py
│       ├── browser.py             # Playwright lifecycle/session handling
│       ├── auth.py                # supported login flow; no MFA bypass
│       ├── portal/
│       │   ├── bookings_page.py
│       │   ├── filters.py
│       │   ├── pagination.py
│       │   └── parser.py
│       ├── airtable_client.py
│       ├── field_mapping.py
│       ├── normalize.py
│       ├── sync_service.py
│       ├── jobs/
│       │   ├── recent_50.py
│       │   └── upcoming_7_days.py
│       ├── logging_config.py
│       └── cli.py
├── tests/
│   ├── fixtures/
│   ├── test_normalize.py
│   ├── test_field_mapping.py
│   ├── test_upsert.py
│   ├── test_pagination.py
│   └── test_date_window.py
└── logs/                          # ignored by Git; preferably use stdout in hosted runner
```

The coding AI may adjust the structure if it records the reason in `PROJECT_MEMORY.md`.

---

## 4. Technology choices

### Python
Use a supported, pinned Python version available in the deployment environment.

### Playwright
Use Playwright for browser-driven UI automation **only if this use is permitted by the account terms and portal rules**. Prefer an official API, export, webhook, or supported integration if one is available and suitable.

- Prefer semantic/accessibility locators (`get_by_role`, labels, text) where stable.
- Avoid brittle selectors tied to generated CSS classes.
- Do not use arbitrary sleeps as the main synchronization strategy; wait for observable page states.
- Handle timeouts and navigation errors with bounded retries.
- Keep screenshots/HTML traces for failures only when they contain no unnecessary personal data; restrict access and retention.
- Never attempt to bypass CAPTCHA, MFA, access controls, or rate limits. If interactive verification is required, pause for an authorized human or use a supported session flow.

### Airtable API
Use Airtable's supported API and a personal access token with the minimum required scopes and base access. Confirm the base, table, field names, and API limits before writing.

### Configuration
Use environment variables loaded from `.env` for local development. In production, use the hosting provider's secret manager/environment settings.

Example `.env.example` (placeholders only):

```dotenv
# GetYourGuide portal credentials are not committed to source control.
GYG_LOGIN_EMAIL=
# Use only if an approved flow requires a password; never commit a real value.
GYG_LOGIN_PASSWORD=

AIRTABLE_PAT=
AIRTABLE_BASE_ID=
AIRTABLE_TABLE_NAME=Bookings

# Set only after confirming the account's intended timezone.
PORTAL_TIMEZONE=Africa/Cairo

HEADLESS=false
DRY_RUN=true
LOG_LEVEL=INFO
```

Do not store real credentials in `PROJECT_MEMORY.md`, logs, screenshots, Git, or prompts sent to third-party services. Add `.env`, browser profiles, traces, logs, and local state to `.gitignore`.

---

## 5. Data discovery and Airtable mapping

Do not finalize the schema from the list-card screenshot alone. Open `Show details` on representative bookings and inventory the exact fields available.

### Candidate source → Airtable mapping

| Source field / concept | Airtable target (proposed) | Notes |
|---|---|---|
| Booking reference | `Booking ID` | Required unique key; preserve exact text |
| Customer name | `Client Name` | Confirm exact source label and privacy requirements |
| Product/activity title | `Product` | Preserve source text |
| Activity date | `Activity Date` | Normalize to ISO date/time while preserving timezone meaning |
| Activity time | `Activity Time` or combined `Activity DateTime` | Decide after inspecting details |
| Participants | `Participants` | Confirm whether total or per category |
| Purchase date | `Purchase Date` | Do not confuse with activity date |
| Total/booking price | `Total Price` | Confirm currency and whether this is gross/net |
| Currency | `Currency` | Do not infer if not shown |
| Pickup place | `Pickup Place` | May require opening details; may be absent for some products |
| Booking status | `Booking Status` | Record exact status options and meanings |
| Product/option/variant | `Option` | Add if available and useful |
| Agency/supplier source | `Agency` | Confirm expected Airtable meaning before populating |
| Portal URL | `Source URL` | Optional, if safe and useful |
| Last successful sync | `Last Synced At` | Managed by this automation |
| Last seen in portal | `Last Seen At` | Updated when record is observed |
| Content fingerprint | `Data Hash` | Hash of normalized source fields, not credentials |
| Sync state | `Sync Status` | e.g. Created, Updated, Unchanged, Failed |
| Last error | `Sync Error` | Avoid storing unnecessary customer data |

**Mapping rule:** never create a guessed Airtable column automatically in production. Compare this table against the existing base and produce a mapping report. If a required field is missing, ask the operator or use a documented configuration decision.

### Required discovery artifacts
1. Screenshot of `Show details` expanded for one ordinary booking.
2. Screenshot of a booking with pickup information, if the product has pickup.
3. Screenshot of the bottom of the results page showing pagination controls.
4. Screenshot of the Activity date picker after selecting a date range.
5. Airtable table field names and field types (hide tokens and sensitive customer details).
6. One sample booking with customer details obscured, if needed for parsing.

---

## 6. Portal automation behavior

### Login and session
- Use the normal authorized login process.
- If MFA/OTP appears, do not try to defeat it. Prefer a supported persistent authenticated session or human-assisted login, if permitted.
- Do not store session cookies in Git or share them in project files.
- If the portal invalidates the session, stop safely and log `AUTH_REQUIRED`; do not loop indefinitely.
- Do not attempt to defeat anti-bot mechanisms or circumvent access controls.

### List parsing
For each booking card:
1. Locate the card container using stable accessible structure.
2. Extract visible reference, product title, activity date/time, participant count, purchase date, and visible status badges.
3. Open `Show details` when additional required fields are missing.
4. Parse the detail panel without assuming the same fields exist for every product.
5. Validate that a booking reference exists before sending the record to Airtable.
6. Record parsing failures as per-booking errors and continue where safe.

### Pagination
- Determine whether the portal uses numbered pages, next/previous controls, infinite scroll, or a load-more pattern.
- For Automation A, collect no more than the intended latest 50 unique booking references after confirming ordering.
- Stop at the correct boundary; deduplicate by booking reference across pages.
- For Automation B, continue through all pages returned by the date filter.
- Detect a pagination loop (same page/signature repeatedly) and stop with a clear error.
- Do not silently treat a partial page read as a complete successful run.

### Filters
- Automation A: clear stale filters first; confirm the intended default ordering; collect the latest 50.
- Automation B: set Activity date start/end dynamically at each run; confirm the UI accepted both dates and that results correspond to the range.
- Record the applied date window in run logs.
- Confirm inclusive/exclusive boundary behavior and timezone handling during testing.

---

## 7. Sync and deduplication logic

Use the booking reference as the external identity, not customer name or activity date.

Recommended algorithm:

1. Parse and normalize one booking.
2. Validate required identity fields.
3. Query Airtable for an exact match on `Booking ID`.
4. Compute a deterministic hash over the normalized fields being synchronized.
5. If no record exists, create it.
6. If a record exists and the hash differs, update only the mapped source fields and sync metadata.
7. If the hash matches, skip the business-field update but refresh `Last Seen At` / run metrics as configured.
8. Record a structured result: `created`, `updated`, `unchanged`, `failed`, or `skipped_invalid`.
9. Apply bounded retries for transient network/rate-limit failures, honoring `Retry-After` when provided.
10. Never delete a booking because it is absent from one filtered search.

Consider a local cache only as an optimization; Airtable's unique key lookup remains the source for determining whether a record exists. If concurrent runs are possible, add a lock or ensure the scheduler prevents overlapping runs.

### Hashing
- Use a deterministic serialization of normalized, mapped source fields.
- Exclude volatile fields such as sync timestamps and logs.
- Do not hash or log secrets.
- Avoid false changes from formatting differences (whitespace, date formatting, currency formatting).

---

## 8. The important update-detection limitation

Automation B's next-seven-days Activity date filter will detect changes only for bookings that appear in the result set when the job runs. It will not guarantee discovery of an edit to an old booking that no longer falls inside that window.

Investigate these options in order:
1. Official API/webhook or supported modified-since mechanism, if available for this supplier account.
2. Booking-update notifications/email, parsed as a separate update signal and reconciled by booking reference.
3. A broader scheduled reconciliation (for example, all upcoming bookings or a rolling longer period), if permitted and operationally reasonable.
4. Periodic export/download comparison, if the portal's export supports the required fields and date range.

Do not describe the two jobs as guaranteeing every historical update until one of these mechanisms has been verified and tested.

---

## 9. Scheduling and hosting

Target a hosted scheduled runner so the local PC does not need to stay powered on. Evaluate options only after the login/session behavior and run duration are understood.

Deployment requirements:
- Store secrets as platform secrets, not in files committed to Git.
- Install Playwright browser dependencies in the runner image.
- Use a persistent profile only if allowed, secured, and necessary; protect it like a credential.
- Ensure jobs cannot overlap.
- Set timeouts and a maximum retry budget.
- Keep logs and alert on authentication failure, repeated portal changes, Airtable errors, or incomplete pagination.
- Confirm hosting terms, sleep limits, execution time, and cost before choosing a provider.
- A free tier must not be described as permanently free unless its current terms establish that.

---

## 10. Testing and acceptance criteria

### Unit tests
- Normalize dates, times, currencies, participant counts, whitespace, and missing optional fields.
- Map source fields to Airtable fields correctly.
- Generate stable hashes for equivalent data.
- Identify changed fields and unchanged records.
- Calculate the rolling 7-day window correctly across month/year boundaries.
- Deduplicate references appearing on multiple pages.

### Integration tests
Use a test Airtable table/base first:
- New booking creates one record.
- Re-running the same input creates no duplicate.
- Changed source fields update the existing record.
- Unchanged source fields are not rewritten unnecessarily.
- API failure is retried safely.
- Invalid booking with no reference is rejected and logged.
- Filter pagination handles more than 10 results.
- An incomplete run is reported as incomplete rather than success.
- Dry-run makes no writes.

### Acceptance criteria
- Automation A processes exactly the intended latest 50 unique bookings when at least 50 are available and the UI supports that model.
- Automation B processes every result in the verified Activity date window.
- Both jobs are idempotent by booking reference.
- Existing records are updated when source fields change.
- Failures are visible and recoverable.
- No real credentials are in source control or memory files.
- A run report lists counts of created, updated, unchanged, failed, and skipped records.
- No claim is made about historical-update coverage without a tested mechanism.

---

## 11. Implementation phases

### Phase 0 — Discovery (no writes)
- Inspect the list, details panel, filters, sort order, pagination, and login behavior.
- Inspect Airtable base/table schema.
- Record exact selectors, source labels, and mapping decisions in `PROJECT_MEMORY.md`.
- Deliver a discovery report and identify uncertainties.

### Phase 1 — Project scaffold
- Create package, configuration, logging, `.env.example`, `.gitignore`, CLI, and tests.
- Add a dry-run default.
- Verify dependencies install cleanly.

### Phase 2 — Portal reader
- Implement authorized login/session handling.
- Read list cards and detail panels.
- Implement robust pagination.
- Save sanitized fixtures for tests where appropriate.

### Phase 3 — Normalization and mapping
- Normalize source data.
- Validate required fields.
- Confirm Airtable mapping with the operator.

### Phase 4 — Airtable sync
- Implement lookup/upsert by booking reference.
- Add hash-based change detection, retries, rate-limit handling, and run summaries.
- Test against a test table before production.

### Phase 5 — Two jobs
- Implement `recent_50` and `upcoming_7_days`.
- Verify sorting, page boundaries, date filters, and timezone behavior.
- Add safeguards against overlapping runs.

### Phase 6 — Update coverage
- Test whether the portal exposes last-modified data or supported notifications/API.
- If not, document the limitation and propose broader reconciliation.

### Phase 7 — Deployment
- Choose a hosted runner.
- Configure secrets, schedule, logs, alerts, and recovery instructions.
- Run a monitored pilot before enabling unattended production runs.

### Phase 8 — Handover
- Update this README if architecture changes.
- Update `PROJECT_MEMORY.md`.
- Provide runbook, environment variable list, known limitations, tests, and rollback steps.

---

## 12. Operational safety

- Start with `DRY_RUN=true`.
- Never run bulk writes against production before the mapping is reviewed.
- Use minimum Airtable permissions.
- Redact credentials, cookies, tokens, and unnecessary customer data from logs.
- Respect the supplier portal's terms, access restrictions, rate limits, and privacy obligations.
- Do not bypass MFA, CAPTCHA, or anti-bot protections.
- Keep an audit trail of record changes made by the automation.
- Add a kill switch / disable-schedule procedure.

---

## 13. First task for the coding AI

**Do not immediately build a full scraper.** Start with Phase 0 and ask for missing screenshots/schema details. Inspect the portal's current UI, confirm the exact data fields and pagination model, and create a written discovery report. Only then implement the reader and test it in read-only/dry-run mode.
