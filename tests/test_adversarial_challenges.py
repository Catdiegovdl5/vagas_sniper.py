import os
import json
import pytest
import asyncio
import groq
from scrapers.ai_filter import score_job_match

@pytest.mark.asyncio
async def test_senior_candidate_with_experience_job():
    """
    Bug 1: Sênior candidate applying to an experience-required job is incorrectly rejected
    by the python hard-lock override.
    """
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
        # AI correctly evaluates that for a Sênior, the job requiring experience is approved (aprovado=True)
        content = {
            "aprovado": True,
            "is_freelance": False,
            "vaga_corresponde_ao_cargo": True,
            "localidade_correta": True,
            "exige_experiencia": True,  # Job does require experience, which is correct for Senior
            "exige_faculdade": False,
            "salary_declared": True,
            "has_benefits": True,
            "score": 95,
            "justificativa_curta": "Candidato Sênior atende plenamente aos requisitos da vaga.",
            "reqs": "Python, Django, 5 anos de experiência",
            "bonus": "AWS",
            "benefits": "R$ 15.000",
            "model": "Remoto"
        }
        return MockResp(json.dumps(content))

    original_create = groq.AsyncGroq().chat.completions.create
    groq.AsyncGroq().chat.completions.create = mock_create

    try:
        resume_text = "Diego Candidate. Senior Python Developer. 10 years of experience. Sem Formação."
        job = {
            "title": "Senior Python Developer",
            "company": "BigTech",
            "requirements": "Looking for a Senior Python Developer with 5+ years of experience.",
            "link": "https://example.com/senior-job",
            "platform": "LinkedIn"
        }
        
        evaluation = await score_job_match(
            resume_text=resume_text,
            job=job,
            target_keyword="Python",
            target_location="Brasil (Remoto)",
            target_level="Sênior",
            target_education="Sem Formação"
        )
        
        # EXPECTED: The job should be approved since target_level is Sênior.
        # ACTUAL: Python hard-lock override unconditionally rejects it due to exige_experiencia == True.
        assert evaluation["aprovado"] is True, "Sênior job was incorrectly rejected by hard-lock override."
        
    finally:
        groq.AsyncGroq().chat.completions.create = original_create

@pytest.mark.asyncio
async def test_graduate_candidate_with_degree_job():
    """
    Bug 2: Candidates with degrees/no restrictions are unconditionally rejected for jobs
    requiring a college degree due to python hard-lock override.
    """
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
        content = {
            "aprovado": True,
            "is_freelance": False,
            "vaga_corresponde_ao_cargo": True,
            "localidade_correta": True,
            "exige_experiencia": False,
            "exige_faculdade": True,  # Job requires degree, which is acceptable since candidate has a degree
            "salary_declared": True,
            "has_benefits": True,
            "score": 90,
            "justificativa_curta": "Candidato tem ensino superior e atende aos requisitos.",
            "reqs": "Bacharelado em Ciência da Computação",
            "bonus": "Nenhum",
            "benefits": "R$ 5.000",
            "model": "Remoto"
        }
        return MockResp(json.dumps(content))

    original_create = groq.AsyncGroq().chat.completions.create
    groq.AsyncGroq().chat.completions.create = mock_create

    try:
        resume_text = "Diego Candidate. Junior Python Developer. Has a Bachelor's Degree in Computer Science."
        job = {
            "title": "Junior Developer",
            "company": "Corp",
            "requirements": "Requires a Bachelor's Degree in Computer Science or related fields.",
            "link": "https://example.com/degree-job",
            "platform": "LinkedIn"
        }
        
        evaluation = await score_job_match(
            resume_text=resume_text,
            job=job,
            target_keyword="Python",
            target_location="Brasil (Remoto)",
            target_level="Júnior",
            target_education="Todos"  # Has no education restrictions, or has degree
        )
        
        # EXPECTED: The job should be approved.
        # ACTUAL: Python hard-lock override unconditionally rejects it due to exige_faculdade == True.
        assert evaluation["aprovado"] is True, "Job requiring degree was incorrectly rejected for candidate with degree."
        
    finally:
        groq.AsyncGroq().chat.completions.create = original_create

@pytest.mark.asyncio
async def test_foreign_currency_and_english_leakage():
    """
    Bug 3: Lack of Python-level hard-locks for foreign currency (USD/Euro) or fluent English
    requirements. If the LLM hallucinatingly/incorrectly returns aprovado=True, the system
    does not catch it.
    """
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
        # LLM hallucination: returns aprovado=True for a USD salary job
        content = {
            "aprovado": True,
            "is_freelance": False,
            "vaga_corresponde_ao_cargo": True,
            "localidade_correta": True,
            "exige_experiencia": False,
            "exige_faculdade": False,
            "salary_declared": True,
            "has_benefits": False,
            "score": 90,
            "justificativa_curta": "LLM incorrectly approved a USD/Euro job.",
            "reqs": "Python",
            "bonus": "Nenhum",
            "benefits": "$5,000/month",
            "model": "Remoto"
        }
        return MockResp(json.dumps(content))

    original_create = groq.AsyncGroq().chat.completions.create
    groq.AsyncGroq().chat.completions.create = mock_create

    try:
        resume_text = "Diego Candidate. Junior Python Developer. No college degree. English: basic."
        job = {
            "title": "Python Developer (USD)",
            "company": "US Corp",
            "requirements": "Looking for a python developer. Salary paid in USD ($5000/month).",
            "link": "https://example.com/usd-job",
            "platform": "LinkedIn"
        }
        
        evaluation = await score_job_match(
            resume_text=resume_text,
            job=job,
            target_keyword="Python",
            target_location="Brasil (Remoto)",
            target_level="Júnior",
            target_education="Sem Formação"
        )
        
        # EXPECTED: The job should be rejected since the system forbids USD/Euro jobs.
        # ACTUAL: Since there is no Python-level hard-lock for this category, it leaks and gets approved.
        assert evaluation["aprovado"] is False, "USD/Euro job leaked and was approved due to lack of Python-level hard-lock."
        
    finally:
        groq.AsyncGroq().chat.completions.create = original_create
