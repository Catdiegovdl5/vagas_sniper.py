# E2E Test Infrastructure Specification

This document details the End-to-End (E2E) testing infrastructure, architecture, and feature verification plan for the **vagas_bot** autonomous recruitment pipeline.

---

## 1. Test Philosophy

Our testing philosophy is designed around **hermetic isolation**, **zero-flakiness**, and **contract verification**:
- **Real Behavior over Dummies**: All mock stubs (`mock_glassdoor.py`, `mock_infojobs.py`, `mock_auto_apply.py`) and background servers maintain internal state and run real business logic (e.g. interacting with database and making local requests) rather than returning static hardcoded outcomes.
- **Offline/Sandboxed Execution**: External network interactions (LinkedIn, Glassdoor, InfoJobs, Indeed, Jooble, Groq APIs) are completely mocked at the library level (`requests`, `curl_cffi`, `playwright`, `groq`) to prevent network calls while preserving OS-level portability and speed.
- **Dynamic Adaptability**: Tests dynamically inspect the environment for real implementations. If real modules exist (e.g., when transitioning from Milestone 1/2 to production), E2E tests target them automatically. Otherwise, they fallback onto the mock stubs.

---

## 2. Feature Inventory under Test

The E2E test suite targets 4 main core features:

### A. S-Tier Scrapers
- **Scope**: Extraction of vacancies from LinkedIn, Glassdoor, InfoJobs, Indeed, and Jooble.
- **Contract**: Scrapers must return lists of job dicts matching the required schema:
  - `title`, `company`, `budget` (salary string/float), `link`, `platform`, `requirements` (full vacancy text, >=500 chars).
- **Mocks**: Stubs simulate response payload schemas, handling keywords and pagination dynamically.

### B. Snippet Bypass
- **Scope**: Anti-bot challenge detection and headless browser rendering.
- **Contract**: Scrapers must successfully utilize curl_cffi impersonate headers or Playwright sync/async automation to access vacancy pages and bypass basic cloudflare checks without hitting actual network calls.
- **Mocks**: Playwright browser/page objects are mocked in `conftest.py` to simulate browser rendering and return custom static HTML templates containing Cloudflare patterns.

### C. IA Ranking
- **Scope**: Match scoring, intent parsing, and keyword recommendation.
- **Contract**: Evaluates candidate compatibility by invoking Groq AI with a specific schema.
- **Mocks**: AsyncGroq chat completions are mocked to return structured JSON complying with the `JobEvaluation` Pydantic class.

### D. Auto-Apply Engine
- **Scope**: Easy Apply form detection, resume upload, and submission.
- **Contract**: Scans SQLite DB for jobs with match score >= 80, retrieves the resume `temp_curriculo.pdf`, and performs form filling/posting to the ATS platform.
- **Mocks**: A local Mock ATS FastAPI server is run in a background thread to receive and validate the multipart application submissions.

---

## 3. Test Architecture

The E2E testing framework is structured using `pytest`:

```
vagas_bot/
├── tests/
│   ├── conftest.py             # Database isolation, HTTP mocks, Playwright mocks, Mock ATS Server lifecycle
│   ├── mock_glassdoor.py       # Glassdoor scraper stub
│   ├── mock_infojobs.py        # InfoJobs scraper stub
│   ├── mock_auto_apply.py      # Auto-apply engine stub
│   ├── test_tier1.py           # Feature Coverage (20 tests)
│   ├── test_tier2.py           # Boundary & Corner Cases (20 tests)
│   ├── test_tier3.py           # Cross-Feature combinations (4 tests)
│   └── test_tier4.py           # Real-world application scenarios (5 tests)
├── run_tests.py                # Main test runner execution entrypoint
└── TEST_INFRA.md               # Infrastructure documentation
```

### Mock ATS Server Specs
- **Endpoints**:
  - `GET /form`: Serves standard HTML markup mockup form.
  - `POST /apply`: Accepts multipart form data (job_link, name, email, resume PDF file upload). Checks file size and returns `{"status": "success", ...}`.
- **Thread Lifecycle**: Automatically started and bound to `127.0.0.1:8081` on pytest initialization and cleanly torn down upon test session completion.

---

## 4. Coverage Thresholds

| Systematic Tier | Target Focus | Required Count | Current Count | Status |
|---|---|---|---|---|
| **Tier 1** | Feature Coverage (>=5 tests per feature) | 20 | 20 | Pass |
| **Tier 2** | Boundary & Corner Cases (>=5 tests per feature) | 20 | 20 | Pass |
| **Tier 3** | Cross-Feature Pairwise Combinations | 4 | 4 | Pass |
| **Tier 4** | Real-world Application Workflows | 5 | 5 | Pass |
| **Total** | | **49** | **49** | **Pass** |
