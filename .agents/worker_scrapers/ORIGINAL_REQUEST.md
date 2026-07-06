## 2026-07-04T13:44:22Z

Implement Milestone 2: S-Tier Scrapers & Snippet Bypass in vagas_bot.
Your working directory is: C:\Users\99196\OneDrive\Documentos\vagas_bot\.agents\worker_scrapers

You must complete the following implementation tasks:
1. **LinkedIn Scraper Rewrite** (`scrapers/linkedin.py`):
   - Rewrite to extract `job_id` from search cards.
   - Fetch full description using guest API: `https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}`.
   - Parse and extract full description text from container classes (e.g., `show-more-less-html__markup` or `description__text`).
   - Filter for full-time jobs only. Check for "Tempo integral" or "Full-time" (or case-insensitive variations) in job criteria (employment type span) or description.
   - Ensure the description text has >= 500 characters.
   - Return at least 10 valid jobs. Increment `start` offset page searches (e.g., 0, 25, 50, 75, 100, 125) until at least 10 valid jobs are obtained or max pages reached.
   - Signature must be: `def scrape(keyword, level="Todos", country="Brasil")`.

2. **Glassdoor Scraper Implementation** (`scrapers/glassdoor.py`):
   - Create the scraper using Playwright Chromium in stealth mode (`playwright-stealth`).
   - Use search URL: `https://www.glassdoor.com.br/Job/jobs.htm?sc.keyword={encoded_keyword}`.
   - Click each card to load the details pane, and extract description text from `[data-test="jobDescription"]`, `div.jobDescriptionContent`, or similar.
   - Signature: `def scrape(keyword, level="Todos", country="Brasil")`.

3. **Infojobs Scraper Implementation** (`scrapers/infojobs.py`):
   - Create the scraper using Playwright Chromium in stealth mode to navigate the search page `https://www.infojobs.com.br/vagas-de-emprego.aspx?palavra={encoded_keyword}`.
   - For each card, extract job detail link and fetch full description. Use `curl_cffi` (impersonate chrome) to fetch the details page HTML and extract from `div.description`, `div.vaga-desc`, or similar. If `curl_cffi` is blocked, fallback to navigating detail page with Playwright.
   - Signature: `def scrape(keyword, level="Todos", country="Brasil")`.

4. **Indeed Scraper Rewrite** (`scrapers/indeed.py`):
   - Rewrite to fetch full description page for each job card using `curl_cffi` at `https://br.indeed.com/viewjob?jk={jobkey}`.
   - If blocked by Cloudflare, fallback to opening a new page context in Playwright to fetch and extract `#jobDescriptionText`.
   - Signature: `def scrape(keyword, level="Todos", country="Brasil")`.

5. **Jooble Scraper Rewrite** (`scrapers/jooble.py`):
   - Rewrite to follow the redirect link of each job using `requests` or `curl_cffi` with `allow_redirects=True`.
   - Inspect final destination URL. If it redirects to Jooble itself, Gupy, Indeed, etc., use their specific description selectors. Provide a robust generic fallback text extractor.
   - Signature: `def scrape(keyword, level="Todos", country="Brasil")`.

6. **Integrate with `bot.py`**:
   - Add "glassdoor" and "infojobs" under `user_settings["platforms"]` (enabled by default) and ensure they are processed correctly in `bot.py` (specifically check if they need the `country` parameter inside `bot.py`'s search loop).

7. **Create verification test script** (`scrapers/run_test.py`):
   - Write a script that imports and runs each scraper for a query (e.g. keyword="Python", level="Todos", country="Brasil") and asserts that the returned results match the interface contracts (dictionary keys, description length, etc.).
   - Execute the test script using python and document the output in your handoff.

**MANDATORY INTEGRITY WARNING**:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Document your changes and run verification, then write handoff.md with output.
