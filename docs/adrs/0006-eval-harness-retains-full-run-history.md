# 0006. Evaluation harness retains full run history for regression comparison

Status: Accepted

## Context

Validating a training change needed to go beyond "does this one message extract correctly right now" - we wanted to know whether a change to a namespace made previously-passing queries start failing (a regression), fixed previously-failing ones, or only affected new/unlabeled queries.

## Decision

Store test cases, test runs, and per-case run results as their own persisted history (`test_cases`/`test_runs`/`test_run_results`), rather than only keeping the latest result per case. Each result's status (`pass`/`regression`/`fixed`/`fail`/`new`/`needs_review`) is computed by comparing it against that same case's result in the *immediately preceding* run.

## Consequences

- Positive: regressions and fixes are visible directly, without a human manually diffing two runs' worth of output.
- Positive: accuracy trends over time (and per-run accuracy) fall out of the same stored history for free.
- Negative: storage grows with every run times every test case, unbounded - there's no pruning of old runs.

## Alternatives considered

- Keep only the latest result per test case (overwrite on each run) - rejected because it makes regression/fixed detection and trend charts impossible; there'd be nothing to compare a new run against.
- Compute regression status on the fly by diffing arbitrary pairs of runs at read time - rejected in favor of computing and storing the status once, at run time, against the fixed "previous run" comparison - simpler to reason about and to query.
