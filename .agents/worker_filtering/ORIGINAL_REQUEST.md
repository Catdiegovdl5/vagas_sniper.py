## 2026-07-04T15:38:34Z
You are the Worker. Your working directory is C:\Users\99196\OneDrive\Documentos\vagas_bot\.agents\worker_filtering.
Your objective is to implement the following changes in the codebase:

1. **Fix Mock Mismatches**:
   Update mock JSON completions in the test suite to include the missing fields `exige_faculdade`, `salary_declared`, and `has_benefits` to prevent Pydantic ValidationError. Modify:
   - `tests/conftest.py` (around lines 347-359)
   - `tests/test_tier1.py` (around lines 197-208)
   - `tests/test_tier2.py` (around lines 193-204)
   Add `"exige_faculdade": false, "salary_declared": true, "has_benefits": true` to the dictionary templates.

2. **R1: Python Hard-Locks**:
   Modify `scrapers/ai_filter.py`. After parsing the `JobEvaluation` Pydantic object, check if `aprovado` is `True`. If it is `True`, check the following safety boolean fields:
   - `vaga_corresponde_ao_cargo == False`
   - `is_freelance == True`
   - `localidade_correta == False`
   - `exige_faculdade == True`
   - `exige_experiencia == True`
   If any of these conditions are met, override and set `aprovado = False`, reset the `score` to `0`, and update the `reason` to show a `[Hard-Lock Override]` message containing the violated conditions.
   Make sure the returned dictionary from `score_job_match` includes the fields: `aprovado`, `score`, `reason`, `reqs`, `bonus`, `benefits`, `model`, `salary_declared`, `has_benefits`, `exige_faculdade`, `is_freelance`, `vaga_corresponde_ao_cargo`, `localidade_correta`, `exige_experiencia`.

3. **R2: Groq Model Upgrade**:
   Update `scrapers/ai_filter.py` to replace `"llama-3.1-8b-instant"` with `"llama3-70b-8192"` (or `"llama-3.3-70b-versatile"`) at all three completion model fields. Reduce the concurrency semaphore from `8` to `4` to prevent rate limit issues under the 70B model.

4. **R3: 50-Job Sanity Test Battery**:
   Create a JSON dataset `tests/sanity_battery.json` containing 50 trick jobs that must be blocked. The jobs must cover categories like:
   - USD/Euro salaries (when candidate is junior / remote BR)
   - Freelance / Workana / Hourly projects
   - Seniority level mismatches (junior candidate vs Pleno/Senior requirements)
   - Mandatory college/education degree (candidate is Sem Formação)
   - Fluent English requirements (candidate is junior / remote BR)
   Create `tests/test_sanity_battery.py` which runs a pytest test that loads these 50 jobs, runs `score_job_match` for each, and asserts that the approval rate is strictly 0% (every job is rejected with `aprovado = False`).

5. **Verify**:
   Run the test suite via `python run_tests.py` and confirm that all 49 existing tests pass.
   Run `pytest tests/test_sanity_battery.py` and confirm that all 50 trick jobs are correctly rejected and the test passes.
   Document the exact commands run and the output in your handoff report.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write your progress.md and handoff.md inside your working directory C:\Users\99196\OneDrive\Documentos\vagas_bot\.agents\worker_filtering and send a message when done.
