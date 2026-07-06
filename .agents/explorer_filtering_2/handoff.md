# Handoff Report: AI Filter Analysis and Recommendations

## 1. Observation

Direct observations and findings in the codebase:

### AI Filter Implementation (`scrapers/ai_filter.py`):
1. **Pydantic Model for Job Evaluation** (lines 18-32):
   ```python
   class JobEvaluation(BaseModel):
       aprovado: bool = Field(description="True se a vaga atende aos critérios obrigatórios. False se violar as regras de reprovação imediata.")
       is_freelance: bool = Field(description="True se a vaga for projeto pontual, freelancer ou remunerada por hora.")
       vaga_corresponde_ao_cargo: bool
       localidade_correta: bool
       exige_experiencia: bool
       exige_faculdade: bool = Field(description="True se a vaga exigir ensino superior obrigatório (completo ou cursando).")
       salary_declared: bool = Field(description="True se a vaga exibe um valor de salário/remuneração real (ex: R$ 2.000, R$ 3.500). False se disser 'A combinar' ou não informar.")
       has_benefits: bool = Field(description="True se a vaga listar benefícios concretos como VR, VA, VT, plano de saúde. False se não mencionar.")
       score: int
       justificativa_curta: str
       reqs: str
       bonus: str
       benefits: str
       model: str
   ```
2. **Current Model Selection** (line 86, 146, 195):
   ```python
   model="llama-3.1-8b-instant"
   ```
3. **Pydantic Validation and Returned Dict** (lines 98-112):
   ```python
   # Validação estrita via Pydantic
   eval_obj = JobEvaluation(**result_json)
   
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
   *Note: The fields `vaga_corresponde_ao_cargo`, `is_freelance`, `localidade_correta`, and `exige_experiencia` are populated in `eval_obj` but are not returned in the dictionary.*

### Bot Pre-filtering Behavior (`bot.py`):
4. **Pre-filter Platform and Language Check** (lines 255-273):
   ```python
   PLATAFORMAS_FREELANCE = ["workana", "99freelas", "freelancer", "upwork", "vintepila"]
   def is_valid_source(job_source):
       if any(plat in job_source.lower() for plat in PLATAFORMAS_FREELANCE):
           return False
       return True
       
   vagas_br = []
   for job in all_jobs:
       if is_valid_source(job.get('platform', '')) and is_brazilian_job(job.get('requirements', '')):
           vagas_br.append(job)
   ```
   *Note: Jobs from freelance platforms are skipped entirely in the bot execution if they match these strings, but might be passed to the AI filter in automated tests, or freelance jobs might appear on LinkedIn/Indeed.*

---

## 2. Logic Chain

1. **R1: Python Hard-Locks Implementation**
   - *Premise*: If the AI returns `aprovado = True`, we want to guarantee that programmatic checks override it and force `aprovado = False` under five conditions:
     - `vaga_corresponde_ao_cargo == False`
     - `is_freelance == True`
     - `localidade_correta == False`
     - `exige_faculdade == True`
     - `exige_experiencia == True`
   - *Reasoning*: Programmatic overrides act as a "safety net" if the LLM fails to reason correctly but still outputs the correct binary/boolean flags, or if the LLM output is inconsistent.
   - *Actionable Code Proposal*: Modify `score_job_match` to perform a check after parsing `JobEvaluation` and change the return dict:
     ```python
     # Validação estrita via Pydantic
     eval_obj = JobEvaluation(**result_json)
     
     aprovado = eval_obj.aprovado
     reason = eval_obj.justificativa_curta
     score = eval_obj.score
     
     # R1: Hard-locks override
     if aprovado:
         violations = []
         if not eval_obj.vaga_corresponde_ao_cargo:
             violations.append("vaga_corresponde_ao_cargo == False")
         if eval_obj.is_freelance:
             violations.append("is_freelance == True")
         if not eval_obj.localidade_correta:
             violations.append("localidade_correta == False")
         if eval_obj.exige_faculdade:
             violations.append("exige_faculdade == True")
         if eval_obj.exige_experiencia:
             violations.append("exige_experiencia == True")
         
         if violations:
             aprovado = False
             score = 0  # Force zero compatibility score for rejected jobs
             reason = f"[Python Hard-Lock Override] Reprovado devido a: {', '.join(violations)}. Original: {eval_obj.justificativa_curta}"
             logger.info(f"Vaga '{job.get('title')}' reprovada via Python hard-lock: {', '.join(violations)}")
     ```

2. **R2: Groq Model Upgrade to 70B+**
   - *Premise*: Replace `llama-3.1-8b-instant` with a 70B+ model (like `llama3-70b-8192` or `llama-3.1-70b-versatile`).
   - *Trade-off analysis*:
     - **Llama 3 70B (`llama3-70b-8192`)**: Excellent structured output compliance, high reasoning, but lower rate limits.
     - **Llama 3.1 70B (`llama-3.1-70b-versatile`)**: Upgraded context window (128k vs 8k in Llama 3) and slightly better multilingual reasoning.
     - **Llama 3.3 70B (`llama-3.3-70b-versatile`)**: Latest Groq model offering the best reasoning capacity.
   - *Recommendation*: Use `llama3-70b-8192` or `llama-3.3-70b-versatile`. Update `sem = asyncio.Semaphore(4)` (currently `8`) because Groq's 70B RPM and TPM limits are lower, and concurrent bursts of 8 requests are prone to 429 limits even with API key rotation.

3. **R3: Sanity Battery Design (50 Trick Jobs)**
   - *Goal*: Build a suite of 50 edge-case job descriptions (each violating at least one criteria) to verify the system filters out 100% of them (0% approval).
   - *Layout*: Create `tests/sanity_battery.json` (dataset) and a test script `tests/test_sanity_battery.py`.
   - *Categories of Trick Jobs*:
     - **Freelance/Hourly/Workana (10 jobs)**: payment per task, hourly, temporary contracts, mentions of Upwork/Workana/99freelas.
     - **USD/Euro & English Required (10 jobs)**: listings targeting global remote devs paying $3k-$5k USD, requiring fluent English conversation (candidate profile: Junior).
     - **Location/Hybrid/On-site Mismatch (10 jobs)**: target is "Brasil (Remoto)", but job requires presence in São Paulo, Rio, etc.
     - **Seniority/Experience Mismatch (10 jobs)**: target is "Júnior", but job requires 3+ years experience, Lead/Senior roles.
     - **Education/Degree Requirement (5 jobs)**: candidate is "Sem Formação", but job requires CS Degree.
     - **Role/Keyword Mismatch (5 jobs)**: keyword is "Python Scraping", but job is for a Sales Representative, Chef, UI Designer.

---

## 3. Caveats

- **Rate Limits on Groq**: Groq imposes tight rate limits on 70B+ models compared to 8B. While the scraper rotates through `API_KEYS`, parallel requests might trigger rate limits. Reducing `sem` from `8` to `4` (or `3`) is recommended to mitigate this.
- **Freelance Platforms Pre-filtering**: In `bot.py`, freelance platforms are blacklisted before sending to the AI filter. Therefore, test scenarios testing Workana/Freelancer jobs directly must pass them straight to `ai_filter.score_job_match` rather than running the full `bot.py` routine.
- **English Language Detection**: The pre-filter in `bot.py` deletes non-PT-BR jobs using `langdetect`. Sanity tests with English/USD jobs must be passed directly to the AI filter endpoint, bypassing `is_brazilian_job(job.get('requirements', ''))`.

---

## 4. Conclusion

- Implement programmatic hard-locks in `scrapers/ai_filter.py` directly under `JobEvaluation(**result_json)` to verify variables `vaga_corresponde_ao_cargo`, `is_freelance`, `localidade_correta`, `exige_faculdade`, and `exige_experiencia`.
- Upgrade the model in `scrapers/ai_filter.py` to `llama3-70b-8192` or `llama-3.3-70b-versatile`, adjusting the semaphore limit to prevent rate limiting.
- Establish a parametrized pytest suite loading 50 trick jobs from a static JSON file to test the zero-percent-approval behavior of the filter.

---

## 5. Verification Method

### Test Scripts and Datasets Proposal:
To implement and verify, run the following steps:

1. **Modify `scrapers/ai_filter.py`**:
   Apply model changes and the Python hard-lock override.
2. **Execute Existing Tests**:
   Run the pytest command to ensure no regressions:
   `python run_tests.py`

### Proposed `tests/sanity_battery.json` snippet:
```json
[
  {
    "id": "usd_salary_junior",
    "title": "Junior Python Dev",
    "company": "US Corp",
    "budget": "$3,000 USD/month",
    "requirements": "Looking for a junior python engineer. Payment is in USD. Must be fluent in English.",
    "candidate": {"level": "Júnior", "location": "Brasil (Remoto)", "keyword": "Python", "education": "Todos"}
  },
  {
    "id": "freelance_workana",
    "title": "Python Scripting Project",
    "company": "Client",
    "budget": "R$ 500 total",
    "requirements": "This is a one-time freelance project to script a website scraper. Pays per completion.",
    "candidate": {"level": "Júnior", "location": "Brasil (Remoto)", "keyword": "Python", "education": "Todos"}
  }
]
```

### Proposed `tests/test_sanity_battery.py`:
```python
import json
import pytest
import asyncio
from scrapers.ai_filter import score_job_match

def load_sanity_battery():
    with open("tests/sanity_battery.json", "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.mark.parametrize("job_data", load_sanity_battery())
def test_sanity_battery_must_reject_all(job_data):
    loop = asyncio.get_event_loop()
    candidate = job_data["candidate"]
    job = {
        "title": job_data["title"],
        "company": job_data["company"],
        "budget": job_data["budget"],
        "link": f"https://example.com/{job_data['id']}",
        "requirements": job_data["requirements"]
    }
    
    result = loop.run_until_complete(
        score_job_match(
            resume_text="Diego Candidate. Python junior developer.",
            job=job,
            target_keyword=candidate["keyword"],
            target_location=candidate["location"],
            target_level=candidate["level"],
            target_education=candidate["education"]
        )
    )
    
    # Assert rejection
    assert result["aprovado"] is False, f"Job {job_data['id']} was incorrectly approved!"
    assert result["score"] == 0
```
