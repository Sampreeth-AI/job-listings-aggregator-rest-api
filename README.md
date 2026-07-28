# Job Listings Aggregator & REST API

A polished Flask job board that aggregates permitted job-board listings, stores them in MySQL (or SQLite for local development), exposes a searchable REST API, and schedules periodic imports with APScheduler.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

The default `.env` uses SQLite. For MySQL, create a database and set:

```env
DATABASE_URL=mysql+pymysql://USER:PASSWORD@localhost/job_aggregator
```

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Service health check |
| GET | `/api/v1/jobs` | List jobs; supports `search`, `location`, `source`, `page`, `per_page` |
| GET | `/api/v1/jobs/<id>` | Get a single listing |
| POST | `/api/v1/jobs` | Add a listing manually |
| DELETE | `/api/v1/jobs/<id>` | Remove a listing |
| POST | `/api/v1/scrape` | Run configured source adapters now |

The web dashboard is available at `http://127.0.0.1:5000/`.

Example:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:5000/api/v1/jobs -ContentType 'application/json' -Body '{"title":"Backend Engineer","company":"Acme","url":"https://example.com/job/1","source":"manual","location":"Remote"}'
```

## Adding a source

In `app/services/scraper.py`, add an `HtmlSource` with the site URL and CSS selectors. The scraper uses BeautifulSoup, ignores incomplete cards, and upserts listings by canonical job URL. Only configure sites whose terms of service and robots policy allow automated access. The `POST /scrape` endpoint should be protected with authentication before public deployment.

## Test

```powershell
python -m unittest discover -s tests
```
