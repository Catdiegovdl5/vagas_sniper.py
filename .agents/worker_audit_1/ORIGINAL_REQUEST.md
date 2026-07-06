## 2026-07-06T18:46:57Z
You are the Codebase Cleaner & Optimizer (archetype: teamwork_preview_worker).
Your working directory is: C:\Users\99196\OneDrive\Documentos\vagas_bot\.agents\worker_audit_1

Task:
Implement the cleanup, stability fixes, and performance/architecture optimizations across the vagas_bot codebase based on the Explorer's audit findings.

Specifically, implement the following changes:

1. R1: Aggressive Codebase Audit and Cleanup:
- Delete the unused scraper files: `scrapers/catho.py`, `scrapers/gupy.py`, and `scrapers/trampos.py`.
- Clean up imports in `bot.py`: remove unused imports `sqlite3` and `random` at the top; remove duplicate imports of `os` and `scrapers.ai_filter` at lines 266-268.
- Remove any inline testing mocks/patches from `scrapers/glassdoor.py` and `scrapers/infojobs.py` (e.g. `_patch_mock_page_if_needed(page)`) if they pollute the production files, but ensure that tests still run successfully (check if the test suite depends on them or mocks playwright directly).

2. R2: Bug Fixing and Stability:
- Add `await callback.answer()` to all callback query handlers in `bot.py` to clear the Telegram interface loading spinner.
- Resolve the global settings multi-user hazard in `bot.py`: Refactor the global `user_settings` dictionary to a dictionary `user_settings_db = {}` mapping `chat_id` / `user_id` to their respective settings dictionary. Implement a helper `get_user_settings(chat_id)` that returns or initializes default settings for that chat ID. Update all command and callback handlers to retrieve and update settings for the message/callback query sender's chat ID.
- Resolve the PDF resume upload race condition in `bot.py`: Save uploaded PDF files and write extracted resume text to unique filenames containing the user's ID (e.g. `f"temp_curriculo_{user_id}.pdf"` and `f"curriculo_{user_id}.txt"`), rather than the static `temp_curriculo.pdf` and `curriculo.txt` files, to prevent data leakage and race conditions between concurrent users.
- Resolve headless Gmail OAuth hangs in `scrapers/gmail.py`: If `token.json` is missing or invalid and cannot be refreshed, print a warning and return an empty list `[]` instead of running `flow.run_local_server(port=0)` which hangs indefinitely in headless hosting environments.
- Resolve missing dependency crash risks: In `scrapers/workana.py` and `scrapers/remotar.py`, change the BeautifulSoup parser from `'lxml'` to the Python built-in `'html.parser'`.
- Resolve FastAPI event-loop blockages in `app.py`: In the `/api/trigger` endpoint, wrap all synchronous scraper calls (`module.scrape(...)`) and database insert operations (`insert_jobs(...)`) in `asyncio.to_thread()` to run them on worker threads and keep the FastAPI event loop responsive.
- Fix `launcher.py` to start both `bot.py` and `app.py` (FastAPI web server) as concurrent subprocesses, and terminate both cleanly when the launcher is closed.

3. R3: Performance and Architecture Improvements:
- Fix location/country mismatch: In `scrapers/jsearch.py` and `scrapers/jooble.py`, change the country check from `country == "Brasil"` to `"Brasil" in country` so that the default location `"Brasil (Remoto)"` passed by the bot correctly matches.
- Fix Groq API key handling in `scrapers/ai_filter.py`: Filter out empty strings from the `API_KEYS` list so that `random.choice(API_KEYS)` never selects an empty key and causes API errors. Also, ensure the Groq model parameter is upgraded to `"llama3-70b-8192"` in all chat completion calls.
- Align Auto-Apply structure: Expose the core functions `apply_to_job` and `run_auto_apply` (with the same signatures and functionality as in `tests/mock_auto_apply.py`) inside `auto_apply.py` at the root of the workspace. Delete `scrapers/auto_apply.py` if it is obsolete or redirect it. Ensure that the test suite `tests/test_tier1.py` can import `auto_apply` from the root directory.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Verification:
- Run `python run_tests.py` and verify all tests pass.
- Write your handoff report to `C:\Users\99196\OneDrive\Documentos\vagas_bot\.agents\worker_audit_1\handoff.md`. Include the test execution output and verify that the layout complies with the codebase.
- Once done, send a message back to me (the Project Orchestrator) with the recipient ID 97bd06a1-244c-4528-bfca-f3f7f2a78259.
