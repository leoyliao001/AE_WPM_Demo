<template>
  <div
    class="donut-chart"
    :class="{ 'donut-chart--compact': compact, 'donut-chart--inline': inline }"
  >
    <div v-if="inline && title" class="donut-chart__header">
      <h4 class="donut-chart__title">{{ title }}</h4>
    </div>

    <div v-if="segments.length" class="donut-chart__layout">
      <svg
        class="donut-chart__svg"
        :viewBox="`0 0 ${chartSize} ${chartSize}`"
        role="img"
        aria-label="Donut chart"
      >
        <circle
          :cx="chartCenter"
          :cy="chartCenter"
          :r="chartRadius"
          class="donut-chart__track"
          :stroke-width="strokeWidth"
        />

        <g :transform="`rotate(-90 ${chartCenter} ${chartCenter})`">
          <circle
            v-for="segment in segments"
            :key="segment.key"
            :cx="chartCenter"
            :cy="chartCenter"
            :r="chartRadius"
            class="donut-chart__segment"
            :stroke="segment.color"
            :stroke-width="strokeWidth"
            :stroke-dasharray="segment.dasharray"
            :stroke-dashoffset="segment.offset"
            :opacity="segmentOpacity(segment)"
            :class="{
              'donut-chart__segment--active': activeKey === segment.key,
              'donut-chart__segment--muted': segment.muted
            }"
            @click="onSegmentSelect(segment)"
          />
        </g>

        <circle :cx="chartCenter" :cy="chartCenter" :r="coreRadius" class="donut-chart__core" />
        <text
          :x="chartCenter"
          :y="chartCenter - (inline ? 5 : 7)"
          class="donut-chart__center-label"
          text-anchor="middle"
        >
          {{ centerLabel }}
        </text>
        <text
          :x="chartCenter"
          :y="chartCenter + (inline ? 14 : 18)"
          class="donut-chart__center-value"
          text-anchor="middle"
        >
          {{ valueFormatter(total) }}
        </text>
      </svg>

      <div class="donut-chart__legend" :class="{ 'donut-chart__legend--inline': inline }">
        <button
          v-for="segment in segments"
          :key="`legend-${segment.key}`"
          type="button"
          class="donut-chart__legend-item"
          :class="{
            'donut-chart__legend-item--active': activeKey === segment.key,
            'donut-chart__legend-item--muted': segment.muted
          }"
          :disabled="segment.muted"
          @click="onSegmentSelect(segment)"
        >
          <span
            class="donut-chart__swatch"
            :style="{ backgroundColor: segment.color }"
            aria-hidden="true"
          />
          <span class="donut-chart__legend-copy">
            <strong>{{ segment.label }}</strong>
            <span v-if="!inline">{{ valueFormatter(segment.value) }} · {{ segment.share }}%</span>
          </span>
        </button>
      </div>
    </div>

    <p v-else class="donut-chart__empty">{{ emptyText }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  activeKey: { type: String, default: '' },
  centerLabel: { type: String, default: 'Total' },
  valueFormatter: {
    type: Function,
    default: (value) => String(Math.round(Number(value) || 0))
  },
  emptyText: { type: String, default: 'No chart data available.' },
  compact: { type: Boolean, default: false },
  inline: { type: Boolean, default: false },
  title: { type: String, default: '' }
})

const emit = defineEmits(['select'])

const onSegmentSelect = (segment) => {
  if (segment?.muted) return
  emit('select', segment.key)
}

const segmentOpacity = (segment) => {
  if (segment.muted) return 1
  if (props.activeKey && props.activeKey !== segment.key) return 0.28
  return 1
}

const chartSize = computed(() => {
  if (props.inline) return 140
  if (props.compact) return 180
  return 220
})

const chartCenter = computed(() => chartSize.value / 2)

const chartRadius = computed(() => {
  if (props.inline) return 50
  if (props.compact) return 58
  return 74
})

const coreRadius = computed(() => {
  if (props.inline) return chartRadius.value - 18
  return chartRadius.value - 18
})

const strokeWidth = computed(() => {
  if (props.inline) return 16
  if (props.compact) return 20
  return 22
})

const circumference = computed(() => 2 * Math.PI * chartRadius.value)

const palette = ['#0B8DBF', '#6DAA28', '#F3B562', '#E85454', '#7B61FF', '#13B0A5']

const segments = computed(() => {
  const source = props.items.filter((item) => Number(item?.value) > 0)
  const totalValue = source.reduce((sum, item) => sum + (Number(item.value) || 0), 0)
  let consumed = 0

  return source.map((item, index) => {
    const value = Number(item.value) || 0
    const arc = totalValue ? (value / totalValue) * circumference.value : 0
    const segment = {
      ...item,
      color: item.color || palette[index % palette.length],
      dasharray: `${arc} ${circumference.value - arc}`,
      offset: -consumed,
      share: totalValue ? ((value / totalValue) * 100).toFixed(0) : '0'
    }
    consumed += arc
    return segment
  })
})

const total = computed(() =>
  segments.value.reduce((sum, segment) => sum + (Number(segment.value) || 0), 0)
)
</script>

<style scoped>
.donut-chart {
  min-height: 260px;
}

.donut-chart__layout {
  align-items: center;
  display: grid;
  gap: 16px;
  grid-template-columns: minmax(0, 220px) minmax(0, 1fr);
}

.donut-chart__svg {
  height: auto;
  max-width: 220px;
  width: 100%;
}

.donut-chart__track {
  fill: none;
  stroke: #eef2f6;
}

.donut-chart__segment {
  cursor: pointer;
  fill: none;
  stroke-linecap: round;
  transition: opacity 0.18s ease;
}

.donut-chart__segment--active {
  opacity: 1 !important;
}

.donut-chart__segment--muted {
  cursor: default;
}

.donut-chart__legend-item--muted {
  cursor: default;
  opacity: 0.72;
}

.donut-chart__legend-item--muted:disabled {
  pointer-events: none;
}

.donut-chart__core {
  fill: #fff;
}

.donut-chart__center-label {
  fill: #94a3b8;
  font-size: 10px;
  font-weight: 500;
}

.donut-chart__center-value {
  fill: #161616;
  font-size: 22px;
  font-weight: 800;
}

.donut-chart__legend {
  display: grid;
  gap: 10px;
}

.donut-chart__legend-item {
  align-items: center;
  background: linear-gradient(180deg, #fff, #fbfdff);
  border: 1px solid rgba(12, 35, 64, 0.08);
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  text-align: left;
  transition: border-color 0.18s ease;
}

.donut-chart__legend-item:hover {
  border-color: rgba(0, 119, 184, 0.2);
}

.donut-chart__legend-item--active {
  background: rgba(0, 119, 184, 0.04);
  border-color: rgba(0, 119, 184, 0.24);
}

.donut-chart__swatch {
  border-radius: 999px;
  flex-shrink: 0;
  height: 10px;
  width: 10px;
}

.donut-chart__legend-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.donut-chart__legend-copy strong {
  color: #334155;
  font-size: 12px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.donut-chart__legend-copy span {
  color: #94a3b8;
  font-size: 11px;
}

.donut-chart__empty {
  color: #6c757d;
  font-size: 13px;
  margin: 0;
  padding: 24px 0;
  text-align: center;
}

.donut-chart--compact {
  min-height: 0;
}

.donut-chart--compact .donut-chart__layout {
  gap: 12px;
  grid-template-columns: 1fr;
}

.donut-chart--compact .donut-chart__svg {
  margin: 0 auto;
  max-width: 180px;
}

.donut-chart--inline {
  display: grid;
  gap: 6px;
  min-height: 0;
  width: 100%;
}

.donut-chart--inline .donut-chart__header {
  align-items: center;
  display: flex;
  min-height: 24px;
}

.donut-chart--inline .donut-chart__title {
  color: #161616;
  font-size: 14px;
  font-weight: 700;
  margin: 0;
}

.donut-chart--inline .donut-chart__layout {
  gap: 8px;
  grid-template-columns: 1fr;
  justify-items: start;
}

.donut-chart--inline .donut-chart__svg {
  display: block;
  height: 140px;
  margin: 0;
  max-width: 140px;
  width: 140px;
}

.donut-chart--inline .donut-chart__center-label {
  font-size: 9px;
}

.donut-chart--inline .donut-chart__center-value {
  font-size: 18px;
  font-weight: 800;
}

.donut-chart--inline .donut-chart__legend {
  gap: 4px;
  justify-items: start;
  width: 100%;
}

.donut-chart--inline .donut-chart__legend--inline {
  display: grid;
  gap: 4px;
}

.donut-chart--inline .donut-chart__legend-item {
  background: transparent;
  border: 0;
  border-radius: 0;
  gap: 8px;
  padding: 2px 0;
}

.donut-chart--inline .donut-chart__legend-item:hover {
  background: transparent;
}

.donut-chart--inline .donut-chart__legend-item--active .donut-chart__legend-copy strong {
  color: #161616;
  font-weight: 700;
}

.donut-chart--inline .donut-chart__legend-copy {
  flex-direction: row;
  gap: 0;
}

.donut-chart--inline .donut-chart__legend-copy strong {
  color: #64748b;
  font-size: 12px;
  font-weight: 500;
}

.donut-chart--inline .donut-chart__swatch {
  height: 8px;
  width: 8px;
}

@media (max-width: 640px) {
  .donut-chart__layout {
    grid-template-columns: 1fr;
  }
}
</style>
