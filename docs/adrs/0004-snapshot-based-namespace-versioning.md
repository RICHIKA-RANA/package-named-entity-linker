# 0004. Snapshot-based namespace versioning

Status: Accepted

## Context

Training a namespace is inherently experimental - a training session can make it worse, and there was no way to undo that short of manually fixing the data back up. We wanted git-like history: commit the current state, see past commits, and roll back to any of them.

## Decision

A commit snapshots the *entire* current state of a namespace (its entity graph and regex rules) as one JSON blob attached to a row in a `commits` table, linked to its parent commit. Rolling back restores a prior commit by replacing current state with that snapshot and creating a *new* commit on top of it - history is never rewritten or deleted, so rollback is itself just another commit.

## Consequences

- Positive: simple, predictable model - "what does commit X look like" is always a direct read, never a replay of a diff chain.
- Positive: rollback is non-destructive by construction; nothing before or after the rolled-back-to commit is ever lost.
- Negative: storage grows linearly with the number of commits times the size of a namespace's full state - there's no delta compression between adjacent commits.
- Negative: there's no way to see *what changed* between two commits without diffing their snapshots client-side; the model doesn't track that directly.

## Alternatives considered

- Diff/event-log based versioning (store only what changed per commit, replay events to reconstruct state) - rejected as significantly more complex to implement and reason about correctly, for namespace sizes where full snapshots are cheap enough.
- Destructive rollback (actually delete commits after the rollback point) - rejected; losing history on rollback is exactly the failure mode this feature exists to prevent.
