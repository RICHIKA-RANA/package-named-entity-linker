# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [6.0.0] - Playground UI shell + /api prefix (breaking)

Phase 2 of the training playground: a Vite + React app (`playground/`) served by FastAPI itself, visible at `/`. This release lists/creates namespaces and links into a (currently stub) namespace detail page - training/testing/history/graph screens are still to come.

### Added

- `playground/` - React app scaffold (namespace list + create form at `/`, stub namespace detail page at `/namespaces/:name`). Built with `npm run build`, served directly by FastAPI when `playground/dist/` exists.
- Docker image now builds the frontend in a separate stage and bundles the built assets.
- CI gains a `build-playground` job that builds the frontend on every push/PR.

### Changed (breaking)

- **Every API route moves under `/api`**: `POST/GET /namespaces` -> `POST/GET /api/namespaces`, and likewise for every namespace/entity/fact/extraction route added in [5.0.0](#500---namespaces-and-training-version-control-breaking). Needed because the frontend's client-side route for a namespace's detail page (`/namespaces/{name}`) is otherwise indistinguishable from the REST endpoint of the same path - a client hitting `GET /namespaces/{name}` directly (as opposed to loading it through the browser) would get routed to whichever handler FastAPI resolves first. Prefixing the API frees the entire bare URL space for the frontend, permanently, not just for this one route.

## [5.0.0] - Namespaces and training version control (breaking)

Foundation for the training playground: every entity/fact/regex/extraction endpoint now lives under an isolated **namespace** - a fully separate entity graph, dictionary, and regex ruleset, addressable by name. This is the first of two things that make this release breaking:

### Added

- `POST /namespaces`, `GET /namespaces`, `GET /namespaces/{namespace}` - create/list/get a namespace.
- `POST /namespaces/{namespace}/commits` - snapshot the namespace's current entity graph and regex rules as a named commit, so training can be tested against before being made permanent.
- `GET /namespaces/{namespace}/commits`, `GET /namespaces/{namespace}/commits/{commit_id}` - commit history and detail.
- `POST /namespaces/{namespace}/commits/{commit_id}/rollback` - restore a prior commit's state. Rollback is non-destructive: it records itself as a new commit rather than erasing history.
- `GET /namespaces/{namespace}/graph` - the namespace's entities and facts as a graph (nodes/edges).

### Changed (breaking)

- Every existing route gains a `/namespaces/{namespace}` prefix: `POST /entities` -> `POST /namespaces/{namespace}/entities`, and likewise for `GET /entities`, `GET /entities/{entity_id}`, `POST /entities/{entity_id}/surface-texts`, `POST /entities/{entity_id}/regex-rules`, `POST /facts`, `GET /facts`, `GET /facts/{fact_id}`, and `POST /extractions`.
- A namespace must be created (`POST /namespaces`) before any of the above will work - they 404 if the namespace doesn't exist.

### Fixed

- **Entity/fact data is now actually persisted.** Previously, `EntityModel` mutations (`create_entity`, `add_surface_text`, `create_fact`) were never saved to SQLite - every entity/fact trained through the API was silently lost on process restart. Every mutation now calls `entity_model.save(...)`.
- **`longest_word_length` staleness across matchers.** `word_matcher` and `phrase_matcher` share one dictionary table; a single-word surface text collides (both insert the identical string), so whichever matcher touches it second hit the "already exists" branch of `create_dictionary_entry()` and never learned its own longest-word length - silently breaking exact-match extraction for any namespace whose only entity is a single word. Previously masked in the old single shared "default" namespace by other, longer entities happening to be trained first.

Requires [`base-tdb-models`](https://github.com/TalkingDB/base-tdb-models) with `DictionaryModel.clear()` (added alongside this release) for the rollback dictionary rebuild.

## [4.0.0] - Resource-based API redesign (breaking)

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
