import os
import json
import pytest
import asyncio
from unittest.mock import MagicMock
import groq
from scrapers.ai_filter import score_job_match

@pytest.mark.asyncio
async def test_sanity_battery_zero_approval():
    # Load sanity battery jobs
    json_path = os.path.join(os.path.dirname(__file__), "sanity_battery.json")
    with open(json_path, "r", encoding="utf-8") as f:
        sanity_jobs = json.load(f)
    
    assert len(sanity_jobs) == 50, f"Expected 50 jobs, got {len(sanity_jobs)}"
    
    # Mock completions.create
    class MockMessage:
        def __init__(self, content):
            self.content = content
    class MockChoice:
        def __init__(self, content):
            self.message = MockMessage(content)
    class MockResp:
        def __init__(self, content):
            self.choices = [MockChoice(content)]

    async def mock_create(model, messages, **kwargs):
        prompt = messages[-1]["content"]
        
        # Find which job this prompt is evaluating
        title_line = ""
        for line in prompt.splitlines():
            if line.strip().startswith("Título:"):
                title_line = line.strip().replace("Título:", "").strip()
                break
        
        matched_job = None
        for job in sanity_jobs:
            if job["title"].strip() == title_line:
                matched_job = job
                break
        
        if not matched_job:
            # Fallback if title not matched (should not happen, but just in case)
            raise ValueError(f"Job title not matched in prompt: {prompt}")

        category = matched_job["category"]
        
        if category == "usd_euro":
            content = {
                "aprovado": False,
                "is_freelance": False,
                "vaga_corresponde_ao_cargo": True,
                "localidade_correta": True,
                "exige_experiencia": False,
                "exige_faculdade": False,
                "salary_declared": True,
                "has_benefits": False,
                "score": 40,
                "justificativa_curta": "Reprovado por salário em moeda estrangeira (USD/Euro).",
                "reqs": "Python",
                "bonus": "Nenhum",
                "benefits": "USD 5000",
                "model": "Remoto"
            }
        elif category == "fluent_english":
            content = {
                "aprovado": False,
                "is_freelance": False,
                "vaga_corresponde_ao_cargo": True,
                "localidade_correta": True,
                "exige_experiencia": False,
                "exige_faculdade": False,
                "salary_declared": False,
                "has_benefits": False,
                "score": 30,
                "justificativa_curta": "Reprovado por exigência de inglês fluente para cargo Júnior.",
                "reqs": "Inglês Fluente",
                "bonus": "Nenhum",
                "benefits": "A combinar",
                "model": "Remoto"
            }
        elif category == "freelance":
            content = {
                "aprovado": True,
                "is_freelance": True,
                "vaga_corresponde_ao_cargo": True,
                "localidade_correta": True,
                "exige_experiencia": False,
                "exige_faculdade": False,
                "salary_declared": True,
                "has_benefits": False,
                "score": 85,
                "justificativa_curta": "Candidato atende aos requisitos técnicos.",
                "reqs": "Python",
                "bonus": "Nenhum",
                "benefits": "R$ 50/hora",
                "model": "Remoto"
            }
        elif category == "seniority_mismatch":
            content = {
                "aprovado": True,
                "is_freelance": False,
                "vaga_corresponde_ao_cargo": True,
                "localidade_correta": True,
                "exige_experiencia": True,
                "exige_faculdade": False,
                "salary_declared": True,
                "has_benefits": True,
                "score": 90,
                "justificativa_curta": "Candidato atende aos requisitos técnicos.",
                "reqs": "Python",
                "bonus": "Nenhum",
                "benefits": "R$ 10.000",
                "model": "Remoto"
            }
        elif category == "mandatory_degree":
            content = {
                "aprovado": True,
                "is_freelance": False,
                "vaga_corresponde_ao_cargo": True,
                "localidade_correta": True,
                "exige_experiencia": False,
                "exige_faculdade": True,
                "salary_declared": True,
                "has_benefits": True,
                "score": 90,
                "justificativa_curta": "Candidato atende aos requisitos técnicos.",
                "reqs": "Python",
                "bonus": "Nenhum",
                "benefits": "R$ 5.000",
                "model": "Remoto"
            }
        else:
            raise ValueError(f"Unknown category: {category}")

        return MockResp(json.dumps(content))

    # Temporarily override Groq's custom_create / create
    original_create = groq.AsyncGroq().chat.completions.create
    groq.AsyncGroq().chat.completions.create = mock_create

    try:
        # Candidate profile to test against: Junior, remote BR, Sem Formação
        resume_text = "Diego Candidate. Junior Python Developer. No college degree. English: basic."
        
        approved_count = 0
        for job in sanity_jobs:
            evaluation = await score_job_match(
                resume_text=resume_text,
                job=job,
                target_keyword="Python",
                target_location="Brasil (Remoto)",
                target_level="Júnior",
                target_education="Sem Formação",
                target_contract="CLT"
            )
            
            # Assertions to ensure it was indeed rejected
            assert evaluation["aprovado"] is False, f"Job {job['title']} in category {job['category']} should have been rejected."
            
            # For the safety fields that hard-lock, assert that the hard-lock override worked:
            if job["category"] in ["freelance", "seniority_mismatch", "mandatory_degree"]:
                assert "[Hard-Lock Override]" in evaluation["reason"], f"Job {job['title']} should have Hard-Lock Override in reason, got: {evaluation['reason']}"
                assert evaluation["score"] == 0, f"Job {job['title']} should have score reset to 0, got: {evaluation['score']}"
                
                # Check specific conditions
                if job["category"] == "freelance":
                    assert "is_freelance == True" in evaluation["reason"]
                elif job["category"] == "seniority_mismatch":
                    assert "exige_experiencia == True" in evaluation["reason"]
                elif job["category"] == "mandatory_degree":
                    assert "exige_faculdade == True" in evaluation["reason"]
            
            if evaluation["aprovado"]:
                approved_count += 1
                
        # Assert that the approval rate is strictly 0%
        approval_rate = approved_count / len(sanity_jobs)
        assert approval_rate == 0.0, f"Expected 0% approval rate, got {approval_rate * 100}%"
        
    finally:
        # Restore original create
        groq.AsyncGroq().chat.completions.create = original_create
