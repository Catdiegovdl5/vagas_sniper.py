# Handoff Report - Discovery Phase

## 1. Observation
- **Database Schema**: In `database.py` (lines 9-27), the `init_db()` function establishes the table schema as follows:
  ```python
  CREATE TABLE IF NOT EXISTS jobs (
      id TEXT PRIMARY KEY,
      title TEXT,
      company TEXT,
      budget TEXT,
      link TEXT,
      platform TEXT,
      added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  )
  ```
  And then appends `job_type`, `profession`, `level`, and `requirements`. No columns exist for storing AI evaluation metadata (`ai_score`, `ai_reason`, `ai_reqs`, etc.).
- **LinkedIn Scraper**: In `scrapers/linkedin.py` (lines 61-62), the requirements field is initialized with a static placeholder text:
  ```python
  "requirements": f"Localização: {location} (Vaga encontrada via LinkedIn Ghost API. Detalhes completos direto na página da vaga)."
  ```
- **Indeed Scraper**: In `scrapers/indeed.py` (lines 35-48), the scraper parses `snippet` from the JSON mosaic provider and uses that as the description:
  ```python
  snippet = r.get("snippet", "")
  ...
  "requirements": f"Local: {location}. Resumo: {clean_snippet}"
  ```
- **Jooble Scraper**: In `scrapers/jooble.py` (lines 38-43), the API snippet is sliced to 150 characters:
  ```python
  desc = item.get("snippet", "")
  ...
  if len(desc) > 150:
      req_text = desc[:150] + "..."
  ```
- **FastAPI Web App Webhook/Trigger Inconsistency**: In `app.py` (lines 69-85), `/api/trigger` executes `scrape()` and inserts directly to the database:
  ```python
  jobs = module.scrape(keyword=keyword, level=level)
  all_jobs.extend(jobs)
  ...
  inserted = insert_jobs(all_jobs)
  ```
  It bypasses the Groq AI filter logic entirely.
- **Candidate CV**: The `curriculo.txt` contains candidate details: "Diego Antônio de Jesus Santos", "Growth Engineer | Arquiteto de Automação IA", residing in Assaí, PR.

## 2. Logic Chain
- **Pillar 1 Requirement**: S-Tier scrapers must pull the full text of vacancies. Currently, `scrapers/linkedin.py` only writes static text to the `requirements` field. To pull the complete text, the scraper must extract the `job_id` from the card URL and query `https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}`.
- **Pillar 2 Requirement**: Indeed and Jooble must extract complete details instead of snippets. Currently, both scrapers extract short snippets directly from listing results. To obtain full details, the scrapers must navigate to the destination link (Indeed via Playwright to parse `#jobDescriptionText`; Jooble via HTTP client/Playwright to parse description tags).
- **Pillar 3 Requirement**: IA Ranking by salary/benefits. The Groq pipeline evaluates jobs and assigns an `ai_score`. Currently, database.py lacks columns to save `ai_score` or AI metadata, meaning the web dashboard cannot show or sort by these values. Therefore, SQLite schema migrations are required, and the FastAPI orchestrator flow must be updated to apply the AI filter, matching the Telegram Bot flow in `bot.py`.
- **Pillar 4 Requirement**: Auto-Apply Engine. We must write a script to locate input fields using generic selectors (e.g., `input[type="email"]`, `input[type="file"]`) and submit them. To verify this, a mock ATS server in `test_apply.py` returning status 200 is sufficient.

## 3. Caveats
- Since this is a read-only investigation, no code execution was performed.
- Assumed that the anonymous guest job API of LinkedIn does not block high-frequency guest detail requests; we may need rate limit delays (e.g., 2-3 seconds) or proxies if blocked.
- InfoJobs and Glassdoor might require Playwright stealth parameters to bypass anti-bot systems (Cloudflare).

## 4. Conclusion
The implementation of the 4 pillars requires:
1. Rewriting `scrapers/linkedin.py` to target the guest details API and filter for full-time jobs.
2. Creating `scrapers/glassdoor.py` and `scrapers/infojobs.py`.
3. Adding a secondary navigation stage in `scrapers/indeed.py` and `scrapers/jooble.py` to retrieve full description DOM elements (Deep Scrape).
4. Migrating the SQLite database to store AI evaluation columns.
5. Updating `app.py` `/api/trigger` to execute the Groq AI filter before inserting into the database.
6. Writing `auto_apply.py` (Playwright-based candidate auto-filler) and `test_apply.py` (FastAPI Mock ATS + Playwright candidate submission test).

## 5. Verification Method
1. Inspect the written report `analysis.md` at `C:\Users\99196\OneDrive\Documentos\vagas_bot\.agents\explorer_discovery\analysis.md`.
2. Verify that all four pillars are fully detailed with specific design structures, selectors, URL endpoints, and schema recommendations.
