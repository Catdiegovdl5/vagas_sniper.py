# Orchestration Plan - Sniper_bot IA Filtering Intelligence Refinement

This plan details the steps to implement Python hard-locks, upgrade the LLM model to 70B+, and establish a 50-job sanity test battery with a 0% approval rate for trick jobs.

## Milestones

### Milestone 1: Decompose & Design
- **Objective**: Detailed assessment of `scrapers/ai_filter.py` and layout of required code changes.
- **Worker**: `teamwork_preview_explorer` (conv: explorer_filtering)
- **Status**: PLANNED

### Milestone 2: Implementation of Hard-Locks & Model Upgrade (R1 & R2)
- **Objective**: Implement model upgrade to `llama3-70b-8192` (or mixtral-8x7b-32768) and code-level override safety logic.
- **Worker**: `teamwork_preview_worker` (conv: worker_filtering)
- **Status**: PLANNED

### Milestone 3: 50-Job Trick Dataset & Sanity Test Battery (R3)
- **Objective**: Create `tests/trick_jobs_dataset.json` with 50 diverse trick jobs and `tests/test_sanity_battery.py` to evaluate them.
- **Worker**: `teamwork_preview_worker` (conv: worker_filtering) or a new worker instance.
- **Status**: PLANNED

### Milestone 4: Verification & Reviews
- **Objective**: Run E2E test suite, run the 50-job sanity battery, review code correctness and robustness.
- **Worker**: `teamwork_preview_reviewer` (conv: reviewer_filtering) + `teamwork_preview_challenger` (conv: challenger_filtering)
- **Status**: PLANNED

### Milestone 5: Forensic Audit
- **Objective**: Independent audit of the implementation to verify no cheating, no hardcoding, and correct logic.
- **Worker**: `teamwork_preview_auditor` (conv: auditor_filtering)
- **Status**: PLANNED

## Execution Strategy
1. Dispatch Explorer to inspect `scrapers/ai_filter.py` and draft the exact logic for Python hard-locks and the model upgrade.
2. Dispatch Worker to implement R1 (hard-locks) and R2 (model upgrade).
3. Dispatch Worker to create the 50 trick jobs dataset and sanity test script.
4. Dispatch Reviewer and Challenger to verify all tests (existing 49 tests + new sanity test) pass, and verify 0% approval on the trick jobs.
5. Dispatch Forensic Auditor to verify integrity.
6. Compile final `handoff.md` and notify parent.
