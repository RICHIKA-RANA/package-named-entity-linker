import { useMemo } from 'react'
import { buildBarChartLayout, type BarChartDatum } from './barChart'

interface BarChartProps {
  data: BarChartDatum[]
  width?: number
  height?: number
  ariaLabel: string
}

export default function BarChart({ data, width = 480, height = 220, ariaLabel }: BarChartProps) {
  const layout = useMemo(() => buildBarChartLayout(data, width, height), [data, width, height])

  if (data.length === 0) {
    return <p className="muted small">No data yet</p>
  }

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="chart"
      role="img"
      aria-label={ariaLabel}
      preserveAspectRatio="xMidYMid meet"
    >
      {layout.bars.map((bar) => (
        <g key={bar.label}>
          <rect
            x={bar.x}
            y={bar.y}
            width={bar.width}
            height={Math.max(bar.height, 1)}
            rx={3}
            className="chart-bar"
          />
          <text x={bar.x + bar.width / 2} y={bar.y - 6} textAnchor="middle" className="chart-value">
            {bar.value}
          </text>
          <text
            x={bar.x + bar.width / 2}
            y={height - 6}
            textAnchor="middle"
            className="chart-axis-label"
          >
            {bar.label.length > 10 ? `${bar.label.slice(0, 9)}…` : bar.label}
          </text>
        </g>
      ))}
    </svg>
  )
}
