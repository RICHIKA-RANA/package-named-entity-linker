# 0002. Serve the playground SPA from FastAPI as one deployable unit

Status: Accepted

## Context

The API needed a UI (namespace management, training, testing). Running it as a separate frontend deployment would mean two services to build, version, and deploy in lockstep, and CORS/proxy configuration between them in every environment.

## Decision

Build the playground as a Vite + React SPA and have FastAPI serve it directly: static assets are mounted, and a catch-all route falls back to `index.html` for any path that isn't a static file or an API route, so client-side routing works. The service still functions with no frontend build present at all (e.g. bare API deployments) - mounting is a no-op if the built `dist/` directory doesn't exist.

## Consequences

- Positive: one deployable artifact, one process, no cross-origin/proxy configuration in any real environment.
- Positive: the API keeps working unchanged for any consumer or environment that never builds the frontend.
- Negative: the backend repo now owns a frontend build step and its toolchain (Node/Vite) as part of getting a fully working deployment, even though the API itself doesn't need it.

## Alternatives considered

- Separate frontend deployment (its own static host or Node server) - rejected to avoid a second deployable, a second release cadence, and cross-origin configuration in every environment.
- Server-rendered templates instead of an SPA - rejected; the playground's interaction model (multi-pane workspace, live extraction preview) needs client-side state that templates don't fit well.
