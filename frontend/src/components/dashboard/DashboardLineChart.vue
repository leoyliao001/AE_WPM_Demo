<template>
  <div class="line-chart" @mouseleave="onChartLeave">
    <div
      v-if="hasData && (title || series.length > 1)"
      class="line-chart__header"
    >
      <h4 v-if="title" class="line-chart__title">{{ title }}</h4>
      <div v-if="series.length > 1" class="line-chart__legend" role="group" aria-label="Toggle chart series">
        <button
          v-for="item in series"
          :key="item.key"
          type="button"
          class="line-chart__legend-item"
          :class="{ 'line-chart__legend-item--hidden': isSeriesHidden(item.key) }"
          :aria-pressed="!isSeriesHidden(item.key)"
          :title="`${isSeriesHidden(item.key) ? 'Show' : 'Hide'} ${item.label}`"
          @click="toggleSeries(item.key)"
        >
          <span
            class="line-chart__legend-dot"
            :style="{ backgroundColor: isSeriesHidden(item.key) ? '#cbd5e1' : item.color }"
          />
          {{ item.label }}
        </button>
      </div>
    </div>

    <div v-if="hasData" ref="chartWrapRef" class="line-chart__canvas">
      <svg
        ref="svgRef"
        class="line-chart__svg"
        :viewBox="`0 0 ${layoutWidth} ${height}`"
        role="img"
        aria-label="Line chart"
        @mousemove="onChartMove"
        @touchmove.prevent="onChartTouch"
        @touchend="onChartLeave"
      >
      <g v-if="leftScale" v-for="(tick, index) in leftScale.ticks" :key="`grid-${index}`">
        <line
          :x1="padLeft"
          :x2="layoutWidth - padRight"
          :y1="yPosLeft(tick)"
          :y2="yPosLeft(tick)"
          class="line-chart__grid-line"
        />
        <text
          :x="padLeft - 10"
          :y="yPosLeft(tick) + 4"
          class="line-chart__axis-label line-chart__axis-label--y"
          text-anchor="end"
        >
          {{ formatAxisValue(tick, 'left') }}
        </text>
      </g>

      <g v-if="dualAxis && rightScale && hasVisibleRightSeries">
        <text
          v-for="(tick, index) in rightScale.ticks"
          :key="`right-${index}`"
          :x="layoutWidth - padRight + 10"
          :y="yPosRight(tick) + 4"
          class="line-chart__axis-label line-chart__axis-label--y line-chart__axis-label--y-right"
          text-anchor="start"
        >
          {{ formatAxisValue(tick, 'right') }}
        </text>
      </g>

      <g v-for="seriesItem in visibleNormalizedSeries" :key="seriesItem.key">
        <path
          :d="seriesItem.path"
          fill="none"
          :stroke="seriesItem.color"
          class="line-chart__line"
        />
      </g>

      <g v-if="hoveredIndex >= 0">
        <line
          :x1="activeX"
          :x2="activeX"
          :y1="padTop"
          :y2="height - padBottom"
          class="line-chart__cursor-line"
        />

        <g v-for="seriesItem in visibleNormalizedSeries" :key="`focus-${seriesItem.key}`">
          <circle
            v-if="seriesItem.coords[activeIndex]"
            :cx="seriesItem.coords[activeIndex].x"
            :cy="seriesItem.coords[activeIndex].y"
            r="4"
            class="line-chart__focus-dot"
            :style="{ stroke: seriesItem.color }"
          />
        </g>

        <g v-if="showTooltip" :transform="`translate(${tooltipX}, ${tooltipY})`">
          <rect
            class="line-chart__tooltip-box"
            :x="-tooltipWidth / 2"
            y="0"
            :width="tooltipWidth"
            :height="tooltipHeight"
            rx="6"
          />
          <polygon
            class="line-chart__tooltip-caret"
            :points="`${-tooltipCaretWidth / 2},${tooltipHeight} ${tooltipCaretWidth / 2},${tooltipHeight} 0,${tooltipHeight + tooltipCaretHeight}`"
          />
          <text :x="0" :y="13" class="line-chart__tooltip-label" text-anchor="middle">
            {{ activeLabel }}
          </text>
          <text
            v-for="(row, index) in tooltipRows"
            :key="row.key"
            :x="0"
            :y="24 + index * 12"
            class="line-chart__tooltip-value"
            :class="{ 'line-chart__tooltip-value--secondary': index > 0 }"
            text-anchor="middle"
          >
            {{ row.text }}
          </text>
        </g>
      </g>

      <g v-for="(label, index) in labels" :key="`label-${label}-${index}`">
        <text
          v-show="showXAxisLabel(index)"
          :x="xPos(index)"
          :y="height - 6"
          class="line-chart__axis-label line-chart__axis-label--x"
          :class="{ 'line-chart__axis-label--x-active': hoveredIndex >= 0 && index === activeIndex }"
          text-anchor="middle"
        >
          {{ formatXLabel(label) }}
        </text>
      </g>

      <rect
        :x="padLeft"
        :y="padTop"
        :width="layoutWidth - padLeft - padRight"
        :height="height - padTop - padBottom"
        class="line-chart__hit-area"
        @mousemove="onChartMove"
        @mouseleave="onChartLeave"
      />
    </svg>
    </div>

    <p v-else class="line-chart__empty">{{ emptyText }}</p>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  labels: { type: Array, default: () => [] },
  series: { type: Array, default: () => [] },
  valueFormatter: {
    type: Function,
    default: (value) => String(Math.round(Number(value) || 0))
  },
  emptyText: { type: String, default: 'No chart data available.' },
  dualAxis: { type: Boolean, default: false },
  title: { type: String, default: '' }
})

const layoutWidth = ref(720)
const height = 168
const padTop = 8
const padBottom = 26
const tooltipWidth = 112
const tooltipCaretWidth = 10
const tooltipCaretHeight = 5

const padLeft = computed(() => (props.dualAxis ? 28 : 36))
const padRight = computed(() => (props.dualAxis ? 24 : 12))

const chartWrapRef = ref(null)
const svgRef = ref(null)
const hoveredIndex = ref(-1)
const hiddenKeys = ref([])

const hiddenKeySet = computed(() => new Set(hiddenKeys.value))

const isSeriesHidden = (key) => hiddenKeySet.value.has(key)

const visibleSeries = computed(() =>
  props.series.filter((item) => !hiddenKeySet.value.has(item.key))
)

const hasVisibleRightSeries = computed(() =>
  visibleSeries.value.some((item) => item.yAxis === 'right')
)

const toggleSeries = (key) => {
  const next = new Set(hiddenKeySet.value)
  if (next.has(key)) {
    next.delete(key)
  } else if (visibleSeries.value.length <= 1) {
    return
  } else {
    next.add(key)
  }
  hiddenKeys.value = [...next]
}

const hasData = computed(() => props.labels.length > 0 && props.series.length > 0)

let resizeObserver = null

const syncLayoutWidth = () => {
  const node = chartWrapRef.value
  if (!node) return
  const nextWidth = Math.round(node.getBoundingClientRect().width)
  if (nextWidth > 0 && nextWidth !== layoutWidth.value) {
    layoutWidth.value = nextWidth
  }
}

const bindResizeObserver = () => {
  if (typeof ResizeObserver === 'undefined' || !chartWrapRef.value || resizeObserver) return

  resizeObserver = new ResizeObserver(() => {
    syncLayoutWidth()
  })
  resizeObserver.observe(chartWrapRef.value)
  syncLayoutWidth()
}

onMounted(async () => {
  await nextTick()
  bindResizeObserver()
})

onUnmounted(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
})

watch(
  () => props.series.map((item) => item.key).join('|'),
  () => {
    hiddenKeys.value = []
  }
)

watch(
  () => hasData.value,
  async (ready) => {
    if (!ready) return
    await nextTick()
    bindResizeObserver()
    syncLayoutWidth()
  },
  { immediate: true }
)

const defaultSeriesColors = ['#161616', '#b8d96e', '#0077b8']

const buildScale = (values) => {
  const nums = values.map((value) => Number(value) || 0)
  const max = Math.max(...nums, 1)
  const rawStep = max / 4
  const magnitude = 10 ** Math.floor(Math.log10(rawStep || 1))
  const step = Math.max(Math.ceil(rawStep / magnitude) * magnitude, 1)
  const top = step * 4
  return { top, ticks: [0, step, step * 2, step * 3, top] }
}

const leftSeriesValues = computed(() =>
  visibleSeries.value
    .filter((item) => !props.dualAxis || item.yAxis !== 'right')
    .flatMap((item) => item.values ?? [])
)

const rightSeriesValues = computed(() =>
  visibleSeries.value.filter((item) => item.yAxis === 'right').flatMap((item) => item.values ?? [])
)

const leftScale = computed(() => {
  if (!leftSeriesValues.value.length) return null
  return buildScale(leftSeriesValues.value)
})

const rightScale = computed(() => {
  if (!props.dualAxis || !rightSeriesValues.value.length) return null
  return buildScale(rightSeriesValues.value)
})

const yPosForScale = (value, scale) => {
  const usableHeight = height - padTop - padBottom
  const top = scale?.top || 1
  return padTop + (1 - (Number(value) || 0) / top) * usableHeight
}

const yPosLeft = (value) => yPosForScale(value, leftScale.value)

const yPosRight = (value) => yPosForScale(value, rightScale.value)

const yPosForSeries = (value, seriesItem) => {
  if (props.dualAxis && seriesItem.yAxis === 'right') {
    return yPosRight(value)
  }
  return yPosLeft(value)
}

const formatAxisValue = (tick, axis) => {
  const seriesForAxis = visibleSeries.value.find(
    (item) => (axis === 'right' ? item.yAxis === 'right' : item.yAxis !== 'right')
  )
  const formatter = seriesForAxis?.valueFormatter || props.valueFormatter
  return formatter(tick)
}

const xPos = (index) => {
  const usableWidth = layoutWidth.value - padLeft.value - padRight.value
  const denominator = Math.max(props.labels.length - 1, 1)
  return padLeft.value + (usableWidth * index) / denominator
}

const showXAxisLabel = (index) => {
  const total = props.labels.length
  if (total <= 8) return true
  return index % 2 === 0 || index === total - 1
}

const formatXLabel = (label) => {
  const text = String(label || '')
  const match = text.match(/^([A-Za-z]{3})/)
  return match ? match[1] : text
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

const normalizedSeries = computed(() => {
  const chartWidth = layoutWidth.value
  const left = padLeft.value
  const right = padRight.value

  return props.series
    .filter((item) => !hiddenKeySet.value.has(item.key))
    .map((seriesItem, index) => {
    const coords = (seriesItem.values ?? []).map((value, pointIndex) => ({
      x: left + ((chartWidth - left - right) * pointIndex) / Math.max(props.labels.length - 1, 1),
      y: yPosForSeries(value, seriesItem)
    }))

    return {
      ...seriesItem,
      color: seriesItem.color || defaultSeriesColors[index % defaultSeriesColors.length],
      coords,
      path: smoothPath(coords)
    }
  })
})

const visibleNormalizedSeries = computed(() =>
  normalizedSeries.value.filter((item) => !hiddenKeySet.value.has(item.key))
)

const activeIndex = computed(() => hoveredIndex.value)
const activeX = computed(() => {
  const chartWidth = layoutWidth.value
  const usableWidth = chartWidth - padLeft.value - padRight.value
  const denominator = Math.max(props.labels.length - 1, 1)
  return padLeft.value + (usableWidth * activeIndex.value) / denominator
})
const activeLabel = computed(() => props.labels[activeIndex.value] ?? '')

const tooltipRows = computed(() => {
  if (activeIndex.value < 0) return []
  return visibleNormalizedSeries.value.map((seriesItem) => {
    const value = Number(seriesItem.values?.[activeIndex.value]) || 0
    const formatter = seriesItem.valueFormatter || props.valueFormatter
    return {
      key: seriesItem.key,
      text: `${seriesItem.label}: ${formatter(value)}`
    }
  })
})

const tooltipHeight = computed(() =>
  normalizedSeries.value.length > 1 ? 28 + normalizedSeries.value.length * 12 : 34
)

const safeCoord = (value, fallback = 0) => {
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : fallback
}

const primaryFocusY = computed(() => {
  const primary = visibleNormalizedSeries.value[0]?.coords?.[activeIndex.value]
  return safeCoord(primary?.y, padTop + 12)
})

const tooltipX = computed(() => {
  const minX = padLeft.value + tooltipWidth / 2 + 4
  const maxX = layoutWidth.value - padRight.value - tooltipWidth / 2 - 4
  return safeCoord(Math.min(Math.max(activeX.value, minX), maxX), minX)
})

const tooltipY = computed(() =>
  safeCoord(Math.max(padTop, primaryFocusY.value - tooltipHeight.value - 10), padTop)
)

const showTooltip = computed(() =>
  Number.isFinite(tooltipX.value) && Number.isFinite(tooltipY.value)
)

const resolveIndexFromClientX = (clientX) => {
  const svg = svgRef.value
  if (!svg || !props.labels.length) return -1

  const rect = svg.getBoundingClientRect()
  const relativeX = ((clientX - rect.left) / rect.width) * layoutWidth.value

  let nearest = 0
  let nearestDistance = Infinity
  for (let index = 0; index < props.labels.length; index += 1) {
    const distance = Math.abs(xPos(index) - relativeX)
    if (distance < nearestDistance) {
      nearestDistance = distance
      nearest = index
    }
  }
  return nearest
}

const onChartMove = (event) => {
  hoveredIndex.value = resolveIndexFromClientX(event.clientX)
}

const onChartTouch = (event) => {
  const touch = event.touches?.[0]
  if (!touch) return
  hoveredIndex.value = resolveIndexFromClientX(touch.clientX)
}

const onChartLeave = () => {
  hoveredIndex.value = -1
}

watch(
  () => props.labels.length,
  () => {
    hoveredIndex.value = -1
  }
)
</script>

<style scoped>
.line-chart {
  display: grid;
  gap: 4px;
  min-height: 0;
  width: 100%;
}

.line-chart__canvas {
  width: 100%;
}

.line-chart__svg {
  display: block;
  height: 168px;
  overflow: visible;
  width: 100%;
}

.line-chart__header {
  align-items: center;
  display: flex;
  gap: 12px;
  justify-content: space-between;
  min-height: 24px;
}

.line-chart__title {
  color: #161616;
  font-size: 14px;
  font-weight: 700;
  margin: 0;
}

.line-chart__legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  justify-content: flex-end;
  margin-left: auto;
  max-width: 72%;
}

.line-chart__legend-item {
  align-items: center;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 999px;
  color: #6c757d;
  cursor: pointer;
  display: inline-flex;
  font-size: 10px;
  font-weight: 500;
  gap: 5px;
  padding: 3px 8px;
  transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}

.line-chart__legend-item:hover {
  background: rgba(22, 22, 22, 0.04);
  border-color: rgba(22, 22, 22, 0.08);
}

.line-chart__legend-item--hidden {
  color: #94a3b8;
  opacity: 0.72;
  text-decoration: line-through;
}

.line-chart__legend-item[title] {
  cursor: pointer;
}

.line-chart__legend-dot {
  border-radius: 999px;
  flex-shrink: 0;
  height: 7px;
  width: 7px;
}

.line-chart__grid-line {
  stroke: rgba(148, 163, 184, 0.32);
  stroke-dasharray: 3 4;
  stroke-width: 1;
}

.line-chart__axis-label {
  fill: #94a3b8;
  font-size: 10px;
}

.line-chart__axis-label--y {
  font-variant-numeric: tabular-nums;
}

.line-chart__axis-label--y-right {
  fill: #b8d96e;
}

.line-chart__axis-label--x {
  fill: #94a3b8;
  font-size: 10px;
  font-weight: 500;
}

.line-chart__axis-label--x-active {
  fill: #161616;
  font-weight: 700;
}

.line-chart__line {
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 2;
}

.line-chart__cursor-line {
  stroke: rgba(148, 163, 184, 0.75);
  stroke-dasharray: 4 4;
  stroke-width: 1;
}

.line-chart__focus-dot {
  fill: #fff;
  stroke-width: 2;
}

.line-chart__tooltip-box {
  fill: #161616;
}

.line-chart__tooltip-caret {
  fill: #161616;
}

.line-chart__tooltip-label {
  fill: rgba(255, 255, 255, 0.62);
  font-size: 9px;
  font-weight: 500;
}

.line-chart__tooltip-value {
  fill: #fff;
  font-size: 10px;
  font-weight: 600;
}

.line-chart__tooltip-value--secondary {
  fill: rgba(255, 255, 255, 0.9);
  font-size: 10px;
  font-weight: 500;
}

.line-chart__hit-area {
  cursor: crosshair;
  fill: transparent;
}

.line-chart__empty {
  color: #6c757d;
  font-size: 13px;
  margin: 0;
  padding: 24px 0;
}
</style>
