# Codebase Audit Handoff Report

## 1. Observation
Below are the exact file paths, line numbers, and verbatim code observed during the audit of the `vagas_bot` codebase.

### R1: Unused/Obsolete Files and Code
- **Catho Scraper**: `scrapers/catho.py` (lines 1-61) is present in the repository but is not referenced in the keys of `user_settings["platforms"]` in `bot.py` (lines 49-63). It is never imported dynamically or statically in production flows.
- **Gupy Scraper**: `scrapers/gupy.py` (lines 1-62) is present in the repository but is not configured in `user_settings["platforms"]` in `bot.py` (lines 49-63) and is not imported in production flows.
- **Trampos Scraper**: `scrapers/trampos.py` (lines 1-64) is present in the repository but is not configured in `user_settings["platforms"]` in `bot.py` (lines 49-63) and is not imported in production flows.
- **Unused Imports in `bot.py`**:
  - `import sqlite3` (line 2): Imported but never used in the script.
  - `import random` (line 3): Imported but never used in the script.
- **Duplicate Imports in `bot.py`**:
  - `import scrapers.ai_filter as ai_filter` is imported twice at line 267 and line 268:
    ```python
    267:     import scrapers.ai_filter as ai_filter
    268:     import scrapers.ai_filter as ai_filter
    ```
  - `import os` is imported at line 266, which duplicates the top-level import at line 14:
    ```python
    14: import os
    ```
- **Inline Testing Mocks (Code Pollution)**:
  - `scrapers/glassdoor.py` contains `_patch_mock_page_if_needed(page)` at lines 10-57, which injects runtime mocks on Playwright's Page class during normal operation.
  - `scrapers/infojobs.py` contains `_patch_mock_page_if_needed(page)` at lines 17-64, which also injects runtime mocks.

### R2: Stability Bugs and Crash Vectors
- **Omission of Callback Query Answers in `bot.py`**:
  - Callback query handlers in `bot.py` do not call `await callback.answer()`.
  - Example (lines 71-74):
    ```python
    @dp.callback_query(F.data == "main_menu")
    async def callback_main_menu(callback: CallbackQuery):
        markup = get_main_menu_markup()
        await callback.message.edit_text("🤖 *Sniper Bot Nativo 100% Operante*\n\nO que você deseja fazer?", reply_markup=markup, parse_mode="Markdown")
    ```
- **Global Settings Multi-User Hazard in `bot.py`**:
  - The dictionary `user_settings` is defined as a global variable at lines 43-65. It is updated globally inside event handlers:
    ```python
    120:     user_settings["level"] = levels[(idx + 1) % len(levels)]
    ```
- **PDF Resume Upload Race Condition & Data Leakage in `bot.py`**:
  - PDF uploads are downloaded to a static filename at lines 462-463:
    ```python
    462:     file_path = "temp_curriculo.pdf"
    463:     await bot.download_file(file.file_path, file_path)
    ```
  - The extracted text is then written to a static filename at line 473:
    ```python
    473:         with open("curriculo.txt", "w", encoding="utf-8") as f:
    ```
- **Headless Gmail OAuth Blocking Flow in `scrapers/gmail.py`**:
  - If credentials or token files are invalid or expired, the scraper attempts to run a local web server for authorization at line 29:
    ```python
    29:             creds = flow.run_local_server(port=0)
    ```
- **Missing Dependencies for Scrapers (lxml Crash Risk)**:
  - `scrapers/workana.py` (lines 19, 35, 44) and `scrapers/remotar.py` (line 18) instantiate `BeautifulSoup` with `'lxml'`:
    ```python
    19:             soup = BeautifulSoup(r.text, 'lxml')
    ```
  - However, `requirements.txt` (lines 1-13) does not list `lxml`.
- **FastAPI Sync Blocking Calls inside Async Endpoints in `app.py`**:
  - The `/api/trigger` endpoint (lines 57-86) is an `async def` but executes synchronous scraper and database calls directly on the main event loop thread:
    ```python
    73:             jobs = module.scrape(keyword=keyword, level=level)
    ...
    80:         inserted = insert_jobs(all_jobs)
    ```
- **Launcher Fails to Start FastAPI in `launcher.py`**:
  - `launcher.py` only starts `bot.py` (lines 12-14) and does not launch `app.py`:
    ```python
    12:     bot_process = subprocess.Popen(
    13:         [sys.executable, "bot.py"]
    14:     )
    ```

### R3: Performance and Architecture Improvements
- **RapidAPI JSearch and Jooble Location/Country Mismatch**:
  - `scrapers/jsearch.py` (line 13) and `scrapers/jooble.py` (line 20) check `country == "Brasil"`:
    ```python
    13:         if country == "Brasil":
    ```
  - However, in `bot.py`, the location parameter is passed as `"Brasil (Remoto)"` (line 236):
    ```python
    236:                         return await asyncio.to_thread(module.scrape, keyword=keyword, level=user_settings["level"], country=user_settings["location"])
    ```
- **Empty API Keys Handling in `scrapers/ai_filter.py`**:
  - The API keys list is constructed directly from environment variables without filtering at lines 10-14:
    ```python
    10: API_KEYS = [
    11:     os.environ.get("GROQ_API_KEY_1", ""),
    12:     os.environ.get("GROQ_API_KEY_2", ""),
    13:     os.environ.get("GROQ_API_KEY_3", "")
    14: ]
    ```
  - An empty API key chosen by `random.choice(API_KEYS)` causes immediate API errors.
- **Groq API Rate Limiting and Linear Back-Off**:
  - On receiving 429 rate limit exceptions, `scrapers/ai_filter.py` uses linear back-off retry logic at line 197:
    ```python
    197:                     await asyncio.sleep(2 + tentativa)
    ```
- **Auto-Apply Production vs. Mock Testing Discrepancy**:
  - `tests/test_tier1.py` imports `auto_apply` (line 36) but falls back to `tests.mock_auto_apply` if `import auto_apply` fails.
  - The functions `apply_to_job` and `run_auto_apply` (tested extensively) only exist in the test mock file `tests/mock_auto_apply.py` and are missing from `scrapers/auto_apply.py`.

---

## 2. Logic Chain
1. **Unused Scrapers**: `scrapers/catho.py`, `scrapers/gupy.py`, and `scrapers/trampos.py` are never listed in the platforms menu or settings, nor are they imported by `bot.py` or `app.py`. Therefore, they constitute dead code files that can be deleted to clean up the codebase.
2. **Spinner Timeout**: Telegram's Bot API expects a callback query response to clear the loading spinner on the interface. Omiting `callback.answer()` results in a persistent spinner, which triggers UI lags and client connection overhead. Adding `await callback.answer()` resolves this.
3. **Global Settings Bug**: In python, referencing a mutable global dictionary `user_settings` across multiple concurrent event handlers means settings changed by one Telegram user will overwrite the settings for all users. This makes the bot completely unusable in a multi-user environment. Refactoring it to map settings per `chat_id` / `user_id` resolves this.
4. **PDF Upload Concurrency Bug**: Downloading the uploaded file to `"temp_curriculo.pdf"` and writing the text to `"curriculo.txt"` uses the same files for every user. If two users upload documents concurrently, they overwrite each other's files, leading to a race condition and data leakage (User A getting User B's AI analysis and resume). Creating unique filenames based on the user's ID resolves this.
5. **Headless OAuth Hang**: `InstalledAppFlow.from_client_secrets_file` launches a local web server to capture OAuth redirect tokens. In a headless hosting service (e.g. Render, Docker containers), a browser cannot open, causing the execution to hang indefinitely. Failing fast with a descriptive log prevents thread blockages.
6. **lxml Missing Dependency**: Beautiful Soup throws a `FeatureNotFound` exception if `'lxml'` is requested as the parser but the `lxml` package is not installed. Since `lxml` is missing from `requirements.txt`, running workana or remotar scrapers will crash on systems without `lxml`. Switching to the built-in `'html.parser'` fixes this.
7. **FastAPI Thread Blocking**: By running sync Playwright browser launches and sync SQLite writes directly on the main event loop thread of FastAPI, the main thread is blocked. Wrapping these calls in `asyncio.to_thread` shifts execution to a worker thread, keeping the event loop responsive.
8. **JSearch/Jooble Global Mismatch**: Since `country` is passed as `"Brasil (Remoto)"` (the default user location), checks like `country == "Brasil"` evaluate to `False`, forcing the scrapers to execute global searches (returning gringo jobs that get discarded, yielding 0 results). Checking if `"Brasil" in country` fixes the routing.
9. **Groq Empty API Key Choice**: If the user has only configured `GROQ_API_KEY_1`, the second and third entries in `API_KEYS` will be `""`. The call `random.choice(API_KEYS)` will choose `""` 66% of the time, immediately crashing or returning authorization errors. Filtering empty strings resolves this.

---

## 3. Caveats
- **Apify Token**: The `meta_ads.py` scraper relies on `APIFY_API_TOKEN` to run. If this is not set, the meta ads scraper will return `[]`. The audit assumes this is expected behavior for users who don't configure Apify.
- **Indeed Web Scraping Robustness**: Scraping Indeed depends on CSS selectors like `[data-testid='jobDescriptionText']`. These selectors change frequently and may need updates over time.

---

## 4. Conclusion
The codebase contains critical architectural flaws (shared global settings, PDF concurrency hazards), performance bottlenecks (sync blocking code in FastAPI, JSearch/Jooble country mismatch), and code pollution (embedded test patches, unused scrapers, missing dependencies). Implementing the proposed fixes will yield a production-ready, stable, and highly performant job hunter bot.

---

## 5. Verification Method
1. **Executing the Test Suite**: Run `python run_tests.py` to confirm that the existing E2E and sanity battery tests pass successfully.
2. **Post-Implementation Test Cases**:
   - Concurrently trigger `/api/trigger` using curl from two terminals to verify that FastAPI handles requests concurrently without blocking.
   - Run the Telegram bot, send `/start` from two different accounts, and verify that changing configurations (e.g. Location or Level) in one account does not affect the other.
   - Concurrently send two different PDF resumes to the Telegram bot and verify that the correct keywords and professions are extracted for each user without data leakage.
