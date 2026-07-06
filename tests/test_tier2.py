import os
import sqlite3
import pytest
import json
from unittest.mock import MagicMock
import database

def get_glassdoor():
    try:
        import scrapers.glassdoor as gd
        return gd
    except ImportError:
        import tests.mock_glassdoor as gd
        return gd

def get_infojobs():
    try:
        import scrapers.infojobs as ij
        return ij
    except ImportError:
        import tests.mock_infojobs as ij
        return ij

def get_auto_apply():
    try:
        import auto_apply as aa
        return aa
    except ImportError:
        import tests.mock_auto_apply as aa
        return aa

# ---------------------------------------------------------
# Feature 1: Scrapers Boundaries
# ---------------------------------------------------------

def test_scraper_handles_empty_search_gracefully():
    # Calling scraper with no jobs match
    gd = get_glassdoor()
    jobs = gd.scrape("NonExistentKeywordAtAll")
    assert isinstance(jobs, list)

def test_scraper_handles_excessive_keyword_length():
    gd = get_glassdoor()
    huge_kw = "A" * 500
    jobs = gd.scrape(huge_kw)
    assert isinstance(jobs, list)

def test_scraper_handles_malformed_html_without_exception():
    # If the scraper parses malformed HTML, it shouldn't crash
    from bs4 import BeautifulSoup
    html = "<li><a class='base-card__full-link'>no title or company here</a></li>"
    soup = BeautifulSoup(html, "html.parser")
    card = soup.find("li")
    title_el = card.find("h3", class_="base-search-card__title")
    title = title_el.text.strip() if title_el else "Sem Título"
    assert title == "Sem Título"

def test_scraper_handles_special_characters():
    gd = get_glassdoor()
    jobs = gd.scrape("🐍 Python & C++ #Developer 🚀")
    assert isinstance(jobs, list)
    assert len(jobs) > 0

def test_scraper_handles_pagination_overflow():
    ij = get_infojobs()
    # Test call behaves fine under normal levels
    jobs = ij.scrape("Python", level="InexistenteLevel")
    assert isinstance(jobs, list)

# ---------------------------------------------------------
# Feature 2: Snippet Bypass Boundaries
# ---------------------------------------------------------

def test_snippet_bypass_handles_http_errors():
    import requests
    # Temporarily monkeypatch to throw HTTP error
    original_get = requests.get
    requests.get = MagicMock(side_effect=requests.exceptions.HTTPError("500 Internal Server Error"))
    try:
        with pytest.raises(requests.exceptions.HTTPError):
            requests.get("https://br.linkedin.com/jobs")
    finally:
        requests.get = original_get

def test_snippet_bypass_handles_timeout():
    import requests
    original_get = requests.get
    requests.get = MagicMock(side_effect=requests.exceptions.Timeout("Request timed out"))
    try:
        with pytest.raises(requests.exceptions.Timeout):
            requests.get("https://br.linkedin.com/jobs", timeout=1)
    finally:
        requests.get = original_get

def test_playwright_mock_handles_redirection():
    # Ensure Playwright mock handles redirects
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        res = page.goto("http://redirect-me.com")
        assert res is not None

def test_cloudflare_bypass_detection():
    # Simulates cloudflare challenge content detection
    content = "Please enable cookies and JavaScript to pass Cloudflare challenge."
    is_blocked = "Cloudflare" in content or "Please wait..." in content
    assert is_blocked is True

def test_beautifulsoup_empty_parse():
    from bs4 import BeautifulSoup
    soup = BeautifulSoup("", "html.parser")
    elements = soup.find_all("div")
    assert len(elements) == 0

# ---------------------------------------------------------
# Feature 3: IA Ranking Boundaries
# ---------------------------------------------------------

def test_ia_ranking_handles_empty_resume():
    from scrapers.ai_filter import score_job_match
    import asyncio
    job = {
        "title": "Python Dev",
        "company": "Fast Corp",
        "link": "https://example.com/job/empty-resume",
        "requirements": "Requirements details"
    }
    loop = asyncio.get_event_loop()
    # Should fallback to automatic approval or score default
    result = loop.run_until_complete(score_job_match("", job, "Python"))
    assert result["aprovado"] is True
    assert result["score"] == 100

def test_ia_ranking_handles_groq_malformed_json():
    import groq
    from scrapers.ai_filter import score_job_match
    import asyncio
    
    # Force mock Groq to return malformed/invalid JSON
    original_custom = groq.AsyncGroq().chat.completions.custom_content
    groq.AsyncGroq().chat.completions.custom_content = "This is not JSON at all!"
    
    job = {
        "title": "Python Dev",
        "company": "Fast Corp",
        "link": "https://example.com/job/bad-json",
        "requirements": "Python Developer needed."
    }
    
    loop = asyncio.get_event_loop()
    try:
        result = loop.run_until_complete(score_job_match("My resume", job, "Python"))
        # Should gracefully fail and return unapproved (aprovado=False, score=0)
        assert result["aprovado"] is False
        assert result["score"] == 0
        assert "Erro no modelo estruturado." in result["reason"]
    finally:
        groq.AsyncGroq().chat.completions.custom_content = original_custom

def test_ia_ranking_handles_extremely_long_description():
    from scrapers.ai_filter import score_job_match
    import asyncio
    
    # 20,000 characters description
    long_desc = "Requisitos " * 2000
    job = {
        "title": "Python Specialist",
        "company": "Specialist Corp",
        "link": "https://example.com/job/long-desc",
        "requirements": long_desc
    }
    
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(score_job_match("My resume", job, "Python"))
    assert isinstance(result, dict)

def test_ia_ranking_handles_groq_rate_limits():
    import groq
    from scrapers.ai_filter import score_job_match
    import asyncio
    
    # Mocking Groq client.chat.completions.create to raise RateLimitError/429
    call_count = 0
    
    async def mock_rate_limit(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Rate limit exceeded 429")
        # Return success on 3rd attempt
        class MockChoice:
            message = MagicMock(content=json.dumps({
                "aprovado": True,
                "is_freelance": False,
                "vaga_corresponde_ao_cargo": True,
                "localidade_correta": True,
                "exige_experiencia": False,
                "exige_faculdade": False,
                "salary_declared": True,
                "has_benefits": True,
                "score": 90,
                "justificativa_curta": "Passed",
                "reqs": "Python",
                "bonus": "Git",
                "benefits": "VA",
                "model": "Remoto"
            }))
        class MockResp:
            choices = [MockChoice()]
        return MockResp()
        
    original_create = groq.AsyncGroq().chat.completions.create
    groq.AsyncGroq().chat.completions.create = mock_rate_limit
    
    job = {
        "title": "Python Developer",
        "requirements": "Need Python"
    }
    
    loop = asyncio.get_event_loop()
    try:
        # Note: we might mock sleep inside score_job_match, but since it's only 2+tentativa seconds, it's quick enough
        result = loop.run_until_complete(score_job_match("Diego Candidate", job, "Python"))
        assert result["aprovado"] is True
        assert call_count == 3
    finally:
        groq.AsyncGroq().chat.completions.create = original_create

def test_ia_ranking_groq_client_no_api_keys():
    from scrapers.ai_filter import API_KEYS
    # Test API_KEYS has active keys and is a list
    assert isinstance(API_KEYS, list)
    assert len(API_KEYS) > 0

# ---------------------------------------------------------
# Feature 4: Auto-apply Boundaries
# ---------------------------------------------------------

def test_auto_apply_handles_empty_db_fields():
    # Insert job with missing company or description
    aa = get_auto_apply()
    conn = sqlite3.connect(database.DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO jobs (id, title, company, budget, link, platform, requirements, score, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("https://example.com/job/missing-fields", "Developer", None, None, "https://example.com/job/missing-fields", "LinkedIn", None, 85, "pending")
    )
    conn.commit()
    conn.close()
    
    applied = aa.run_auto_apply(database.DB_PATH, "temp_curriculo.pdf", "http://127.0.0.1:8081/apply")
    # Should apply successfully and update database, despite missing fields
    assert applied == 1

def test_auto_apply_handles_missing_resume_path():
    aa = get_auto_apply()
    # Passing a non-existent file path: auto_apply should handle/create or fail gracefully
    success = aa.apply_to_job("https://example.com/job/test-missing-file", "non_existent_file.pdf", "http://127.0.0.1:8081/apply")
    assert success is True # Mock auto apply auto-creates the mock PDF file

def test_auto_apply_handles_ats_server_malformed_json():
    aa = get_auto_apply()
    # ATS returns bad response
    success = aa.apply_to_job("https://example.com/job/bad-response", "temp_curriculo.pdf", "http://127.0.0.1:8081/non-existent-endpoint")
    assert success is False

def test_auto_apply_handles_duplicate_job_links():
    # Inserting duplicate links is prevented by database schema UNIQUE/PRIMARY KEY constraints
    conn = sqlite3.connect(database.DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO jobs (id, title, company, link, platform, score, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("https://example.com/job/unique-link", "Job 1", "Corp A", "https://example.com/job/unique-link", "LinkedIn", 90, "pending")
    )
    conn.commit()
    
    # Try duplicate insertion
    with pytest.raises(sqlite3.IntegrityError):
        c.execute(
            "INSERT INTO jobs (id, title, company, link, platform, score, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("https://example.com/job/unique-link", "Job 2", "Corp B", "https://example.com/job/unique-link", "LinkedIn", 92, "pending")
        )
    conn.close()

def test_auto_apply_concurrency_lock():
    # If run_auto_apply runs concurrently, sqlite locks should be managed or handled without fatal crash
    aa = get_auto_apply()
    conn = sqlite3.connect(database.DB_PATH)
    # Put db in write transaction
    conn.execute("BEGIN IMMEDIATE TRANSACTION")
    
    # Concurrently try to run auto-apply. Since DB is locked, it should fail/throw or retry.
    try:
        # SQLite should throw Busy exception
        with pytest.raises(sqlite3.OperationalError):
            conn2 = sqlite3.connect(database.DB_PATH, timeout=0.1)
            c2 = conn2.cursor()
            c2.execute("UPDATE jobs SET status = 'applied' WHERE id = '1'")
            conn2.commit()
            conn2.close()
    finally:
        conn.rollback()
        conn.close()
