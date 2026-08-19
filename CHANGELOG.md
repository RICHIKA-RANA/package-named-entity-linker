# Changelog

## v4.0.0 - Resource-based API redesign (breaking)

The HTTP API was reshaped from a single flat `/nel/...` router into resource-based routes with proper REST verbs, status codes, and documented request/response schemas. Every endpoint path, several HTTP verbs, and most response bodies changed - this is a breaking release for any HTTP client of this service.

### Endpoint mapping

| Old | New | Notes |
|---|---|---|
| `POST /nel/entity` | `POST /entities` | Body: `_id` -> `entity_id`. Now 201 + the created entity (was `{"success": true}`). Now 409 if `entity_id` already exists (previously silently overwrote it). |
| *(none)* | `GET /entities` | New: list all entities. |
| *(none)* | `GET /entities/{entity_id}` | New: get one entity, 404 if missing. |
| `PUT /nel/surface-text` | `POST /entities/{entity_id}/surface-texts` | `entity_id` moved from the request body into the URL path; body is now just `{"surface_text": str}`. Now returns the updated entity with 201, and raises proper 404/409 instead of `{"success": false, "message": "..."}` with an implicit 200. |
| `POST /nel/regex` | `POST /entities/{entity_id}/regex-rules` | `entity_id` moved into the URL path; body is now just `{"regex": str}`. Now validates the entity exists (404 if not) before adding the rule. |
| `POST /nel/fact` | `POST /facts` | Response now includes the generated fact `id` (previously discarded), 201 status. |
| *(none)* | `GET /facts` | New: list all facts. |
| *(none)* | `GET /facts/{fact_id}` | New: get one fact, 404 if missing. |
| `POST /nel/surface-text` | `POST /extractions` | Renamed to stop colliding with the surface-texts sub-resource above; request/response shape otherwise unchanged apart from the key renames below. |

### Response field renames

- `UniversalEntities` / `RegexEntities` / `NoTagEntities` -> `universal_entities` / `regex_entities` / `no_tag_entities` (top-level keys of the extraction response), for consistency with the rest of the API's snake_case convention.
- Linked entity objects inside `universal_entities[].entities[]`: `_id` -> `entity_id`.
- Regex-matched entities inside `regex_entities[]`: `surfaceText` -> `surface_text`.

### Swagger / OpenAPI

- Routes are now split into three tags - `Entities`, `Facts`, `Extraction` - each with a tag-level description, instead of one flat `NEL` tag.
- Every route now has an explicit `summary`, `description`, and typed request/response models, so Swagger shows real schemas instead of a bare `object`.
- Dropped the redundant `/nel` path prefix (this service only ever exposed the NEL API).
