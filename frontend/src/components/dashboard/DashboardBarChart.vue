<template>
  <div class="bar-chart">
    <svg
      v-if="chartItems.length"
      class="bar-chart__svg"
      :viewBox="`0 0 ${width} ${height}`"
      role="img"
      aria-label="Bar chart"
    >
      <defs>
        <linearGradient id="bar-chart-fill" x1="0" x2="1">
          <stop offset="0%" stop-color="#0b8dbf" />
          <stop offset="100%" stop-color="#0077b8" />
        </linearGradient>
        <linearGradient id="bar-chart-fill-muted" x1="0" x2="1">
          <stop offset="0%" stop-color="#b8d8e9" />
          <stop offset="100%" stop-color="#d8e7f0" />
        </linearGradient>
      </defs>

      <rect
        :x="padLeft"
        :y="padTop"
        :width="width - padLeft - padRight"
        :height="height - padTop - padBottom"
        class="bar-chart__plot-bg"
        rx="16"
      />

      <g v-for="(tick, index) in yTicks" :key="`tick-${index}`">
        <line
          :x1="padLeft"
          :x2="width - padRight"
          :y1="yPos(tick.value)"
          :y2="yPos(tick.value)"
          class="bar-chart__grid-line"
        />
        <text
          :x="padLeft - 8"
          :y="yPos(tick.value) + 4"
          class="bar-chart__axis-label"
          text-anchor="end"
        >
          {{ valueFormatter(tick.value) }}
        </text>
      </g>

      <g v-for="(item, index) in chartItems" :key="item.key">
        <rect
          class="bar-chart__track"
          :x="barX(index)"
          :y="padTop"
          :width="barWidth"
          :height="height - padTop - padBottom"
          rx="14"
        />
        <rect
          class="bar-chart__bar"
          :class="{ 'bar-chart__bar--active': activeKey === item.key }"
          :x="barX(index)"
          :y="yPos(item.value)"
          :width="barWidth"
          :height="Math.max(0, height - padBottom - yPos(item.value))"
          :fill="item.color || 'url(#bar-chart-fill)'"
          :opacity="activeKey && activeKey !== item.key ? 0.35 : 0.95"
          rx="14"
          @click="$emit('select', item.key)"
        />

        <text
          :x="barX(index) + barWidth / 2"
          :y="yPos(item.value) - 8"
          class="bar-chart__value-label"
          text-anchor="middle"
        >
          {{ valueFormatter(item.value) }}
        </text>

        <text
          :x="barX(index) + barWidth / 2"
          :y="height - padBottom + 20"
          class="bar-chart__axis-label bar-chart__axis-label--x"
          text-anchor="middle"
        >
          {{ item.shortLabel || item.label }}
        </text>
      </g>
    </svg>

    <p v-else class="bar-chart__empty">{{ emptyText }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  activeKey: { type: String, default: '' },
  valueFormatter: {
    type: Function,
    default: (value) => String(Math.round(Number(value) || 0))
  },
  emptyText: { type: String, default: 'No chart data available.' }
})

defineEmits(['select'])

const width = 640
const height = 258
const padLeft = 50
const padRight = 18
const padTop = 24
const padBottom = 54

const chartItems = computed(() => props.items.filter((item) => Number(item?.value) > 0))
const maxValue = computed(() => Math.max(...chartItems.value.map((item) => Number(item.value) || 0), 1))
const chartWidth = computed(() => width - padLeft - padRight)
const stepWidth = computed(() => chartWidth.value / Math.max(chartItems.value.length, 1))
const barWidth = computed(() => Math.max(24, Math.min(56, stepWidth.value * 0.58)))

const yPos = (value) => {
  const safeValue = Number(value) || 0
  const usableHeight = height - padTop - padBottom
  return padTop + (1 - safeValue / maxValue.value) * usableHeight
}

const barX = (index) => padLeft + stepWidth.value * index + (stepWidth.value - barWidth.value) / 2

const yTicks = computed(() =>
  Array.from({ length: 5 }, (_, index) => {
    const ratio = index / 4
    const value = Math.round(maxValue.value * (1 - ratio))
    return { value }
  })
)
</script>

<style scoped>
.bar-chart {
  min-height: 258px;
}

.bar-chart__svg {
  height: auto;
  width: 100%;
}

.bar-chart__plot-bg {
  fill: #fcfdff;
  stroke: rgba(12, 35, 64, 0.06);
}

.bar-chart__grid-line {
  stroke: rgba(126, 151, 169, 0.2);
}

.bar-chart__track {
  fill: #eef4f8;
}

.bar-chart__axis-label {
  fill: #6e7c88;
  font-size: 10px;
}

.bar-chart__axis-label--x {
  fill: #425364;
  font-size: 10px;
  font-weight: 600;
}

.bar-chart__value-label {
  fill: #203040;
  font-size: 10px;
  font-weight: 700;
}

.bar-chart__bar {
  cursor: pointer;
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.bar-chart__bar:hover,
.bar-chart__bar--active {
  opacity: 1;
  transform: translateY(-1px);
}

.bar-chart__empty {
  color: #6c757d;
  font-size: 13px;
  margin: 0;
  padding: 24px 0;
}
</style>
