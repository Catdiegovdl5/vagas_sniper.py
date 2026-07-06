# Original User Request

## Initial Request — 2026-07-04T13:36:15Z

You are the E2E Testing Track Orchestrator.
Your working directory is: C:\Users\99196\OneDrive\Documentos\vagas_bot\.agents\sub_orch_testing
Your parent is orchestrator (conv ID: parent).

**Objective**:
Design and implement a comprehensive, opaque-box E2E test suite derived from the requirements in C:\Users\99196\OneDrive\Documentos\vagas_bot\.agents\ORIGINAL_REQUEST.md.
You must:
1. Create `TEST_INFRA.md` at the project root outlining the test philosophy, feature inventory (at least 4 features: S-Tier scrapers, Snippet bypass, IA ranking, Auto-apply engine), test architecture, and coverage thresholds.
2. Implement the test cases using a systematic 4-tier approach:
   - Tier 1: Feature Coverage (>=5 tests per feature)
   - Tier 2: Boundary & Corner Cases (>=5 tests per feature)
   - Tier 3: Cross-Feature combinations (pairwise coverage)
   - Tier 4: Real-world application scenarios (at least 5 application-level tests)
   - Total minimum: ~11 * N + max(5, N/2) where N is number of features (~4).
3. Set up the testing runner/infrastructure to execute all E2E tests and ensure they exit with 0 when successful.
4. Once the test suite is complete and passing (or ready to be used by the implementation track), publish `TEST_READY.md` at the project root detailing the coverage and run commands.
5. Write your handoff and report completion.

**Scope boundaries**:
- You must NOT modify any product source code (such as `bot.py`, `app.py`, `database.py`, or scraper files). You can only write test scripts, test fixtures, and verification scripts.
- Write your agent metadata files only in `C:\Users\99196\OneDrive\Documentos\vagas_bot\.agents\sub_orch_testing`.

**Completion criteria**:
- `TEST_INFRA.md` and `TEST_READY.md` are present at the project root.
- The test suite is runnable via the command specified in `TEST_READY.md`.
