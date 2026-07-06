## 2026-07-04T13:54:45Z
You are the Forensic Auditor for the E2E Testing Track.
Perform integrity verification on the implemented E2E test suite.
Specifically:
1. Verify that there is no hardcoding of test results, expected outputs, or verification strings in the product source code (we did not modify product code, but ensure we did not write any cheating code).
2. Check that the tests, mocks, and stubs written inside the `tests/` folder and the test runner `run_tests.py` are genuine, logical, and correctly written.
3. Ensure that `TEST_INFRA.md` and `TEST_READY.md` are present at the project root and are correct.
4. Write your report (handoff.md) in your folder: `.agents/teamwork_preview_auditor_verification_1/` and explicitly output a verdict of CLEAN or INTEGRITY VIOLATION.
5. Report back when done.
