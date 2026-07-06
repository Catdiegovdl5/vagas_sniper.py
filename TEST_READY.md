# Test Execution Ready Details

The E2E Test Suite has been fully integrated and is ready for local and CI execution.

## 1. Run Command

To execute the test suite and verify the entire Recruiter pipeline, run:

```bash
python run_tests.py
```

This runner script automatically initializes the test configuration, spins up the background Mock ATS Server, runs `pytest` over the 49 systematic tests, shuts down the background server, and returns exit code 0 on success.

Alternatively, you can run `pytest` directly:

```bash
pytest tests/
```

---

## 2. Test Coverage & Tiers

The test suite covers exactly **49 tests** structured across 4 specialized testing tiers:

### Tier 1: Feature Coverage (20 tests)
- **LinkedIn, Glassdoor, InfoJobs, Indeed, Jooble Scrapers** (5 tests): Confirms schema compliance (title, company, budget, link, platform, requirements length).
- **Snippet Bypass** (5 tests): Confirms curl_cffi and Playwright mocks are invoked, and Cloudflare challenge conditions are parsed.
- **IA Ranking** (5 tests): Confirms compatibility scoring, intent extraction, and resume keywords suggestions logic.
- **Auto-Apply Engine** (5 tests): Validates resume PDF uploads, SQLite status transitions, and skip criteria.

### Tier 2: Boundary & Corner Cases (20 tests)
- **Scraper Boundaries** (5 tests): Evaluates pagination overflow, special characters encoding, missing HTML elements, and excessive keyword sizes.
- **Snippet Bypass Boundaries** (5 tests): Exercises connection timeouts, redirection handling, and server error codes (e.g. 500/403).
- **IA Ranking Boundaries** (5 tests): Exercises malformed JSON responses, rate limiting retries (429), empty resume inputs, and extreme text length limits.
- **Auto-Apply Boundaries** (5 tests): Tests database SQLite transaction locks (concurrency), missing DB fields, empty resume uploads, and duplicate link handling.

### Tier 3: Cross-Feature Combinations (4 tests)
- Tests pairwise integration combinations:
  1. `Scraper + Snippet Bypass` (Indeed/Playwright challenge bypass integration).
  2. `Scraper + DB Ingestion + IA Ranking` (InfoJobs to AI scoring pipeline).
  3. `IA Ranking + Auto-Apply Engine` (High-score filtering triggers automatic ATS submission).
  4. `Scraper + IA Ranking + Auto-Apply Engine` (Full end-to-end recruiter cycle).

### Tier 4: Real-World Scenarios (5 tests)
- Simulates complete system API endpoints:
  1. `/api/trigger`: Triggers end-to-end scrapers run and DB recording.
  2. `/api/jobs`: Serves vacancies dashboard backend JSON structure.
  3. `/api/webhook/n8n`: Direct ingestion of external JSON vacancy lists.
  4. `/api/logs`: Retrieves system runtime logs from the logger.
  5. `Full Cycle`: Simulation of a job landing via n8n, AI rating, and submission via Auto-Apply.

---

## 3. Test Isolation Specifications

- **Database**: Uses `tests/jobs_test.db` which is fully isolated from the production `jobs.db` database. Schema is created and deleted dynamically before and after each test.
- **Mock ATS Server**: Automatically runs in a background daemon thread on `http://127.0.0.1:8081`. Accepts submissions with `temp_curriculo.pdf`.
- **Mocks**: Zero network dependency. Fully mocks:
  - `requests` (bypassing local/127.0.0.1 to let ATS server talk directly)
  - `curl_cffi`
  - `playwright.sync_api` and `playwright.async_api`
  - `groq.AsyncGroq` (stable JSON response generator)
