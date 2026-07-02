<template>
  <div class="bubble-panel">
    <svg class="bubble-svg" :viewBox="`0 0 ${width} ${height}`" role="img" aria-label="Task quadrant bubble chart">
      <rect :x="padLeft" :y="padTop" :width="xCut - padLeft" :height="yCut - padTop" fill="#f1f5f9" opacity="0.5" />
      <rect :x="xCut" :y="padTop" :width="width - padRight - xCut" :height="yCut - padTop" fill="#e2e8f0" opacity="0.55" />
      <rect :x="padLeft" :y="yCut" :width="xCut - padLeft" :height="height - padBottom - yCut" fill="#f8fafc" opacity="0.7" />
      <rect :x="xCut" :y="yCut" :width="width - padRight - xCut" :height="height - padBottom - yCut" fill="#eef2f7" opacity="0.6" />

      <line :x1="xCut" :y1="padTop" :x2="xCut" :y2="height - padBottom" stroke="#94a3b8" stroke-dasharray="5 4" />
      <line :x1="padLeft" :y1="yCut" :x2="width - padRight" :y2="yCut" stroke="#94a3b8" stroke-dasharray="5 4" />

      <text :x="padLeft + 10" :y="padTop + 22" class="quad-label">Low GSC · High cost</text>
      <text :x="width - padRight - 10" :y="padTop + 22" class="quad-label quad-label--right">High GSC · High cost</text>
      <text :x="padLeft + 10" :y="height - padBottom - 10" class="quad-label">Low GSC · Low cost</text>
      <text :x="width - padRight - 10" :y="height - padBottom - 10" class="quad-label quad-label--right">High GSC · Low cost</text>

      <g v-for="(tick, index) in yTicks" :key="`y-${index}`">
        <line :x1="padLeft" :x2="width - padRight" :y1="tick.y" :y2="tick.y" stroke="#e2e8f0" opacity="0.5" />
        <text :x="padLeft - 8" :y="tick.y + 4" class="tick-label" text-anchor="end">{{ tick.label }}</text>
      </g>

      <text
        v-for="tick in xTicks"
        :key="`x-${tick}`"
        :x="xPos(tick)"
        :y="height - padBottom + 22"
        class="tick-label"
        text-anchor="middle"
      >
        {{ tick }}%
      </text>

      <text :x="(padLeft + width - padRight) / 2" :y="height - 6" class="axis-title" text-anchor="middle">
        GSC share of task volume →
      </text>
      <text
        :x="18"
        :y="(padTop + height - padBottom) / 2"
        class="axis-title"
        text-anchor="middle"
        :transform="`rotate(-90 18 ${(padTop + height - padBottom) / 2})`"
      >
        Area cost at stake →
      </text>

      <circle
        v-for="(task, index) in tasks"
        :key="task.task"
        :cx="xPos(task.gsc)"
        :cy="yPos(task.areaCost)"
        :r="radius(task.vol)"
        :fill="quadrantColors[task.q]"
        :opacity="activeQuadrant && activeQuadrant !== task.q ? 0.08 : 0.5"
        :stroke="quadrantColors[task.q]"
        :stroke-width="activeQuadrant && activeQuadrant !== task.q ? 0 : 1.3"
        class="bubble"
        @mouseenter="hovered = task"
        @mouseleave="hovered = null"
      >
        <title>{{ task.task }}</title>
      </circle>

      <text
        v-for="task in highlighted"
        :key="`label-${task.task}`"
        :x="xPos(task.gsc)"
        :y="yPos(task.areaCost) - radius(task.vol) - 3"
        class="bubble-label"
        text-anchor="middle"
      >
        {{ task.task.slice(0, 20) }}
      </text>
    </svg>

    <div v-if="hovered" class="bubble-tip">
      <strong>{{ hovered.task }}</strong>
      <span>GSC: {{ hovered.gsc }}% · Area cost: {{ formatMoney(hovered.areaCost) }}</span>
      <span>Modelled diff.: {{ formatMoney(hovered.save) }}/mo · Vol: {{ formatNumber(hovered.vol) }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { formatMoney, formatNumber } from '../../utils/serviceModelFormat'

const props = defineProps({
  tasks: { type: Array, required: true },
  activeQuadrant: { type: String, default: null }
})

const width = 900
const height = 540
const padLeft = 78
const padRight = 28
const padTop = 42
const padBottom = 66
const xCut = 50
const yCut = 10000

const quadrantColors = {
  Q1: '#334155',
  Q2: '#64748b',
  Q3: '#94a3b8',
  Q4: '#b8c2cf'
}

const hovered = ref(null)

const ymax = computed(() => Math.max(...props.tasks.map((t) => t.areaCost), yCut * 1.2))
const vmax = computed(() => Math.max(...props.tasks.map((t) => t.vol)))

const yPos = (value) => padTop + (1 - value / ymax.value) * (height - padTop - padBottom)
const xPos = (value) => padLeft + (value / 100) * (width - padLeft - padRight)
const radius = (vol) => 4 + Math.sqrt(vol / vmax.value) * 27

const yTicks = computed(() =>
  [0, 0.25, 0.5, 0.75, 1].map((ratio) => {
    const value = ymax.value * ratio
    return { y: yPos(value), label: formatMoney(value) }
  })
)

const xTicks = [0, 25, 50, 75, 100]

const highlighted = computed(() =>
  props.tasks.filter((t) => t.q === 'Q1' && (!props.activeQuadrant || props.activeQuadrant === t.q)).slice(0, 5)
)
</script>

<style scoped>
.bubble-svg {
  height: auto;
  width: 100%;
}

.quad-label {
  fill: #475569;
  font-size: 12px;
  font-weight: 800;
  opacity: 0.85;
}

.quad-label--right {
  text-anchor: end;
}

.tick-label {
  fill: #64748b;
  font-size: 10px;
}

.axis-title {
  fill: #334155;
  font-size: 12px;
  font-weight: 700;
}

.bubble {
  cursor: pointer;
}

.bubble-label {
  fill: #334155;
  font-size: 9px;
  font-weight: 600;
}

.bubble-tip {
  background: #0f172a;
  border-radius: 8px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
  color: #fff;
  display: flex;
  flex-direction: column;
  font-size: 12px;
  gap: 4px;
  line-height: 1.5;
  margin-top: 10px;
  max-width: 320px;
  padding: 9px 12px;
}
</style>
