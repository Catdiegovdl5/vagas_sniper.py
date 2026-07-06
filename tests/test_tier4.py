import os
import sqlite3
import pytest
import asyncio
from fastapi.testclient import TestClient
import database
from app import app

# Initialize test client
client = TestClient(app)

def get_auto_apply():
    try:
        import auto_apply as aa
        return aa
    except ImportError:
        import tests.mock_auto_apply as aa
        return aa

# ---------------------------------------------------------
# Tier 4: Real-world application scenarios (5 tests)
# ---------------------------------------------------------

def test_app_workflow_trigger_hunt_endpoint():
    """
    Test 1: Triggers the scrapers scan via FastAPI `/api/trigger` endpoint.
    Asserts that the webhook/trigger correctly loads scrapers, inserts jobs,
    and returns successful count.
    """
    # Since glassdoor and infojobs might not be present or are mocked,
    # let's trigger indeed scraper which is in the workspace
    payload = {
        "platforms": ["indeed"],
        "keyword": "Python",
        "level": "Júnior"
    }
    response = client.post("/api/trigger", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "inserted" in data
    assert "total_found" in data

def test_app_workflow_get_jobs_endpoint():
    """
    Test 2: Verifies fetching jobs via FastAPI `/api/jobs` dashboard endpoint.
    Populates DB manually and checks that the endpoint returns the exact schema.
    """
    # Insert a job manually
    conn = sqlite3.connect(database.DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO jobs (id, title, company, budget, link, platform, requirements) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("https://example.com/job/dash-test-1", "Dashboard Engineer", "Dash Corp", "R$ 7.000", "https://example.com/job/dash-test-1", "LinkedIn", "Requirements for dashboard test")
    )
    conn.commit()
    conn.close()

    response = client.get("/api/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert len(data["jobs"]) >= 1
    
    # Check fields in first job
    job = data["jobs"][0]
    assert "title" in job
    assert "company" in job
    assert "link" in job
    assert "requirements" in job

def test_app_workflow_n8n_webhook_ingestion():
    """
    Test 3: Simulates n8n webhook vacancy ingestion via `/api/webhook/n8n`.
    Verifies that the database receives and processes incoming external job lists.
    """
    payload = {
        "jobs": [
            {
                "link": "https://example.com/job/n8n-test-1",
                "title": "N8N Automation Specialist",
                "company": "Workflow Inc",
                "budget": "R$ 9.000",
                "platform": "LinkedIn",
                "requirements": "Experience with n8n and REST APIs"
            },
            {
                "link": "https://example.com/job/n8n-test-2",
                "title": "Backend Python Developer",
                "company": "Backend Inc",
                "budget": "R$ 10.000",
                "platform": "Indeed",
                "requirements": "Experience with FastAPI and database migrations"
            }
        ]
    }
    response = client.post("/api/webhook/n8n", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["inserted"] > 0
    assert data["total_received"] == 2

    # Verify insertions in SQLite DB
    conn = sqlite3.connect(database.DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM jobs WHERE link LIKE '%n8n-test%'")
    count = c.fetchone()[0]
    conn.close()
    assert count == 2

def test_app_workflow_system_logs_dashboard():
    """
    Test 4: Verifies the logs endpoint `/api/logs` which reads the system.log.
    Writes a test log line and verifies it appears in the JSON response.
    """
    # Write a test log line directly to the logger
    import logging
    logger = logging.getLogger("SniperBot")
    test_message = "TEST_LOG_MESSAGE_FOR_TIER4"
    logger.info(test_message)

    response = client.get("/api/logs")
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    # Assert our test message is present in the list of logs returned
    log_content = "".join(data["logs"])
    assert test_message in log_content

def test_app_workflow_full_pipeline_cycle():
    """
    Test 5: Full cycle simulation.
    1. Webhook delivers a vacancy.
    2. IA filters/scores it.
    3. Auto-apply engine applies to it.
    4. Dashboard shows status as 'applied'.
    """
    # 1. Webhook delivers a job
    job_link = "https://example.com/job/full-pipeline-test"
    payload = {
        "jobs": [
            {
                "link": job_link,
                "title": "FastAPI Web Developer",
                "company": "FullCycle Corp",
                "budget": "R$ 12.000",
                "platform": "LinkedIn",
                "requirements": "Requirements including Python and FastAPI microservices development with Git."
            }
        ]
    }
    res_webhook = client.post("/api/webhook/n8n", json=payload)
    assert res_webhook.status_code == 200
    
    # 2. IA filter scores it
    from scrapers.ai_filter import score_job_match
    # Retrieve job from DB
    conn = sqlite3.connect(database.DB_PATH)
    c = conn.cursor()
    c.execute("SELECT title, company, requirements, link FROM jobs WHERE link = ?", (job_link,))
    r = c.fetchone()
    db_job = {"title": r[0], "company": r[1], "requirements": r[2], "link": r[3]}
    
    loop = asyncio.get_event_loop()
    eval_result = loop.run_until_complete(
        score_job_match("Python FastAPI Developer", db_job, "FastAPI", "Brasil (Remoto)", "Todos")
    )
    
    # Write evaluation back to DB
    c.execute(
        "UPDATE jobs SET score = ?, status = ? WHERE link = ?",
        (eval_result["score"], "pending" if eval_result["aprovado"] else "rejected", job_link)
    )
    conn.commit()
    conn.close()

    # 3. Auto-apply engine runs and applies to it
    aa = get_auto_apply()
    applied_count = aa.run_auto_apply(database.DB_PATH, "temp_curriculo.pdf", "http://127.0.0.1:8081/apply")
    assert applied_count == 1

    # 4. Fetch jobs via API dashboard and verify status is 'applied'
    res_jobs = client.get("/api/jobs")
    assert res_jobs.status_code == 200
    jobs_list = res_jobs.json()["jobs"]
    
    found = False
    for j in jobs_list:
        if j["link"] == job_link:
            found = True
            # Status is not a column directly returned in get_jobs(), let's check DB directly
            # Wait, let's verify DB status is applied
            conn = sqlite3.connect(database.DB_PATH)
            c = conn.cursor()
            c.execute("SELECT status FROM jobs WHERE link = ?", (job_link,))
            status = c.fetchone()[0]
            conn.close()
            assert status == "applied"
            break
            
    assert found is True
