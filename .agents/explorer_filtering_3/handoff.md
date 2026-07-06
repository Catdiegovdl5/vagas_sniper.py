# Handoff Report - Explorer 3

## 1. Observation
We analyzed the codebase of `vagas_bot` to address requirements R1, R2, and R3. Specifically, we investigated `scrapers/ai_filter.py` and ran the existing test suite (`run_tests.py`).

### Direct Code Observations in `scrapers/ai_filter.py`
* **JSON Schema and Pydantic Model (`JobEvaluation` at lines 18-32):**
  ```python
  class JobEvaluation(BaseModel):
      aprovado: bool = Field(description="...")
      is_freelance: bool = Field(description="...")
      vaga_corresponde_ao_cargo: bool
      localidade_correta: bool
      exige_experiencia: bool
      exige_faculdade: bool = Field(description="...")
      salary_declared: bool = Field(description="...")
      has_benefits: bool = Field(description="...")
      score: int
      justificativa_curta: str
      reqs: str
      bonus: str
      benefits: str
      model: str
  ```
* **Return block in `score_job_match` (lines 101-112):**
  ```python
  return {
      "aprovado": eval_obj.aprovado,
      "score": eval_obj.score,
      "reason": eval_obj.justificativa_curta,
      "reqs": eval_obj.reqs,
      "bonus": eval_obj.bonus,
      "benefits": eval_obj.benefits,
      "model": eval_obj.model,
      "salary_declared": eval_obj.salary_declared,
      "has_benefits": eval_obj.has_benefits,
      "exige_faculdade": eval_obj.exige_faculdade
  }
  ```
* **Model Configuration in `scrapers/ai_filter.py` (lines 86, 146, 195):**
  ```python
  model="llama-3.1-8b-instant"
  ```
  The model `"llama-3.1-8b-instant"` is hardcoded at three API invocation sites inside `scrapers/ai_filter.py`.

### Test Suite Execution Observations
Running `python run_tests.py` fails with **5 failed tests out of 49 total**.
Verbatim traceback from `task-31.log` reveals Pydantic validation errors:
```
3 validation errors for JobEvaluation
exige_faculdade
  Field required [type=missing, input_value={'aprovado': True, 'is_fr... VT', 'model': 'Remoto'}, input_type=dict]
salary_declared
  Field required [type=missing, input_value={'aprovado': True, 'is_fr... VT', 'model': 'Remoto'}, input_type=dict]
has_benefits
  Field required [type=missing, input_value={'aprovado': True, 'is_fr... VT', 'model': 'Remoto'}, input_type=dict]
```
These validation errors occur in the mock outputs located in:
1. `tests/conftest.py` lines 347-359 (`_default_create`)
2. `tests/test_tier1.py` lines 197-208 (`test_ia_ranking_rejects_non_matching_job`)
3. `tests/test_tier2.py` lines 193-204 (`test_ia_ranking_handles_groq_rate_limits`)

---

## 2. Logic Chain
1. **R1: Python Hard-Locks Implementation**
   * If the LLM returns `aprovado = True`, Python code must verify that the following conditions are met:
     * `vaga_corresponde_ao_cargo` must be `True`
     * `is_freelance` must be `False`
     * `localidade_correta` must be `True`
     * `exige_faculdade` must be `False`
     * `exige_experiencia` must be `False`
   * If any of these rules are violated, Python should force `aprovado = False`.
   * To implement this, we can intercept the deserialized `eval_obj` directly inside `score_job_match` before returning, perform the checks, construct an overridden reason string to preserve transparency, and return the modified boolean.
   * Additionally, we should expand the return dictionary of `score_job_match` to output the checked flags (`is_freelance`, `vaga_corresponde_ao_cargo`, `localidade_correta`, `exige_experiencia`) to assist calling modules and debugging.

2. **R2: Groq Model Upgrade to 70B+**
   * The current model is `llama-3.1-8b-instant`.
   * To upgrade to a 70B+ model, we recommend modifying the `model` parameter inside `scrapers/ai_filter.py` at all three occurrences to `"llama3-70b-8192"` (or the more modern and reasoning-capable `"llama-3.3-70b-versatile"`).
   * Upgrading will improve instruction compliance and reduce edge-case errors, but it may incur lower rate limit thresholds. We should suggest lowering the concurrency semaphore (`sem = asyncio.Semaphore(8)`) to `4` or `3` if HTTP 429 rate limit exceptions occur too frequently.

3. **R3: 50-Job Sanity Battery Design**
   * To verify the filter's robust operation (guaranteeing a 0% approval rate for invalid jobs), we need a suite of 50 edge-case/adversarial job postings.
   * We propose storing these test cases in a JSON file `tests/sanity_battery.json` structured as an array of job dictionary payloads along with candidate profiles and the expected hard-lock reasons.
   * A test script `tests/test_sanity_battery.py` should load this file, run the filter, and assert that the approval rate is exactly 0/50.

---

## 3. Caveats
* **Rate Limits:** Groq has tighter Token-Per-Minute (TPM) and Request-Per-Minute (RPM) limits for 70B+ models compared to 8B models. Upgrading might cause more 429 responses, which are handled by the retry decorator but will introduce latency.
* **API Key Rotating:** The code rotates between 3 keys in `API_KEYS`. If all keys share the same account quota, rotating them might not prevent account-wide rate limits if Groq enforces them globally per account/IP.
* **Test Suite Failures:** The current test suite fails due to schema mismatches in the mocks. These must be resolved before verifying the implementations of R1 and R2.

---

## 4. Conclusion & Recommendations
We recommend implementing the changes in `scrapers/ai_filter.py` as detailed in the patch proposals below, upgrading the model to `llama-3.3-70b-versatile` or `llama3-70b-8192`, and establishing a sanity test battery.

### R1: Python Hard-Locks Recommendation
Replace lines 98-112 in `scrapers/ai_filter.py` with:
```python
                # Validação estrita via Pydantic
                eval_obj = JobEvaluation(**result_json)
                
                aprovado_final = eval_obj.aprovado
                reason_final = eval_obj.justificativa_curta
                
                # R1 Python Hard-Locks Check
                if aprovado_final:
                    violations = []
                    if eval_obj.vaga_corresponde_ao_cargo is False:
                        violations.append("vaga_corresponde_ao_cargo == False")
                    if eval_obj.is_freelance is True:
                        violations.append("is_freelance == True")
                    if eval_obj.localidade_correta is False:
                        violations.append("localidade_correta == False")
                    if eval_obj.exige_faculdade is True:
                        violations.append("exige_faculdade == True")
                    if eval_obj.exige_experiencia is True:
                        violations.append("exige_experiencia == True")
                    
                    if violations:
                        aprovado_final = False
                        reason_final = f"[Hard-Lock Override] Reprovado devido aos critérios: {', '.join(violations)}. Justificativa original da IA: {eval_obj.justificativa_curta}"
                
                return {
                    "aprovado": aprovado_final,
                    "score": eval_obj.score if aprovado_final else 0,  # Reset score to 0 on hard lock rejection
                    "reason": reason_final,
                    "reqs": eval_obj.reqs,
                    "bonus": eval_obj.bonus,
                    "benefits": eval_obj.benefits,
                    "model": eval_obj.model,
                    "salary_declared": eval_obj.salary_declared,
                    "has_benefits": eval_obj.has_benefits,
                    "exige_faculdade": eval_obj.exige_faculdade,
                    # Extra keys returned for debugging/validation
                    "is_freelance": eval_obj.is_freelance,
                    "vaga_corresponde_ao_cargo": eval_obj.vaga_corresponde_ao_cargo,
                    "localidade_correta": eval_obj.localidade_correta,
                    "exige_experiencia": eval_obj.exige_experiencia
                }
```

### R2: Model Upgrade Recommendation
In `scrapers/ai_filter.py`, replace `model="llama-3.1-8b-instant"` with `model="llama-3.3-70b-versatile"` or `model="llama3-70b-8192"` on lines 86, 146, and 195.
Additionally, adjust the semaphore to avoid rate-limiting issues if needed:
```python
sem = asyncio.Semaphore(4)  # Concurrency reduced from 8 to 4 for 70B+ models
```

### R3: Sanity Battery Recommendation
Create a JSON file `tests/sanity_battery.json` containing 50 trick jobs categorized across the main failure triggers:
1. **Freelance & Hourly Platforms (10 jobs):** Project-based, Workana/99freelas sources, "payment per task", "temporary 1-month contract".
2. **Foreign Currency Salaries (10 jobs):** Salary declared in USD ($20/hour) or Euros (€3000/month) for Brazilian junior candidate roles.
3. **High Experience for Juniors (10 jobs):** Disguised junior titles requiring 3+ years experience, full-stack seniors disguised as juniors, Pleno/Sênior level responsibilities.
4. **College/Education Requirements (10 jobs):** Mandatory computer science/engineering degrees, active enrollment in specific universities required (for candidate settings "Sem Formação").
5. **Language Mismatch (10 jobs):** Fluency in English required for junior roles where the candidate only has basic/Portuguese capability.

#### Example JSON Entry in `tests/sanity_battery.json`:
```json
[
  {
    "id": "trick_freelance_01",
    "job": {
      "title": "Ajuste de Script Python e Automação",
      "company": "Freelance Inc",
      "budget": "R$ 150 por projeto",
      "platform": "Workana",
      "job_type": "Freelance",
      "requirements": "Necessito de um profissional para ajustar um script Python simples que faz scraping. Projeto de 2 dias."
    },
    "candidate_settings": {
      "keyword": "Python",
      "location": "Brasil (Remoto)",
      "level": "Júnior",
      "education": "Todos"
    },
    "expected_rejection": "is_freelance"
  },
  {
    "id": "trick_salary_usd_02",
    "job": {
      "title": "Python Junior Developer",
      "company": "US Tech Startup",
      "budget": "$12 - $15 / hour",
      "platform": "LinkedIn",
      "job_type": "PJ",
      "requirements": "Looking for a junior Python engineer to assist in API integrations. Payment in USD. English required."
    },
    "candidate_settings": {
      "keyword": "Python",
      "location": "Brasil (Remoto)",
      "level": "Júnior",
      "education": "Todos"
    },
    "expected_rejection": "exige_experiencia" 
  }
]
```

Create a corresponding test file `tests/test_sanity_battery.py`:
```python
import json
import os
import pytest
import asyncio
from scrapers.ai_filter import score_job_match

def test_sanity_battery_0_percent_approval():
    battery_path = os.path.join(os.path.dirname(__file__), "sanity_battery.json")
    with open(battery_path, "r", encoding="utf-8") as f:
        trick_jobs = json.load(f)
        
    loop = asyncio.get_event_loop()
    approved_count = 0
    
    for entry in trick_jobs:
        job = entry["job"]
        settings = entry["candidate_settings"]
        
        result = loop.run_until_complete(
            score_job_match(
                resume_text="Diego Candidate. Python Developer. Django. SQL.", 
                job=job, 
                target_keyword=settings["keyword"], 
                target_location=settings["location"], 
                target_level=settings["level"], 
                target_education=settings["education"]
            )
        )
        
        # Verify that every job is rejected
        assert result["aprovado"] is False, f"Job {entry['id']} was approved but should have been rejected!"
        approved_count += 1 if result["aprovado"] else 0
        
    assert approved_count == 0, f"Approval rate must be 0%. {approved_count} jobs were approved!"
```

---

## 5. Verification Method
1. **Fix Mock Mismatches:**
   * Update the mocks in `tests/conftest.py`, `tests/test_tier1.py`, and `tests/test_tier2.py` to return the missing Pydantic fields (`exige_faculdade`, `salary_declared`, `has_benefits`).
   * Run the test suite: `python run_tests.py` and confirm all 49 existing tests pass successfully.
2. **Verify R1 Hard-Locks:**
   * Implement a test job where the mock response sets `aprovado = True` but `is_freelance = True`.
   * Assert that `score_job_match` returns `aprovado = False` and `reason` contains the `[Hard-Lock Override]` text.
3. **Verify R2 Model Upgrade:**
   * Inspect the `scrapers/ai_filter.py` source code to verify that the `model` argument contains `"llama-3.3-70b-versatile"` or `"llama3-70b-8192"`.
4. **Verify R3 Sanity Battery:**
   * Add the `tests/sanity_battery.json` containing 50 trick jobs.
   * Run the `pytest tests/test_sanity_battery.py` command and verify that the exit code is 0 (all 50 jobs rejected).
