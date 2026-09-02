<template>
  <div class="bar-chart">
    <div v-if="chartItems.length" ref="chartWrapRef" class="bar-chart__canvas">
      <svg
        ref="svgRef"
        class="bar-chart__svg"
        :viewBox="`0 0 ${layoutWidth} ${height}`"
        role="img"
        aria-label="Bar chart"
      >
        <g v-for="(tick, index) in yTicks" :key="`tick-${index}`">
          <line
            :x1="padLeft"
            :x2="layoutWidth - padRight"
            :y1="yPos(tick.value)"
            :y2="yPos(tick.value)"
            class="bar-chart__grid-line"
          />
          <text
            :x="padLeft - 8"
            :y="yPos(tick.value) + 4"
            class="bar-chart__axis-label bar-chart__axis-label--y"
            text-anchor="end"
          >
            {{ valueFormatter(tick.value) }}
          </text>
        </g>

        <g v-for="(item, index) in chartItems" :key="item.key">
          <rect
            class="bar-chart__bar"
            :class="{
              'bar-chart__bar--active': activeKey === item.key,
              'bar-chart__bar--muted': item.muted
            }"
            :x="barX(index)"
            :y="yPos(item.value)"
            :width="barWidth"
            :height="Math.max(0, height - padBottom - yPos(item.value))"
            :fill="item.color || '#0077b8'"
            :opacity="barOpacity(item)"
            :rx="barRadius"
            @click="onBarSelect(item)"
          >
            <title>{{ item.label }}</title>
          </rect>

          <text
            v-if="item.value > 0"
            :x="barX(index) + barWidth / 2"
            :y="Math.max(padTop + 10, yPos(item.value) - 6)"
            class="bar-chart__value-label"
            text-anchor="middle"
          >
            {{ valueFormatter(item.value) }}
          </text>

          <text
            :x="barX(index) + barWidth / 2"
            :y="height - 8"
            class="bar-chart__axis-label bar-chart__axis-label--x"
            :class="{ 'bar-chart__axis-label--x-active': activeKey === item.key }"
            text-anchor="middle"
          >
            {{ item.shortLabel || item.label }}
          </text>
        </g>
      </svg>
    </div>

    <p v-else class="bar-chart__empty">{{ emptyText }}</p>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  activeKey: { type: String, default: '' },
  valueFormatter: {
    type: Function,
    default: (value) => String(Math.round(Number(value) || 0))
  },
  emptyText: { type: String, default: 'No chart data available.' }
})

const emit = defineEmits(['select'])

const layoutWidth = ref(640)
const height = 220
const padLeft = 36
const padRight = 12
const padTop = 12
const padBottom = 28
const barRadius = 4

const chartWrapRef = ref(null)
const svgRef = ref(null)

const chartItems = computed(() =>
  props.items.filter((item) => Number(item?.value) > 0)
)

const hasData = computed(() => chartItems.value.length > 0)

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
  () => hasData.value,
  async (ready) => {
    if (!ready) return
    await nextTick()
    bindResizeObserver()
    syncLayoutWidth()
  },
  { immediate: true }
)

const maxValue = computed(() =>
  Math.max(...chartItems.value.map((item) => Number(item.value) || 0), 1)
)

const chartWidth = computed(() => layoutWidth.value - padLeft - padRight)
const stepWidth = computed(() => chartWidth.value / Math.max(chartItems.value.length, 1))
const barWidth = computed(() =>
  Math.max(18, Math.min(48, stepWidth.value * 0.62))
)

const buildYScale = () => {
  const max = maxValue.value
  const rawStep = max / 4
  const magnitude = 10 ** Math.floor(Math.log10(rawStep || 1))
  const step = Math.max(Math.ceil(rawStep / magnitude) * magnitude, 1)
  const top = step * 4
  return { top, ticks: [0, step, step * 2, step * 3, top] }
}

const yScale = computed(() => buildYScale())

const yTicks = computed(() =>
  yScale.value.ticks.map((value) => ({ value }))
)

const yPos = (value) => {
  const usableHeight = height - padTop - padBottom
  const top = yScale.value.top || 1
  return padTop + (1 - (Number(value) || 0) / top) * usableHeight
}

const barX = (index) =>
  padLeft + stepWidth.value * index + (stepWidth.value - barWidth.value) / 2

const barOpacity = (item) => {
  if (item.muted) return 0.55
  if (props.activeKey && props.activeKey !== item.key) return 0.38
  return 1
}

const onBarSelect = (item) => {
  if (item?.muted) return
  emit('select', item.key)
}
</script>

<style scoped>
.bar-chart {
  min-height: 220px;
  width: 100%;
}

.bar-chart__canvas {
  width: 100%;
}

.bar-chart__svg {
  display: block;
  height: 220px;
  overflow: visible;
  width: 100%;
}

.bar-chart__grid-line {
  stroke: rgba(148, 163, 184, 0.32);
  stroke-dasharray: 3 4;
  stroke-width: 1;
}

.bar-chart__axis-label {
  fill: #94a3b8;
  font-size: 10px;
}

.bar-chart__axis-label--y {
  font-variant-numeric: tabular-nums;
}

.bar-chart__axis-label--x {
  font-size: 10px;
  font-weight: 500;
}

.bar-chart__axis-label--x-active {
  fill: #161616;
  font-weight: 700;
}

.bar-chart__value-label {
  fill: #64748b;
  font-size: 9px;
  font-weight: 600;
}

.bar-chart__bar {
  cursor: pointer;
  transition: opacity 0.18s ease;
}

.bar-chart__bar--muted {
  cursor: default;
}

.bar-chart__bar:hover:not(.bar-chart__bar--muted),
.bar-chart__bar--active {
  opacity: 1 !important;
}

.bar-chart__empty {
  color: #6c757d;
  font-size: 13px;
  margin: 0;
  padding: 24px 0;
  text-align: center;
}
</style>
