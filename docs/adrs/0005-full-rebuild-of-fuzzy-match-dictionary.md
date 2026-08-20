# 0005. Full rebuild of the fuzzy-match dictionary on mutation

Status: Accepted

## Context

The fuzzy-match dictionary is a derived index over every entity's surface texts (used for typo correction). Any operation that changes what surface texts exist - rolling back a namespace, editing or deleting an entity, editing or deleting a regex rule - leaves that derived index out of sync unless it's updated too. The underlying model layer has no incremental "remove this surface text's contribution" operation.

## Decision

Every mutation that can change the set of surface texts clears and fully rebuilds the fuzzy-match dictionary from the current entity/rule state, rather than attempting an incremental update. The namespace's cached bundle is evicted afterward so the next access rebuilds its matchers against the fresh dictionary instead of reusing stale cached metadata.

## Consequences

- Positive: the dictionary is always provably consistent with current state - no class of bugs from a partial or missed incremental update.
- Positive: one rebuild code path is reused across rollback, entity edit/delete, and regex edit/delete, instead of four separate incremental-update implementations.
- Negative: every such mutation costs a full rebuild proportional to namespace size, instead of a cheap targeted update - namespaces with very large entity/surface-text counts will feel this on every edit or delete.

## Alternatives considered

- Incremental removal (subtract just the affected surface texts from the index) - rejected because the model layer has no such operation, and building/maintaining one correctly (handling shared surface texts across entities, edit distance recalculation) was judged more complex and error-prone than a full rebuild at current namespace sizes.
