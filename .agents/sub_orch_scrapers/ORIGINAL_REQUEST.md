# Original User Request

## Initial Request — 2026-07-04T10:36:16-03:00

You are the Scrapers Implementation Track Orchestrator.
Your working directory is: C:\Users\99196\OneDrive\Documentos\vagas_bot\.agents\sub_orch_scrapers
Your parent is orchestrator (conv ID: parent).

**Objective**:
Implement S-Tier scrapers and Snippet Bypass (Milestone 2 in `PROJECT.md`).
You must:
1. Rewrite `scrapers/linkedin.py` to:
   - Retrieve the full job description text from `https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}`.
   - Filter for full-time jobs only, ignoring others.
   - Ensure the description text has at least 500 characters and return at least 10 valid jobs.
2. Implement `scrapers/glassdoor.py` to:
   - Perform search using Playwright (stealth mode suggested to bypass Cloudflare).
   - Retrieve the full vacancy description text.
3. Implement `scrapers/infojobs.py` to:
   - Extract full vacancy text using `curl_cffi` to mimic standard TLS fingerprinted browser behavior or Playwright.
4. Rewrite/Optimize `scrapers/indeed.py` to:
   - Navigate to each job detail page `https://br.indeed.com/viewjob?jk={jobkey}` and extract full description text in the DOM rather than returning the snippet.
5. Rewrite/Optimize `scrapers/jooble.py` to:
   - Follow the redirect link to the original job listing and extract the full description text instead of a 150-char snippet.
6. Verify your implementation by spawning Workers, Reviewers, Challengers, and Forensic Auditors. Ensure all builds and tests pass, and the Forensic Auditor gives a CLEAN verdict.
7. Report completion to parent.

**MANDATORY INTEGRITY WARNING**:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

**Scope boundaries**:
- You must write only to your own metadata directory `C:\Users\99196\OneDrive\Documentos\vagas_bot\.agents\sub_orch_scrapers`.
- Implement product files inside the `scrapers/` directory of the workspace.
