import { describe, expect, it } from 'vitest'
import { bucketByDay } from './activity'

const NOW = new Date('2026-08-20T12:00:00.000Z')

describe('bucketByDay', () => {
  it('returns exactly `days` buckets, oldest first, all zero when no timestamps', () => {
    const result = bucketByDay([], 3, NOW)

    expect(result).toEqual([
      { date: '2026-08-18', count: 0 },
      { date: '2026-08-19', count: 0 },
      { date: '2026-08-20', count: 0 },
    ])
  })

  it('counts timestamps falling on the same day, ignoring time-of-day', () => {
    const result = bucketByDay(
      [
        '2026-08-20T01:00:00.000Z',
        '2026-08-20T23:59:59.000Z',
        '2026-08-19T00:00:00.000Z',
      ],
      3,
      NOW,
    )

    expect(result).toEqual([
      { date: '2026-08-18', count: 0 },
      { date: '2026-08-19', count: 1 },
      { date: '2026-08-20', count: 2 },
    ])
  })

  it('ignores timestamps outside the trailing window', () => {
    const result = bucketByDay(['2026-08-01T00:00:00.000Z'], 3, NOW)

    expect(result.every((bucket) => bucket.count === 0)).toBe(true)
  })
})
