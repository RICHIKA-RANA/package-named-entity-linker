# 0003. Namespace isolation via a per-namespace bundle registry

Status: Accepted

## Context

The service originally operated on one hardcoded set of entity/dictionary/regex state. Supporting isolated training environments (namespaces) meant every entity, fact, regex rule, and fuzzy-match dictionary needed to be scoped to a namespace, without requiring every namespace to be provisioned or migrated up front.

## Decision

Keep the existing shared SQLite connections as-is, and partition rows within them by a per-namespace key derived from the namespace name. On top of that, a `NamespaceRegistry` lazily builds and caches one `NamespaceBundle` (model instances, matchers, extractor) per namespace the first time it's touched, and can evict a namespace's cached bundle when its underlying data changes (e.g. after a rollback rebuilds the dictionary).

## Consequences

- Positive: new namespaces need no provisioning step - they exist the moment something is created in them.
- Positive: no per-namespace connection/file management; the storage layer didn't need to change, only how it's keyed.
- Negative: all namespaces share the same underlying SQLite connections/files, so there's no per-namespace storage isolation (e.g. for backup, quota, or blast-radius purposes) - a bad query or a very large namespace affects the same file every other namespace uses.
- Negative: cached bundles must be explicitly evicted whenever a namespace's derived state (like the fuzzy-match dictionary) changes out from under it, or stale in-memory state would be served.

## Alternatives considered

- A separate SQLite file per namespace - rejected as unnecessary operational complexity (file lifecycle, connection pooling per namespace) for the expected namespace count and size at the time.
- Eagerly building every namespace's bundle at startup - rejected in favor of lazy, on-demand construction so startup time and memory don't scale with the number of namespaces that merely exist but aren't in use.
