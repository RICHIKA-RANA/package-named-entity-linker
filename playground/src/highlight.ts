export interface HighlightSpan {
  start: number
  end: number // inclusive, matching the backend's [start, end] convention
  kind: string
  label: string
}

export interface Segment {
  text: string
  kind: string | null
  label: string | null
}

/**
 * Slice `text` into segments per `spans`, marking matched ranges with
 * their kind/label and leaving everything else as plain (kind: null)
 * segments. Spans are sorted by start; any span whose start falls
 * before the current cursor (i.e. it overlaps a span already placed)
 * is skipped rather than rendered.
 */
export function buildSegments(text: string, spans: HighlightSpan[]): Segment[] {
  const segments: Segment[] = []
  let cursor = 0

  const sorted = [...spans].sort((a, b) => a.start - b.start)

  for (const span of sorted) {
    const start = Math.max(span.start, 0)
    const end = Math.min(span.end, text.length - 1)

    if (start > end || start < cursor) continue

    if (start > cursor) {
      segments.push({ text: text.slice(cursor, start), kind: null, label: null })
    }

    segments.push({ text: text.slice(start, end + 1), kind: span.kind, label: span.label })
    cursor = end + 1
  }

  if (cursor < text.length) {
    segments.push({ text: text.slice(cursor), kind: null, label: null })
  }

  return segments
}
