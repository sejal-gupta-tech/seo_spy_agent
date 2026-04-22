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

## API Endpoints

- `POST /analyze-url`
- `POST /generate-fix`
- `GET /download-report/{task_id}`

## Notes

- If `OPENAI_API_KEY` is missing, the app still starts and falls back to non-AI defaults where supported.
- Reports are written to the `reports/` directory.
