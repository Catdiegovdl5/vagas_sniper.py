## 2026-07-06T18:41:27Z

You are the Codebase Auditor (archetype: teamwork_preview_explorer).
Your working directory is: C:\Users\99196\OneDrive\Documentos\vagas_bot\.agents\explorer_audit_1

Task:
Perform a comprehensive audit of the entire vagas_bot codebase (root Python files: bot.py, app.py, database.py, launcher.py, render_bot.py; all scrapers in scrapers/; all tests in tests/) to identify cleanup, stability, and performance optimization opportunities.

Specifically address:
1. R1: Aggressive Codebase Audit and Cleanup:
- Identify all dead code, unused imports, or unused files. Check which scrapers in `scrapers/` are actually used/imported, and which ones are dead/obsolete.
- Locate inefficient or overly complex logic.
2. R2: Bug Fixing and Stability:
- Identify potential unhandled exceptions, edge cases, or logical errors that could crash the Telegram bot (bot.py) or the FastAPI web server (app.py).
3. R3: Performance and Architecture Improvements:
- Find performance bottlenecks (e.g. sync blocking calls in async code, DB connection locks).
- Analyze the Groq AI API rate-limiting strategy (in scrapers/ai_filter.py) and propose optimizations/back-off retry handling.
- Suggest ways to improve scraper reliability.

Output:
Write a detailed report to your handoff file: C:\Users\99196\OneDrive\Documentos\vagas_bot\.agents\explorer_audit_1\handoff.md. Your report must include:
- A list of unused/obsolete files that should be deleted.
- A list of unused imports and dead code sections to remove from each file.
- Specific stability bugs or potential crash vectors with proposed fixes.
- Specific performance/architectural optimizations (especially Groq API rate-limiting and async handling) with proposed designs.

Coordinate your findings clearly so the subsequent Worker can implement them. Follow all constraints. Do not write or execute any code yourself. Once done, write progress.md and handoff.md, then send a message back to me (the Project Orchestrator) with the recipient ID 97bd06a1-244c-4528-bfca-f3f7f2a78259.
