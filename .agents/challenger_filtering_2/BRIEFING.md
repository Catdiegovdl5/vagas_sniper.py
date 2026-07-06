# BRIEFING — 2026-07-04T15:44:37Z

## Mission
Empirically verify the correctness and robustness of the safety hard-locks and the 50-job sanity battery.

## 🔒 My Identity
- Archetype: Empirical Challenger
- Roles: critic, specialist
- Working directory: C:\Users\99196\OneDrive\Documentos\vagas_bot\.agents\challenger_filtering_2
- Original parent: 38b97bc9-06e8-487a-8010-4a139a7a12f2
- Milestone: Verify safety hard-locks and sanity battery
- Instance: 1 of 1

## 🔒 Key Constraints
- Review-only — do NOT modify implementation code.
- Rely on empirical testing and reproduction.
- Report findings without fixing them.

## Current Parent
- Conversation ID: 38b97bc9-06e8-487a-8010-4a139a7a12f2
- Updated: 2026-07-04T15:44:37Z

## Review Scope
- **Files to review**: `run_tests.py`, `tests/test_sanity_battery.py`, files defining safety hard-locks and sanity battery.
- **Interface contracts**: `PROJECT.md` or equivalent project specs.
- **Review criteria**: Correctness, safety hard-locks, correctness of tests, edge case challenges.

## Key Decisions Made
- Created `tests/test_adversarial_challenges.py` to write and execute custom regression tests verifying the limitations of python-level hard-locks.
- Performed log analysis on the initial `python run_tests.py` execution to isolate failures related to port 8081 being blocked or in TIME_WAIT.

## Artifact Index
- C:\Users\99196\OneDrive\Documentos\vagas_bot\.agents\challenger_filtering_2\handoff.md — Handoff report documenting test results and empirical validation.

## Attack Surface
- **Hypotheses tested**: Assessed the resilience of safety overrides against varying candidate levels (Sênior vs Junior), education status, and checked for foreign currency/English requirement leakage if the LLM hallucinatingly approves the job.
- **Vulnerabilities found**:
  1. Regression bug in `exige_experiencia` hard-lock: Unconditionally rejects experience-required jobs, breaking search for Pleno/Sênior candidates.
  2. Regression bug in `exige_faculdade` hard-lock: Unconditionally rejects degree-required jobs, breaking search for candidates with degrees.
  3. Gap in USD/Euro and Fluent English rules: No Python-level safety overrides exist for these categories.
- **Untested angles**: None. The 50-job sanity battery and hard-locks were fully stress-tested.

## Loaded Skills
- None

