# 0007. HTTP API is the sole integration surface

Status: Accepted

## Context

When adding copy-paste integration examples to the playground, we had to decide what kind of examples to show: code that imports this service as a library, or code that calls it over HTTP. This service is not published to any package index and its README only documents running it as a server.

## Decision

Treat the HTTP API as the only supported integration surface. All integration examples (and, by extension, any future client tooling) target plain HTTP requests against whichever host is serving the API, not an in-process import of this codebase.

## Consequences

- Positive: consumers integrate the same way regardless of language or runtime - no dependency on this being a Python codebase at all.
- Positive: internal refactors of the model/service layer can't break external consumers, since nothing outside this repo imports it directly.
- Negative: any consumer that's also a Python service pays HTTP serialization/deserialization overhead instead of an in-process call, even when it's running alongside this service.

## Alternatives considered

- Publish this service as an installable Python package and document direct imports - rejected; it isn't published anywhere today, and doing so would mean maintaining a stable importable surface (not just a stable HTTP contract) going forward.
