import { buildSegments, type HighlightSpan } from '../highlight'

export default function HighlightedText({
  text,
  spans,
}: {
  text: string
  spans: HighlightSpan[]
}) {
  const segments = buildSegments(text, spans)

  return (
    <p className="highlighted-text">
      {segments.map((segment, index) =>
        segment.kind ? (
          <mark
            key={index}
            className={`highlight-${segment.kind}`}
            title={segment.label ?? undefined}
          >
            {segment.text}
          </mark>
        ) : (
          <span key={index}>{segment.text}</span>
        ),
      )}
    </p>
  )
}
