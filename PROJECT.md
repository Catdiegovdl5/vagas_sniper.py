# Project: vagas_bot Autonomous Recruitment

## Architecture
- **Data Flow**:
  - Scrapers (`scrapers/linkedin.py`, `scrapers/glassdoor.py`, `scrapers/infojobs.py`, `scrapers/indeed.py`, `scrapers/jooble.py`) search and retrieve raw vacancies.
  - Deep scraping retrieves the full description from Indeed/Jooble.
  - Groq AI Filter (`scrapers/ai_filter.py`) evaluates and scores vacancies, generating `JobEvaluation` objects (score, salary, benefits, etc.).
  - Database (`database.py`) inserts the filtered jobs along with their AI scores and application status.
  - FastAPI Web App (`app.py`) displays the database content on a dashboard, allowing users to trigger runs, which must execute the AI filtering pipeline.
  - Auto-Apply module (`auto_apply.py`) polls pending jobs with high matching scores, fills Easy Apply forms, uploads `temp_curriculo.pdf`, and submits applications.
- **Code Layout**:
  - `database.py`: DB schema and helpers (SQLAlchemy/SQLite).
  - `bot.py`: Telegram Bot flow.
  - `app.py`: FastAPI Web App backend and endpoints.
  - `scrapers/`: Directory for all scrapers.
  - `auto_apply.py`: Core logic for form detection, input filling, resume uploading, and form submission.
  - `test_apply.py`: Mock ATS server and automated submission test case.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | E2E Testing Track | Design E2E test infrastructure, feature inventory, Tier 1-4 tests, publish `TEST_READY.md` | none | DONE |
| 2 | S-Tier Scrapers & Snippet Bypass | Implement S-Tier scrapers (LinkedIn, Glassdoor, InfoJobs) and Deep Scraping (Indeed, Jooble) | none | IN_PROGRESS (Conv: e02a576f-5864-4b55-bf93-7ec0017e77ec) |
| 3 | DB Schema & AI Ranking Update | Perform DB migrations, update Groq prompts/scores, update FastAPI trigger to filter jobs | M2 | PLANNED |
| 4 | Auto-Apply Engine & Mock ATS | Implement form autofill, resume upload, and mock server tests (`test_apply.py`) | M3 | PLANNED |
| 5 | final_milestone | Pass all E2E test tiers and perform Adversarial Coverage Hardening | M1, M4 | PLANNED |

## Interface Contracts
### `scrapers/*` ↔ `database.py`
- Scrapers return lists of dicts conforming to standard schema:
  - `title`, `company`, `budget` (salary string/float), `link`, `platform`, `requirements` (full vacancy text, >=500 chars).
- `database.py` provides:
  - `insert_jobs(jobs: List[dict])`: Stores jobs, checking for duplicates using `link`.
  - `update_apply_status(job_id: str, status: str)`: Updates application state.

### `scrapers/ai_filter.py` ↔ `database.py` / `bot.py` / `app.py`
- `ai_filter.py` provides `score_job_match(requirements: str, title: str, company: str, curriculo: str) -> JobEvaluation`.
- `JobEvaluation` attributes:
  - `aprovado: bool`, `score: int` (0-100), `salario_extraido: float`, `justificativa_curta: str`, `reqs: str`, `bonus: str`, `benefits: str`, `model: str`.
