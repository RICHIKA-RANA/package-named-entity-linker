# 0001. Resource-oriented REST API

Status: Accepted

## Context

The API started as a single flat router (`/nel/...`) with one tag, mixing entity, fact, and extraction operations under one namespace with inconsistent conventions (ids in the body instead of the path, ad hoc success/error shapes, no read endpoints for resources the model layer already supported).

## Decision

Organize the API as resource-oriented REST: separate routers/tags for **Entities**, **Facts**, and **Extraction**, with identifiers in the URL path, standard status codes (201 on create, 404/409 where appropriate), and full read/write parity for each resource the model layer supports.

## Consequences

- Positive: predictable, standard REST semantics make the API self-describing and easier for new consumers (including the playground UI added later) to work against.
- Positive: room to add CRUD per resource incrementally without reshaping unrelated endpoints.
- Negative: every existing endpoint path and response shape changed at once - a breaking change for any existing consumer, requiring coordinated migration.

## Alternatives considered

- Keep the flat `/nel/...` router and just fix individual inconsistencies - rejected because the inconsistencies were symptoms of the underlying structure, not isolated bugs.
- GraphQL - rejected as disproportionate for this service's surface area and consumer base at the time.
