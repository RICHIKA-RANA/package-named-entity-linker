import { describe, expect, it } from 'vitest'
import { buildSegments } from './highlight'

describe('buildSegments', () => {
  it('returns the whole text as one plain segment when there are no spans', () => {
    expect(buildSegments('hello world', [])).toEqual([
      { text: 'hello world', kind: null, label: null },
    ])
  })

  it('splits into before/match/after around a single span', () => {
    const spans = [{ start: 6, end: 10, kind: 'entity', label: 'World' }]

    expect(buildSegments('hello world', spans)).toEqual([
      { text: 'hello ', kind: null, label: null },
      { text: 'world', kind: 'entity', label: 'World' },
    ])
  })

  it('handles a span touching the start of the text', () => {
    const spans = [{ start: 0, end: 4, kind: 'entity', label: 'Hello' }]

    expect(buildSegments('hello world', spans)).toEqual([
      { text: 'hello', kind: 'entity', label: 'Hello' },
      { text: ' world', kind: null, label: null },
    ])
  })

  it('handles adjacent spans with no gap between them', () => {
    const spans = [
      { start: 0, end: 4, kind: 'entity', label: 'Hello' },
      { start: 5, end: 5, kind: 'regex', label: 'space' },
      { start: 6, end: 10, kind: 'entity', label: 'World' },
    ]

    expect(buildSegments('hello world', spans)).toEqual([
      { text: 'hello', kind: 'entity', label: 'Hello' },
      { text: ' ', kind: 'regex', label: 'space' },
      { text: 'world', kind: 'entity', label: 'World' },
    ])
  })

  it('sorts unsorted input spans by start', () => {
    const spans = [
      { start: 6, end: 10, kind: 'entity', label: 'World' },
      { start: 0, end: 4, kind: 'entity', label: 'Hello' },
    ]

    expect(buildSegments('hello world', spans).map((s) => s.label)).toEqual([
      'Hello',
      null,
      'World',
    ])
  })

  it('skips a span that overlaps one already placed', () => {
    const spans = [
      { start: 0, end: 4, kind: 'entity', label: 'First' },
      { start: 2, end: 8, kind: 'regex', label: 'Overlapping' },
    ]

    expect(buildSegments('hello world', spans)).toEqual([
      { text: 'hello', kind: 'entity', label: 'First' },
      { text: ' world', kind: null, label: null },
    ])
  })

  it('clamps a span whose end exceeds the text length', () => {
    const spans = [{ start: 6, end: 999, kind: 'entity', label: 'World' }]

    expect(buildSegments('hello world', spans)).toEqual([
      { text: 'hello ', kind: null, label: null },
      { text: 'world', kind: 'entity', label: 'World' },
    ])
  })
})
