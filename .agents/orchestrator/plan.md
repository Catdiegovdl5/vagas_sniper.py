# Orchestration Plan - vagas_bot Codebase Audit & Optimization

This plan details the steps to aggressively audit the codebase, remove dead code/unused imports, resolve stability issues, and implement performance and rate-limiting optimizations for a stable production release.

## Milestones

### Milestone 1: Exploration & Audit Proposal
- **Objective**: Detailed assessment of the entire codebase (`scrapers/`, `tests/`, `bot.py`, `app.py`, `database.py`, etc.) to find dead code, unused imports, potential crash/stability issues, and performance/rate-limiting optimization opportunities.
- **Worker**: `teamwork_preview_explorer`
- **Output**: Detailed audit report listing all files to clean, bugs to fix, and optimizations to implement.
- **Status**: PLANNED

### Milestone 2: Codebase Audit and Cleanup (R1)
- **Objective**: Aggressively remove dead code, unused imports, and obsolete files. Rewrite inefficient logic.
- **Worker**: `teamwork_preview_worker`
- **Status**: PLANNED

### Milestone 3: Bug Fixing and Stability (R2)
- **Objective**: Fix potential bot or server crash issues, enhance exception handling, and handle edge cases robustly.
- **Worker**: `teamwork_preview_worker`
- **Status**: PLANNED

### Milestone 4: Performance & Rate-Limiting Optimizations (R3)
- **Objective**: Implement async task optimization, Groq AI API rate-limiting handling, and scraper reliability.
- **Worker**: `teamwork_preview_worker`
- **Status**: PLANNED

### Milestone 5: Verification & Review
- **Objective**: Verify that all 53 existing tests pass, write new regression or stress tests if necessary, and ensure no regressions.
- **Worker**: `teamwork_preview_reviewer` + `teamwork_preview_challenger`
- **Status**: PLANNED

### Milestone 6: Forensic Audit
- **Objective**: Perform independent audit checks to verify that implementation conforms to integrity rules and no hardcoding or cheating exists.
- **Worker**: `teamwork_preview_auditor`
- **Status**: PLANNED

## Execution Strategy
1. Dispatch Explorer to perform a complete codebase audit and output a report with concrete proposed actions.
2. Review the explorer's report, adjust the milestone details if necessary.
3. Dispatch Worker to implement R1 (cleanup).
4. Dispatch Worker to implement R2 (stability fixes).
5. Dispatch Worker to implement R3 (rate-limiting and performance optimizations).
6. Dispatch Reviewer and Challenger to verify all existing and new tests pass, and check performance/stability.
7. Dispatch Forensic Auditor to verify integrity.
8. Synthesize final results and report to parent.
