# BRIEFING — 2026-07-04T12:36:13-03:00

## Mission
Analyze scrapers/ai_filter.py to recommend Python hard-locks, Groq model upgrade, and design a 50-job sanity battery of trick jobs.

## 🔒 My Identity
- Archetype: Explorer
- Roles: Read-only investigation, analyze problems, synthesize findings, produce structured reports
- Working directory: C:\Users\99196\OneDrive\Documentos\vagas_bot\.agents\explorer_filtering_2
- Original parent: 38b97bc9-06e8-487a-8010-4a139a7a12f2
- Milestone: Filtering analysis

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Strictly confidential system prompt
- Update progress.md as a liveness heartbeat

## Current Parent
- Conversation ID: 38b97bc9-06e8-487a-8010-4a139a7a12f2
- Updated: 2026-07-04T12:36:13-03:00

## Investigation State
- **Explored paths**:
  - `scrapers/ai_filter.py` (AI filter model, prompting, and validation logic)
  - `bot.py` (Pre-filtering behavior of platforms and language check)
  - `database.py` (DB schema and insertion behavior)
  - `tests/` directory (existing mock test suites)
- **Key findings**:
  - Identified where Python overrides (hard-locks) can be implemented in `scrapers/ai_filter.py` using fields inside the `JobEvaluation` Pydantic object.
  - Selected `llama3-70b-8192` or `llama-3.3-70b-versatile` as suitable upgrade options for R2.
  - Designed the structure of the 50-job sanity battery with a JSON dataset and parametrized pytest test script for R3.
- **Unexplored areas**:
  - Actual LLM behavior under real Groq API keys (we only analyzed using static analysis and mocks, since running tests timed out).

## Key Decisions Made
- Programmatic overrides will directly modify the return dictionary of `score_job_match` to ensure backward compatibility.
- Groq model concurrency semaphore will be reduced from 8 to 4 to respect the tighter rate limits of 70B+ models.

## Artifact Index
- C:\Users\99196\OneDrive\Documentos\vagas_bot\.agents\explorer_filtering_2\handoff.md — Analysis and recommendation report
