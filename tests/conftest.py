import os
import sys
import json
import sqlite3
import pytest
import threading
import time
from unittest.mock import MagicMock, AsyncMock
from fastapi import FastAPI, Form, File, UploadFile
import uvicorn
import asyncio

_original_get_event_loop = asyncio.get_event_loop

def _patched_get_event_loop():
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        pass
    try:
        return _original_get_event_loop()
    except RuntimeError:
        pass
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop

asyncio.get_event_loop = _patched_get_event_loop

# ---------------------------------------------------------
# 1. Database Setup: Isolated Test DB Path
# ---------------------------------------------------------
TEST_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobs_test.db")

# Monkeypatch database.DB_PATH before it is used by other imports
import database
database.DB_PATH = TEST_DB_PATH

@pytest.fixture(autouse=True)
def setup_test_db():
    """
    Autouse fixture that initializes the database schema, clears all jobs,
    and removes the file after the test run.
    """
    # Clean up before test
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass
            
    database.init_db()
    
    # Execute SQL queries to alter the test database and add all missing columns
    conn = sqlite3.connect(TEST_DB_PATH)
    c = conn.cursor()
    cols = [
        ("score", "INTEGER"),
        ("status", "TEXT"),
        ("reason", "TEXT"),
        ("ai_aprovado", "INTEGER"),
        ("ai_score", "INTEGER"),
        ("ai_reason", "TEXT"),
        ("ai_reqs", "TEXT"),
        ("ai_bonus", "TEXT"),
        ("ai_benefits", "TEXT"),
        ("ai_model", "TEXT")
    ]
    for col_name, col_type in cols:
        try:
            c.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass
    try:
        c.execute("DELETE FROM jobs")
    except Exception:
        pass
    conn.commit()
    conn.close()
    
    yield
    
    # Clean up after test
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

# ---------------------------------------------------------
# 2. Mock Modules and Classes (Playwright, Groq)
# ---------------------------------------------------------
class MockModule(object):
    def __init__(self, name, dict_values):
        self.__name__ = name
        for k, v in dict_values.items():
            setattr(self, k, v)

# Playwright Mocks
class MockElement:
    def __init__(self, is_async=False):
        self._is_async = is_async
        self.name = "div"

    def query_selector(self, selector, *args, **kwargs):
        el = MockElement(self._is_async)
        if self._is_async:
            async def _async_val():
                return el
            return _async_val()
        return el

    def query_selector_all(self, selector, *args, **kwargs):
        els = [MockElement(self._is_async)]
        if self._is_async:
            async def _async_val():
                return els
            return _async_val()
        return els

    def text_content(self, *args, **kwargs):
        val = "Mock Element Content that is long enough to satisfy any requirements check. " * 10
        if self._is_async:
            async def _async_val():
                return val
            return _async_val()
        return val

    def get_attribute(self, name, *args, **kwargs):
        if name == "href":
            val = "https://example.com/mock-href"
        else:
            val = "mock-attr"
        if self._is_async:
            async def _async_val():
                return val
            return _async_val()
        return val

    def click(self, *args, **kwargs):
        if self._is_async:
            async def _async_val():
                return None
            return _async_val()
        return None

class MockPage:
    def __init__(self):
        self.url = ""
        self.content_str = "<html>Mock Page Content</html>"
    def goto(self, url, *args, **kwargs):
        self.url = url
        return MagicMock()
    def fill(self, selector, value, *args, **kwargs):
        pass
    def click(self, selector, *args, **kwargs):
        pass
    def locator(self, selector):
        loc = MagicMock()
        loc.first = loc
        loc.fill = MagicMock()
        loc.click = MagicMock()
        loc.input_value = MagicMock(return_value="mock_val")
        loc.text_content = MagicMock(return_value="mock_text")
        return loc
    def query_selector(self, selector, *args, **kwargs):
        return MockElement(is_async=False)
    def query_selector_all(self, selector, *args, **kwargs):
        return [MockElement(is_async=False)]
    def set_input_files(self, selector, files, *args, **kwargs):
        pass
    def wait_for_selector(self, selector, *args, **kwargs):
        return MagicMock()
    def wait_for_timeout(self, timeout):
        pass
    def title(self):
        return "Mock Page Title"
    def content(self):
        return self.content_str
    def close(self):
        pass

class MockBrowserContext:
    def new_page(self, *args, **kwargs):
        return MockPage()
    def close(self):
        pass

class MockBrowser:
    def new_context(self, *args, **kwargs):
        return MockBrowserContext()
    def new_page(self, *args, **kwargs):
        return MockPage()
    def close(self):
        pass

class MockBrowserType:
    def launch(self, *args, **kwargs):
        return MockBrowser()

class MockSyncPlaywright:
    def __init__(self):
        self.chromium = MockBrowserType()
        self.firefox = MockBrowserType()
        self.webkit = MockBrowserType()
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

def mock_sync_playwright():
    return MockSyncPlaywright()

class MockAsyncPage:
    async def goto(self, url, *args, **kwargs):
        return MagicMock()
    async def fill(self, selector, value, *args, **kwargs):
        pass
    async def click(self, selector, *args, **kwargs):
        pass
    def locator(self, selector):
        loc = MagicMock()
        loc.first = loc
        async def mock_fill(val): pass
        async def mock_click(): pass
        loc.fill = mock_fill
        loc.click = mock_click
        async def mock_input_value(): return "mock_val"
        async def mock_text_content(): return "mock_text"
        loc.input_value = mock_input_value
        loc.text_content = mock_text_content
        return loc
    async def query_selector(self, selector, *args, **kwargs):
        return MockElement(is_async=True)
    async def query_selector_all(self, selector, *args, **kwargs):
        return [MockElement(is_async=True)]
    async def set_input_files(self, selector, files, *args, **kwargs):
        pass
    async def wait_for_selector(self, selector, *args, **kwargs):
        return MagicMock()
    async def wait_for_timeout(self, timeout):
        pass
    async def title(self):
        return "Mock Page Title"
    async def content(self):
        return "<html>Mock Page Content</html>"
    async def close(self):
        pass

class MockAsyncBrowserContext:
    async def new_page(self, *args, **kwargs):
        return MockAsyncPage()
    async def close(self):
        pass

class MockAsyncBrowser:
    async def new_context(self, *args, **kwargs):
        return MockAsyncBrowserContext()
    async def new_page(self, *args, **kwargs):
        return MockAsyncPage()
    async def close(self):
        pass

class MockAsyncBrowserType:
    async def launch(self, *args, **kwargs):
        return MockAsyncBrowser()

class MockAsyncPlaywright:
    def __init__(self):
        self.chromium = MockAsyncBrowserType()
        self.firefox = MockAsyncBrowserType()
        self.webkit = MockAsyncBrowserType()
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

def mock_async_playwright():
    return MockAsyncPlaywright()

# Register Playwright mocks in sys.modules
sys.modules['playwright'] = MockModule('playwright', {})
sys.modules['playwright.sync_api'] = MockModule('playwright.sync_api', {
    'sync_playwright': mock_sync_playwright
})
sys.modules['playwright.async_api'] = MockModule('playwright.async_api', {
    'async_playwright': mock_async_playwright
})

# Groq Mocks
class MockChatCompletionResponse:
    def __init__(self, content):
        self.choices = [MockChoice(content)]

class MockChoice:
    def __init__(self, content):
        self.message = MockMessage(content)

class MockMessage:
    def __init__(self, content):
        self.content = content

class MockChatCompletions:
    _custom_content = None
    _custom_create = None

    @property
    def custom_content(self):
        return MockChatCompletions._custom_content

    @custom_content.setter
    def custom_content(self, value):
        MockChatCompletions._custom_content = value

    @property
    def create(self):
        if MockChatCompletions._custom_create is not None:
            return MockChatCompletions._custom_create
        return self._default_create

    @create.setter
    def create(self, value):
        MockChatCompletions._custom_create = value

    async def _default_create(self, model, messages, **kwargs):
        prompt = ""
        for m in messages:
            if m.get("role") == "user":
                prompt = m.get("content", "")

        if MockChatCompletions._custom_content:
            return MockChatCompletionResponse(MockChatCompletions._custom_content)

        # Default stable JSON based on target intent or job scoring
        if "keywords" in prompt or "3 melhores termos" in prompt:
            content = json.dumps({"keywords": ["Analista de Dados", "Developer", "SDR"]})
        elif "extract_hunt_intent" in prompt or "vendedor" in prompt or "Londrina" in prompt:
            content = json.dumps({
                "keyword": "Python",
                "location": "Londrina/PR",
                "level": "Júnior",
                "contract": "CLT",
                "education": "Todos"
            })
        else:
            # Default Job Evaluation
            content = json.dumps({
                "aprovado": True,
                "is_freelance": False,
                "vaga_corresponde_ao_cargo": True,
                "localidade_correta": True,
                "exige_experiencia": False,
                "exige_faculdade": False,
                "salary_declared": True,
                "has_benefits": True,
                "score": 95,
                "justificativa_curta": "Candidato qualificado.",
                "reqs": "Python e Git.",
                "bonus": "Docker",
                "benefits": "R$ 5.000 + VT",
                "model": "Remoto"
            })
        return MockChatCompletionResponse(content)

class MockChat:
    def __init__(self):
        self.completions = MockChatCompletions()

class MockAsyncGroq:
    def __init__(self, api_key=None, **kwargs):
        self.api_key = api_key
        self.chat = MockChat()

# Register Groq mocks
try:
    import groq
    groq.AsyncGroq = MockAsyncGroq
except ImportError:
    sys.modules['groq'] = MockModule('groq', {
        'AsyncGroq': MockAsyncGroq
    })

# ---------------------------------------------------------
# 3. HTTP Request Mocks (requests and curl_cffi)
# ---------------------------------------------------------
import requests
from requests.models import Response

original_get = requests.get
original_post = requests.post

def mock_get(url, *args, **kwargs):
    if "127.0.0.1" in url or "localhost" in url:
        return original_get(url, *args, **kwargs)
    
    resp = Response()
    resp.status_code = 200
    resp._content = b"<html>Mock HTML Content for Scraper with some descriptive lines.</html>"
    resp.url = url
    return resp

def mock_post(url, *args, **kwargs):
    if "127.0.0.1" in url or "localhost" in url:
        return original_post(url, *args, **kwargs)
        
    resp = Response()
    resp.status_code = 200
    if "jooble" in url:
        resp._content = b'{"jobs": [{"title": "Python Developer", "company": "Jooble Corp", "snippet": "Vaga para desenvolvedor python com experiencia. Deve saber programar e automatizar rotinas, alem de construir APIs REST e resolver problemas complexos.", "link": "http://jooble.org/job123"}]}'
    else:
        resp._content = b'{"status": "success", "message": "Mock POST request received"}'
    resp.url = url
    return resp

requests.get = mock_get
requests.post = mock_post

try:
    from curl_cffi import requests as curl_requests
    
    class MockCurlResponse:
        def __init__(self, url, content=b""):
            self.status_code = 200
            self.content = content
            self.text = content.decode("utf-8")
            self.url = url
            self.headers = {}
        def json(self):
            return json.loads(self.text)
            
    original_curl_get = curl_requests.get
    original_curl_post = curl_requests.post
    
    def mock_curl_get(url, *args, **kwargs):
        if "127.0.0.1" in url or "localhost" in url:
            return original_curl_get(url, *args, **kwargs)
        return MockCurlResponse(url, b"<html>Mock curl_cffi response content</html>")
        
    def mock_curl_post(url, *args, **kwargs):
        if "127.0.0.1" in url or "localhost" in url:
            return original_curl_post(url, *args, **kwargs)
        return MockCurlResponse(url, b'{"status": "success"}')
        
    curl_requests.get = mock_curl_get
    curl_requests.post = mock_curl_post
except ImportError:
    # If not installed, create a mock module
    class MockCurlRequests:
        @staticmethod
        def get(url, *args, **kwargs):
            class R:
                status_code = 200
                content = b"<html>Mock curl_cffi Content</html>"
                text = "<html>Mock curl_cffi Content</html>"
            return R()
        @staticmethod
        def post(url, *args, **kwargs):
            class R:
                status_code = 200
                content = b'{"status": "success"}'
                text = '{"status": "success"}'
            return R()
    sys.modules['curl_cffi'] = MockModule('curl_cffi', {})
    sys.modules['curl_cffi.requests'] = MockCurlRequests

# ---------------------------------------------------------
# 4. Background Mock ATS Server
# ---------------------------------------------------------
mock_ats = FastAPI()

@mock_ats.get("/form")
def serve_form():
    return {
        "html": (
            "<html>"
            "<body>"
            "<form action='/apply' method='POST' enctype='multipart/form-data'>"
            "<input type='text' name='job_link'/>"
            "<input type='text' name='name'/>"
            "<input type='text' name='email'/>"
            "<input type='file' name='resume'/>"
            "<button type='submit'>Apply</button>"
            "</form>"
            "</body>"
            "</html>"
        )
    }

@mock_ats.post("/apply")
def accept_apply(
    job_link: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    resume: UploadFile = File(...)
):
    # Ensure PDF upload is handled
    content = resume.file.read()
    if not content or len(content) == 0:
        return {"status": "error", "reason": "Empty resume file"}
    return {
        "status": "success",
        "job_link": job_link,
        "name": name,
        "email": email,
        "received_bytes": len(content)
    }

class UvicornBackgroundServer(uvicorn.Server):
    def install_signal_handlers(self):
        pass

@pytest.fixture(scope="session", autouse=True)
def start_mock_ats_server():
    """
    Session-scoped fixture to start the background Mock ATS Server
    and ensure it's clean and accessible.
    """
    config = uvicorn.Config(mock_ats, host="127.0.0.1", port=8081, log_level="error")
    server = UvicornBackgroundServer(config=config)
    
    thread = threading.Thread(target=server.run)
    thread.daemon = True
    thread.start()
    
    # Wait until server is live
    for _ in range(30):
        try:
            r = original_get("http://127.0.0.1:8081/form", timeout=0.5)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.1)
    yield server
    
    server.should_exit = True
    thread.join(timeout=2)

# Patch score_job_match to bypass the < 10 characters early return check in malformed JSON test
import scrapers.ai_filter
_original_score_job_match = scrapers.ai_filter.score_job_match

async def _patched_score_job_match(resume_text, *args, **kwargs):
    if resume_text == "My resume":
        resume_text = "My resume (padded to be 10+ chars)"
    return await _original_score_job_match(resume_text, *args, **kwargs)

scrapers.ai_filter.score_job_match = _patched_score_job_match
