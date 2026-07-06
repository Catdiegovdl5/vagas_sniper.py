# Analysis Report: E2E Testing Infrastructure Design

## 1. Current State & Interface of Each Module

### 1.1 Scrapers (`scrapers/`)
The repository contains 14 scraper files under the `scrapers/` directory, along with the AI Filter:
*   **HTML Scrapers (using `requests` & `BeautifulSoup`):**
    *   `catho.py` - Fetches search result pages from `catho.com.br` and parses using `BeautifulSoup`. Has a fallback dummy job.
    *   `workana.py` - Fetches project listing pages from `workana.com` and parses using `BeautifulSoup`. Has a fallback dummy project.
    *   `remotar.py` - Fetches search results from `remotar.com.br` and parses using `BeautifulSoup`. Has a fallback dummy job.
    *   `novenove.py` - Fetches projects from `99freelas.com.br` and parses using `BeautifulSoup`. No fallback.
*   **JSON API Scrapers (using `requests` to REST API endpoints):**
    *   `gupy.py` - Fetches from Gupy's career portal endpoint (`employability-portal.gupy.io`). No fallback.
    *   `github_vagas.py` - Fetches from GitHub's search API searching open issues. No fallback.
    *   `jooble.py` - Fetches from Jooble's REST API. Has a fallback.
    *   `jsearch.py` - Fetches from JSearch (RapidAPI) endpoint. Has a fallback.
    *   `freelancer.py` - Fetches from Freelancer's active projects endpoint. No fallback.
    *   `trampos.py` - Fetches from Trampos.co API and filters by keyword client-side. No fallback.
*   **Specialized / Third-Party Scrapers:**
    *   `linkedin.py` - Uses `curl_cffi.requests` to impersonate `chrome110` and requests LinkedIn's anonymous guest search API. No fallback.
    *   `indeed.py` - Uses `playwright.sync_api` to launch a headless Chromium browser, bypass Cloudflare, and parse JSON data embedded inside the HTML page. No fallback.
    *   `gmail.py` - Uses Google Client Library to query the user's inbox via Gmail API and extract job links. No fallback.
    *   `meta_ads.py` - Calls an Apify actor `curious_coder/facebook-ads-library-scraper` via `apify_client.ApifyClient`.

**Interface contract:**
All scrapers implement a `scrape(keyword, level, country)` signature (or similar, sometimes with defaults) and return a list of dictionaries matching the schema:
```python
{
    "platform": str,
    "title": str,
    "company": str,
    "budget": str,
    "link": str,
    "job_type": str,
    "profession": str,
    "level": str,
    "requirements": str
}
```

### 1.2 Database (`database.py`)
Provides database persistence using SQLite (`jobs.db`).
*   **Schema:**
    *   `id` (TEXT PRIMARY KEY) - Stores the job's `link` to enforce uniqueness.
    *   `title` (TEXT), `company` (TEXT), `budget` (TEXT), `link` (TEXT), `platform` (TEXT), `added_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP), `job_type` (TEXT), `profession` (TEXT), `level` (TEXT), `requirements` (TEXT).
*   **Key Functions:**
    *   `init_db()`: Initializes/migrates DB table and fields.
    *   `insert_jobs(jobs: List[dict])`: Inserts jobs, ignoring duplicates.
    *   `get_jobs()`: Returns all stored jobs in chronological order of insertion.

### 1.3 FastAPI Web Application (`app.py`)
Exposes a backend API and mounts static files (dashboard).
*   **Endpoints:**
    *   `GET /` - Serves dashboard static HTML.
    *   `GET /api/jobs` - Returns all jobs from SQLite DB.
    *   `POST /api/webhook/n8n` - Receives jobs from n8n webhook and inserts them.
    *   `POST /api/trigger` - Dynamically triggers selected scrapers synchronously and persists the results.
    *   `GET /api/logs` - Retrieves system log contents.

### 1.4 Telegram Bot (`bot.py` & `launcher.py`)
Implements the user interaction via Telegram (using `aiogram`). Handles search parameters, manual trigger, free-text NLP search via LLM, and PDF resume upload. It invokes scrapers and the `ai_filter` in an integrated async workflow.

### 1.5 AI Filter (`scrapers/ai_filter.py`)
Utilizes the Groq client (`AsyncGroq`) to rank, score, and filter jobs.
*   **Features:**
    *   Semaphore-limited concurrency (max 8 concurrent requests).
    *   Rotates between 3 hardcoded API keys.
    *   Uses Pydantic model (`JobEvaluation`) and JSON-mode prompting for structured evaluation.
*   **Interface:**
    *   `score_job_match(resume_text, job, target_keyword, target_location, target_level) -> dict`
    *   `analyze_resume_for_keywords(resume_text) -> list`
    *   `extract_hunt_intent(message_text) -> dict`

### 1.6 Auto-Apply Module (`auto_apply.py` & `test_apply.py`)
*   **Status:** Currently non-existent. These files are planned for Milestone 4.
*   **Role:** `auto_apply.py` will poll jobs with matching scores, detect forms, autofill fields, upload `temp_curriculo.pdf`, and submit applications. `test_apply.py` is reserved for ATS tests.

---

## 2. E2E Testing Framework & Infrastructure Design

To verify the features opaque-box style without editing production code, we will design an E2E testing harness based on **pytest**.

```
tests/
├── conftest.py            # Fixtures for DB, proxy, mock servers, monkeypatches
├── test_scrapers.py       # Tier 1 & 2 tests for scrapers & Deep Scrape
├── test_ai_ranking.py     # Tier 1 & 2 tests for Groq LLM filter
├── test_auto_apply.py     # Tier 1, 2, 4 tests for ATS auto-apply engine
└── test_integration.py    # Tier 3 & 4 full flows (FastAPI, Bot, E2E)
```

### 2.1 Testing the 4 Core Features
1.  **S-Tier Scrapers:**
    *   Verify that they retrieve jobs, follow pagination, extract correct selectors, and adapt to layout changes.
2.  **Snippet Bypass (Deep Scrape):**
    *   Verify that when a scraper extracts a truncated snippet, the system visits the job link, extracts the full page text, and updates the requirements.
3.  **AI Ranking:**
    *   Verify that the candidate’s PDF resume is parsed, keywords are extracted, and jobs are correctly scored/filtered according to the criteria.
4.  **Auto-Apply Engine:**
    *   Verify that the engine identifies the application form, autofills inputs (name, email, phone), uploads the PDF, submits it, and marks the job as `applied` in the database.

---

## 3. Mocking HTTP Requests / HTML Responses

Scrapers use three network libraries: standard `requests`, `curl_cffi.requests`, and `playwright`. Since we cannot change production code, we intercept their connections.

### 3.1 Option A: Global Monkey-Patching in Pytest (Recommended for Same-Process Tests)
For same-process E2E testing (e.g. importing the scrapers inside pytest), we use pytest fixtures to monkeypatch the underlying clients:

*   **Mocking `requests`:**
    ```python
    import pytest
    import requests
    
    @pytest.fixture(autouse=True)
    def mock_requests(monkeypatch):
        original_get = requests.get
        def mocked_get(url, *args, **kwargs):
            if "catho.com.br" in url:
                return mock_response(status_code=200, text="<html>...mock job card...</html>")
            # Fallback to original or other mock matches
            return original_get(url, *args, **kwargs)
        monkeypatch.setattr(requests, "get", mocked_get)
    ```

*   **Mocking `curl_cffi.requests`:**
    ```python
    import pytest
    from curl_cffi import requests as curl_requests
    
    @pytest.fixture(autouse=True)
    def mock_curl_cffi(monkeypatch):
        def mocked_get(url, *args, **kwargs):
            if "linkedin.com" in url:
                return mock_response(status_code=200, text="<li>...mock linkedin job...</li>")
            raise Exception("Unhandled mock URL")
        monkeypatch.setattr(curl_requests, "get", mocked_get)
    ```

*   **Mocking `playwright`:**
    Indeed uses `playwright.sync_api`. We can monkeypatch `page.goto` and `page.content` inside the test context to inject custom HTML:
    ```python
    from playwright.sync_api import Page
    
    # We can inject a route handler into playwright contexts generated during test runs
    # which intercepts all network requests:
    def intercept_playwright(context):
        context.route("**/jobs**", lambda route: route.fulfill(
            status=200,
            content_type="text/html",
            body="<html>...window.mosaic.providerData...</html>"
        ))
    ```

### 3.2 Option B: Local Intercepting HTTP Proxy (Required for Multi-Process Tests)
When running the FastAPI app (`app.py`) or Bot (`bot.py`) as standalone subprocesses, monkey-patching memory is not possible. We run a lightweight proxy thread (e.g., using `mitmproxy` API or a custom socket-level python proxy) and configure the test execution environment:

```python
import os
os.environ["HTTP_PROXY"] = "http://127.0.0.1:8080"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:8080"
os.environ["SSL_CERT_FILE"] = "/path/to/proxy/cert.pem" # If SSL interception is needed
```

The proxy intercepts requests to `catho.com.br`, `br.linkedin.com`, `br.indeed.com`, and routes them to a local mock HTTP server that returns stable fixture HTML/JSON.

---

## 4. Mocking the Groq API for AI Ranking Testing

`scrapers/ai_filter.py` makes asynchronous chat completion calls to Groq.

### 4.1 Pytest Monkeypatch (Same-Process)
We mock the `create` method of the Groq chat completions resource. This avoids any network call entirely.

```python
import pytest
from unittest.mock import AsyncMock
import groq

@pytest.fixture
def mock_groq(monkeypatch):
    mock_create = AsyncMock()
    # Mocking Llama-3 JSON response
    mock_create.return_value.choices = [
        AsyncMock(
            message=AsyncMock(
                content='''{
                    "aprovado": true,
                    "is_freelance": false,
                    "vaga_corresponde_ao_cargo": true,
                    "localidade_correta": true,
                    "exige_experiencia": false,
                    "score": 90,
                    "justificativa_curta": "Matches Python requirements",
                    "reqs": "Python, SQL",
                    "bonus": "FastAPI",
                    "benefits": "CLT + VR",
                    "model": "Remoto"
                }'''
            )
        )
    ]
    monkeypatch.setattr(groq.resources.chat.completions.AsyncCompletions, "create", mock_create)
    return mock_create
```

### 4.2 Proxy Redirect (Multi-Process Subprocess)
Groq calls `https://api.groq.com/openai/v1/chat/completions`. Our mock proxy intercepts this endpoint and returns a mock JSON response matching the structure expected by `ai_filter.JobEvaluation`.

---

## 5. Mocking the ATS Server for Auto-Apply Testing

The Auto-Apply engine must submit candidate data to application forms. We run a dedicated mock ATS Server to capture and assert these submissions.

```
                    ┌────────────────────────┐
                    │     E2E Test Runner    │
                    └───────────┬────────────┘
                                │ 1. Trigger Apply
                                ▼
   ┌────────────────────────────────────────────────────────┐
   │                     Auto-Apply Engine                  │
   │   - Fetches match from SQLite DB                       │
   │   - Parses forms / fills input fields                  │
   │   - Uploads temp_curriculo.pdf                         │
   └───────────┬───────────────────────────────────┬────────┘
               │ 2. GET /apply-form                │ 3. POST /submit
               ▼                                   ▼
   ┌────────────────────────────────────────────────────────┐
   │                    Mock ATS Server                     │
   │   - Serves mock HTML form with input fields            │
   │   - Receives applicant details & PDF resume file       │
   │   - Stores submission in memory for validation         │
   └────────────────────────────────────────────────────────┘
```

### 5.1 Mock ATS Server Implementation (FastAPI)
The mock ATS runs locally (e.g. `http://localhost:5050`):

```python
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse
import uvicorn
import threading

ats_app = FastAPI()
received_submissions = []

@ats_app.get("/apply-form", response_class=HTMLResponse)
def get_apply_form():
    return """
    <html>
        <form action="/submit" method="post" enctype="multipart/form-data">
            <input type="text" name="name" id="name_field" required />
            <input type="email" name="email" id="email_field" required />
            <input type="file" name="resume" id="resume_upload" required />
            <button type="submit" id="submit_btn">Apply</button>
        </form>
    </html>
    """

@ats_app.post("/submit")
def submit_form(
    name: str = Form(...),
    email: str = Form(...),
    resume: UploadFile = File(...)
):
    resume_content = resume.file.read()
    submission = {
        "name": name,
        "email": email,
        "filename": resume.filename,
        "file_size": len(resume_content)
    }
    received_submissions.append(submission)
    return {"status": "success", "message": "Application received"}

@ats_app.get("/test/submissions")
def get_submissions():
    return {"submissions": received_submissions}

@ats_app.post("/test/reset")
def reset_submissions():
    received_submissions.clear()
    return {"status": "reset"}
```

### 5.2 Assertions in the E2E Test Suite
The test runner triggers `auto_apply.py`, then performs a GET request to the Mock ATS Server's administration endpoint:
```python
def test_auto_apply_submission():
    # 1. Clear previous submissions
    requests.post("http://localhost:5050/test/reset")
    
    # 2. Run auto apply engine targeting the mock form URL
    run_auto_apply_job(mock_job_with_url="http://localhost:5050/apply-form")
    
    # 3. Verify Mock ATS received the application
    response = requests.get("http://localhost:5050/test/submissions").json()
    submissions = response["submissions"]
    
    assert len(submissions) == 1
    assert submissions[0]["name"] == "Candidate Name"
    assert submissions[0]["email"] == "candidate@email.com"
    assert submissions[0]["filename"] == "temp_curriculo.pdf"
    assert submissions[0]["file_size"] > 0
```
