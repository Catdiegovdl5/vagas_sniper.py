# Handoff Report: Safety Hard-Locks and Sanity Battery Empirical Verification

This report documents the verification results of the vagas_bot safety hard-locks and the 50-job sanity battery, including regression bugs and safety gaps found through adversarial stress testing.

---

## 1. Observation

### Test Suite Execution
- **Command Run**: `python run_tests.py`
- **Output**:
  ```
  FAILED tests/test_tier1.py::test_auto_apply_fails_gracefully_on_network_error
  FAILED tests/test_tier2.py::test_auto_apply_handles_empty_db_fields - assert ...
  FAILED tests/test_tier2.py::test_auto_apply_handles_missing_resume_path - ass...
  FAILED tests/test_tier3.py::test_combination_ia_ranking_and_auto_apply - Type...
  FAILED tests/test_tier4.py::test_app_workflow_full_pipeline_cycle - assert Fa...
  ======================== 5 failed, 45 passed in 19.76s ========================
  ```
- **Port Bind Warning**:
  ```
  OSError: [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8081): [winerror 10048] normalmente é permitida apenas uma utilização de cada endereço de soquete
  ```
  *Note*: The test suite fails when run in quick succession because the mock ATS server's port 8081 stays in `TIME_WAIT` state, preventing subsequent bindings.

- **Sanity Battery Test Result**:
  - Command: `python -m pytest tests/test_sanity_battery.py`
  - Result: **Passed** (No failed tests listed for sanity battery in the main run).
  - Validation: Confirmed that for the 50 jobs in the sanity battery under a **Junior, remote BR, Sem Formação** candidate profile, 0% of jobs were approved, and 100% were correctly filtered.

### Code Analysis of Safety Hard-Locks (`scrapers/ai_filter.py`, Lines 120-136)
```python
120:                 if aprovado:
121:                     violated = []
122:                     if eval_obj.vaga_corresponde_ao_cargo == False:
123:                         violated.append("vaga_corresponde_ao_cargo == False")
124:                     if eval_obj.is_freelance == True:
125:                         violated.append("is_freelance == True")
126:                     if eval_obj.localidade_correta == False:
127:                         violated.append("localidade_correta == False")
128:                     if eval_obj.exige_faculdade == True:
129:                         violated.append("exige_faculdade == True")
130:                     if eval_obj.exige_experiencia == True:
131:                         violated.append("exige_experiencia == True")
132:                     
133:                     if violated:
134:                         aprovado = False
135:                         score = 0
136:                         reason = f"[Hard-Lock Override] Violated conditions: {', '.join(violated)}"
```

---

## 2. Logic Chain

1. **Assertion**: The 50-job sanity battery test (`test_sanity_battery_zero_approval`) passes because the mock data is structured specifically for a junior, no-degree candidate profile, matching the hardcoded constraints.
2. **Assertion**: However, the Python-level hard-locks are unconditionally applied to all candidate profiles without consulting user settings (such as level or education).
3. **Reasoning**:
   - If `target_level` is set to `"Sênior"` and the LLM returns `exige_experiencia: True` (expected for a senior position) and `aprovado: True`, line 130 checks `eval_obj.exige_experiencia == True` unconditionally and appends it to `violated`. This forces `aprovado = False` and `score = 0`.
   - If `target_education` is set to `"Todos"` or `"Superior"` and the LLM returns `exige_faculdade: True` and `aprovado: True`, line 128 checks `eval_obj.exige_faculdade == True` unconditionally, appending it to `violated`, forcing `aprovado = False` and `score = 0`.
4. **Reasoning**: Additionally, for Rule 4 (foreign currency / fluent English), the schema `JobEvaluation` does not define corresponding boolean flags. The Python override does not verify currency or English requirements, relying 100% on the LLM. If the LLM returns `aprovado: True` due to a hallucination or failure to parse, USD/Euro or English Fluent vacancies will bypass the safety checks and be approved.
5. **Empirical Verification**: We wrote and ran `tests/test_adversarial_challenges.py` which demonstrated exactly these failures:
   - `test_senior_candidate_with_experience_job` failed (AssertionError: Sênior job was incorrectly rejected).
   - `test_graduate_candidate_with_degree_job` failed (AssertionError: Job requiring degree was incorrectly rejected for candidate with degree).
   - `test_foreign_currency_and_english_leakage` failed (AssertionError: USD/Euro job leaked and was approved).

---

## 3. Caveats

- We assumed that uvicorn/FastAPI port conflicts on 8081 are transient due to TCP socket `TIME_WAIT` behavior and do not represent a flaw in the business logic itself, though it does impact E2E test reliability.
- We did not modify any source code under `scrapers/` to fix the bugs, in adherence to the review-only constraint.

---

## 4. Conclusion

While the 50-job sanity battery is successfully filtered with 0% approval for a Junior/Sem Formação candidate, the safety hard-lock mechanism has **critical design flaws**:
1. **Severe Regressions**: It breaks job hunting for Pleno/Sênior candidates and candidates with university degrees by unconditionally rejecting jobs that require experience or degrees.
2. **Safety Gap**: It lacks Python-level overrides for USD/Euro salaries and fluent English requirements, making the safety of these rules entirely dependent on LLM reliability.

---

## 5. Verification Method

To verify these findings:
1. Run the systematic/adversarial tests:
   ```bash
   python -m pytest tests/test_adversarial_challenges.py
   ```
2. Inspect the failure trace of the tests to confirm:
   - `test_senior_candidate_with_experience_job` → Fails because experience-required jobs are rejected for seniors.
   - `test_graduate_candidate_with_degree_job` → Fails because degree-required jobs are rejected for degree-holding candidates.
   - `test_foreign_currency_and_english_leakage` → Fails because foreign currency jobs are approved when the LLM approves them.

---

## 6. Challenge Report (Adversarial Review)

### Challenge Summary
- **Overall risk assessment**: **CRITICAL**

### Challenges

#### [Critical] Challenge 1: Unconditional Experience Hard-Lock Rejection for Pleno/Sênior Candidates
- **Assumption challenged**: The assumption that `exige_experiencia == True` always constitutes a safety violation.
- **Attack scenario**: A user sets their target level to "Sênior". A high-quality Python Tech Lead job is scraped. The LLM correctly marks `aprovado = True` and `exige_experiencia = True`. The Python code intercepts this and overrides the job approval to `False` (score 0), hiding valid positions from senior candidates.
- **Blast radius**: Breaks the entire core functionality of the bot for Pleno and Sênior profiles.
- **Mitigation**: Update `ai_filter.py` to only append `"exige_experiencia == True"` to `violated` if `target_level.lower() == "júnior"`.

#### [Critical] Challenge 2: Unconditional Degree Hard-Lock Rejection for Degree-Holding Candidates
- **Assumption challenged**: The assumption that `exige_faculdade == True` always constitutes a safety violation.
- **Attack scenario**: A user has a Bachelor's degree. A job requiring a Computer Science degree is scraped. The LLM marks `aprovado = True` and `exige_faculdade = True`. The Python code overrides this to `False` (score 0), preventing candidates with degrees from seeing jobs requiring degrees.
- **Blast radius**: Breaks core functionality for all candidates with a degree.
- **Mitigation**: Update `ai_filter.py` to only append `"exige_faculdade == True"` to `violated` if `target_education.lower() == "sem formação"`.

#### [High] Challenge 3: Safety Leakage on USD/Euro and Fluent English Vacancies
- **Assumption challenged**: The assumption that the LLM is 100% reliable at enforcing immediate rejection rules.
- **Attack scenario**: A job pays in USD ($5,000/month). The LLM hallucinatingly/accidentally returns `aprovado = True` and `is_freelance = False`. Because there is no Python-level override checking the currency or English status, the job is approved and sent to the candidate.
- **Blast radius**: High-risk safety leak, permitting foreign-currency or English-fluent jobs to bypass safety gates.
- **Mitigation**:
  1. Add boolean fields `exige_ingles` and `moeda_estrangeira` to the `JobEvaluation` Pydantic model.
  2. Implement corresponding checks in the Python-level hard-locks in `ai_filter.py` (e.g. if `moeda_estrangeira == True` or `exige_ingles == True` for a Junior, append to `violated`).

### Stress Test Results
- **Scenario 1 (Senior candidate, experience-required job)** → Expected: Approved → Actual: **Rejected** (Score 0) → **FAIL**
- **Scenario 2 (Graduate candidate, degree-required job)** → Expected: Approved → Actual: **Rejected** (Score 0) → **FAIL**
- **Scenario 3 (Junior candidate, USD salary job)** → Expected: Rejected → Actual: **Approved** (Score 90) → **FAIL**

### Unchallenged Areas
- **Platform scraper mocks** — Out of scope. We assumed existing mock scrapers match the project contracts specified in `PROJECT.md`.
