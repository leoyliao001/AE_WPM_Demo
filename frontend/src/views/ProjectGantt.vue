<template>
  <PageShell
    :title="pageTitle"
    :subtitle="pageSubtitle"
    tag="Gantt"
    :back-to="backTo"
    back-label="Back to project"
    full-width
  >
    <mc-notification
      v-if="loadError"
      appearance="error"
      fit="medium"
      heading="Unable to load Gantt"
      :body="loadError"
    />

    <template v-else>
      <section class="gantt-panel">
        <div class="panel-head">
          <div>
            <h2>{{ fieldLabels.migrationKeySteps }}</h2>
            <p>
              {{
                !editMode
                  ? 'View mode — turn on Edit to change summary or Plan bars.'
                  : isDirty
                    ? 'Unsaved changes — edit summary or Plan bars, then Save.'
                    : savedAt
                      ? `Saved plan · last update ${savedAtLabel}`
                      : 'Using fixed Migration Key Steps — edit Plan bars, then Save for this project.'
              }}
            </p>
          </div>
          <div class="panel-actions">
            <mc-tag
              appearance="neutral"
              fit="small"
              :label="`${tasks.length} steps · ${weeks.length} weeks`"
            />
            <mc-button
              :appearance="editMode ? 'primary' : 'neutral'"
              :variant="editMode ? 'filled' : 'outlined'"
              fit="small"
              :label="editMode ? 'Editing on' : 'Enable edit'"
              :icon="editMode ? 'mi-pencil' : 'mi-lock'"
              :disabled="saving || loading"
              @click="editMode = !editMode"
            />
            <mc-button
              appearance="neutral"
              variant="outlined"
              fit="small"
              label="Reset template"
              :disabled="saving || loading || !editMode"
              @click="resetToTemplate"
            />
            <mc-button
              appearance="primary"
              variant="filled"
              fit="small"
              label="Save"
              :disabled="saving || loading || !isDirty"
              @click="saveGantt"
            />
          </div>
        </div>

        <ProjectGanttChart
          v-if="!loading"
          :editable="editMode"
          :weeks="weeks"
          :tasks="tasks"
          :bar-types="barTypes"
          :meta="meta"
          :field-labels="fieldLabels"
          :today-week="todayWeek"
          @update-task="onUpdateTask"
          @update-meta="onUpdateMeta"
        />

        <aside v-for="note in notes" :key="note.title" class="gantt-notes">
          <h3>{{ note.title }}</h3>
          <ul>
            <li v-for="item in note.items" :key="item">{{ item }}</li>
          </ul>
        </aside>
      </section>

      <mc-dialog
        :open="resultDialogOpen"
        :heading="resultDialogHeading"
        dimension="small"
        showclosebutton
        @closing="closeResultDialog"
      >
        <div
          class="result-dialog"
          :class="resultDialogIsError ? 'result-dialog--error' : 'result-dialog--success'"
        >
          <div class="result-dialog__badge" aria-hidden="true">
            <mc-icon
              :icon="resultDialogIsError ? 'mi-times' : 'mi-check-circle'"
              size="28"
            />
          </div>
          <p class="result-dialog__eyebrow">
            {{ resultDialogIsError ? 'Something went wrong' : 'All set' }}
          </p>
          <p class="result-dialog__message">{{ resultDialogMessage }}</p>
        </div>
        <div slot="footer" class="result-dialog-footer">
          <mc-button
            type="button"
            appearance="primary"
            variant="filled"
            fit="medium"
            :label="resultDialogIsError ? 'Close' : 'Done'"
            @click="closeResultDialog"
          />
        </div>
      </mc-dialog>
    </template>
  </PageShell>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'
import ProjectGanttChart from '../components/ProjectGanttChart.vue'
import {
  projectGanttFixture,
  buildProjectGanttWeeks,
  projectGanttBarTypes
} from '../data/projectGanttFixture.js'
import '@maersk-global/mds-components-core/mc-notification'
import '@maersk-global/mds-components-core/mc-tag'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-dialog'
import '@maersk-global/mds-components-core/mc-icon'

const cloneRange = (range) => {
  if (!range || typeof range !== 'object') return null
  const startWeek = Number(range.startWeek)
  const endWeek = Number(range.endWeek)
  if (!Number.isFinite(startWeek) || !Number.isFinite(endWeek)) return null
  return { startWeek, endWeek }
}

const cloneTasks = (rows) =>
  rows.map((task) => ({
    id: task.id,
    name: task.name,
    standard: cloneRange(task.standard) || { startWeek: 1, endWeek: 1 },
    plan: cloneRange(task.plan) || cloneRange(task.standard) || { startWeek: 1, endWeek: 1 },
    actual: cloneRange(task.actual),
    completedAt: task.completedAt ?? null,
    actualStatus: task.actualStatus ?? null
  }))

const cloneMeta = (source = {}) => ({
  projectPhase: source.projectPhase ?? '',
  scope: source.scope ?? '',
  migratableFte: source.migratableFte ?? '',
  learningCurve: source.learningCurve ?? '',
  tlTmHc: source.tlTmHc ?? '',
  mngrHc: source.mngrHc ?? '',
  totalWoBuffer: source.totalWoBuffer ?? '',
  total: source.total ?? ''
})

const route = useRoute()
const project = ref(null)
const loadError = ref('')
const loading = ref(true)
const saving = ref(false)
const resultDialogOpen = ref(false)
const resultDialogHeading = ref('Saved')
const resultDialogMessage = ref('')
const resultDialogIsError = ref(false)
const savedAt = ref(null)
const isDirty = ref(false)
const editMode = ref(false)
const fieldLabels = projectGanttFixture.fieldLabels
const weeks = ref(buildProjectGanttWeeks())
const barTypes = ref([...projectGanttBarTypes])
const notes = projectGanttFixture.notes
const todayWeek = projectGanttFixture.todayWeek
const tasks = ref(cloneTasks(projectGanttFixture.tasks))
const templateTasks = ref(cloneTasks(projectGanttFixture.tasks))
const meta = ref(cloneMeta(projectGanttFixture.meta))

const backTo = computed(() => `/migration-dashboard/${route.params.id}`)

const pageTitle = computed(() =>
  project.value?.projectName ? `Gantt — ${project.value.projectName}` : 'Project Gantt'
)

const pageSubtitle = computed(() => {
  if (project.value) {
    const start = weeks.value?.[0]?.calendarWeek
    return start
      ? `${project.value.migrationRequestId} — Calendar weeks start at ${start} (intake week + 1).`
      : `${project.value.migrationRequestId} — edit fixed Migration Key Steps Plan bars for this project.`
  }
  return 'Edit fixed Migration Key Steps Plan bars for this project.'
})

const savedAtLabel = computed(() => {
  if (!savedAt.value) return ''
  try {
    return new Date(savedAt.value).toLocaleString()
  } catch {
    return savedAt.value
  }
})

const applyGanttPayload = (data, projectData = null) => {
  const nextTasks = Array.isArray(data?.tasks) ? data.tasks : []
  const nextTemplate = Array.isArray(data?.template_tasks)
    ? data.template_tasks
    : projectGanttFixture.tasks
  tasks.value = cloneTasks(nextTasks.length ? nextTasks : projectGanttFixture.tasks)
  templateTasks.value = cloneTasks(nextTemplate)

  if (Array.isArray(data?.weeks) && data.weeks.length) {
    weeks.value = data.weeks.map((week, index) => ({
      index: week.index ?? index + 1,
      timelineWeek: week.timelineWeek || `wk${String(index + 1).padStart(2, '0')}`,
      calendarWeek: week.calendarWeek || '',
      calendarWeekNumber: week.calendarWeekNumber,
      calendarYear: week.calendarYear
    }))
  } else {
    const createdAt =
      data?.intake_created_at || projectData?.createdAt || project.value?.createdAt || null
    weeks.value = buildProjectGanttWeeks(createdAt || undefined)
  }

  if (data?.meta && typeof data.meta === 'object') {
    meta.value = mergeSavedMeta(data.meta)
  }

  barTypes.value = Array.isArray(data?.barTypes) && data.barTypes.length
    ? data.barTypes
    : [...projectGanttBarTypes]

  savedAt.value = data?.updated_at || null
}

const mergeSavedMeta = (savedMeta) => {
  const base = cloneMeta(projectGanttFixture.meta)
  if (!savedMeta || typeof savedMeta !== 'object') return base
  return cloneMeta({ ...base, ...savedMeta })
}

const rangesEqual = (a, b) =>
  a?.startWeek === b?.startWeek && a?.endWeek === b?.endWeek

/** Monday (UTC) of an ISO week. */
const mondayOfIsoWeek = (year, week) => {
  const jan4 = new Date(Date.UTC(year, 0, 4))
  const day = jan4.getUTCDay() || 7
  const monday = new Date(jan4)
  monday.setUTCDate(jan4.getUTCDate() - day + 1 + (week - 1) * 7)
  return monday
}

const parseLocalDateOnly = (isoDate) => {
  const text = String(isoDate || '').trim()
  const match = text.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (match) {
    return new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])))
  }
  const date = new Date(text)
  if (Number.isNaN(date.getTime())) return null
  return new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
}

/**
 * Map a completion date to timeline week index (1..N).
 * Uses day-offset from the chart's first calendar week Monday.
 * Dates outside the chart are clamped to the nearest week so Actual can still render.
 */
const weekIndexFromDate = (isoDate) => {
  if (!isoDate || !weeks.value?.length) return null
  const target = parseLocalDateOnly(isoDate)
  if (!target) return null

  const first = weeks.value[0]
  const year = Number(first.calendarYear)
  const weekNum = Number(first.calendarWeekNumber)
  if (!Number.isFinite(year) || !Number.isFinite(weekNum)) return null

  const startMonday = mondayOfIsoWeek(year, weekNum)
  const diffDays = Math.floor((target.getTime() - startMonday.getTime()) / 86400000)
  const rawIndex = Math.floor(diffDays / 7) + 1
  const maxIndex = weeks.value.length
  return Math.min(maxIndex, Math.max(1, rawIndex))
}

const refreshActualFromCompletion = (task, completedAt, plan) => {
  if (!completedAt) {
    return { actual: null, actualStatus: null, completedAt: null }
  }
  const week = weekIndexFromDate(completedAt)
  if (!week || !plan) {
    return { actual: null, actualStatus: null, completedAt }
  }
  const startWeek = Math.min(plan.startWeek, week)
  const endWeek = week
  const actual = { startWeek, endWeek }
  const actualStatus = endWeek <= plan.endWeek ? 'on_time' : 'late'
  return { actual, actualStatus, completedAt }
}

const onUpdateTask = (payload) => {
  const { id } = payload || {}
  if (!id) return
  const index = tasks.value.findIndex((task) => task.id === id)
  if (index < 0) return
  const current = tasks.value[index]

  let nextPlan = current.plan
  if (payload.plan && typeof payload.plan === 'object') {
    nextPlan = cloneRange(payload.plan) || current.plan
  } else if (
    Number.isFinite(Number(payload.startWeek)) &&
    Number.isFinite(Number(payload.endWeek))
  ) {
    nextPlan =
      cloneRange({
        startWeek: payload.startWeek,
        endWeek: payload.endWeek
      }) || current.plan
  }

  const hasCompletedAt = Object.prototype.hasOwnProperty.call(payload, 'completedAt')
  const nextCompletedAt = hasCompletedAt
    ? payload.completedAt || null
    : current.completedAt || null

  const planChanged = !rangesEqual(current.plan, nextPlan)
  const completedChanged =
    hasCompletedAt && String(current.completedAt || '') !== String(nextCompletedAt || '')

  if (!planChanged && !completedChanged) return

  let nextActual = current.actual
  let nextActualStatus = current.actualStatus
  let nextCompleted = current.completedAt || null

  if (hasCompletedAt || (planChanged && nextCompletedAt)) {
    const actualFields = refreshActualFromCompletion(current, nextCompletedAt, nextPlan)
    nextActual = actualFields.actual
    nextActualStatus = actualFields.actualStatus
    nextCompleted = actualFields.completedAt
  } else if (planChanged && current.actual) {
    nextActualStatus =
      current.actual.endWeek <= nextPlan.endWeek ? 'on_time' : 'late'
  }

  const next = [...tasks.value]
  next[index] = {
    ...current,
    plan: nextPlan,
    completedAt: nextCompleted,
    actual: nextActual,
    actualStatus: nextActualStatus
  }
  tasks.value = next
  isDirty.value = true
}

const onUpdateMeta = ({ key, value }) => {
  if (!(key in meta.value)) return
  if (meta.value[key] === value) return
  meta.value = { ...meta.value, [key]: value }
  isDirty.value = true
}

const resetToTemplate = () => {
  tasks.value = cloneTasks(templateTasks.value.length ? templateTasks.value : projectGanttFixture.tasks)
  meta.value = cloneMeta(projectGanttFixture.meta)
  isDirty.value = true
}

const openResultDialog = ({ heading, message, isError = false }) => {
  resultDialogHeading.value = heading
  resultDialogMessage.value = message
  resultDialogIsError.value = isError
  resultDialogOpen.value = true
}

const closeResultDialog = () => {
  resultDialogOpen.value = false
}

const loadAll = async () => {
  loading.value = true
  loadError.value = ''
  resultDialogOpen.value = false
  project.value = null
  isDirty.value = false
  tasks.value = cloneTasks(projectGanttFixture.tasks)
  templateTasks.value = cloneTasks(projectGanttFixture.tasks)
  meta.value = cloneMeta(projectGanttFixture.meta)
  barTypes.value = [...projectGanttBarTypes]
  savedAt.value = null

  try {
    const [projectRes, ganttRes] = await Promise.all([
      axios.get(`/api/migration-dashboard/projects/${route.params.id}/`),
      axios.get(`/api/migration-dashboard/projects/${route.params.id}/gantt/`)
    ])
    project.value = projectRes.data
    applyGanttPayload(ganttRes.data || {}, projectRes.data)
  } catch (error) {
    loadError.value =
      error?.response?.data?.error ?? 'Unable to load this project Gantt. Please try again.'
  } finally {
    loading.value = false
  }
}

const saveGantt = async () => {
  saving.value = true
  try {
    const { data } = await axios.put(
      `/api/migration-dashboard/projects/${route.params.id}/gantt/`,
      {
        tasks: tasks.value,
        meta: meta.value
      }
    )
    applyGanttPayload(data || {})
    isDirty.value = false
    openResultDialog({
      heading: 'Saved',
      message: 'Gantt plan and project parameters saved for this project.',
      isError: false
    })
  } catch (error) {
    openResultDialog({
      heading: 'Save failed',
      message: error?.response?.data?.error ?? 'Unable to save Gantt. Please try again.',
      isError: true
    })
  } finally {
    saving.value = false
  }
}

onMounted(loadAll)
watch(() => route.params.id, loadAll)
</script>
<style scoped>
.gantt-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 4px 2px 2px;
}

.panel-head h2 {
  margin: 0 0 6px;
  font-size: 1.2rem;
  color: #0f172a;
  font-family: 'Maersk Headline', 'Maersk Text', sans-serif;
  letter-spacing: -0.02em;
  font-weight: 700;
}

.panel-head p {
  margin: 0;
  color: #64748b;
  font-size: 0.9rem;
  line-height: 1.45;
  max-width: 56rem;
}

.panel-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.gantt-notes {
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  padding: 16px 18px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
}

.gantt-notes h3 {
  margin: 0 0 8px;
  font-size: 0.95rem;
  color: #0f172a;
  font-family: 'Maersk Headline', 'Maersk Text', sans-serif;
  letter-spacing: -0.01em;
}

.gantt-notes ul {
  margin: 0;
  padding-left: 1.1rem;
  color: #64748b;
  font-size: 0.88rem;
  line-height: 1.55;
}

.gantt-notes li + li {
  margin-top: 4px;
}

.result-dialog {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  margin: 2px 0 4px;
  padding: 16px 16px 14px;
  border-radius: 14px;
  border: 1px solid transparent;
  animation: result-dialog-in 220ms ease-out;
}

.result-dialog--success {
  background: linear-gradient(165deg, #f0fdf6 0%, #ecfdf5 48%, #f8fafc 100%);
  border-color: #bbf7d0;
}

.result-dialog--error {
  background: linear-gradient(165deg, #fff1f2 0%, #fef2f2 48%, #f8fafc 100%);
  border-color: #fecaca;
}

.result-dialog__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  margin-bottom: 2px;
  border-radius: 50%;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
}

.result-dialog--success .result-dialog__badge {
  color: #047857;
  background: #d1fae5;
}

.result-dialog--error .result-dialog__badge {
  color: #b91c1c;
  background: #fee2e2;
}

.result-dialog__eyebrow {
  margin: 0;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #64748b;
}

.result-dialog--success .result-dialog__eyebrow {
  color: #047857;
}

.result-dialog--error .result-dialog__eyebrow {
  color: #b91c1c;
}

.result-dialog__message {
  margin: 0;
  color: #334155;
  font-size: 0.95rem;
  line-height: 1.55;
  max-width: 28rem;
}

.result-dialog-footer {
  display: flex;
  justify-content: flex-end;
}

@keyframes result-dialog-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
