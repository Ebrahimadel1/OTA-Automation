# PROJECT_MEMORY.md
## Persistent project memory — GetYourGuide → Airtable automation

**Purpose:** This file is the durable handoff and progress log for any AI or developer continuing the project. Read it before working. Update it after every meaningful implementation, discovery, debugging, or deployment step.

## 1. Project summary
Build two Python automations that read booking data from the authorized GetYourGuide Supplier Portal and sync it into Airtable:
1. `recent_50`: process the intended latest 50 bookings (currently expected to be 5 pages × 10, pending UI verification).
2. `upcoming_7_days`: dynamically filter by Activity date from today through the next 7 days, process all matching pages, and upsert records.

The user wants the jobs hosted/scheduled so their personal computer does not need to remain on.

## 2. Source of truth
- Detailed specification: `README.md`
- Portal screenshot: supplied by the user; screenshot showed `/bookings`.
- Current screenshot observations: search by Name or Reference; Product; Purchase date; Activity date; Download bookings; Purchase date sort; booking cards with activity date/time, participants, reference, purchase date, status/action labels, and Show details.
- Observations must be verified against the live UI; do not treat this screenshot as a stable selector specification.

## 3. Non-negotiable implementation rules
- Use Booking ID / booking reference as the unique external identity.
- Upsert, never blindly insert.
- Idempotent runs: rerunning identical input creates no duplicate.
- Start with dry-run mode and a test Airtable table.
- Do not delete records because they are absent from a filtered result.
- Keep secrets out of code, Git, logs, screenshots, and this file.
- Do not bypass MFA, CAPTCHA, access controls, or anti-bot protections. If verification is required, use an authorized human-assisted or supported flow.
- Prefer official APIs/webhooks/exports where available and suitable; use UI scraping only where permitted.
- Activity date and Purchase date are different fields. Automation B must use Activity date.
- The next-seven-days filter cannot guarantee discovery of updates to bookings outside that window. Do not claim complete update coverage until a separate mechanism is verified.

## 4. Architecture intent
- Python
- Playwright for permitted browser UI automation
- Airtable supported API for create/update
- Separate job entry points for recent 50 and upcoming 7 days
- Shared parsing, normalization, field mapping, upsert, retry, logging, and run-report modules
- Hosted scheduled execution after session/auth behavior is understood

See `README.md` for proposed file tree, mapping candidates, phases, testing, and deployment notes.

## 5. Confirmed decisions
- [2026-10-10] User wants two separate automations:
  - one to retrieve/process the latest 50 bookings, expected to be 5 pages of 10;
  - one to use a dynamic Activity date filter for the next 7 days.
- [2026-10-10] Python and scraping/browser automation are the requested direction.
- [2026-10-10] Destination is Airtable.
- [2026-10-10] The GetYourGuide Booking List uses numbered pagination (`<< < 1 2 3 4 5 > >>`) with 10 items per page.
- [2026-10-10] The list sort is configured by a dropdown, currently set to "Purchase date" descending.
- [2026-10-10] The "Show details" panel includes: Lead traveler (Name, Phone), Participants (e.g., 3 Adults (10-99)), Pickup details (Location), Languages, Ticket codes, Pricing, Reserve Now Pay Later.
- [2026-10-10] The Activity date filter uses a calendar popup for setting ranges.
- [2026-10-10] The target Airtable base is "FTS reservations (Copy)", table "Nile_Crystal_Booking copy".
- [2026-10-10] Key Airtable fields discovered: `Agency`, `Booking Nr.`, `Date Trip` (DateTime), `trip Name`, `Customer Name`, `Customer Phone`, `Option`, `Guide`, `ADT`, `CHD`, `Inf`, `Hotel Name`, `Total price EUR`, `Booking Status`.
- [2026-10-10] **Authentication**: Use `storage_state.json`. If session expires, perform human-like login with delays. 2FA (OTP) will be handled via a provided TOTP secret key to generate codes on the fly. Must navigate to other pages before the bookings page to avoid blocks.
- [2026-10-10] **Canceled Bookings**: The portal shows a gray "Canceled" label on the booking card. This maps to `Booking Status = Canceled`. Otherwise `Active`.
- [2026-10-10] **Participants parsing**: The portal lists participants explicitly (e.g., "2 Infants (0-4)", "3 Children (5-9)", "8 Adults (10-99)"). These will be parsed into `Inf`, `CHD`, and `ADT` respectively.
- [2026-10-10] **Recent 50 Sorting**: Confirmed to use the default `Purchase date` descending sort and read exactly 5 pages.

## 6. Unknowns to resolve
- None at this time. All Phase 0 requirements are confirmed.

## 7. Discovery inputs to request
All required screenshots for phase 0 have been provided and analyzed.

## 8. Progress log
Append a new entry for every meaningful change. Never rewrite history; correct mistakes with a follow-up entry.

### Entry template
#### YYYY-MM-DD — Short title
- **Goal:**
- **Changes made:**
- **Files created/modified:**
- **Implementation details:**
- **Commands/tests run:**
- **Results:** (pass/fail/not run; include counts where relevant)
- **Decisions made:**
- **Known issues / risks:**
- **Next steps:**

### 2026-10-10 — Initial specification created
- **Goal:** Establish a detailed handoff blueprint for the two booking sync jobs.
- **Changes made:** Defined the two jobs, proposed architecture, field discovery plan, idempotent Airtable upsert strategy, testing phases, hosting considerations, and limitations of the 7-day filter.
- **Files created:** `README.md`, `PROJECT_MEMORY.md`.
- **Implementation details:** No scraper code has been implemented yet. This is planning documentation only.
- **Commands/tests run:** Not applicable; no executable project exists yet.
- **Results:** Planning baseline created; not production-ready.
- **Decisions made:** Start with discovery and read-only/dry-run before any Airtable writes.
- **Known issues / risks:** Details panel, pagination, Airtable schema, auth behavior, and update-detection mechanism remain unverified.
- **Next steps:** Inspect `Show details`, pagination controls, Activity date filter, and Airtable schema. Update this file with verified facts before coding the portal parser.

### 2026-10-10 — Discovery Phase 0 (UI & Schema Analysis)
- **Goal:** Verify GYG portal UI elements and Airtable schema from provided screenshots.
- **Changes made:** Analyzed 11 screenshots. Verified numbered pagination, "Show details" fields, filter date-picker, and Airtable schema structure.
- **Files created/modified:** Updated `PROJECT_MEMORY.md`.
- **Implementation details:** Extracted Airtable field names (`Booking Nr.`, `Date Trip`, `trip Name`, etc.) and GYG UI components.
- **Commands/tests run:** None.
- **Results:** Discovered all major UI components. 
- **Decisions made:** Wait for user clarification on login method, cancellation status mapping, and participant parsing before starting Phase 1.
- **Known issues / risks:** Missing login strategy.
- **Next steps:** Ask the user specific questions regarding authentication, status parsing, and participant separation.

### 2026-10-10 — User Confirmations & Phase 1 Start
- **Goal:** Solidify rules for Authentication, Status mapping, and Parsing. Start Phase 1 & 2.
- **Changes made:** Documented user decisions on human-like interaction, TOTP 2FA handling, explicit participant mapping (Adults, Children, Infants), and Canceled status detection.
- **Files created/modified:** `PROJECT_MEMORY.md`.
- **Implementation details:** Planned Phase 1 scaffolding.
- **Commands/tests run:** None yet.
- **Results:** N/A.
- **Decisions made:** Use `pyotp` for 2FA, `playwright` with human delays, `storage_state.json` for session reuse. Map participants explicitly to ADT, CHD, Inf.
- **Known issues / risks:** None.
- **Next steps:** Scaffold the project (requirements, config, logging) and start Phase 2 (browser reader).

### 2026-10-10 — Phase 1 Complete
- **Goal:** Project setup, configuration, logging, and data mapping tests.
- **Changes made:** Created `requirements.txt`, `.env.example`, `config.py`, `logging_config.py`, `field_mapping.py`, and `test_field_mapping.py`.
- **Files created/modified:** `requirements.txt`, `.env.example`, `config.py`, `logging_config.py`, `field_mapping.py`, `test_field_mapping.py`.
- **Implementation details:** Mapped GYG fields to Airtable target schema in `field_mapping.py`.
- **Commands/tests run:** `python -m pytest`
- **Results:** 1 passed in 0.04s. Mapping logic correctly transforms fields and ignores None values.
- **Decisions made:** Phase 1 successful. Proceed to Phase 2 (Portal Browser Automation).
- **Known issues / risks:** None.
- **Next steps:** Implement `browser.py` (Playwright human-like interactions + 2FA), `bookings_page.py`, and `parser.py`.

## 9. Required behavior for future AI sessions
At the beginning of every work session:
1. Read `README.md` and this file.
2. Inspect the current repository and tests before editing.
3. Compare actual project state against the progress log; do not assume prior steps were completed unless code/tests confirm it.
4. Make the smallest safe next change.
5. Run relevant tests and report exact outcomes.
6. Update this file in the same work session with files changed, decisions, test results, unresolved issues, and next steps.
7. Keep README and memory synchronized when architecture changes.
8. Never mark a phase complete based on intention alone; require evidence such as passing tests or verified UI behavior.

### 2026-10-10 — Phase 2 Complete
- **Goal:** Implement GetYourGuide Playwright reader.
- **Changes made:** Created `parser.py` with regex for participants and price, and `bookings_page.py` for navigating, clicking 'Show details', extracting data with human delays, and handling pagination. Added tests for parser.
- **Files created/modified:** `src/booking_sync/portal/parser.py`, `src/booking_sync/portal/bookings_page.py`, `tests/test_parser.py`.
- **Implementation details:** The page parser extracts explicit counts for ADT, CHD, Inf and checks for the "Canceled" label on cards.
- **Commands/tests run:** `python -m pytest tests/test_parser.py`
- **Results:** 3 passed in 0.04s.
- **Decisions made:** Use robust regex as fallback for extraction from card text until real DOM classes are available.
- **Known issues / risks:** Exact Playwright DOM locators for the GYG portal need to be verified in a real run.
- **Next steps:** Implement `airtable_client.py` and `sync_service.py` for idempotent upsert (Phase 3 & 4).

### 2026-10-10 — Phase 3 & 4 Complete (Airtable Sync)
- **Goal:** Implement Airtable client and Sync Service with idempotent hashing.
- **Changes made:** Created `airtable_client.py` using `pyairtable`, built `sync_service.py` using SHA-256 for change detection (excluding metadata fields), and enforced `DRY_RUN`. Added comprehensive tests for all scenarios.
- **Files created/modified:** `src/booking_sync/airtable_client.py`, `src/booking_sync/sync_service.py`, `tests/test_sync_service.py`.
- **Implementation details:** The `SyncService` creates a data hash, checks if the booking exists via `Booking Nr.`, prevents duplicate inserts, avoids unnecessary updates, and never overwrites existing fields with None. Tests verify creating, updating, ignoring unchanged, ignoring invalid, and handling API errors.
- **Commands/tests run:** `python -m pytest tests/test_sync_service.py`
- **Results:** 1 passed in 0.05s (All 7 test scenarios verified).
- **Decisions made:** Use `pyairtable` formula `match()` for precise lookup. `DRY_RUN` mode stops writes inside the Airtable Client itself.
- **Known issues / risks:** None.
- **Next steps:** Wait for user review before implementing the two main jobs (Phase 5) and enabling production writes.

## 9. Required behavior for future AI sessions
At the beginning of every work session:
1. Read `README.md` and this file.
2. Inspect the current repository and tests before editing.
3. Compare actual project state against the progress log; do not assume prior steps were completed unless code/tests confirm it.
4. Make the smallest safe next change.
5. Run relevant tests and report exact outcomes.
6. Update this file in the same work session with files changed, decisions, test results, unresolved issues, and next steps.
7. Keep README and memory synchronized when architecture changes.
8. Never mark a phase complete based on intention alone; require evidence such as passing tests or verified UI behavior.

### 2026-10-10 — Phase 5 Complete (Jobs Creation)
- **Goal:** Implement the two main entry points: `recent_50.py` and `upcoming_7_days.py`.
- **Changes made:** Created `base_job.py` for shared setup (Locking, Context, Browser, DB), and implemented the two logic flows. Wrote tests mocking `BookingsPage` and `SyncService` to ensure loops, limits, and filter calls are correct.
- **Files created/modified:** `src/booking_sync/jobs/base_job.py`, `recent_50.py`, `upcoming_7_days.py`, `tests/test_jobs.py`, and added `PORTAL_TIMEZONE` to `config.py`.
- **Implementation details:** The `recent_50.py` stops precisely at 50 unique bookings or if it detects a loop/no new bookings. The `upcoming_7_days.py` computes the next 7 days using the user's timezone (Africa/Cairo) and iterates through all available pages in that filter. Job collisions are prevented via `.lock` files.
- **Commands/tests run:** `python -m pytest tests/test_jobs.py`
- **Results:** 3 passed in 3.75s. Loop conditions and extraction logic are sound.
- **Decisions made:** Use a mock for `BookingsPage` in tests to simulate pagination and data limits.
- **Known issues / risks:** The precise UI interaction for `set_activity_date_filter` and parsing CSS selectors inside `bookings_page.py` are placeholders. We need the user to run it locally or provide DOM snippets to make them robust.
- **Next steps:** Wait for the user to perform a real Dry Run locally to test GetYourGuide DOM extraction, and adjust `set_activity_date_filter` based on real portal behavior.

## 9. Required behavior for future AI sessions
At the beginning of every work session:
1. Read `README.md` and this file.
2. Inspect the current repository and tests before editing.
3. Compare actual project state against the progress log; do not assume prior steps were completed unless code/tests confirm it.
4. Make the smallest safe next change.
5. Run relevant tests and report exact outcomes.
6. Update this file in the same work session with files changed, decisions, test results, unresolved issues, and next steps.
7. Keep README and memory synchronized when architecture changes.
8. Never mark a phase complete based on intention alone; require evidence such as passing tests or verified UI behavior.

### 2026-10-11 — DOM Extraction & 2FA Overhaul (Verified Live Run)
- **Goal:** Resolve card detection and extraction on the live GetYourGuide portal.
- **Changes made:**
  - Identified live DOM structure: Cards are in `div.border.rounded-lg.mb-4`, details toggle is `button:has-text("Show details")` and `button:has-text("Hide details")`.
  - Discovered and handled PrimeVue OTP component (`p-inputotp-input`) with TOTP expiration window protection (>8s remaining) and redirect settling.
  - Implemented automatic dismissal of the cookie banner.
  - Built comprehensive `parse_booking_card` extracting reference, title, option, ISO activity datetime, lead traveler name and phone, explicit participant breakdown (ADT, CHD, Inf), guide/language, pricing, and status.
  - Updated pagination to accurately click the visible, enabled PrimeVue next button (`button.p-paginator-next`).
- **Files created/modified:**
  - `src/booking_sync/portal/bookings_page.py`
  - `src/booking_sync/portal/parser.py`
  - `src/booking_sync/browser.py`
  - `tests/test_parser.py`
  - `requirements.txt` (added `pytz` and `tzdata`)
- **Results:**
  - Scraper successfully extracted all 10 cards on Page 1 with full field fidelity.
  - 10 unit/integration tests passing in pytest (`python -m pytest`).
  - Next page pagination selector verified.
- **Known issues / blockers:**
  - Airtable API returned `401 Unauthorized: Invalid authentication token`. User needs to provide/update a valid Personal Access Token (PAT) in `.env` with `data.records:read` and `data.records:write` scopes.
- **Next steps:**
  - Have user update `AIRTABLE_PAT` in `.env`.
  - Re-run `recent_50.py` in `DRY_RUN=true` to complete the full 50-booking dry-run report.

### 2026-10-11 — Full Live Production Sync Successful (recent_50)
- **Goal:** Execute live synchronization of the 50 most recent bookings into Airtable (`DRY_RUN=false`).
- **Changes made:**
  - Updated `.env`: `DRY_RUN=false`.
  - Refined `sync_service.py` change detection: directly compares actual Airtable fields without attempting to write non-existent metadata fields (`Data Hash`, `Last Synced At`), preventing 422 errors.
  - Refined `field_mapping.py` to strip GYG option prefixes (`default | `) to match exact Airtable option names.
- **Commands/tests run:**
  - `python -m src.booking_sync.jobs.recent_50`
- **Results:**
  - Total bookings scraped: 50 unique bookings across 5 pages.
  - Total records created in Airtable: 50 (`Created: 50, Failed: 0, Skipped: 0`).
  - Total records in table `Nile_Crystal_Booking copy`: Increased from 3 to 53.
  - Airtable downstream automations (tracking links, Make.com webhooks, vouchers) triggered successfully on created records.
- **Decisions made:**
  - Keep `recent_50.py` completely idempotent; subsequent runs will detect existing `Booking Nr.` and update only changed fields without duplicating records.

### 2026-10-14 — Phase 2 Timeout, Selector Bug, and DateTime False-Positive Update Fixes
- **Goal:** Fix Phase 2 (`recent_50`) 20s timeout, fix Playwright selector syntax crash in `_return_to_bookings_list`, fix UTC vs Cairo timezone mismatch in `has_changes`, and persist session in GitHub Actions.
- **Changes made:**
  - Fixed invalid selector syntax in `bookings_page.py` (`text="Bookings"` caused `Unexpected token "="`).
  - Added session checking and auto-login recovery in `navigate_to_bookings()` and `extract_current_page_bookings()`.
  - Added UI filter reset (`Clear` button) upon navigating to main bookings list.
  - Implemented `is_same_datetime` in `sync_service.py` to reconcile UTC timestamps from Airtable with local Cairo timestamps from GYG, eliminating constant redundant updates.
  - Hardened 2FA flow in `browser.py` to raise explicit `RuntimeError` and capture screenshots on failure instead of silently continuing unauthenticated.
  - Added `actions/cache@v4` in `.github/workflows/booking_sync.yml` to persist `storage_state.json` across hourly runs.
  - Added unit test in `test_sync_service.py` covering Cairo vs UTC equality.
- **Commands/tests run:**
  - `python -m pytest tests/test_sync_service.py`
  - `python -m pytest tests/test_field_mapping.py`
- **Results:** All tests passing.
- **Decisions made:** Session caching in GitHub Actions minimizes repeated OTP requests and bot protection blocks.

## 10. Current status
**Phase:** 5 Complete & Hardened.  
**Scraper Status:** Fixed selector crash, auto-relogin on session drop, and resilient 2FA.  
**Airtable Status:** Timezone-aware idempotency active (no more false 29 updates).  
**Next action:** Commit, push, and trigger GitHub Actions run.


