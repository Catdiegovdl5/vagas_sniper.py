# Handoff Report: Empirical Verification of Safety Hard-Locks and Sanity Battery

This report documents the verification of the vagas_bot safety filters and the 50-job sanity battery.

---

## 1. Observation
- **Test Commands Executed**:
  - `python run_tests.py`
  - `python -m pytest tests/test_sanity_battery.py`
- **Verbatim Test Output (Sanity Battery)**:
  ```
  tests\test_sanity_battery.py .                                           [100%]
  ======================== 1 passed, 2 warnings in 1.07s ========================
  ```
  This indicates that `test_sanity_battery_zero_approval` passed, successfully rejecting all 50 jobs (0% approval rate) under mocked LLM conditions.
- **Verbatim Test Failures (E2E Suite)**:
  `python run_tests.py` reported **5 failed, 45 passed** (exit code 1).
  The failing tests:
  - `test_auto_apply_handles_empty_db_fields`
  - `test_auto_apply_handles_missing_resume_path`
  - `test_combination_ia_ranking_and_auto_apply`
  - `test_combination_scraper_ia_ranking_and_auto_apply`
  - `test_app_workflow_full_pipeline_cycle`
  
  All 5 tests failed with the following traceback pattern:
  ```
  Error during auto-apply HTTP request to http://127.0.0.1:8081/apply: HTTPConnectionPool(host='127.0.0.1', port=8081): Max retries exceeded with url: /apply (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=8081): Failed to establish a new connection: [WinError 10061] Nenhuma conexão pôde ser feita porque a máquina de destino as recusou ativamente"))
  ```
- **Code Inspection of `scrapers/ai_filter.py`**:
  - **Truncation (Line 54)**:
    ```python
    req_trunc = job.get('requirements', '')[:1200]
    ```
  - **Python Hard-Lock Overrides (Lines 120-137)**:
    ```python
    if aprovado:
        violated = []
        if eval_obj.vaga_corresponde_ao_cargo == False:
            violated.append("vaga_corresponde_ao_cargo == False")
        if eval_obj.is_freelance == True:
            violated.append("is_freelance == True")
        if eval_obj.localidade_correta == False:
            violated.append("localidade_correta == False")
        if eval_obj.exige_faculdade == True:
            violated.append("exige_faculdade == True")
        if eval_obj.exige_experiencia == True:
            violated.append("exige_experiencia == True")
        
        if violated:
            aprovado = False
            score = 0
            reason = f"[Hard-Lock Override] Violated conditions: {', '.join(violated)}"
    ```

---

## 2. Logic Chain
1. **O1 (Sanity Battery Pass)**: Shows that the 50-job sanity battery test (`test_sanity_battery_zero_approval`) completes with a 100% success rate under the test environment (0% job approval rate).
2. **O2 (E2E Failures)**: Shows that the mock uvicorn ATS server started in `tests/conftest.py` is inaccessible at `http://127.0.0.1:8081/apply` on this Windows machine during E2E runs, leading to a 5-test failure rate in the general suite.
3. **O3 (1200-Character Truncation)**: Shows that requirements are sliced to 1200 characters before formatting the prompt.
4. **Inference 1 (Truncation Vulnerability)**: If a job post lists its mandatory requirements (e.g. bachelor's degree required, 5+ years experience, or freelance status) after character index 1200, these rules will not exist in the prompt. The LLM will classify the truncated text and return `aprovado: True`, setting the structured classification fields `exige_faculdade`, `exige_experiencia`, and `is_freelance` to `False`. The Python hard-lock override will not trigger, resulting in an unsafe application.
5. **O4 (Missing Python-Level Overrides)**: Shows that `scrapers/ai_filter.py` hard-lock override block has no checks for `usd_euro` or `fluent_english`.
6. **Inference 2 (Prompt-Only Vulnerability)**: The USD/Euro and Fluent English rules are entirely dependent on LLM prompt obedience. If the LLM hallucinates or ignores the system prompt instruction and returns `aprovado: True` for a USD/Euro or English-requiring job, there is no Python-level validation to override it.

---

## 3. Caveats
- The mock uvicorn ATS server connection refusal was not fully diagnosed on the OS level (port conflict vs timing/resolving delay on Windows).
- All tests assume mock client libraries (`AsyncGroq`) are functional.

---

## 4. Conclusion
- **Sanity Battery status**: Correct and fully robust under tested mock scenarios (0/50 jobs approved).
- **Hard-Locks status**: The python hard-locks are functioning as designed, but are structurally vulnerable to:
  1. **Truncation Leakage**: Bypassed if requirements occur after 1200 characters.
  2. **Prompt-Only Verification**: USD/Euro and Fluent English rules lack Python-level validation/override.
- **E2E test suite status**: 5 failures out of 50 tests due to uvicorn binding/access issues on `127.0.0.1:8081`.

---

## 5. Verification Method
- Execute the test suite runner using:
  ```bash
  python run_tests.py
  ```
- Run the specific sanity battery test:
  ```bash
  python -m pytest tests/test_sanity_battery.py
  ```
- Inspect `scrapers/ai_filter.py` line 54 and lines 120-137.

---

# Adversarial Review Challenge Report

**Overall risk assessment**: MEDIUM

## Challenges

### [High] Truncation Safety Bypass
- **Assumption challenged**: That the first 1200 characters of a job description contain all safety-critical requirement details.
- **Attack scenario**: A job poster adds 1200+ characters of company culture fluff, then puts "Requisitos obrigatórios: Bacharelado completo em TI" or "Contrato Freelancer/Bico" at the end of the text.
- **Blast radius**: The LLM will approve the job and report `exige_faculdade: False` or `is_freelance: False` (since it never saw the text). The python override will not catch it, causing the bot to automatically apply to a job that violates the safety requirements.
- **Mitigation**: Increase the truncation limit (e.g., to 4000+ characters) or prioritize extracting the requirements section before truncation.

### [Medium] Prompt-Only Safety Dependency (USD/Euro and English)
- **Assumption challenged**: That the LLM will always obey the system prompt rules regarding foreign currencies and English requirements.
- **Attack scenario**: The LLM hallucinates or fails to parse the budget `$5000/month` or the requirement "Fluent English required" correctly and returns `aprovado: True`.
- **Blast radius**: Because there are no Python-level hard-locks checking for foreign currency symbols or English language requirements in the returned JSON, the job is approved.
- **Mitigation**: Add boolean fields `is_usd_euro` and `exige_ingles` to `JobEvaluation`, or perform regex checks for currency symbols (`$`, `€`, `£`) and keywords (`inglês fluente`, `fluent english`) directly in Python before approval.

### [Medium] Hard-Lock Dependency on LLM Output
- **Assumption challenged**: That the Python hard-lock overrides are independent of the LLM.
- **Attack scenario**: If the LLM returns `aprovado: True` and hallucinates that `is_freelance: False` for a freelance job (even if it saw the requirements), the Python override checks `if eval_obj.is_freelance == True:` which will evaluate to `False` and let it pass.
- **Blast radius**: If the LLM makes a classification error, the Python hard-locks fail silently.
- **Mitigation**: Perform independent string matching in python (e.g. check if "freelance" or "bico" is in the text) instead of relying solely on the LLM's classification fields.
