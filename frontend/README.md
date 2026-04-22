# SEO Spy Studio Frontend

Next.js App Router frontend for the SEO Spy Agent backend.

## What It Does

- renders the audit output in a polished report dashboard
- proxies browser requests through Next route handlers
- relays generated PDF downloads
- exposes the AI fix generator from the backend

## Run It

Start the backend in the repo root first:

```bash
./run.sh --host 127.0.0.1 --port 8010
```

Create the frontend env file if you want to pin the backend to a specific URL:

```bash
cp .env.local.example .env.local
```

Set:

```bash
BACKEND_API_URL=http://127.0.0.1:8010
ALLOWED_DEV_ORIGINS=192.168.1.9
```

Then start the frontend:

```bash
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Open `http://127.0.0.1:3000`.

If your LAN IP changes, update `ALLOWED_DEV_ORIGINS` in `.env.local` and restart `npm run dev`.
If `BACKEND_API_URL` is omitted, the frontend probes `127.0.0.1` and `localhost` on ports `8000` and `8010` and uses the first server that exposes the `SEO Spy Agent` OpenAPI schema.

## Useful Commands

```bash
npm run lint
npm run build
```

## Routes

- `/` dashboard UI
- `/api/analyze-url` backend analysis proxy
- `/api/analyze-url/stream` streamed backend analysis proxy for live crawl telemetry
- `/api/generate-fix` backend fix-generator proxy
- `/api/download-report/[taskId]` PDF/html download proxy
