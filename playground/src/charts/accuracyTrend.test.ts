import { describe, expect, it } from 'vitest'
import { computeAccuracyTrend } from './accuracyTrend'

describe('computeAccuracyTrend', () => {
  it('sorts runs oldest to newest and computes accuracy per run', () => {
    const runs = [
      { id: 'r2', created_at: '2026-08-20T12:00:00Z' },
      { id: 'r1', created_at: '2026-08-19T12:00:00Z' },
    ]
    const resultsByRun = {
      r1: [{ passed: true }, { passed: false }],
      r2: [{ passed: true }, { passed: true }],
    }

    expect(computeAccuracyTrend(runs, resultsByRun)).toEqual([
      { runId: 'r1', createdAt: '2026-08-19T12:00:00Z', accuracy: 0.5 },
      { runId: 'r2', createdAt: '2026-08-20T12:00:00Z', accuracy: 1 },
    ])
  })

  it('excludes needs_review (null passed) results from the accuracy calculation', () => {
    const runs = [{ id: 'r1', created_at: '2026-08-19T12:00:00Z' }]
    const resultsByRun = {
      r1: [{ passed: true }, { passed: null }, { passed: null }],
    }

    expect(computeAccuracyTrend(runs, resultsByRun)).toEqual([
      { runId: 'r1', createdAt: '2026-08-19T12:00:00Z', accuracy: 1 },
    ])
  })

  it('returns null accuracy when nothing is graded', () => {
    const runs = [{ id: 'r1', created_at: '2026-08-19T12:00:00Z' }]
    const resultsByRun = { r1: [{ passed: null }] }

    expect(computeAccuracyTrend(runs, resultsByRun)[0].accuracy).toBeNull()
  })

  it('treats a run missing from resultsByRun as having no results', () => {
    const runs = [{ id: 'r1', created_at: '2026-08-19T12:00:00Z' }]

    expect(computeAccuracyTrend(runs, {})[0].accuracy).toBeNull()
  })
})
