export interface RunResultLike {
  passed: boolean | null
}

export interface RunLike {
  id: string
  created_at: string
}

export interface AccuracyPoint {
  runId: string
  createdAt: string
  accuracy: number | null
}

export function computeAccuracyTrend(
  runs: RunLike[],
  resultsByRun: Record<string, RunResultLike[]>,
): AccuracyPoint[] {
  return runs
    .slice()
    .sort((a, b) => a.created_at.localeCompare(b.created_at))
    .map((run) => {
      const results = resultsByRun[run.id] ?? []
      const graded = results.filter((r) => r.passed !== null)
      const accuracy = graded.length
        ? graded.filter((r) => r.passed).length / graded.length
        : null

      return { runId: run.id, createdAt: run.created_at, accuracy }
    })
}
