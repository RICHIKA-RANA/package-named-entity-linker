# 0000. Record architecture decisions

Status: Accepted

## Context

This service has gone through several architecture-level decisions (API shape, versioning model, deployment model, evaluation harness) with no single place recording *why* things ended up the way they did. Contributors reading the code have to reconstruct that reasoning from PR descriptions or ask around.

## Decision

We will record significant architecture decisions as short Architecture Decision Records (ADRs) in `docs/adrs/`, numbered sequentially starting at `0000`. Each ADR captures context, the decision, its consequences, and the alternatives considered - not implementation detail.

## Consequences

- Positive: future contributors (and our future selves) can see why an architecture choice was made without re-deriving it from a diff.
- Positive: alternatives and their rejection reasons are preserved, so they don't get silently re-litigated later without knowing they were already considered.
- Negative: another artifact to keep up to date - an ADR that's superseded should be marked so, not silently left to look current.

## Alternatives considered

- No record at all, relying on PR descriptions and commit history - rejected because PR descriptions describe *what* changed, not the standing architectural reasoning, and get harder to find as the repo grows.
- A single running `ARCHITECTURE.md` doc - rejected because it tends to describe current state only and loses the "we considered X and rejected it because Y" reasoning over time as it gets edited in place.
