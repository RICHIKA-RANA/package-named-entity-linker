# Architecture (C4 model)

These diagrams follow the [C4 model](https://c4model.com): **Context** (who uses the system and what it talks to), **Container** (the separately-runnable pieces it's built from), and **Component** (what one of those containers is made of internally). They're written as [Mermaid](https://mermaid.js.org/syntax/c4.html) - plain text, rendered natively wherever GitHub shows this file, no build step. For *why* a given box or boundary looks the way it does, see [`docs/adrs/`](../adrs/README.md).

## Level 1 — System Context

```mermaid
C4Context
  title System Context — TalkingDB Named Entity Linker

  Person(trainer, "ML Engineer / Trainer", "Trains and tests entity linking")
  System(nel, "Named Entity Linker", "FastAPI service + Playground SPA, served as one deployable unit")

  Rel(trainer, nel, "Trains, tests, and inspects namespaces via", "HTTPS, browser")
```

No other system calls this service's API at runtime today - checked against every sibling repo in this workspace. It's used exclusively through its own bundled Playground UI right now; this diagram should gain a second `System_Ext` box the day a real external consumer shows up, not before.

## Level 2 — Containers

```mermaid
C4Container
  title Container Diagram — Named Entity Linker

  Person(trainer, "ML Engineer / Trainer")

  System_Boundary(nel, "Named Entity Linker") {
    Container(spa, "Playground SPA", "React 19 + TypeScript, Vite", "Dashboard, training, testing, history, inspect, and code-snippet screens")
    Container(api, "API & Backend", "Python, FastAPI", "Resource-oriented REST API (namespaces, entities, facts, extraction, test suite); serves the built SPA")
    ContainerDb(entitiesDb, "Entity / Namespace / Test-suite store", "SQLite — entities.db", "Entity graphs, namespace + commit history, test cases/runs/results")
    ContainerDb(regexDb, "Regex rule store", "SQLite — regex.db", "Per-entity regex rules")
    ContainerDb(dictDb, "Fuzzy-match dictionary", "SQLite — dictionary.db", "Word/phrase index used for typo correction")
  }

  Rel(trainer, spa, "Uses", "HTTPS, browser")
  Rel(spa, api, "Calls", "JSON/HTTPS")
  Rel(api, entitiesDb, "Reads/writes", "SQLite")
  Rel(api, regexDb, "Reads/writes", "SQLite")
  Rel(api, dictDb, "Reads/writes", "SQLite")
```

The SPA is built ahead of time and committed, then served by the same FastAPI process - one deployable unit, two runtimes ([ADR-0002](../adrs/0002-serve-playground-spa-from-fastapi.md)). Each store is a single shared connection reused by every namespace; isolation is by row-key prefix, not separate files per namespace ([ADR-0003](../adrs/0003-namespace-isolation-via-bundle-registry.md)). `entities.db` backs three otherwise-unrelated concerns (entity graphs, namespace/commit history, and the evaluation harness) in one file - a real seam, not an oversight.

## Level 3 — Components (API & Backend)

```mermaid
C4Component
  title Component Diagram — API & Backend (talkingdb_nel)

  Container_Boundary(api, "API & Backend") {
    Component(namespacesApi, "Namespaces API", "FastAPI router", "Namespace CRUD, commit history, rollback, graph export")
    Component(entitiesApi, "Entities API", "FastAPI router", "Entity CRUD, bulk upload, surface texts, regex rules")
    Component(factsApi, "Facts API", "FastAPI router", "Fact CRUD between entities")
    Component(extractionApi, "Extraction API", "FastAPI router", "Runs the symbolic pipeline over free text")
    Component(testsuiteApi, "Test Suite API", "FastAPI router", "Test-case CRUD, bulk upload, runs, accept/reject")

    Component(registry, "Namespace Registry", "Python", "Lazily builds and caches one bundle of models/matchers per namespace")
    Component(versioning, "Versioning Service", "Python", "Commit / rollback / purge; full dictionary rebuild after any mutation")
    Component(entityService, "Entity Service", "Python", "Entity/fact/regex CRUD; orchestrates extraction")
    Component(symbolic, "Symbolic Matching Engine", "Python", "Tokenizer, word/phrase fuzzy matchers, regex controller, lemmatizer")
    Component(evalHarness, "Evaluation Harness", "Python", "Test-run execution; labels each case pass/regression/fixed/fail vs. the previous run")
  }

  System_Ext(models, "base-tdb-models", "EntityModel, RegexModel, DictionaryModel — persistence/domain layer")
  System_Ext(clients, "base-tdb-clients", "SQLite connection factory")

  Rel(namespacesApi, registry, "Uses")
  Rel(namespacesApi, versioning, "Uses")
  Rel(entitiesApi, entityService, "Uses")
  Rel(factsApi, entityService, "Uses")
  Rel(extractionApi, entityService, "Uses")
  Rel(testsuiteApi, evalHarness, "Uses")
  Rel(entityService, symbolic, "Uses")
  Rel(evalHarness, entityService, "Invokes, to grade cases against live extraction")
  Rel(registry, models, "Loads/saves via")
  Rel(versioning, models, "Reads/writes via")
  Rel(registry, clients, "Opens connections via")
```

The Symbolic Matching Engine groups several files (`tokenizer.py`, `matcher/word.py`, `matcher/phrase.py`, `regex.py`, `lemmatizer.py`, `notag.py`, `distance.py`) into one component - the tokenize→match→correct pipeline is one architectural unit, not five. Namespace Registry, Versioning, and the fuzzy-dictionary rebuild strategy are covered by [ADR-0003](../adrs/0003-namespace-isolation-via-bundle-registry.md), [ADR-0004](../adrs/0004-snapshot-based-namespace-versioning.md), and [ADR-0005](../adrs/0005-full-rebuild-of-fuzzy-match-dictionary.md); the Evaluation Harness's run-history model is [ADR-0006](../adrs/0006-eval-harness-retains-full-run-history.md).
