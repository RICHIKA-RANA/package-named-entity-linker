# TalkingDB NEL Playground

Vite + React + TypeScript UI for the NEL training playground. Served by the FastAPI app at `/` once built - see `talkingdb_nel/main.py`.

## Development

```bash
npm install
npm run dev
```

The dev server proxies `/api/*` requests to a FastAPI server running on `http://localhost:8092` (see `vite.config.ts`) - start that separately (`make local` from the repo root).

## Build

```bash
npm run build
```

Outputs to `dist/`, which FastAPI serves directly when present.
