import { scaleBand, scaleLinear } from 'd3-scale'
import { max } from 'd3-array'

export interface BarChartDatum {
  label: string
  value: number
}

export interface BarChartBar {
  label: string
  value: number
  x: number
  y: number
  width: number
  height: number
}

export interface BarChartLayout {
  bars: BarChartBar[]
  width: number
  height: number
}

const DEFAULT_PADDING = { top: 20, right: 8, bottom: 24, left: 8 }

export function buildBarChartLayout(
  data: BarChartDatum[],
  width: number,
  height: number,
  padding = DEFAULT_PADDING,
): BarChartLayout {
  const innerWidth = Math.max(0, width - padding.left - padding.right)
  const innerHeight = Math.max(0, height - padding.top - padding.bottom)

  const xScale = scaleBand<string>()
    .domain(data.map((datum) => datum.label))
    .range([0, innerWidth])
    .padding(0.35)

  const yMax = max(data, (datum) => datum.value) ?? 0
  const yScale = scaleLinear()
    .domain([0, yMax || 1])
    .range([innerHeight, 0])

  const bars = data.map((datum) => {
    const barHeight = innerHeight - yScale(datum.value)

    return {
      label: datum.label,
      value: datum.value,
      x: padding.left + (xScale(datum.label) ?? 0),
      y: padding.top + yScale(datum.value),
      width: xScale.bandwidth(),
      height: barHeight,
    }
  })

  return { bars, width, height }
}
