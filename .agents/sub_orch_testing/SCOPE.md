# Scope: E2E Testing Track

## Architecture
- **E2E Testing Harness**:
  - Independent of implementation source code. It should interact with the application via its public interfaces (e.g. database file `jobs.db`, mock HTTP servers, and execution of CLI scripts like `bot.py` or running the FastAPI app `app.py`).
  - To test scrapers and Deep Scrape without hitting live external servers, the E2E test runner will use a mock HTTP server simulating LinkedIn, Glassdoor, InfoJobs, Indeed, and Jooble pages.
  - To test the Groq AI Ranking, it will mock/intercept the Groq API calls or use simulated responses.
  - To test the Auto-Apply engine, it will run a local Mock ATS Server (simulating an ATS receiving applications) and verify that the auto-apply engine successfully POSTs data and resumes.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | E2E Test Infra & Mocks | Implement test structure, config, and mock HTTP servers for job sites and ATS. | none | DONE |
| 2 | Tier 1 & Tier 2 Tests | Implement Feature Coverage (>=5 tests per feature) and Boundary Cases (>=5 tests per feature). | M1 | DONE |
| 3 | Tier 3 & Tier 4 Tests | Implement Cross-Feature Combinations and Real-World Application scenarios. | M2 | DONE |
| 4 | Execution & Verification | Run the full E2E test suite, ensure 100% pass rate, and generate `TEST_READY.md`. | M3 | IN_PROGRESS |

## Interface Contracts
### E2E Test Runner ↔ Mock Servers
- The E2E test runner spins up mock HTTP servers (e.g. on localhost ports) before launching the tests.
- Scrapers/deep scraping must be configured via environment variables (like a custom base URL) or local DNS/hosts (if supported) to target the mock servers instead of the live web.
