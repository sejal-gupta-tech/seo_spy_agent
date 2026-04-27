# SEO Spy Agent

FastAPI service for SEO analysis, report generation, and AI-assisted fix suggestions.

## Requirements

- Python 3.11+ available on `PATH`
- Optional: `OPENAI_API_KEY` in `.env` for full AI-backed analysis

## Run The Project

The root runner handles:

- OS detection for macOS, Linux, and Windows
- `venv` / `.venv` reuse
- virtual environment creation when missing
- dependency install only when `requirements.txt` changed or packages are missing
- local smoke checks before startup

### macOS / Linux

```bash
./run.sh
```

### Windows

```bat
run.bat
```

### Direct Python

```bash
python3 run_project.py
```

## Verification Commands

Check the environment and smoke tests without starting the API server:

```bash
./run.sh --check-only
```

Run a full live analysis check against a public site:

```bash
./run.sh --check-only --live-url https://books.toscrape.com/
```

Start the server on a custom port:

```bash
./run.sh --host 127.0.0.1 --port 8001
```

## Frontend

A Next.js frontend now lives in [frontend/README.md](/Users/upendra/Documents/GitHub/seo_spy_agent/frontend/README.md).

Start both frontend and backend together from the repo root:

```bash
./run.sh
```

The launcher:
- starts the frontend on `127.0.0.1:3000`
- waits until `/` returns `200`
- retries once after clearing `frontend/.next` if the Next dev cache is stale
- skips frontend startup automatically when you use `--check-only`

If you want to run the services separately, start the FastAPI backend first:

```bash
./run.sh --host 127.0.0.1 --port 8010
```

Then start the frontend:

```bash
cd frontend
cp .env.local.example .env.local
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Set this in `frontend/.env.local` only if the backend is not on one of the common local ports:

```bash
BACKEND_API_URL=http://127.0.0.1:8010
```

## API Endpoints

- `POST /analyze-url`
- `POST /analyze-url/stream`
- `POST /generate-fix`
- `GET /download-report/{task_id}`

## Notes

- If `OPENAI_API_KEY` is missing, the app still starts and falls back to non-AI defaults where supported.
- Reports are written to the `reports/` directory.
- The Next.js frontend proxies API calls through its own route handlers, so the browser does not call the Python API directly.

## MongoDB Data Storage Design

The SEO Spy Agent uses MongoDB to store audit results in a structured, modular, and scalable way. Instead of storing one large JSON document, the system splits data across specialized collections for efficient querying and market analysis.

### Collections

1.  **`projects`**: Main metadata and high-level scoring.
    *   `url`: The audited website URL.
    *   `business_type`: Categorization (e.g., `real_estate`, `ecommerce`).
    *   `seo_score`: Numeric technical health score (0-100).
    *   `report_url`: Link to the generated PDF.

2.  **`audit_results`**: Technical SEO metrics and detailed findings.
    *   `metric_summary`: Pass/Fail status for core SEO signals.
    *   `findings`: Comprehensive list of issues, recommendations, and evidence.

3.  **`ai_insights`**: AI-generated strategic content.
    *   `executive_summary`: High-level narrative for stakeholders.
    *   `management_summary`: Board-ready verdict and risk/opportunity analysis.
    *   `recommended_roadmap`: Actionable steps for improvement.

4.  **`seo_data`**: Competitive intelligence and keyword analysis.
    *   `competitive_intelligence`: Market overlap, content gaps, and opportunities.

5.  **`crawl_data`**: Page-level technical details.
    *   `pages`: Array of specific page metrics (SEO health, link counts, critical issues).

### Relationship Design

All collections are linked via a `project_id` (the `ObjectId` of the main document in the `projects` collection). This modular design allows for:
*   **Scalability**: Optimized storage and memory usage.
*   **Modular Queries**: Fetch only technical health or only AI insights based on the UI view.
*   **Business Intelligence**: Fast filtering by `business_type` across the entire dataset.
