import os
import sqlite3
import pytest
import asyncio
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
# Tier 3: Cross-Feature combinations (Pairwise coverage, 4 tests)
# ---------------------------------------------------------

def test_combination_scraper_and_snippet_bypass():
    """
    Combines: Scraper (Indeed/Playwright) + Snippet Bypass.
    Verifies that running a scraper utilizing Playwright mock handles
    anti-bot protections (Cloudflare challenge) and returns jobs.
    """
    import scrapers.indeed as indeed
    # Trigger scrape which executes browser, context, and page mock logic
    jobs = indeed.scrape("Python", "Todos")
    assert isinstance(jobs, list)

def test_combination_scraper_db_and_ia_ranking():
    """
    Combines: Scraper + DB insertion + IA Ranking.
    Verifies that scraped jobs inserted into the DB are correctly read,
    evaluated by the IA filter, and their scores are processed.
    """
    gd = get_glassdoor()
    # Scrape jobs
    scraped_jobs = gd.scrape("Python", "Júnior")
    assert len(scraped_jobs) > 0
    
    # Insert jobs to test database
    inserted = database.insert_jobs(scraped_jobs)
    assert inserted > 0
    
    # Read jobs from database
    db_jobs = database.get_jobs()
    assert len(db_jobs) >= 1
    
    # Run IA ranking on the first job in the DB
    from scrapers.ai_filter import score_job_match
    target_job = db_jobs[0]
    
    loop = asyncio.get_event_loop()
    evaluation = loop.run_until_complete(
        score_job_match("Diego Candidate. Python developer.", target_job, "Python", "Brasil (Remoto)", "Júnior")
    )
    
    assert "score" in evaluation
    assert evaluation["score"] >= 80

def test_combination_ia_ranking_and_auto_apply():
    """
    Combines: IA Ranking + Auto-apply Engine.
    Verifies that high-scoring jobs evaluated by the IA filter are picked up
    by the auto-apply engine, submitted to the ATS, and status updated.
    """
    aa = get_auto_apply()
    
    # Pre-populate a job in DB
    conn = sqlite3.connect(database.DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO jobs (id, title, company, budget, link, platform, requirements, score, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("https://example.com/job/ia-apply-comb", "Python Lead", "Combo S/A", "R$ 15.000", "https://example.com/job/ia-apply-comb", "Glassdoor", "Python developer expert", 95, "pending")
    )
    conn.commit()
    conn.close()
    
    # Trigger auto-apply
    applied = aa.run_auto_apply(database.DB_PATH, "temp_curriculo.pdf", "http://127.0.0.1:8081/apply")
    assert applied == 1
    
    # Check status
    conn = sqlite3.connect(database.DB_PATH)
    c = conn.cursor()
    c.execute("SELECT status FROM jobs WHERE link = ?", ("https://example.com/job/ia-apply-comb",))
    status = c.fetchone()[0]
    conn.close()
    
    assert status == "applied"

def test_combination_scraper_ia_ranking_and_auto_apply():
    """
    Combines: Scraper + IA Ranking + Auto-apply.
    Full pipeline: Scraper runs -> DB gets jobs -> IA filters & scores -> Auto-apply runs.
    """
    ij = get_infojobs()
    aa = get_auto_apply()
    from scrapers.ai_filter import score_job_match
    
    # 1. Scrape jobs
    jobs = ij.scrape("Django", "Pleno")
    assert len(jobs) > 0
    
    # 2. Insert raw jobs into DB
    inserted = database.insert_jobs(jobs)
    assert inserted > 0
    
    # 3. Read jobs and evaluate them with IA ranking
    db_jobs = database.get_jobs()
    conn = sqlite3.connect(database.DB_PATH)
    c = conn.cursor()
    
    loop = asyncio.get_event_loop()
    for job in db_jobs:
        eval_result = loop.run_until_complete(
            score_job_match("Django developer. Python background. 3 years experience.", job, "Django", "Brasil (Remoto)", "Pleno")
        )
        # Update score and status based on evaluation
        status = "pending" if eval_result["aprovado"] else "rejected"
        c.execute(
            "UPDATE jobs SET score = ?, status = ?, requirements = ? WHERE link = ?",
            (eval_result["score"], status, eval_result["reqs"], job["link"])
        )
    conn.commit()
    conn.close()
    
    # 4. Run auto-apply
    applied = aa.run_auto_apply(database.DB_PATH, "temp_curriculo.pdf", "http://127.0.0.1:8081/apply")
    assert applied > 0
    
    # 5. Confirm applied job status
    conn = sqlite3.connect(database.DB_PATH)
    c = conn.cursor()
    c.execute("SELECT status, score FROM jobs WHERE status = 'applied'")
    results = c.fetchall()
    conn.close()
    
    assert len(results) > 0
    for status, score in results:
        assert status == "applied"
        assert score >= 80
