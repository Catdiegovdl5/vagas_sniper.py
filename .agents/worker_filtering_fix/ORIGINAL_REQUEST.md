## 2026-07-04T15:51:54Z
You are the Worker. Your working directory is C:\Users\99196\OneDrive\Documentos\vagas_bot\.agents\worker_filtering_fix.
Your objective is to fix three logical bugs/regressions identified in the Python safety hard-locks of scrapers/ai_filter.py:

1. **Experience Hard-Lock Regression**:
   The check for `exige_experiencia == True` should only trigger a violation if `target_level` is set to `"Júnior"`. It should not reject jobs requiring experience if the candidate is Sênior/Pleno.

2. **Degree Hard-Lock Regression**:
   The check for `exige_faculdade == True` should only trigger a violation if `target_education` is set to `"Sem Formação"`. It should not reject jobs requiring degrees for other education levels.

3. **USD/Euro and English Fluency Safety Locks**:
   Add Python-level checks to `scrapers/ai_filter.py` under the safety hard-locks block. If `target_level` is `"Júnior"`, check the raw text of the job budget, requirements, and title for:
   - Foreign currencies (symbol `€`, text `usd`, `euro`, `euros`, `dollar`, `dollars`, and symbol `$` not preceded by `R` or `r`).
   - Fluent English requirements (keywords: `"inglês fluente"`, `"ingles fluente"`, `"fluent english"`, `"fluency in english"`, `"english fluent"`, `"english: fluent"`, `"ingles: fluente"`, `"inglês: fluente"`).
   If any are detected, override `aprovado = False`, set `score = 0`, and append the violation to the reason string.

Please implement these changes carefully in `scrapers/ai_filter.py`.

4. **Verify**:
   Run the adversarial test suite to verify the fixes:
   ```bash
   python -m pytest tests/test_adversarial_challenges.py
   ```
   All tests in this suite must now pass!
   Also verify that `pytest tests/test_sanity_battery.py` and the main `python run_tests.py` continue to execute successfully.
   Document the exact commands run and output results in your handoff.md report inside your working directory C:\Users\99196\OneDrive\Documentos\vagas_bot\.agents\worker_filtering_fix.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
