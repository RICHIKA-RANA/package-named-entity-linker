import { describe, expect, it } from 'vitest'
import { buildRunSummary } from './testRunSummary'
import type { TestRun, TestRunResult } from './api'

const run: TestRun = {
  id: 'run-1',
  namespace: 'ns1',
  created_at: '2026-01-01T00:00:00Z',
  triggering_commit_id: null,
}

function makeResult(overrides: Partial<TestRunResult> = {}): TestRunResult {
  return {
    id: 'r1',
    run_id: 'run-1',
    test_case_id: 'case-1',
    actual: [],
    passed: true,
    status_label: 'pass',
    ...overrides,
  }
}

describe('buildRunSummary', () => {
  it('reports null accuracy when nothing is graded', () => {
    const summary = buildRunSummary(run, [makeResult({ passed: null, status_label: 'needs_review' })])

    expect(summary.accuracy).toBeNull()
    expect(summary.graded_count).toBe(0)
    expect(summary.total_count).toBe(1)
  })

  it('computes accuracy from graded results only, ignoring ungraded ones', () => {
    const summary = buildRunSummary(run, [
      makeResult({ id: 'r1', passed: true }),
      makeResult({ id: 'r2', passed: false }),
      makeResult({ id: 'r3', passed: null, status_label: 'needs_review' }),
    ])

    expect(summary.graded_count).toBe(2)
    expect(summary.passed_count).toBe(1)
    expect(summary.accuracy).toBe(0.5)
    expect(summary.total_count).toBe(3)
  })

  it('carries the run and full results array through unchanged', () => {
    const results = [makeResult()]
    const summary = buildRunSummary(run, results)

    expect(summary.run).toBe(run)
    expect(summary.results).toBe(results)
  })
})
