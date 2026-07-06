# Handoff Report - Filtering and Validation Upgrade

## 1. Observation

During the read-only investigation of the `vagas_bot` codebase, we observed the following:

*   **File `scrapers/ai_filter.py`**:
    *   **Pydantic Model**: Lines 18-32 define `JobEvaluation`:
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
    *   **Model Execution**: Lines 99-112 load `result_json` into `JobEvaluation` and return the dictionary back to the caller:
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
    *   **AI Model Selection**: Line 86 sets the model to `"llama-3.1-8b-instant"` in `score_job_match`:
        ```python
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant", 
            messages=[...],
            ...
        )
        ```
        And the same 8B model is used for `analyze_resume_for_keywords` (line 146) and `extract_hunt_intent` (line 195).

*   **File `bot.py`**:
    *   Lines 280-308 show that the bot handles the return from `score_job_match` as `match_data` and filters using `ai_aprovado`:
        ```python
        job['ai_aprovado'] = match_data.get('aprovado', False)
        # ...
        premium_jobs = [j for j in scored_jobs if j.get('ai_aprovado', False)]
        ```

*   **File `tests/conftest.py`**:
    *   Lines 347-359 define the Mock Groq response dictionary, which is missing fields like `exige_faculdade`, `salary_declared`, and `has_benefits` that are defined as required (non-default) in the Pydantic `JobEvaluation` model.

---

## 2. Logic Chain

1.  **Python Hard-Locks (R1)**:
    *   Currently, the AI determines the `aprovado` field. If the AI hallucinates, gets confused, or incorrectly sets `aprovado = True` despite also setting one of the veto conditions (e.g. `is_freelance = True` or `exige_experiencia = True`), the bot accepts the job because there is no safety override logic in python.
    *   By intercepting the parsed `eval_obj` after Pydantic validation (line 99) but before generating the return dict (line 101), Python can dynamically enforce these rules.
    *   If `eval_obj.aprovado` is `True`, but any of the following fields violate constraints:
        *   `eval_obj.vaga_corresponde_ao_cargo == False`
        *   `eval_obj.is_freelance == True`
        *   `eval_obj.localidade_correta == False`
        *   `eval_obj.exige_faculdade == True`
        *   `eval_obj.exige_experiencia == True`
    *   We force `aprovado = False` and update the `reason` description to log the specific Python Hardlock Veto trigger. This ensures transparency, clean telemetry in the bot interface, and guarantees 100% adherence to candidate search restrictions.

2.  **Groq Model Upgrade (R2)**:
    *   The `llama-3.1-8b-instant` model has high throughput but lower reasoning capabilities, leading to classification errors on complex requirements (such as identifying subtle freelance indicators, location boundaries, or foreign salary declarations).
    *   Upgrading the model to `llama-3.3-70b-versatile` (or `llama3-70b-8192`) in the primary filter `score_job_match` will improve prompt compliance and reduce hallucinations.
    *   We should *only* upgrade `score_job_match`, leaving `analyze_resume_for_keywords` and `extract_hunt_intent` on the 8B model. This is cost-effective and avoids hitting Groq API rate limits (TPM/RPM) which are significantly lower for 70B+ models.

3.  **Sanity Battery Design (R3)**:
    *   To evaluate model and override performance, we need a test harness running a 50-job dataset of edge-case "trick jobs" designed specifically to trigger the veto filters.
    *   A custom test suite should load these mock job descriptions, pass them to `score_job_match`, and assert that the outcome is always `aprovado == False` (0% bypass/approval rate).

---

## 3. Caveats

*   **Test Suite Key Mock Alignment**: In `tests/conftest.py` (lines 347-359) and `tests/test_tier2.py` (lines 193-205), the mocked JSON responses lack fields required by the `JobEvaluation` model (like `exige_faculdade`). Depending on strictness in local python typing, this might cause validation errors. We recommend updating these test mocks to include the missing keys.
*   **Groq API Rate Limits**: Upgrading to `llama-3.3-70b-versatile` increases the risk of HTTP `429 Too Many Requests` errors under heavy load. The code in `score_job_match` already contains a retry loop with backing off (lines 80-122) and API key rotation (API_KEYS list), which will help mitigate this.
*   **Terminal Execution**: Local tests could not be run synchronously due to terminal approval timeouts; all observations are based on code analysis and verification of mock definitions.

---

## 4. Conclusion and Recommendations

### R1: Python Hard-Locks Implementation Proposal
Modify `scrapers/ai_filter.py` inside `score_job_match` to enforce the overrides post-validation. 

**Proposed Code diff in `scrapers/ai_filter.py`:**

```python
<<<<
                # Validação estrita via Pydantic
                eval_obj = JobEvaluation(**result_json)
                
                return {
                    "aprovado": eval_obj.aprovado,
                    "score": eval_obj.score,
                    "reason": eval_obj.justificativa_curta,
                    ...
====
                # Validação estrita via Pydantic
                eval_obj = JobEvaluation(**result_json)
                
                aprovado_final = eval_obj.aprovado
                justificativa_final = eval_obj.justificativa_curta
                
                if aprovado_final:
                    vetos = []
                    if not eval_obj.vaga_corresponde_ao_cargo:
                        vetos.append("Cargo incompatível (vaga_corresponde_ao_cargo = False)")
                    if eval_obj.is_freelance:
                        vetos.append("Trabalho freelance/pontual (is_freelance = True)")
                    if not eval_obj.localidade_correta:
                        vetos.append("Localidade incorreta (localidade_correta = False)")
                    if eval_obj.exige_faculdade:
                        vetos.append("Exige faculdade obrigatória (exige_faculdade = True)")
                    if eval_obj.exige_experiencia:
                        vetos.append("Exige experiência superior ao perfil (exige_experiencia = True)")
                        
                    if vetos:
                        aprovado_final = False
                        justificativa_final = f"[Veto Python Hard-Lock] Reprovado por: {', '.join(vetos)}."
                
                return {
                    "aprovado": aprovado_final,
                    "score": eval_obj.score,
                    "reason": justificativa_final,
>>>>
```

### R2: Groq Model Upgrade Proposal
Update `scrapers/ai_filter.py` line 86 to target the 70B reasoning model:

```python
<<<<
                response = await client.chat.completions.create(
                    model="llama-3.1-8b-instant", 
                    messages=[
====
                response = await client.chat.completions.create(
                    model="llama-3.3-70b-versatile", # Upgraded to 70B+ for high-accuracy reasoning
                    messages=[
>>>>
```

*Note: Keep `analyze_resume_for_keywords` and `extract_hunt_intent` on `"llama-3.1-8b-instant"` to prevent hitting TPM limits.*

### R3: 50-Job Sanity Battery Design Proposal

To ensure 0% approval rate on trick jobs, we propose creating a structured dataset of 50 test jobs, divided into 5 categories of 10 jobs each.

#### A. Dataset Structure (`tests/trick_jobs_dataset.json`)
Each test case contains:
*   `title`, `company`, `requirements`, `platform`, `budget` (raw vacancy).
*   `context`: `target_keyword`, `target_location`, `target_level`, `target_education` (filters).
*   `expected_veto_reason`: The specific key that must trigger the veto (e.g., `is_freelance`).

#### B. The 5 Trick Categories (10 jobs each)

1.  **Freelance / Hourly Task Veto (`is_freelance == True`)**
    *   *Trick Description*: The job description mentions "Júnior" and "Python" but specifies "Bico de 2 semanas", "Pagamento por tarefa via Workana", "Job freelancer para corrigir bug", or "R$ 40/hora sem vínculo".
    *   *Expected*: `is_freelance: True`, `aprovado: False`.
2.  **USD / Currency / English Veto (Junior candidates - Rule 4)**
    *   *Trick Description*: Vaga de programador júnior com salário de `$2000 USD/mês via Deel`, ou exigindo `Inglês Fluente` para reuniões diárias com equipe no exterior.
    *   *Expected*: `aprovado: False` (triggered by rule 4).
3.  **Degree Requirement Veto (`exige_faculdade == True` when candidate has `education = "Sem Formação"`)**
    *   *Trick Description*: Title matches Python Jr, but description states: "Imprescindível superior completo em Engenharia ou Ciência da Computação (Diploma será exigido)", or "Vaga requer formação universitária obrigatória".
    *   *Expected*: `exige_faculdade: True`, `aprovado: False`.
4.  **Experience Level Mismatch (`exige_experiencia == True` when candidate is `level = "Júnior"`)**
    *   *Trick Description*: Vaga com "Júnior" no título, mas no texto pede "+3 anos de experiência com Django", "sólidos conhecimentos como pleno/sênior", ou "experiência comercial comprovada de pelo menos 2 anos".
    *   *Expected*: `exige_experiencia: True`, `aprovado: False`.
5.  **Location Mismatch (`localidade_correta == False`)**
    *   *Trick Description*: Search is for "Brasil (Remoto)" or "Londrina/PR", but the vacancy is "Estritamente presencial em Porto Alegre - RS (Sem possibilidade de Home Office)".
    *   *Expected*: `localidade_correta: False`, `aprovado: False`.

#### C. Verification Script (`tests/test_trick_battery.py`)

Below is the proposed test script template that reads the dataset and runs the validation:

```python
import json
import pytest
import asyncio
import os
from scrapers.ai_filter import score_job_match

@pytest.mark.asyncio
async def test_50_trick_jobs_battery():
    # Load dataset
    dataset_path = os.path.join(os.path.dirname(__file__), "trick_jobs_dataset.json")
    assert os.path.exists(dataset_path), "Sanity battery dataset is missing!"
    
    with open(dataset_path, "r", encoding="utf-8") as f:
        trick_cases = json.load(f)
        
    assert len(trick_cases) == 50, f"Expected 50 trick jobs, got {len(trick_cases)}"
    
    resume_text = "Diego Candidate. Python Developer. Backend. SQL. Git. No degree. Junior level."
    
    passed_vetoes = []
    failed_vetoes = []
    
    for idx, case in enumerate(trick_cases):
        job = {
            "title": case["title"],
            "company": case["company"],
            "requirements": case["requirements"],
            "platform": case.get("platform", "linkedin"),
            "budget": case.get("budget", "A combinar")
        }
        
        ctx = case["context"]
        
        result = await score_job_match(
            resume_text=resume_text,
            job=job,
            target_keyword=ctx.get("target_keyword", "Python"),
            target_location=ctx.get("target_location", "Brasil (Remoto)"),
            target_level=ctx.get("target_level", "Júnior"),
            target_education=ctx.get("target_education", "Sem Formação")
        )
        
        # Verify strict validation
        if result["aprovado"] is True:
            failed_vetoes.append({
                "index": idx,
                "title": case["title"],
                "expected_veto": case["expected_veto_reason"],
                "reason": result["reason"]
            })
        else:
            passed_vetoes.append(case["title"])
            
    # Report results
    print(f"\n--- SANITY BATTERY RESULTS ---")
    print(f"Total Blocked: {len(passed_vetoes)}/50")
    print(f"Total Bypassed (Errors): {len(failed_vetoes)}/50")
    
    if failed_vetoes:
        for fail in failed_vetoes:
            print(f"🚨 BYPASS DETECTED at Job #{fail['index']}: '{fail['title']}' | Expected Veto: {fail['expected_veto']} | AI Reason: {fail['reason']}")
            
    assert len(failed_vetoes) == 0, f"{len(failed_vetoes)} trick jobs bypassed the filter!"
```

---

## 5. Verification Method

To verify the implementation once applied:

1.  **Test Run**: Run the main E2E test runner:
    ```bash
    python run_tests.py
    ```
    This verifies that our code adjustments in `scrapers/ai_filter.py` do not break existing mocks or database flows.
2.  **Run Sanity Battery**: Execute the new battery test:
    ```bash
    pytest tests/test_trick_battery.py -v
    ```
    Verify that 50/50 test cases pass, demonstrating a **0% bypass rate** on the trick dataset.
3.  **Inspect Logs**: Check the generated logs or print outputs during the run to confirm that the `[Veto Python Hard-Lock]` string is appended to the `reason` field on blocked jobs.
