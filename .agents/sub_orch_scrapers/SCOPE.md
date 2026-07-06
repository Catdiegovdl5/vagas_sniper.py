# Scope: Milestone 2 — S-Tier Scrapers & Snippet Bypass

## Subtasks
| # | Name | Description | Status | Agent Conv ID |
|---|------|-------------|--------|---------------|
| 1 | LinkedIn Scraper Rewrite | Rewrite `scrapers/linkedin.py` to retrieve job details from guest API `https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}`, filter for full-time jobs, and ensure >=500 chars description for >=10 jobs. | DONE | 8883fae0-92ba-44c8-8998-b47aeed87a98 |
| 2 | Glassdoor Scraper Implementation | Implement `scrapers/glassdoor.py` using Playwright in stealth mode to search and retrieve full descriptions. | DONE | 8883fae0-92ba-44c8-8998-b47aeed87a98 |
| 3 | Infojobs Scraper Implementation | Implement `scrapers/infojobs.py` using `curl_cffi` (or Playwright) to bypass TLS fingerprinting and extract full vacancy text. | DONE | 8883fae0-92ba-44c8-8998-b47aeed87a98 |
| 4 | Indeed Scraper Rewrite/Optimize | Rewrite `scrapers/indeed.py` to navigate to `https://br.indeed.com/viewjob?jk={jobkey}` and extract full description text in the DOM. | DONE | 8883fae0-92ba-44c8-8998-b47aeed87a98 |
| 5 | Jooble Scraper Rewrite/Optimize | Rewrite `scrapers/jooble.py` to follow redirect links to the original job listing and extract the full description text. | DONE | 8883fae0-92ba-44c8-8998-b47aeed87a98 |
| 6 | E2E Verification & Forensic Audit | Verify all scrapers together by running them and performing Forensic Audit verification. | DONE | 411c7d94-5d5d-4126-b249-cbbea50000b8 / b884e5d9-2ef6-4450-8686-60fb87541ab2 / 57181df9-be40-47f7-8b63-cbc2d2e3c1d0 |

## Interface Contracts
- All scrapers return a list of dicts with the following fields:
  - `platform` (str): Platform name (e.g. LinkedIn, Glassdoor, Infojobs, Indeed, Jooble)
  - `title` (str): Job title
  - `company` (str): Company name
  - `budget` (str): Salary/Budget string
  - `link` (str): Clean link to job posting
  - `job_type` (str): Job type (e.g., CLT, PJ, Tempo integral, etc.)
  - `profession` (str): Profession/Keyword searched
  - `level` (str): Level searched (e.g. Todos, Junior, Pleno, Senior)
  - `requirements` (str): Full vacancy description (at least 500 characters where specified/available)
