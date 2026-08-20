import type { TestRun, TestRunResult, TestRunSummary } from './api'

export function buildRunSummary(run: TestRun, results: TestRunResult[]): TestRunSummary {
  const graded = results.filter((result) => result.passed !== null)
  const passedCount = graded.filter((result) => result.passed).length

  return {
    run,
    results,
    accuracy: graded.length ? passedCount / graded.length : null,
    graded_count: graded.length,
    passed_count: passedCount,
    total_count: results.length,
  }
}
