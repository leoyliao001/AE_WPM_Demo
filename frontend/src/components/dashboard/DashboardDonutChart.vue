<template>
  <div class="donut-chart">
    <div v-if="segments.length" class="donut-chart__layout">
      <svg
        class="donut-chart__svg"
        :viewBox="`0 0 ${size} ${size}`"
        role="img"
        aria-label="Donut chart"
      >
        <defs>
          <filter id="donut-shadow" x="-30%" y="-30%" width="160%" height="160%">
            <feDropShadow dx="0" dy="2" stdDeviation="2.4" flood-opacity="0.1" />
          </filter>
        </defs>

        <circle :cx="center" :cy="center" :r="radius + 14" class="donut-chart__halo" />
        <circle :cx="center" :cy="center" :r="radius" class="donut-chart__track" />

        <g :transform="`rotate(-90 ${center} ${center})`" filter="url(#donut-shadow)">
          <circle
            v-for="segment in segments"
            :key="segment.key"
            :cx="center"
            :cy="center"
            :r="radius"
            class="donut-chart__segment"
            :class="{ 'donut-chart__segment--active': activeKey === segment.key }"
            :stroke="segment.color"
            :stroke-dasharray="segment.dasharray"
            :stroke-dashoffset="segment.offset"
            :opacity="activeKey && activeKey !== segment.key ? 0.26 : 1"
            @click="$emit('select', segment.key)"
          />
        </g>

        <circle :cx="center" :cy="center" :r="radius - 18" class="donut-chart__core" />
        <text :x="center" :y="center - 7" class="donut-chart__center-label" text-anchor="middle">
          {{ centerLabel }}
        </text>
        <text :x="center" :y="center + 18" class="donut-chart__center-value" text-anchor="middle">
          {{ valueFormatter(total) }}
        </text>
      </svg>

      <div class="donut-chart__legend">
        <button
          v-for="segment in segments"
          :key="`legend-${segment.key}`"
          type="button"
          class="donut-chart__legend-item"
          :class="{ 'donut-chart__legend-item--active': activeKey === segment.key }"
          @click="$emit('select', segment.key)"
        >
          <span
            class="donut-chart__swatch"
            :style="{ backgroundColor: segment.color }"
            aria-hidden="true"
          />
          <span class="donut-chart__legend-copy">
            <strong>{{ segment.label }}</strong>
            <span>{{ valueFormatter(segment.value) }} · {{ segment.share }}%</span>
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
  emptyText: { type: String, default: 'No chart data available.' }
})

defineEmits(['select'])

const size = 220
const center = size / 2
const radius = 74
const circumference = 2 * Math.PI * radius

const palette = ['#0B8DBF', '#6DAA28', '#F3B562', '#E85454', '#7B61FF', '#13B0A5']

const segments = computed(() => {
  const source = props.items.filter((item) => Number(item?.value) > 0)
  const totalValue = source.reduce((sum, item) => sum + (Number(item.value) || 0), 0)
  let consumed = 0

  return source.map((item, index) => {
    const value = Number(item.value) || 0
    const arc = totalValue ? (value / totalValue) * circumference : 0
    const segment = {
      ...item,
      color: item.color || palette[index % palette.length],
      dasharray: `${arc} ${circumference - arc}`,
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

.donut-chart__halo {
  fill: none;
  stroke: rgba(11, 141, 191, 0.08);
  stroke-width: 2;
}

.donut-chart__track {
  fill: none;
  stroke: #eef3f7;
  stroke-width: 22;
}

.donut-chart__segment {
  cursor: pointer;
  fill: none;
  stroke-linecap: round;
  stroke-width: 22;
  transition: opacity 0.18s ease, stroke-width 0.18s ease;
}

.donut-chart__segment--active {
  stroke-width: 24;
}

.donut-chart__core {
  fill: #fff;
  stroke: rgba(12, 35, 64, 0.05);
}

.donut-chart__center-label {
  fill: #6b7883;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.donut-chart__center-value {
  fill: #13293b;
  font-size: 24px;
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
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.donut-chart__legend-item:hover {
  box-shadow: 0 6px 14px rgba(12, 35, 64, 0.06);
  transform: translateY(-1px);
}

.donut-chart__legend-item--active {
  background: rgba(11, 141, 191, 0.05);
  border-color: rgba(11, 141, 191, 0.24);
}

.donut-chart__swatch {
  border-radius: 999px;
  display: inline-flex;
  flex-shrink: 0;
  height: 12px;
  width: 12px;
}

.donut-chart__legend-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.donut-chart__legend-copy strong {
  color: #162a3b;
  font-size: 13px;
}

.donut-chart__legend-copy span {
  color: #6c7a87;
  font-size: 12px;
}

.donut-chart__empty {
  color: #6c757d;
  font-size: 13px;
  margin: 0;
  padding: 24px 0;
}

@media (max-width: 640px) {
  .donut-chart__layout {
    grid-template-columns: 1fr;
  }
}
</style>
