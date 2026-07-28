## Live Demo

[Open RoleRadar Job Board](https://roleradar-job-board.onrender.com/)


# Job Listings Aggregator & REST API

A polished Flask job board that aggregates permitted job-board listings, stores them in MySQL (or SQLite for local development), exposes a searchable REST API, and imports jobs daily with APScheduler.

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
| GET | `/api/v1/jobs` | List jobs; supports `search`, `location`, `skills`, `source`, `page`, `per_page` |
| GET | `/api/v1/jobs/<id>` | Get a single listing |
| POST | `/api/v1/jobs` | Add a listing manually |
| DELETE | `/api/v1/jobs/<id>` | Remove a listing |
| POST | `/api/v1/scrape` | Run configured source adapters now |

The web dashboard is available at `http://127.0.0.1:5000/`.

Example:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:5000/api/v1/jobs -ContentType 'application/json' -Body '{"title":"Backend Engineer","company":"Acme","url":"https://example.com/job/1","source":"manual","location":"Remote"}'
```

## Sources and daily imports

The project imports three permitted public feeds: We Work Remotely Programming RSS, We Work Remotely Design RSS, and the Remote OK public jobs feed. Listings are deduplicated by canonical job URL and updated when a source changes. BeautifulSoup parses the RSS feeds. The daily job runs at `SCRAPE_HOUR_UTC` (default: 02:00 UTC / 7:30 AM IST). You can import immediately using:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:5000/api/v1/scrape
```

Source terms can change; review them before enabling production scraping. Protect the scrape endpoint with authentication before public deployment.

## Test

```powershell
python -m unittest discover -s tests
```

## Deploy a public demo on Render

1. Push this repository to GitHub.
2. In [Render](https://render.com), choose **New** → **Web Service** and connect the GitHub repository.
3. Use `pip install -r requirements.txt` as the build command and `gunicorn run:app --bind 0.0.0.0:$PORT` as the start command. Render creates a public `onrender.com` URL.

The initial public demo includes three sample roles. Render's free web services use an ephemeral filesystem, so a SQLite database can reset after a restart. For permanent public listings, set `DATABASE_URL` to a managed MySQL database URL in Render's environment variables.
