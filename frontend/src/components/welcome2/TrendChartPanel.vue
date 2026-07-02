<template>
  <div class="trend-panel">
    <div class="trend-toggle">
      <mc-button
        v-for="opt in options"
        :key="opt.id"
        :appearance="metric === opt.id ? 'primary' : 'neutral'"
        :variant="metric === opt.id ? 'filled' : 'plain'"
        fit="small"
        :label="opt.label"
        @click="$emit('update:metric', opt.id)"
      />
    </div>

    <svg class="trend-svg" :viewBox="`0 0 ${width} ${height}`" role="img" aria-label="Three month trend chart">
      <g v-for="(tick, index) in yTicks" :key="`y-${index}`">
        <line :x1="padLeft" :x2="width - padRight" :y1="tick.y" :y2="tick.y" class="grid-line" />
        <text :x="padLeft - 8" :y="tick.y + 4" class="axis-label axis-label--y" text-anchor="end">
          {{ tick.label }}
        </text>
      </g>

      <text
        v-for="(month, index) in months"
        :key="month"
        :x="xPos(index)"
        :y="height - 8"
        class="axis-label axis-label--x"
        text-anchor="middle"
      >
        {{ month }}
      </text>

      <polyline
        v-for="series in seriesList"
        :key="series.key"
        :points="series.points"
        fill="none"
        :stroke="series.color"
        stroke-width="2.5"
        stroke-linejoin="round"
      />

      <g v-for="series in seriesList" :key="`${series.key}-dots`">
        <circle
          v-for="(point, index) in series.coords"
          :key="index"
          :cx="point.x"
          :cy="point.y"
          r="4"
          fill="#fff"
          :stroke="series.color"
          stroke-width="2.5"
        />
      </g>
    </svg>

    <div class="legend">
      <span v-for="series in seriesList" :key="`leg-${series.key}`">
        <span class="dot" :style="{ background: series.color }" />
        {{ series.label }}
      </span>
    </div>

    <div class="trend-table-wrap">
      <mc-table
        :data.prop="tableRows"
        :columns.prop="tableColumns"
        datakey="id"
        caption="Trend summary table"
        fit="small"
        height="auto"
        outerborderstyle="solid"
        horizontallinestyle="solid"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatTrendValue } from '../../utils/serviceModelFormat'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-table'

const props = defineProps({
  metric: { type: String, required: true },
  months: { type: Array, required: true },
  series: { type: Object, required: true }
})

defineEmits(['update:metric'])

const options = [
  { id: 'cpt', label: 'Cost / Transaction' },
  { id: 'total_cost', label: 'Total Cost' },
  { id: 'total_vol', label: 'Volume' },
  { id: 'total_fte', label: 'FTE' }
]

const width = 520
const height = 260
const padLeft = 58
const padRight = 18
const padTop = 18
const padBottom = 40

const colors = {
  total: '#0077b8',
  area: '#f3880e',
  gsc: '#00a989'
}

const labels = {
  total: 'Total',
  area: 'Areas',
  gsc: 'GSC'
}

const allValues = computed(() => [
  ...props.series.total,
  ...props.series.area,
  ...props.series.gsc
])

const scale = computed(() => {
  const max = Math.max(...allValues.value)
  const min = Math.min(...allValues.value)
  const pad = (max - min) * 0.15 || max * 0.1
  return { min: Math.max(0, min - pad), max: max + pad }
})

const yPos = (value) => {
  const { min, max } = scale.value
  return padTop + (1 - (value - min) / (max - min)) * (height - padTop - padBottom)
}

const xPos = (index) => padLeft + index * ((width - padLeft - padRight) / (props.months.length - 1))

const yTicks = computed(() =>
  Array.from({ length: 5 }, (_, i) => {
    const value = scale.value.min + ((scale.value.max - scale.value.min) * i) / 4
    return { y: yPos(value), label: formatTrendValue(props.metric, value) }
  })
)

const seriesList = computed(() =>
  ['total', 'area', 'gsc'].map((key) => {
    const coords = props.series[key].map((value, index) => ({ x: xPos(index), y: yPos(value) }))
    return {
      key,
      label: labels[key],
      color: colors[key],
      coords,
      points: coords.map((p) => `${p.x},${p.y}`).join(' ')
    }
  })
)

const tableColumns = [
  { id: 'measure', label: 'Measure', noWrap: true },
  { id: 'feb', label: 'Feb', noWrap: true },
  { id: 'mar', label: 'Mar', noWrap: true },
  { id: 'apr', label: 'Apr', noWrap: true },
  { id: 'delta', label: 'Δ', noWrap: true }
]

const tableRows = computed(() =>
  ['total', 'area', 'gsc'].map((key) => {
    const values = props.series[key]
    const first = values[0]
    const last = values[values.length - 1]
    const pct = first ? ((last - first) / first) * 100 : 0
    const arrow = last > first ? '▲' : last < first ? '▼' : '–'
    return {
      id: key,
      measure: labels[key],
      feb: formatTrendValue(props.metric, values[0]),
      mar: formatTrendValue(props.metric, values[1]),
      apr: formatTrendValue(props.metric, values[2]),
      delta: `${arrow} ${Math.abs(pct).toFixed(1)}%`
    }
  })
)
</script>

<style scoped>
.trend-toggle {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.trend-svg {
  height: auto;
  width: 100%;
}

.grid-line {
  stroke: #eef2f7;
}

.axis-label {
  fill: #94a3b8;
  font-size: 10px;
}

.axis-label--x {
  fill: #475569;
  font-size: 12px;
  font-weight: 600;
}

.legend {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  display: flex;
  flex-wrap: wrap;
  font-size: 12px;
  gap: 16px;
  justify-content: center;
  margin-top: 10px;
}

.legend span {
  align-items: center;
  display: inline-flex;
  gap: 6px;
}

.dot {
  border-radius: 50%;
  display: inline-block;
  height: 12px;
  width: 12px;
}

.trend-table-wrap {
  margin-top: 12px;
}
</style>
