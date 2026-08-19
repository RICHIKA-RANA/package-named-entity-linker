export interface ActivityDatum {
  date: string
  count: number
}

function toDayKey(date: Date): string {
  return date.toISOString().slice(0, 10)
}

/**
 * Buckets ISO timestamps into a fixed-size trailing window of whole days
 * (including empty days), so the chart always shows exactly `days` bars
 * regardless of how sparse the activity is.
 */
export function bucketByDay(
  timestamps: string[],
  days: number,
  now: Date,
): ActivityDatum[] {
  const buckets = new Map<string, number>()

  for (let i = days - 1; i >= 0; i--) {
    const day = new Date(now)
    day.setUTCDate(day.getUTCDate() - i)
    buckets.set(toDayKey(day), 0)
  }

  for (const timestamp of timestamps) {
    const day = timestamp.slice(0, 10)

    if (buckets.has(day)) {
      buckets.set(day, (buckets.get(day) ?? 0) + 1)
    }
  }

  return Array.from(buckets.entries()).map(([date, count]) => ({ date, count }))
}
