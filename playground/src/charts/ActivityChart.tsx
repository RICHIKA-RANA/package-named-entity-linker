import { useMemo } from 'react'
import { scaleBand, scaleLinear } from 'd3-scale'
import { max } from 'd3-array'
import { timeFormat } from 'd3-time-format'
import type { ActivityDatum } from './activity'

const formatDay = timeFormat('%d')

interface ActivityChartProps {
  data: ActivityDatum[]
  width?: number
  height?: number
  ariaLabel: string
}

export default function ActivityChart({
  data,
  width = 480,
  height = 160,
  ariaLabel,
}: ActivityChartProps) {
  const layout = useMemo(() => {
    const padding = { top: 12, right: 8, bottom: 20, left: 8 }
    const innerWidth = Math.max(0, width - padding.left - padding.right)
    const innerHeight = Math.max(0, height - padding.top - padding.bottom)

    const xScale = scaleBand<string>()
      .domain(data.map((datum) => datum.date))
      .range([0, innerWidth])
      .padding(0.25)

    const yMax = max(data, (datum) => datum.count) ?? 0
    const yScale = scaleLinear()
      .domain([0, yMax || 1])
      .range([innerHeight, 0])

    return data.map((datum) => {
      const barHeight = innerHeight - yScale(datum.count)

      return {
        ...datum,
        x: padding.left + (xScale(datum.date) ?? 0),
        y: padding.top + yScale(datum.count),
        width: xScale.bandwidth(),
        height: barHeight,
      }
    })
  }, [data, width, height])

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="chart"
      role="img"
      aria-label={ariaLabel}
      preserveAspectRatio="xMidYMid meet"
    >
      {layout.map((bar) => (
        <g key={bar.date}>
          <rect
            x={bar.x}
            y={bar.y}
            width={bar.width}
            height={Math.max(bar.height, 1)}
            rx={2}
            className="chart-bar chart-bar-activity"
          />
          <text
            x={bar.x + bar.width / 2}
            y={height - 4}
            textAnchor="middle"
            className="chart-axis-label"
          >
            {formatDay(new Date(bar.date))}
          </text>
        </g>
      ))}
    </svg>
  )
}
