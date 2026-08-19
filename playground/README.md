# TalkingDB NEL Playground

Vite + React + TypeScript UI for the NEL training playground. Served by the FastAPI app at `/` - see `talkingdb_nel/main.py`.

## Development

```bash
nvm use   # picks up the Node version pinned in .nvmrc
npm install
npm run dev
```

The dev server proxies `/api/*` requests to a FastAPI server running on `http://localhost:8092` (see `vite.config.ts`) - start that separately (`make local` from the repo root).

## Build

**`dist/` is committed to the repo** (not built in CI or Docker) - after any change to `playground/src` or its dependencies, rebuild and commit the result:

```bash
npm run build
git add dist
```

FastAPI serves `dist/` directly when present; CI and the Docker image do not run Node at all.
