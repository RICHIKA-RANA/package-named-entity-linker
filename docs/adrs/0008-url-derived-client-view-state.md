# 0008. Client-side view state is derived from the URL

Status: Accepted

## Context

The playground workspace has a resizable split-pane view where each pane shows one of several sections (Train/Tests/History/Inspect/Code). This state was originally mirrored local component state, seeded from the URL only when the component first mounted. Anything that changed the URL afterward - a sidebar navigation link, a link from one pane to another, or the browser's back/forward buttons - had no effect on what was actually rendered, because the mirrored state never re-derived itself from a later URL change.

## Decision

The workspace's pane state has no state of its own - on every render, which view each pane shows is computed directly from the current URL's search params, and every action that changes it (selecting a view, splitting, closing a split) writes to the URL rather than to component state.

## Consequences

- Positive: the URL is the single source of truth, so every way of changing it - sidebar links, cross-pane links, browser navigation, a shared/bookmarked link - produces the same correct result with no separate synchronization code.
- Positive: a workspace view is always a shareable/bookmarkable link, and refresh preserves it.
- Negative: any future feature adding view state that doesn't belong in a shareable URL (e.g. transient UI state) needs a deliberately separate mechanism, since the established pattern for "this pane's state" is now "put it in the URL."

## Alternatives considered

- Keep local component state and add an effect to re-sync it whenever the URL changes externally - rejected as a second source of truth that has to stay in sync with the first, and the exact bug this decision was made to fix in the first place.
