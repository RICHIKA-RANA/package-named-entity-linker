import { useMemo } from 'react'
import { scaleLinear, scalePoint } from 'd3-scale'
import { line as d3line } from 'd3-shape'
import type { AccuracyPoint } from './accuracyTrend'

interface AccuracyTrendChartProps {
  data: AccuracyPoint[]
  width?: number
  height?: number
}

export default function AccuracyTrendChart({
  data,
  width = 480,
  height = 140,
}: AccuracyTrendChartProps) {
  const graded = data.filter((d) => d.accuracy !== null)

  const layout = useMemo(() => {
    const padding = { top: 12, right: 12, bottom: 12, left: 12 }
    const innerWidth = Math.max(0, width - padding.left - padding.right)
    const innerHeight = Math.max(0, height - padding.top - padding.bottom)

    const xScale = scalePoint<string>()
      .domain(graded.map((d) => d.runId))
      .range([0, innerWidth])
      .padding(0.5)

    const yScale = scaleLinear().domain([0, 1]).range([innerHeight, 0])

    const points = graded.map((d) => ({
      x: padding.left + (xScale(d.runId) ?? 0),
      y: padding.top + yScale(d.accuracy ?? 0),
      accuracy: d.accuracy ?? 0,
      runId: d.runId,
    }))

    const path = d3line<{ x: number; y: number }>()
      .x((p) => p.x)
      .y((p) => p.y)(points)

    return { points, path }
  }, [graded, width, height])

  if (graded.length === 0) {
    return <p className="muted small">No graded runs yet</p>
  }

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="chart"
      role="img"
      aria-label="Accuracy trend across runs"
      preserveAspectRatio="xMidYMid meet"
    >
      {layout.path && <path d={layout.path} className="trend-line" fill="none" />}
      {layout.points.map((point) => (
        <circle key={point.runId} cx={point.x} cy={point.y} r={3.5} className="trend-dot" />
      ))}
    </svg>
  )
}
