<template>
  <div
    class="gantt"
    :class="{ 'gantt--editable': editable }"
    role="region"
    aria-label="Project Gantt chart"
  >
    <div class="gantt-legend">
      <div v-for="phase in phases" :key="phase.id" class="gantt-legend__item">
        <span class="gantt-legend__swatch" :style="{ background: phase.color }" />
        <span class="gantt-legend__label">{{ phase.label }}</span>
      </div>
    </div>

    <div v-if="editable" class="gantt-editor">
      <p class="gantt-hint">
        Click a task to select it. Choose a <strong>Status</strong>, drag the
        <strong>ends</strong> to resize, or drag the <strong>bar</strong> to move.
      </p>

      <div v-if="selectedTask" class="gantt-inspector">
        <div class="gantt-inspector__title" :title="selectedTask.name">
          {{ selectedTask.name }}
        </div>
        <label class="gantt-inspector__field">
          <span>Status</span>
          <select
            :value="selectedTask.phaseId || 'opportunity'"
            @change="onSelectPhase(selectedTask.id, $event)"
          >
            <option v-for="phase in phases" :key="phase.id" :value="phase.id">
              {{ phase.label }}
            </option>
          </select>
        </label>
        <label class="gantt-inspector__field">
          <span>Start</span>
          <select
            :value="selectedTask.startWeek"
            @change="onSelectWeek(selectedTask.id, 'start', $event)"
          >
            <option v-for="week in weeks" :key="`s-${week.index}`" :value="week.index">
              {{ week.timelineWeek }} ({{ week.calendarWeek }})
            </option>
          </select>
        </label>
        <label class="gantt-inspector__field">
          <span>End</span>
          <select
            :value="selectedTask.endWeek"
            @change="onSelectWeek(selectedTask.id, 'end', $event)"
          >
            <option v-for="week in weeks" :key="`e-${week.index}`" :value="week.index">
              {{ week.timelineWeek }} ({{ week.calendarWeek }})
            </option>
          </select>
        </label>
        <div class="gantt-inspector__meta">
          <span
            class="gantt-inspector__swatch"
            :style="{ background: phaseColor(selectedTask.phaseId) }"
          />
          {{ selectedDuration }} week{{ selectedDuration === 1 ? '' : 's' }}
        </div>
        <button type="button" class="gantt-inspector__clear" @click="selectedTaskId = ''">
          Clear selection
        </button>
      </div>
      <div v-else class="gantt-inspector gantt-inspector--empty">
        No task selected — click a task name or bar to edit.
      </div>
    </div>

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

        <!-- Tasks -->
        <template v-for="(task, taskIndex) in displayTasks" :key="task.id">
          <div
            class="gantt-cell gantt-cell--label gantt-row-band"
            :class="{
              'gantt-cell--label-clickable': editable,
              'gantt-row--selected': isSelected(task.id),
              'gantt-row--alt': taskIndex % 2 === 1
            }"
            :title="task.name"
            @click="selectTask(task.id)"
          >
            {{ task.name }}
          </div>
          <div
            class="gantt-cell gantt-cell--axis-blank gantt-row-band"
            :class="{
              'gantt-row--selected': isSelected(task.id),
              'gantt-row--alt': taskIndex % 2 === 1
            }"
          />
          <div
            class="gantt-lane gantt-row-band"
            :class="{
              'gantt-lane--editable': editable,
              'gantt-lane--selected': isSelected(task.id),
              'gantt-row--alt': taskIndex % 2 === 1
            }"
            :data-task-id="task.id"
            :style="{ gridColumn: `span ${weeks.length}` }"
            @mousedown="onLaneMouseDown($event, task)"
          >
            <div
              v-for="week in weeks"
              :key="`${task.id}-bg-${week.index}`"
              class="gantt-lane__cell"
              :class="{ 'gantt-lane__cell--today': isTodayWeek(week.index) }"
            />
            <div
              class="gantt-bar"
              :class="{ 'gantt-bar--selected': isSelected(task.id) }"
              :style="barStyle(task)"
              :title="`${task.name}: ${phaseLabel(task.phaseId)} · ${weekLabel(task.startWeek)} – ${weekLabel(task.endWeek)}`"
              @mousedown.stop="onBarMouseDown($event, task, 'move')"
            >
              <button
                v-if="editable"
                type="button"
                class="gantt-bar__handle gantt-bar__handle--start"
                title="Drag to change start week"
                aria-label="Resize start"
                @mousedown.stop.prevent="onBarMouseDown($event, task, 'resize-start')"
              />
              <span class="gantt-bar__label">
                {{ weekLabel(task.startWeek) }}–{{ weekLabel(task.endWeek) }}
              </span>
              <button
                v-if="editable"
                type="button"
                class="gantt-bar__handle gantt-bar__handle--end"
                title="Drag to change end week"
                aria-label="Resize end"
                @mousedown.stop.prevent="onBarMouseDown($event, task, 'resize-end')"
              />
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { projectGanttFieldLabels } from '../data/projectGanttFixture.js'

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
  axis: 88,
  week: 44
}

const MIN_COL_WIDTHS = {
  label: 160,
  axis: 56,
  week: 28
}

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
  phases: { type: Array, default: () => [] },
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

const displayTasks = computed(() => {
  if (!preview.value) return props.tasks
  const { taskId, startWeek, endWeek, phaseId } = preview.value
  return props.tasks.map((task) =>
    task.id === taskId
      ? {
          ...task,
          startWeek: startWeek ?? task.startWeek,
          endWeek: endWeek ?? task.endWeek,
          phaseId: phaseId ?? task.phaseId
        }
      : task
  )
})

const selectedTask = computed(() => {
  if (!selectedTaskId.value) return null
  return displayTasks.value.find((task) => task.id === selectedTaskId.value) || null
})

const selectedDuration = computed(() => {
  if (!selectedTask.value) return 0
  return selectedTask.value.endWeek - selectedTask.value.startWeek + 1
})

const phaseById = computed(() => {
  const map = new Map()
  for (const phase of props.phases) {
    map.set(phase.id, phase)
  }
  return map
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

const phaseColor = (phaseId) =>
  phaseById.value.get(phaseId)?.color || phaseById.value.get('opportunity')?.color || '#6E6E6E'

const phaseLabel = (phaseId) =>
  phaseById.value.get(phaseId)?.label || 'Opportunity Assessment'

const barStyle = (task) => {
  const color = phaseColor(task.phaseId)
  const count = Math.max(1, maxWeek.value)
  const start = Math.max(0, task.startWeek - 1)
  const span = Math.max(1, task.endWeek - task.startWeek + 1)
  return {
    left: `${(start / count) * 100}%`,
    width: `${(span / count) * 100}%`,
    '--bar-color': color
  }
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
  document.querySelector(`.gantt-lane[data-task-id="${taskId}"]`)

const emitRange = (taskId, startWeek, endWeek, phaseId) => {
  const range = normalizeRange(startWeek, endWeek)
  const current = props.tasks.find((task) => task.id === taskId)
  const nextPhaseId = phaseId || current?.phaseId || 'opportunity'
  if (
    current &&
    current.startWeek === range.startWeek &&
    current.endWeek === range.endWeek &&
    (current.phaseId || 'opportunity') === nextPhaseId
  ) {
    return
  }
  emit('update-task', {
    id: taskId,
    ...range,
    phaseId: nextPhaseId
  })
}

const onSelectWeek = (taskId, which, event) => {
  const task = props.tasks.find((item) => item.id === taskId)
  if (!task) return
  const value = Number(event.target.value)
  if (!Number.isFinite(value)) return
  if (which === 'start') {
    emitRange(taskId, value, Math.max(value, task.endWeek), task.phaseId)
  } else {
    emitRange(taskId, Math.min(value, task.startWeek), value, task.phaseId)
  }
}

const onSelectPhase = (taskId, event) => {
  const task = props.tasks.find((item) => item.id === taskId)
  if (!task) return
  const phaseId = String(event.target.value || '').trim()
  if (!phaseId) return
  emitRange(taskId, task.startWeek, task.endWeek, phaseId)
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

const onBarMouseDown = (event, task, mode) => {
  if (!props.editable || event.button !== 0) return
  selectedTaskId.value = task.id
  const laneEl = event.currentTarget.closest('.gantt-lane') || findLaneEl(task.id)
  if (!laneEl) return
  const anchorWeek = weekFromClientX(event.clientX, laneEl)
  drag.value = {
    mode,
    taskId: task.id,
    originStart: task.startWeek,
    originEnd: task.endWeek,
    anchorWeek,
    duration: task.endWeek - task.startWeek + 1,
    laneEl
  }
  preview.value = {
    taskId: task.id,
    startWeek: task.startWeek,
    endWeek: task.endWeek,
    phaseId: task.phaseId
  }
}

const onLaneMouseDown = (event, task) => {
  if (!props.editable || event.button !== 0) return
  // Clicking empty lane area starts a redraw from that week
  if (event.target.closest('.gantt-bar')) return
  selectedTaskId.value = task.id
  const laneEl = event.currentTarget
  const week = weekFromClientX(event.clientX, laneEl)
  drag.value = {
    mode: 'draw',
    taskId: task.id,
    originStart: week,
    originEnd: week,
    anchorWeek: week,
    duration: 1,
    laneEl
  }
  preview.value = { taskId: task.id, startWeek: week, endWeek: week, phaseId: task.phaseId }
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
  const { mode, taskId, originStart, originEnd, anchorWeek, duration, laneEl } = drag.value
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
  emitRange(taskId, startWeek, endWeek)
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

.gantt-legend__item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  background: #fff;
  border: 1px solid var(--line-soft);
  font-size: 12px;
  color: var(--ink-soft);
  font-weight: 500;
}

.gantt-legend__swatch {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.08);
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
  min-height: 34px;
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
  background: #1e293b;
  font-weight: 500;
  color: #cbd5e1;
}

.gantt-cell--subhead.gantt-cell--label-blank {
  background: #1e293b;
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
  /* Timeline weeks: vertical dashed guides only */
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

.gantt-cell--label-clickable {
  cursor: pointer;
}

.gantt-cell--label-clickable:hover {
  color: #0070c0;
}

.gantt-cell--axis-blank {
  background: transparent;
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
    inset 0 -1px 0 rgba(148, 163, 184, 0.22),
    0 3px 8px -5px rgba(15, 23, 42, 0.14);
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
  min-height: 42px;
  isolation: isolate;
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
    rgba(100, 116, 139, 0.42) 0,
    rgba(100, 116, 139, 0.42) 4px,
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
  top: 8px;
  bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  border: 0;
  background: var(--bar-color);
  box-shadow:
    inset 3px 0 0 rgba(255, 255, 255, 0.28),
    0 2px 4px rgba(15, 23, 42, 0.16),
    0 6px 14px -6px rgba(15, 23, 42, 0.22);
  z-index: 1;
  min-width: calc(100% / var(--week-count));
  cursor: default;
  transition: transform 0.12s ease, box-shadow 0.12s ease;
}

.gantt-lane--editable .gantt-bar {
  cursor: grab;
}

.gantt-lane--editable .gantt-bar:active {
  cursor: grabbing;
}

.gantt-bar--selected {
  transform: translateY(-1px);
  box-shadow:
    inset 3px 0 0 rgba(255, 255, 255, 0.35),
    0 0 0 2px color-mix(in srgb, var(--bar-color) 28%, white),
    0 8px 18px color-mix(in srgb, var(--bar-color) 28%, transparent);
}

.gantt-bar__label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #fff;
  white-space: nowrap;
  pointer-events: none;
  padding: 0 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  text-shadow: 0 1px 1px rgba(15, 23, 42, 0.25);
}

.gantt-bar__handle {
  position: absolute;
  top: 4px;
  bottom: 4px;
  width: 6px;
  border: 0;
  padding: 0;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.85);
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
  left: 4px;
}

.gantt-bar__handle--end {
  right: 4px;
}
</style>
