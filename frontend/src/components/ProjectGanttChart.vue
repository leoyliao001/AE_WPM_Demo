<template>
  <div
    class="gantt"
    :class="{ 'gantt--editable': editable }"
    role="region"
    aria-label="Project Gantt chart"
  >
    <div class="gantt-summary" role="group" aria-label="Project parameters">
      <div v-if="editable" class="gantt-summary__cue" aria-hidden="true">
        <span class="gantt-summary__cue-icon">✎</span>
        <span>Editable — click a value to type, then Save</span>
      </div>
      <label
        v-for="field in summaryFields"
        :key="field.key"
        class="gantt-summary__item"
        :class="{ 'gantt-summary__item--editable': editable }"
        :title="editable ? `Edit ${fieldLabels[field.key]}` : fieldLabels[field.key]"
      >
        <span class="gantt-summary__dot" :style="{ background: field.color }" />
        <span class="gantt-summary__name">{{ fieldLabels[field.key] }}</span>
        <input
          class="gantt-summary__value"
          :type="field.type"
          :inputmode="field.type === 'number' ? 'decimal' : 'text'"
          :step="field.type === 'number' ? 'any' : undefined"
          :value="metaValue(field.key)"
          :readonly="!editable"
          :placeholder="editable ? 'Type…' : ''"
          :aria-label="fieldLabels[field.key]"
          @input="onMetaInput(field.key, field.type, $event)"
        />
      </label>
    </div>

    <div v-if="editable" class="gantt-editor">
      <p class="gantt-hint">
        Only <strong>Plan</strong> is editable. Standard is fixed. Actual updates from
        completion. Drag Plan <strong>ends</strong> to resize, or drag the
        <strong>bar</strong> to move.
      </p>

      <div v-if="selectedTask" class="gantt-inspector">
        <div class="gantt-inspector__title" :title="selectedTask.name">
          {{ selectedTask.name }}
        </div>
        <label class="gantt-inspector__field">
          <span>Plan start</span>
          <select
            :value="selectedTask.plan?.startWeek"
            @change="onSelectPlanWeek(selectedTask.id, 'start', $event)"
          >
            <option v-for="week in weeks" :key="`s-${week.index}`" :value="week.index">
              {{ week.timelineWeek }} ({{ week.calendarWeek }})
            </option>
          </select>
        </label>
        <label class="gantt-inspector__field">
          <span>Plan end</span>
          <select
            :value="selectedTask.plan?.endWeek"
            @change="onSelectPlanWeek(selectedTask.id, 'end', $event)"
          >
            <option v-for="week in weeks" :key="`e-${week.index}`" :value="week.index">
              {{ week.timelineWeek }} ({{ week.calendarWeek }})
            </option>
          </select>
        </label>
        <div class="gantt-inspector__meta">
          <span
            class="gantt-inspector__swatch"
            :style="{ background: barTypeColor('plan') }"
          />
          {{ selectedDuration }} week{{ selectedDuration === 1 ? '' : 's' }}
        </div>
        <label class="gantt-inspector__field">
          <span>Completed at</span>
          <input
            type="date"
            :value="completedAtInputValue(selectedTask.completedAt)"
            @change="onCompletedAtChange(selectedTask.id, $event)"
          />
        </label>
        <p class="gantt-inspector__hint">
          Set a completion date to refresh Actual (green if within Plan, pink if beyond).
          Prefer a date inside the chart calendar
          <template v-if="weeks.length">
            ({{ weeks[0].calendarWeek }}–{{ weeks[weeks.length - 1].calendarWeek }}).
            Dates outside are clamped to the nearest week.
          </template>
        </p>
        <button type="button" class="gantt-inspector__clear" @click="selectedTaskId = ''">
          Clear selection
        </button>
      </div>
      <div v-else class="gantt-inspector gantt-inspector--empty">
        No task selected — click a task name or Plan bar to edit.
      </div>
    </div>

    <div class="gantt-legend" role="group" aria-label="Show bar types">
      <span class="gantt-legend__title">Show</span>
      <button
        type="button"
        class="gantt-legend__all"
        :class="{ 'gantt-legend__all--active': allLanesVisible }"
        title="Show Standard, Plan and Actual"
        @click="showAllLanes"
      >
        All
      </button>
      <button
        v-for="barType in barTypes"
        :key="barType.id"
        type="button"
        class="gantt-legend__item"
        :class="{ 'gantt-legend__item--off': !isLaneVisible(barType.id) }"
        :title="toggleLaneTitle(barType)"
        :aria-pressed="isLaneVisible(barType.id)"
        @click="toggleLane(barType.id)"
      >
        <template v-if="barType.id === 'actual'">
          <span
            class="gantt-legend__swatch"
            :style="{ backgroundColor: barType.color }"
            title="On time"
          />
          <span
            class="gantt-legend__swatch"
            :style="{ backgroundColor: barType.lateColor || '#E57F90' }"
            title="Late"
          />
          <span class="gantt-legend__label">{{ barType.label }}</span>
          <span class="gantt-legend__hint">green · pink late</span>
        </template>
        <template v-else>
          <span
            class="gantt-legend__swatch"
            :style="{ backgroundColor: barType.color }"
          />
          <span class="gantt-legend__label">{{ barType.label }}</span>
        </template>
      </button>
      <span class="gantt-legend__tip">Click to show / hide · multi-select</span>
    </div>

    <div class="gantt-scroll">
      <div class="gantt-grid" :style="gridStyle">
        <!-- Row: Calendar weeks -->
        <div
          class="gantt-cell gantt-cell--head gantt-cell--label-head"
          :title="fieldLabels.migrationKeySteps"
        >
          {{ fieldLabels.migrationKeySteps }}
          <i
            class="gantt-col-resizer"
            title="Drag to resize column"
            @mousedown.prevent.stop="startColResize('label', $event)"
          />
        </div>
        <div class="gantt-cell gantt-cell--head gantt-cell--axis">
          {{ fieldLabels.calendarWeeks }}
          <i
            class="gantt-col-resizer"
            title="Drag to resize column"
            @mousedown.prevent.stop="startColResize('axis', $event)"
          />
        </div>
        <div
          v-for="week in weeks"
          :key="`cal-${week.index}`"
          class="gantt-cell gantt-cell--head gantt-cell--week"
          :class="{ 'gantt-cell--today': isTodayWeek(week.index) }"
        >
          {{ week.calendarWeek }}
          <i
            class="gantt-col-resizer"
            title="Drag to resize week columns"
            @mousedown.prevent.stop="startColResize('week', $event)"
          />
        </div>

        <!-- Row: Timeline weeks -->
        <div class="gantt-cell gantt-cell--subhead gantt-cell--label-head gantt-cell--label-blank" />
        <div class="gantt-cell gantt-cell--subhead gantt-cell--axis">
          {{ fieldLabels.timelineWeeks }}
        </div>
        <div
          v-for="week in weeks"
          :key="`tl-${week.index}`"
          class="gantt-cell gantt-cell--subhead gantt-cell--week"
          :class="{ 'gantt-cell--today': isTodayWeek(week.index) }"
        >
          {{ week.timelineWeek }}
        </div>

        <!-- Tasks: 3 sub-rows each (Standard / Plan / Actual) -->
        <template v-for="(task, taskIndex) in displayTasks" :key="task.id">
          <div
            class="gantt-cell gantt-cell--label gantt-cell--label-span gantt-row-band"
            :class="{
              'gantt-cell--label-clickable': editable,
              'gantt-row--selected': isSelected(task.id),
              'gantt-row--alt': taskIndex % 2 === 1
            }"
            :style="{ gridRow: `span ${laneSpan}` }"
            :title="task.name"
            @click="selectTask(task.id)"
          >
            {{ task.name }}
          </div>

          <template v-for="lane in visibleTaskLanes" :key="`${task.id}-${lane.id}`">
            <div
              class="gantt-cell gantt-cell--type gantt-row-band"
              :class="{
                'gantt-row--selected': isSelected(task.id),
                'gantt-row--alt': taskIndex % 2 === 1,
                [`gantt-cell--type-${lane.id}`]: true
              }"
            >
              {{ lane.rowLabel }}
            </div>
            <div
              class="gantt-lane gantt-row-band"
              :class="{
                'gantt-lane--editable': editable && lane.id === 'plan',
                'gantt-lane--selected': isSelected(task.id),
                'gantt-row--alt': taskIndex % 2 === 1,
                [`gantt-lane--${lane.id}`]: true
              }"
              :data-task-id="task.id"
              :data-bar-type="lane.id"
              :style="{ gridColumn: `span ${weeks.length}` }"
              @mousedown="onLaneMouseDown($event, task, lane.id)"
            >
              <div
                v-for="week in weeks"
                :key="`${task.id}-${lane.id}-bg-${week.index}`"
                class="gantt-lane__cell"
                :class="{ 'gantt-lane__cell--today': isTodayWeek(week.index) }"
              />
              <div
                v-if="laneRange(task, lane.id)"
                class="gantt-bar"
                :class="{
                  'gantt-bar--selected': isSelected(task.id) && lane.id === 'plan',
                  'gantt-bar--readonly': lane.id !== 'plan',
                  [`gantt-bar--${lane.id}`]: true
                }"
                :style="barStyle(laneRange(task, lane.id), barColor(task, lane.id))"
                :title="barTitle(task, lane.id)"
                @mousedown.stop="onBarMouseDown($event, task, lane.id, 'move')"
              >
                <button
                  v-if="editable && lane.id === 'plan'"
                  type="button"
                  class="gantt-bar__handle gantt-bar__handle--start"
                  title="Drag to change Plan start week"
                  aria-label="Resize Plan start"
                  @mousedown.stop.prevent="onBarMouseDown($event, task, 'plan', 'resize-start')"
                />
                <span class="gantt-bar__label">
                  {{ weekLabel(laneRange(task, lane.id).startWeek) }}–{{
                    weekLabel(laneRange(task, lane.id).endWeek)
                  }}
                </span>
                <button
                  v-if="editable && lane.id === 'plan'"
                  type="button"
                  class="gantt-bar__handle gantt-bar__handle--end"
                  title="Drag to change Plan end week"
                  aria-label="Resize Plan end"
                  @mousedown.stop.prevent="onBarMouseDown($event, task, 'plan', 'resize-end')"
                />
              </div>
            </div>
          </template>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import {
  projectGanttBarTypes,
  projectGanttFieldLabels
} from '../data/projectGanttFixture.js'

const COL_WIDTH_STORAGE_KEY = 'ae-wpm-project-gantt-col-widths'

const summaryFields = [
  { key: 'projectPhase', type: 'text', color: '#808080' },
  { key: 'scope', type: 'text', color: '#0070C0' },
  { key: 'migratableFte', type: 'number', color: '#803808' },
  { key: 'learningCurve', type: 'number', color: '#F09810' },
  { key: 'tlTmHc', type: 'number', color: '#2088A8' },
  { key: 'mngrHc', type: 'number', color: '#002060' },
  { key: 'totalWoBuffer', type: 'number', color: '#00B04E' },
  { key: 'total', type: 'number', color: '#6E6E6E' }
]

const DEFAULT_COL_WIDTHS = {
  label: 360,
  axis: 96,
  week: 44
}

const MIN_COL_WIDTHS = {
  label: 160,
  axis: 72,
  week: 28
}

const LANE_ROW_LABELS = {
  standard: 'Standard',
  plan: 'Plan',
  actual: 'Actual'
}

const ALL_LANE_IDS = ['standard', 'plan', 'actual']

const taskLanes = [
  { id: 'standard', rowLabel: LANE_ROW_LABELS.standard },
  { id: 'plan', rowLabel: LANE_ROW_LABELS.plan },
  { id: 'actual', rowLabel: LANE_ROW_LABELS.actual }
]

const loadColWidths = () => {
  try {
    const raw = localStorage.getItem(COL_WIDTH_STORAGE_KEY)
    if (!raw) return { ...DEFAULT_COL_WIDTHS }
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object') return { ...DEFAULT_COL_WIDTHS }
    const next = { ...DEFAULT_COL_WIDTHS }
    for (const key of Object.keys(DEFAULT_COL_WIDTHS)) {
      const value = Number(parsed[key])
      if (Number.isFinite(value)) {
        next[key] = Math.max(MIN_COL_WIDTHS[key] ?? 36, Math.round(value))
      }
    }
    return next
  } catch {
    return { ...DEFAULT_COL_WIDTHS }
  }
}

const persistColWidths = () => {
  try {
    localStorage.setItem(COL_WIDTH_STORAGE_KEY, JSON.stringify(colWidths.value))
  } catch {
    /* ignore quota / private mode */
  }
}

const props = defineProps({
  weeks: { type: Array, default: () => [] },
  tasks: { type: Array, default: () => [] },
  barTypes: { type: Array, default: () => projectGanttBarTypes },
  fieldLabels: {
    type: Object,
    default: () => projectGanttFieldLabels
  },
  meta: {
    type: Object,
    default: () => ({
      projectPhase: '',
      scope: '',
      migratableFte: '',
      learningCurve: '',
      tlTmHc: '',
      mngrHc: '',
      totalWoBuffer: '',
      total: ''
    })
  },
  todayWeek: { type: Number, default: 1 },
  editable: { type: Boolean, default: false }
})

const emit = defineEmits(['update-task', 'update-meta'])

const selectedTaskId = ref('')
const drag = ref(null)
const preview = ref(null)
const colWidths = ref(loadColWidths())
const colResize = ref(null)
/** Which Standard / Plan / Actual rows are visible (multi-select). */
const visibleLaneIds = ref([...ALL_LANE_IDS])

const visibleTaskLanes = computed(() =>
  taskLanes.filter((lane) => visibleLaneIds.value.includes(lane.id))
)

const laneSpan = computed(() => Math.max(1, visibleTaskLanes.value.length))

const allLanesVisible = computed(
  () => visibleLaneIds.value.length === ALL_LANE_IDS.length
)

const isLaneVisible = (laneId) => visibleLaneIds.value.includes(laneId)

const toggleLane = (laneId) => {
  const selected = new Set(visibleLaneIds.value)
  if (selected.has(laneId)) {
    if (selected.size <= 1) return
    selected.delete(laneId)
  } else {
    selected.add(laneId)
  }
  visibleLaneIds.value = ALL_LANE_IDS.filter((id) => selected.has(id))
}

const showAllLanes = () => {
  visibleLaneIds.value = [...ALL_LANE_IDS]
}

const toggleLaneTitle = (barType) => {
  const on = isLaneVisible(barType.id)
  const base = barType.hint || barType.label
  return on
    ? `${base} · click to hide`
    : `${base} · click to show`
}

const gridStyle = computed(() => {
  const widths = colWidths.value
  return {
    '--week-count': props.weeks.length,
    '--col-label': `${widths.label}px`,
    '--col-axis': `${widths.axis}px`,
    '--col-week': `${widths.week}px`
  }
})

const maxWeek = computed(() => props.weeks.length || 44)

const barTypeById = computed(() => {
  const map = new Map()
  for (const item of props.barTypes || []) {
    map.set(item.id, item)
  }
  return map
})

const displayTasks = computed(() => {
  if (!preview.value) return props.tasks
  const { taskId, startWeek, endWeek } = preview.value
  return props.tasks.map((task) =>
    task.id === taskId
      ? {
          ...task,
          plan: {
            startWeek: startWeek ?? task.plan?.startWeek,
            endWeek: endWeek ?? task.plan?.endWeek
          }
        }
      : task
  )
})

const selectedTask = computed(() => {
  if (!selectedTaskId.value) return null
  return displayTasks.value.find((task) => task.id === selectedTaskId.value) || null
})

const selectedDuration = computed(() => {
  if (!selectedTask.value?.plan) return 0
  return selectedTask.value.plan.endWeek - selectedTask.value.plan.startWeek + 1
})

const clampWeek = (week) => Math.max(1, Math.min(maxWeek.value, week))

const normalizeRange = (startWeek, endWeek) => {
  const start = clampWeek(Math.min(startWeek, endWeek))
  const end = clampWeek(Math.max(startWeek, endWeek))
  return { startWeek: start, endWeek: end }
}

const weekLabel = (weekIndex) => {
  const week = props.weeks.find((item) => item.index === weekIndex)
  return week?.timelineWeek || `wk${String(weekIndex).padStart(2, '0')}`
}

const laneRange = (task, barTypeId) => {
  if (barTypeId === 'standard') return task.standard || null
  if (barTypeId === 'plan') return task.plan || null
  if (barTypeId === 'actual') return task.actual || null
  return null
}

const barTypeColor = (barTypeId, late = false) => {
  const meta = barTypeById.value.get(barTypeId)
  if (!meta) {
    if (barTypeId === 'standard') return '#8E9BA8'
    if (barTypeId === 'plan') return '#1E8BB5'
    return late ? '#E57F90' : '#6DBF80'
  }
  if (barTypeId === 'actual' && late) return meta.lateColor || '#E57F90'
  return meta.color
}

const barColor = (task, barTypeId) => {
  if (barTypeId === 'actual') {
    const late = task.actualStatus === 'late'
    return barTypeColor('actual', late)
  }
  return barTypeColor(barTypeId)
}

const barStyle = (range, color) => {
  if (!range) return {}
  const count = Math.max(1, maxWeek.value)
  const start = Math.max(0, range.startWeek - 1)
  const span = Math.max(1, range.endWeek - range.startWeek + 1)
  return {
    left: `${(start / count) * 100}%`,
    width: `${(span / count) * 100}%`,
    '--bar-color': color
  }
}

const barTitle = (task, barTypeId) => {
  const range = laneRange(task, barTypeId)
  if (!range) return `${task.name}: ${LANE_ROW_LABELS[barTypeId] || barTypeId} — none`
  const status =
    barTypeId === 'actual' && task.actualStatus
      ? ` · ${task.actualStatus}`
      : ''
  return `${task.name}: ${LANE_ROW_LABELS[barTypeId] || barTypeId}${status} · ${weekLabel(range.startWeek)} – ${weekLabel(range.endWeek)}`
}

const isTodayWeek = (weekIndex) =>
  Boolean(props.todayWeek) && weekIndex === props.todayWeek

const isSelected = (taskId) => selectedTaskId.value === taskId

const selectTask = (taskId) => {
  if (!props.editable) return
  selectedTaskId.value = taskId
}

const metaValue = (key) => {
  const value = props.meta?.[key]
  return value == null ? '' : String(value)
}

const readInputValue = (event) => event?.target?.value ?? event?.detail?.value ?? ''

const onMetaInput = (key, type, event) => {
  if (!props.editable) return
  const raw = readInputValue(event)
  if (type === 'number') {
    if (raw === '') {
      emit('update-meta', { key, value: '' })
      return
    }
    const number = Number(raw)
    emit('update-meta', { key, value: Number.isFinite(number) ? number : raw })
    return
  }
  emit('update-meta', { key, value: raw })
}

const weekFromClientX = (clientX, laneEl) => {
  const rect = laneEl.getBoundingClientRect()
  if (rect.width <= 0) return 1
  const ratio = (clientX - rect.left) / rect.width
  const index = Math.floor(ratio * maxWeek.value) + 1
  return clampWeek(index)
}

const findLaneEl = (taskId) =>
  document.querySelector(`.gantt-lane[data-task-id="${taskId}"][data-bar-type="plan"]`)

const emitPlanRange = (taskId, startWeek, endWeek) => {
  const range = normalizeRange(startWeek, endWeek)
  const current = props.tasks.find((task) => task.id === taskId)
  if (
    current?.plan &&
    current.plan.startWeek === range.startWeek &&
    current.plan.endWeek === range.endWeek
  ) {
    return
  }
  emit('update-task', {
    id: taskId,
    plan: range
  })
}

const onSelectPlanWeek = (taskId, which, event) => {
  const task = props.tasks.find((item) => item.id === taskId)
  if (!task?.plan) return
  const value = Number(event.target.value)
  if (!Number.isFinite(value)) return
  if (which === 'start') {
    emitPlanRange(taskId, value, Math.max(value, task.plan.endWeek))
  } else {
    emitPlanRange(taskId, Math.min(value, task.plan.startWeek), value)
  }
}

const completedAtInputValue = (value) => {
  if (!value) return ''
  const text = String(value)
  if (/^\d{4}-\d{2}-\d{2}/.test(text)) return text.slice(0, 10)
  try {
    const date = new Date(text)
    if (Number.isNaN(date.getTime())) return ''
    return date.toISOString().slice(0, 10)
  } catch {
    return ''
  }
}

const onCompletedAtChange = (taskId, event) => {
  const raw = String(event.target.value || '').trim()
  emit('update-task', {
    id: taskId,
    completedAt: raw || null
  })
}

const clearColResizeCursor = () => {
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

const startColResize = (key, event) => {
  if (event.button !== 0) return
  if (!(key in colWidths.value)) return
  colResize.value = {
    key,
    startX: event.clientX,
    startWidth: colWidths.value[key]
  }
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

const onBarMouseDown = (event, task, barTypeId, mode) => {
  if (barTypeId !== 'plan') {
    if (props.editable) selectedTaskId.value = task.id
    return
  }
  if (!props.editable || event.button !== 0) return
  selectedTaskId.value = task.id
  const laneEl =
    event.currentTarget.closest('.gantt-lane') || findLaneEl(task.id)
  if (!laneEl || !task.plan) return
  const anchorWeek = weekFromClientX(event.clientX, laneEl)
  drag.value = {
    mode,
    barType: 'plan',
    taskId: task.id,
    originStart: task.plan.startWeek,
    originEnd: task.plan.endWeek,
    anchorWeek,
    duration: task.plan.endWeek - task.plan.startWeek + 1,
    laneEl
  }
  preview.value = {
    taskId: task.id,
    startWeek: task.plan.startWeek,
    endWeek: task.plan.endWeek
  }
}

const onLaneMouseDown = (event, task, barTypeId) => {
  if (barTypeId !== 'plan') {
    if (props.editable) selectedTaskId.value = task.id
    return
  }
  if (!props.editable || event.button !== 0) return
  if (event.target.closest('.gantt-bar')) return
  selectedTaskId.value = task.id
  const laneEl = event.currentTarget
  const week = weekFromClientX(event.clientX, laneEl)
  drag.value = {
    mode: 'draw',
    barType: 'plan',
    taskId: task.id,
    originStart: week,
    originEnd: week,
    anchorWeek: week,
    duration: 1,
    laneEl
  }
  preview.value = { taskId: task.id, startWeek: week, endWeek: week }
}

const onWindowMouseMove = (event) => {
  if (colResize.value) {
    const { key, startX, startWidth } = colResize.value
    const min = MIN_COL_WIDTHS[key] ?? 36
    const next = Math.max(min, Math.round(startWidth + (event.clientX - startX)))
    colWidths.value = { ...colWidths.value, [key]: next }
    return
  }
  if (!drag.value) return
  const { mode, taskId, originStart, originEnd, anchorWeek, duration, laneEl } =
    drag.value
  const week = weekFromClientX(event.clientX, laneEl)

  if (mode === 'resize-start') {
    preview.value = {
      taskId,
      ...normalizeRange(week, originEnd)
    }
    return
  }
  if (mode === 'resize-end') {
    preview.value = {
      taskId,
      ...normalizeRange(originStart, week)
    }
    return
  }
  if (mode === 'draw') {
    preview.value = {
      taskId,
      ...normalizeRange(anchorWeek, week)
    }
    return
  }
  // move
  const delta = week - anchorWeek
  let start = originStart + delta
  let end = start + duration - 1
  if (start < 1) {
    end += 1 - start
    start = 1
  }
  if (end > maxWeek.value) {
    start -= end - maxWeek.value
    end = maxWeek.value
  }
  preview.value = {
    taskId,
    ...normalizeRange(start, end)
  }
}

const onWindowMouseUp = () => {
  if (colResize.value) {
    colResize.value = null
    clearColResizeCursor()
    persistColWidths()
    return
  }
  if (!drag.value || !preview.value) {
    drag.value = null
    preview.value = null
    return
  }
  const { taskId, startWeek, endWeek } = preview.value
  drag.value = null
  preview.value = null
  emitPlanRange(taskId, startWeek, endWeek)
}

onMounted(() => {
  window.addEventListener('mousemove', onWindowMouseMove)
  window.addEventListener('mouseup', onWindowMouseUp)
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onWindowMouseMove)
  window.removeEventListener('mouseup', onWindowMouseUp)
  clearColResizeCursor()
})
</script>

<style scoped>
.gantt {
  --ink: #0f172a;
  --ink-soft: #334155;
  --muted: #64748b;
  --line: #e2e8f0;
  --line-soft: #eef2f7;
  --canvas: #f8fafc;
  --panel: #ffffff;
  --accent: #0e7490;
  --danger: #e11d48;
  --shadow: 0 10px 30px rgba(15, 23, 42, 0.06);

  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  font-family: 'Maersk Text', 'Segoe UI', sans-serif;
  color: var(--ink);
}

.gantt-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  padding: 12px 14px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: linear-gradient(180deg, #fff 0%, #f8fafc 100%);
  box-shadow: var(--shadow);
}

.gantt-legend__title {
  font-size: 12px;
  font-weight: 700;
  color: var(--ink-soft);
  margin-right: 2px;
}

.gantt-legend__all {
  appearance: none;
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid var(--line-soft);
  background: #fff;
  font: inherit;
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-soft);
  cursor: pointer;
  transition: background 0.12s ease, border-color 0.12s ease, color 0.12s ease;
}

.gantt-legend__all:hover {
  border-color: #42b0d5;
  color: #0077b8;
}

.gantt-legend__all--active {
  background: #e8f6fb;
  border-color: #42b0d5;
  color: #0077b8;
}

.gantt-legend__item {
  appearance: none;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  background: #fff;
  border: 1px solid #42b0d5;
  font: inherit;
  font-size: 12px;
  color: var(--ink-soft);
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.12s ease, border-color 0.12s ease, background 0.12s ease;
}

.gantt-legend__item:hover {
  background: #f0f9fd;
}

.gantt-legend__item--off {
  opacity: 0.42;
  border-color: var(--line-soft);
  background: #f8fafc;
}

.gantt-legend__item--off:hover {
  opacity: 0.7;
}

.gantt-legend__swatch {
  width: 14px;
  height: 14px;
  border-radius: 4px;
  flex-shrink: 0;
  box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.08);
  background-image: repeating-linear-gradient(
    -45deg,
    rgba(255, 255, 255, 0.22) 0,
    rgba(255, 255, 255, 0.22) 0.75px,
    transparent 0.75px,
    transparent 5px
  );
}

.gantt-legend__hint {
  font-size: 11px;
  color: var(--muted);
  font-weight: 500;
}

.gantt-legend__tip {
  margin-left: auto;
  font-size: 11px;
  color: var(--muted);
}

.gantt-editor {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.gantt-hint {
  margin: 0;
  font-size: 13px;
  color: var(--muted);
  line-height: 1.5;
}

.gantt-inspector {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 14px;
  padding: 12px 14px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: #fff;
  box-shadow: var(--shadow);
}

.gantt-inspector--empty {
  color: var(--muted);
  font-size: 13px;
}

.gantt-inspector__title {
  flex: 1 1 220px;
  min-width: 0;
  font-weight: 700;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: -0.01em;
}

.gantt-inspector__field {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--muted);
  font-weight: 600;
}

.gantt-inspector__field select {
  min-width: 168px;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 7px 10px;
  background: var(--canvas);
  color: var(--ink);
  font: inherit;
  font-weight: 500;
}

.gantt-inspector__field select:focus {
  outline: 2px solid color-mix(in srgb, var(--accent) 30%, white);
  border-color: var(--accent);
}

.gantt-inspector__meta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--muted);
  font-weight: 500;
}

.gantt-inspector__swatch {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  flex-shrink: 0;
}

.gantt-inspector__readonly {
  font-size: 12px;
  color: var(--muted);
  font-weight: 500;
}

.gantt-inspector__hint {
  color: var(--muted);
  font-size: 11px;
  font-weight: 500;
  line-height: 1.4;
  margin: 0;
  max-width: 28rem;
}

.gantt-inspector__clear {
  margin-left: auto;
  border: 1px solid var(--line);
  background: #fff;
  color: var(--ink-soft);
  font: inherit;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  border-radius: 999px;
  padding: 6px 12px;
}

.gantt-inspector__clear:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.gantt-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: linear-gradient(180deg, #fff 0%, #f8fafc 100%);
  box-shadow: var(--shadow);
}

.gantt-summary__cue {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-right: 4px;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(0, 112, 192, 0.08);
  color: #0070c0;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.01em;
  white-space: nowrap;
}

.gantt-summary__cue-icon {
  font-size: 12px;
  line-height: 1;
}

.gantt-summary__item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  max-width: 100%;
  padding: 6px 10px;
  border-radius: 999px;
  background: #fff;
  border: 1px solid var(--line-soft);
  font-size: 12px;
  color: var(--ink-soft);
  font-weight: 500;
}

.gantt-summary__item--editable {
  cursor: text;
}

.gantt-summary__item--editable:hover {
  border-color: rgba(0, 112, 192, 0.45);
  background: #f5fafe;
}

.gantt-summary__item--editable:focus-within {
  border-color: #0070c0;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(0, 112, 192, 0.14);
}

.gantt-summary__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.08);
}

.gantt-summary__name {
  flex-shrink: 0;
  white-space: nowrap;
}

.gantt-summary__value {
  min-width: 3.25rem;
  max-width: 9rem;
  margin: 0;
  padding: 3px 8px;
  border: 1px dashed rgba(0, 112, 192, 0.35);
  border-radius: 999px;
  background: rgba(0, 112, 192, 0.06);
  color: var(--ink);
  font: inherit;
  font-weight: 700;
  line-height: 1.2;
  outline: none;
  transition: border-color 0.12s ease, background 0.12s ease, box-shadow 0.12s ease;
}

.gantt-summary__item--editable .gantt-summary__value:hover {
  border-color: #0070c0;
  background: rgba(0, 112, 192, 0.1);
}

.gantt-summary__item--editable .gantt-summary__value:focus {
  border-style: solid;
  border-color: #0070c0;
  background: #fff;
  box-shadow: 0 0 0 2px rgba(0, 112, 192, 0.16);
}

.gantt-summary__value::placeholder {
  color: #94a3b8;
  font-weight: 500;
}

.gantt-summary__value[readonly] {
  cursor: default;
  pointer-events: none;
  border-color: transparent;
  background: transparent;
}

.gantt-summary__value[type='number'] {
  font-variant-numeric: tabular-nums;
  -moz-appearance: textfield;
}

.gantt-summary__value[type='number']::-webkit-outer-spin-button,
.gantt-summary__value[type='number']::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.gantt-scroll {
  overflow-x: auto;
  overflow-y: visible;
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 0;
  background: var(--panel);
  box-shadow: var(--shadow);
  user-select: none;
}

.gantt-grid {
  position: relative;
  display: grid;
  grid-template-columns:
    var(--col-label)
    var(--col-axis)
    repeat(var(--week-count), minmax(var(--col-week), 1fr));
  width: 100%;
  min-width: calc(
    var(--col-label) + var(--col-axis) + (var(--week-count) * var(--col-week))
  );
}

.gantt-cell {
  box-sizing: border-box;
  border-right: 1px solid var(--line-soft);
  border-bottom: none;
  min-height: 28px;
  font-size: 10px;
  line-height: 1.15;
}

.gantt-cell--head,
.gantt-cell--subhead {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 5px 3px;
  color: #f8fafc;
  background: #0f172a;
  font-weight: 600;
  text-align: center;
  font-size: 10px;
  letter-spacing: 0.02em;
}

.gantt-cell--subhead {
  background: #475569;
  font-weight: 500;
  color: #f1f5f9;
}

.gantt-cell--subhead.gantt-cell--label-blank {
  background: #475569;
}

.gantt-cell--label-head {
  position: relative;
  justify-content: flex-start;
  padding: 6px 12px;
  font-size: 10px;
  line-height: 1.3;
  text-align: left;
  overflow: hidden;
  color: #f1f5f9;
}

.gantt-cell--axis {
  position: relative;
  font-size: 9px;
  padding: 4px 2px;
  color: #94a3b8;
}

.gantt-cell--week {
  position: relative;
  font-size: 10px;
  white-space: nowrap;
  overflow: hidden;
  padding-inline: 2px;
  font-variant-numeric: tabular-nums;
  border-bottom: none;
  border-right: 1px dashed rgba(148, 163, 184, 0.45);
}

.gantt-col-resizer {
  position: absolute;
  top: 0;
  right: -3px;
  width: 7px;
  height: 100%;
  cursor: col-resize;
  z-index: 4;
}

.gantt-col-resizer:hover,
.gantt-col-resizer:active {
  background: rgba(56, 189, 248, 0.45);
}

.gantt-cell--head.gantt-cell--week,
.gantt-cell--subhead.gantt-cell--week {
  border-right: 1px dashed rgba(148, 163, 184, 0.4);
}

.gantt-cell--label {
  display: flex;
  align-items: center;
  padding: 0 12px;
  background: transparent;
  color: var(--ink);
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.gantt-cell--label-span {
  align-items: center;
  border-bottom: 1px solid rgba(148, 163, 184, 0.28);
}

.gantt-cell--label-clickable {
  cursor: pointer;
}

.gantt-cell--label-clickable:hover {
  color: #0070c0;
}

.gantt-cell--type {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 0 8px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.01em;
  color: var(--muted);
  white-space: nowrap;
  min-height: 18px;
  border-right: 1px dashed rgba(148, 163, 184, 0.45);
}

.gantt-cell--type-standard {
  color: #7a8794;
}

.gantt-cell--type-plan {
  color: #1a8bb0;
}

.gantt-cell--type-actual {
  color: #3d7a4a;
}

/* Row bands: soft fill + diagonal hatch + bottom shadow rail */
.gantt-row-band {
  --row-fill: #ffffff;
  --row-hatch: rgba(0, 112, 192, 0.045);
  background-color: var(--row-fill);
  background-image:
    repeating-linear-gradient(
      -36deg,
      transparent 0,
      transparent 5px,
      var(--row-hatch) 5px,
      var(--row-hatch) 6px
    ),
    linear-gradient(
      180deg,
      rgba(255, 255, 255, 0.55) 0%,
      transparent 42%
    );
  box-shadow:
    inset 0 -1px 0 rgba(148, 163, 184, 0.18),
    0 2px 6px -5px rgba(15, 23, 42, 0.1);
}

.gantt-row-band.gantt-row--alt {
  --row-fill: #f5f8fb;
  --row-hatch: rgba(0, 112, 192, 0.07);
}

.gantt-row-band.gantt-row--selected {
  --row-fill: #eaf4fb;
  --row-hatch: rgba(0, 112, 192, 0.1);
  box-shadow:
    inset 0 -1px 0 rgba(0, 112, 192, 0.28),
    0 4px 12px -5px rgba(0, 112, 192, 0.22);
}

.gantt-lane {
  position: relative;
  display: grid;
  grid-template-columns: repeat(var(--week-count), minmax(0, 1fr));
  min-height: 18px;
  isolation: isolate;
}

.gantt-lane--actual {
  box-shadow:
    inset 0 -1px 0 rgba(148, 163, 184, 0.28),
    0 3px 8px -5px rgba(15, 23, 42, 0.14);
}

.gantt-lane::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 1px;
  background-image: repeating-linear-gradient(
    90deg,
    rgba(100, 116, 139, 0.28) 0,
    rgba(100, 116, 139, 0.28) 4px,
    transparent 4px,
    transparent 9px
  );
  pointer-events: none;
  z-index: 2;
}

.gantt-lane--editable {
  cursor: cell;
}

.gantt-lane__cell {
  box-sizing: border-box;
  border-right: 1px dashed rgba(148, 163, 184, 0.38);
  border-bottom: none;
  background: transparent;
}

.gantt-lane__cell--today {
  box-shadow: inset 2px 0 0 0 var(--danger);
}

.gantt-bar {
  position: absolute;
  top: 2px;
  bottom: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  border: 0;
  overflow: hidden;
  background-color: var(--bar-color);
  background-image: repeating-linear-gradient(
    -45deg,
    rgba(255, 255, 255, 0.22) 0,
    rgba(255, 255, 255, 0.22) 0.75px,
    transparent 0.75px,
    transparent 5px
  );
  box-shadow:
    inset 2px 0 0 rgba(255, 255, 255, 0.18),
    0 1px 2px rgba(0, 63, 110, 0.12);
  z-index: 1;
  min-width: calc(100% / var(--week-count));
  cursor: default;
  transition: transform 0.12s ease, box-shadow 0.12s ease;
}

.gantt-bar--readonly {
  cursor: default;
}

.gantt-lane--editable .gantt-bar:not(.gantt-bar--readonly) {
  cursor: grab;
}

.gantt-lane--editable .gantt-bar:not(.gantt-bar--readonly):active {
  cursor: grabbing;
}

.gantt-bar--selected {
  transform: translateY(-1px);
  box-shadow:
    inset 2px 0 0 rgba(255, 255, 255, 0.3),
    0 0 0 2px color-mix(in srgb, var(--bar-color) 35%, white),
    0 4px 12px color-mix(in srgb, var(--bar-color) 28%, transparent);
}

.gantt-bar__label {
  position: relative;
  z-index: 1;
  font-size: 8px;
  font-weight: 600;
  letter-spacing: 0.01em;
  color: #fff;
  white-space: nowrap;
  pointer-events: none;
  padding: 0 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  text-shadow: 0 1px 1px rgba(0, 63, 110, 0.35);
}

.gantt-bar--actual .gantt-bar__label {
  color: #fff;
  text-shadow: 0 1px 1px rgba(0, 63, 110, 0.35);
}

.gantt-bar--standard .gantt-bar__label {
  color: #fff;
  text-shadow: 0 1px 1px rgba(0, 63, 110, 0.35);
}

.gantt-bar__handle {
  position: absolute;
  top: 1px;
  bottom: 1px;
  width: 5px;
  border: 0;
  padding: 0;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  cursor: ew-resize;
  opacity: 0;
  transition: opacity 0.12s ease;
}

.gantt-bar:hover .gantt-bar__handle,
.gantt-bar--selected .gantt-bar__handle {
  opacity: 1;
}

.gantt-bar__handle:hover {
  background: #fff;
}

.gantt-bar__handle--start {
  left: 3px;
}

.gantt-bar__handle--end {
  right: 3px;
}
</style>
