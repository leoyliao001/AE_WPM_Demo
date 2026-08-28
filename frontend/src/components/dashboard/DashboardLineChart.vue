<template>
  <div class="line-chart">
    <div class="line-chart__topline">
      <div class="line-chart__metrics">
        <span><strong>Latest</strong> {{ valueFormatter(latestValue) }}</span>
        <span><strong>Peak</strong> {{ valueFormatter(peakValue) }}</span>
        <span><strong>Avg</strong> {{ valueFormatter(averageValue) }}</span>
      </div>
      <div v-if="hasData && normalizedSeries.length > 1" class="line-chart__legend">
        <span v-for="seriesItem in normalizedSeries" :key="`legend-${seriesItem.key}`">
          <span class="line-chart__legend-dot" :style="{ backgroundColor: seriesItem.color }" />
          {{ seriesItem.label }}
        </span>
      </div>
    </div>

    <svg
      v-if="hasData"
      class="line-chart__svg"
      :viewBox="`0 0 ${width} ${height}`"
      role="img"
      aria-label="Line chart"
    >
      <defs>
        <linearGradient id="line-chart-area" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stop-color="#0b8dbf" stop-opacity="0.22" />
          <stop offset="100%" stop-color="#0b8dbf" stop-opacity="0.02" />
        </linearGradient>
        <linearGradient id="line-chart-line" x1="0" x2="1">
          <stop offset="0%" stop-color="#0b8dbf" />
          <stop offset="100%" stop-color="#0077b8" />
        </linearGradient>
        <filter id="line-chart-soft-shadow" x="-30%" y="-30%" width="160%" height="160%">
          <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#0b8dbf" flood-opacity="0.13" />
        </filter>
      </defs>

      <rect
        :x="padLeft"
        :y="padTop"
        :width="width - padLeft - padRight"
        :height="height - padTop - padBottom"
        class="line-chart__plot-bg"
        rx="16"
      />

      <g v-for="(tick, index) in yTicks" :key="`tick-${index}`">
        <line
          :x1="padLeft"
          :x2="width - padRight"
          :y1="yPos(tick.value)"
          :y2="yPos(tick.value)"
          class="line-chart__grid-line"
        />
        <text
          :x="padLeft - 10"
          :y="yPos(tick.value) + 3"
          class="line-chart__axis-label"
          text-anchor="end"
        >
          {{ valueFormatter(tick.value) }}
        </text>
      </g>

      <line
        :x1="padLeft"
        :x2="width - padRight"
        :y1="height - padBottom"
        :y2="height - padBottom"
        class="line-chart__baseline"
      />

      <text
        v-for="(label, index) in labels"
        :key="`label-${label}-${index}`"
        v-show="showXAxisLabel(index)"
        :x="xPos(index)"
        :y="height - 6"
        class="line-chart__axis-label line-chart__axis-label--x"
        text-anchor="middle"
      >
        {{ label }}
      </text>

      <path v-if="primaryAreaPath" :d="primaryAreaPath" class="line-chart__area" />

      <g v-for="seriesItem in normalizedSeries" :key="seriesItem.key">
        <path
          :d="seriesItem.path"
          fill="none"
          :stroke="seriesItem.color"
          class="line-chart__line"
          filter="url(#line-chart-soft-shadow)"
        />

        <circle
          v-for="(point, index) in seriesItem.coords"
          :key="`${seriesItem.key}-${index}`"
          :cx="point.x"
          :cy="point.y"
          :r="index === latestIndex ? 4.9 : 2.5"
          fill="#fff"
          :stroke="seriesItem.color"
          :stroke-width="index === latestIndex ? 2.3 : 1.5"
        />
      </g>

      <g v-if="latestPoint">
        <line
          :x1="latestPoint.x"
          :x2="latestPoint.x"
          :y1="latestPoint.y"
          :y2="height - padBottom"
          class="line-chart__latest-guide"
        />

        <circle
          :cx="latestPoint.x"
          :cy="latestPoint.y"
          r="8"
          class="line-chart__latest-ring"
        />

        <rect
          :x="calloutX"
          :y="calloutY"
          width="88"
          height="30"
          rx="9"
          class="line-chart__callout-box"
        />
        <text :x="calloutX + 8" :y="calloutY + 12.5" class="line-chart__callout-label">
          {{ latestLabel }}
        </text>
        <text :x="calloutX + 8" :y="calloutY + 23.5" class="line-chart__callout-value">
          {{ valueFormatter(latestValue) }}
        </text>
      </g>
    </svg>

    <p v-else class="line-chart__empty">{{ emptyText }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  labels: { type: Array, default: () => [] },
  series: { type: Array, default: () => [] },
  valueFormatter: {
    type: Function,
    default: (value) => String(Math.round(Number(value) || 0))
  },
  emptyText: { type: String, default: 'No chart data available.' }
})

const width = 720
const height = 176
const padLeft = 52
const padRight = 18
const padTop = 18
const padBottom = 32

const allValues = computed(() =>
  props.series.flatMap((seriesItem) => seriesItem.values ?? []).map((value) => Number(value) || 0)
)

const hasData = computed(() => allValues.value.some((value) => value > 0))
const maxValue = computed(() => Math.max(...allValues.value, 1))

const yPos = (value) => {
  const usableHeight = height - padTop - padBottom
  return padTop + (1 - (Number(value) || 0) / maxValue.value) * usableHeight
}

const xPos = (index) => {
  const usableWidth = width - padLeft - padRight
  const denominator = Math.max(props.labels.length - 1, 1)
  return padLeft + (usableWidth * index) / denominator
}

const yTicks = computed(() =>
  Array.from({ length: 4 }, (_, index) => {
    const ratio = index / 3
    return { value: Math.round(maxValue.value * (1 - ratio)) }
  })
)

const showXAxisLabel = (index) => {
  const total = props.labels.length
  if (total <= 8) return true
  return index % 2 === 0 || index === total - 1
}

const smoothPath = (coords) => {
  if (!coords.length) return ''
  if (coords.length === 1) return `M ${coords[0].x} ${coords[0].y}`

  let path = `M ${coords[0].x} ${coords[0].y}`
  for (let i = 0; i < coords.length - 1; i += 1) {
    const p0 = coords[i - 1] || coords[i]
    const p1 = coords[i]
    const p2 = coords[i + 1]
    const p3 = coords[i + 2] || p2
    const c1x = p1.x + (p2.x - p0.x) / 6
    const c1y = p1.y + (p2.y - p0.y) / 6
    const c2x = p2.x - (p3.x - p1.x) / 6
    const c2y = p2.y - (p3.y - p1.y) / 6
    path += ` C ${c1x} ${c1y}, ${c2x} ${c2y}, ${p2.x} ${p2.y}`
  }
  return path
}

const normalizedSeries = computed(() =>
  props.series.map((seriesItem) => {
    const coords = (seriesItem.values ?? []).map((value, index) => ({
      x: xPos(index),
      y: yPos(value)
    }))
    return {
      ...seriesItem,
      coords,
      path: smoothPath(coords)
    }
  })
)

const primarySeries = computed(() => normalizedSeries.value[0] ?? null)
const latestIndex = computed(() => Math.max(props.labels.length - 1, 0))
const latestLabel = computed(() => props.labels[latestIndex.value] ?? 'Latest')

const primaryAreaPath = computed(() => {
  const coords = primarySeries.value?.coords ?? []
  if (!coords.length) return ''
  const linePath = smoothPath(coords)
  const first = coords[0]
  const last = coords[coords.length - 1]
  return `${linePath} L ${last.x} ${height - padBottom} L ${first.x} ${height - padBottom} Z`
})

const latestPoint = computed(() => {
  const coords = primarySeries.value?.coords ?? []
  return coords[coords.length - 1] ?? null
})

const latestValue = computed(() => {
  const values = primarySeries.value?.values ?? []
  return Number(values[values.length - 1]) || 0
})

const peakValue = computed(() => Math.max(...(primarySeries.value?.values ?? [0]), 0))

const averageValue = computed(() => {
  const values = (primarySeries.value?.values ?? []).map((value) => Number(value) || 0)
  if (!values.length) return 0
  return values.reduce((sum, value) => sum + value, 0) / values.length
})

const calloutOnLeft = computed(() => (latestPoint.value?.x ?? 0) > width - 130)

const calloutX = computed(() => {
  if (!latestPoint.value) return width - 102
  return calloutOnLeft.value ? latestPoint.value.x - 92 : latestPoint.value.x + 8
})

const calloutY = computed(() => {
  if (!latestPoint.value) return padTop
  return Math.max(padTop + 2, latestPoint.value.y - 34)
})
</script>

<style scoped>
.line-chart {
  min-height: 176px;
}

.line-chart__topline {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 10px 14px;
  justify-content: space-between;
  margin-bottom: 8px;
}

.line-chart__metrics {
  color: #536271;
  display: flex;
  flex-wrap: wrap;
  font-size: 11px;
  gap: 12px;
}

.line-chart__metrics strong {
  color: #203040;
  font-weight: 700;
}

.line-chart__svg {
  height: auto;
  width: 100%;
}

.line-chart__plot-bg {
  fill: #fcfdff;
  stroke: rgba(12, 35, 64, 0.06);
}

.line-chart__grid-line {
  stroke: rgba(126, 151, 169, 0.2);
  stroke-width: 0.85;
}

.line-chart__baseline {
  stroke: #d5e0ea;
  stroke-width: 1.1;
}

.line-chart__axis-label {
  fill: #6e7c88;
  font-size: 9px;
}

.line-chart__axis-label--x {
  fill: #4a5968;
  font-size: 10px;
  font-weight: 600;
}

.line-chart__area {
  fill: url(#line-chart-area);
}

.line-chart__line {
  stroke: url(#line-chart-line);
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 2.35;
}

.line-chart__latest-guide {
  stroke: #a0bccf;
  stroke-dasharray: 3 4;
}

.line-chart__latest-ring {
  fill: #fff;
  stroke: rgba(11, 141, 191, 0.26);
  stroke-width: 5;
}

.line-chart__callout-box {
  fill: #0f4f79;
  opacity: 0.95;
}

.line-chart__callout-label {
  fill: rgba(255, 255, 255, 0.84);
  font-size: 8px;
  font-weight: 600;
}

.line-chart__callout-value {
  fill: #fff;
  font-size: 10px;
  font-weight: 700;
}

.line-chart__legend {
  color: #6c7a87;
  display: flex;
  flex-wrap: wrap;
  font-size: 11px;
  gap: 14px;
}

.line-chart__legend span {
  align-items: center;
  display: inline-flex;
  gap: 6px;
}

.line-chart__legend-dot {
  border-radius: 999px;
  display: inline-block;
  height: 9px;
  width: 9px;
}

.line-chart__empty {
  color: #6c757d;
  font-size: 13px;
  margin: 0;
  padding: 24px 0;
}
</style>
