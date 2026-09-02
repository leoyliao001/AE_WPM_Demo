<template>
  <div class="semi-donut">
    <div v-if="segments.length" class="semi-donut__layout">
      <svg
        class="semi-donut__svg"
        :viewBox="`0 0 ${width} ${height}`"
        role="img"
        aria-label="Semi donut chart"
      >
        <path
          :d="trackPath"
          class="semi-donut__track"
          fill="none"
          :stroke-width="strokeWidth"
        />

        <path
          v-for="segment in segments"
          :key="segment.key"
          :d="trackPath"
          class="semi-donut__segment"
          fill="none"
          :stroke="segment.color"
          :stroke-width="strokeWidth"
          :stroke-dasharray="segment.dasharray"
          :stroke-dashoffset="segment.offset"
          :opacity="activeKey && activeKey !== segment.key ? 0.28 : 1"
          @click="$emit('select', segment.key)"
        />

        <text :x="centerX" :y="centerY - 4" class="semi-donut__center-label" text-anchor="middle">
          {{ centerLabel }}
        </text>
        <text :x="centerX" :y="centerY + 16" class="semi-donut__center-value" text-anchor="middle">
          {{ valueFormatter(total) }}
        </text>
      </svg>

      <div class="semi-donut__legend">
        <button
          v-for="segment in segments"
          :key="`legend-${segment.key}`"
          type="button"
          class="semi-donut__legend-item"
          :class="{ 'semi-donut__legend-item--active': activeKey === segment.key }"
          @click="$emit('select', segment.key)"
        >
          <span
            class="semi-donut__swatch"
            :style="{ backgroundColor: segment.color }"
            aria-hidden="true"
          />
          <span class="semi-donut__legend-copy">
            <strong>{{ segment.label }}</strong>
            <span>{{ valueFormatter(segment.value) }} · {{ segment.share }}%</span>
          </span>
        </button>
      </div>
    </div>

    <p v-else class="semi-donut__empty">{{ emptyText }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  activeKey: { type: String, default: '' },
  centerLabel: { type: String, default: 'Projects' },
  valueFormatter: {
    type: Function,
    default: (value) => String(Math.round(Number(value) || 0))
  },
  emptyText: { type: String, default: 'No chart data available.' }
})

defineEmits(['select'])

const width = 220
const height = 128
const centerX = width / 2
const centerY = height - 8
const radius = 78
const strokeWidth = 20
const arcLength = Math.PI * radius

const palette = ['#0077b8', '#13b0a5', '#6daa28', '#f3b562', '#7b61ff', '#e85454', '#94a3b8']

const describeArc = (cx, cy, r) => {
  const startX = cx - r
  const startY = cy
  const endX = cx + r
  const endY = cy
  return `M ${startX} ${startY} A ${r} ${r} 0 0 1 ${endX} ${endY}`
}

const trackPath = describeArc(centerX, centerY, radius)

const segments = computed(() => {
  const source = props.items.filter((item) => Number(item?.value) > 0)
  const totalValue = source.reduce((sum, item) => sum + (Number(item.value) || 0), 0)
  let consumed = 0

  return source.map((item, index) => {
    const value = Number(item.value) || 0
    const arc = totalValue ? (value / totalValue) * arcLength : 0
    const segment = {
      ...item,
      color: item.color || palette[index % palette.length],
      dasharray: `${arc} ${arcLength * 2}`,
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
.semi-donut {
  min-height: 0;
}

.semi-donut__layout {
  display: grid;
  gap: 10px;
}

.semi-donut__svg {
  display: block;
  height: auto;
  margin: 0 auto;
  max-width: 220px;
  width: 100%;
}

.semi-donut__track {
  stroke: #eef3f7;
  stroke-linecap: round;
}

.semi-donut__segment {
  cursor: pointer;
  stroke-linecap: butt;
  transition: opacity 0.18s ease;
}

.semi-donut__center-label {
  fill: #6b7883;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.semi-donut__center-value {
  fill: #13293b;
  font-size: 22px;
  font-weight: 800;
}

.semi-donut__legend {
  display: grid;
  gap: 6px;
}

.semi-donut__legend-item {
  align-items: center;
  background: #fff;
  border: 1px solid rgba(12, 35, 64, 0.07);
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  gap: 8px;
  padding: 7px 9px;
  text-align: left;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.semi-donut__legend-item:hover {
  border-color: rgba(0, 119, 184, 0.18);
  box-shadow: 0 4px 10px rgba(12, 35, 64, 0.05);
}

.semi-donut__legend-item--active {
  background: rgba(0, 119, 184, 0.04);
  border-color: rgba(0, 119, 184, 0.22);
}

.semi-donut__swatch {
  border-radius: 999px;
  flex-shrink: 0;
  height: 10px;
  width: 10px;
}

.semi-donut__legend-copy {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.semi-donut__legend-copy strong {
  color: #162a3b;
  font-size: 11px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.semi-donut__legend-copy span {
  color: #6c7a87;
  font-size: 10px;
}

.semi-donut__empty {
  color: #6c757d;
  font-size: 12px;
  margin: 0;
  padding: 16px 0;
  text-align: center;
}
</style>
