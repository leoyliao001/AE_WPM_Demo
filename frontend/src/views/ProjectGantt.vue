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
                  ? 'View mode — turn on Edit to change Total, Plan bars, or stages (+/−).'
                  : isDirty
                    ? 'Unsaved changes — first Plan save is free; later Plan updates need a comment on Save.'
                    : savedAt
                      ? `Saved plan · last update ${savedAtLabel}`
                      : 'Empty Plan: set freely. Updating a saved Plan asks for a comment when you Save.'
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
              :disabled="saving || loading || !editMode"
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
          :meta="summaryMeta"
          :field-labels="fieldLabels"
          :today-week="todayWeek"
          @update-task="onUpdateTask"
          @update-meta="onUpdateMeta"
          @duplicate-task="onDuplicateTask"
          @remove-task="onRemoveTask"
          @view-comments="onViewComments"
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

      <mc-dialog
        :open="historyDialogOpen"
        :heading="historyDialogHeading"
        dimension="large"
        showclosebutton
        @closing="closeHistoryDialog"
      >
        <div class="history-dialog">
          <div class="history-dialog__hero">
            <div class="history-dialog__hero-main">
              <p class="history-dialog__eyebrow">Migration Key Steps</p>
              <h3 class="history-dialog__title">{{ historyDialogTaskName || 'Stage' }}</h3>
              <p class="history-dialog__subtitle">
                Append-only Plan change log · oldest to newest ·
                {{ historyDialogComments.length }}
                {{ historyDialogComments.length === 1 ? 'entry' : 'entries' }}
              </p>
            </div>
            <div class="history-dialog__metrics">
              <div class="history-dialog__metric">
                <span>Current Plan</span>
                <strong>{{ formatPlanLabel(historyDialogCurrentPlan) }}</strong>
              </div>
              <div class="history-dialog__metric">
                <span>Standard</span>
                <strong>{{ formatPlanLabel(historyDialogStandard) }}</strong>
              </div>
            </div>
          </div>

          <p v-if="!historyDialogComments.length" class="history-dialog__empty">
            No Plan comments on this stage yet. The first Plan save does not require a comment;
            later updates will.
          </p>

          <ol v-else class="history-dialog__timeline">
            <li
              v-for="(entry, index) in historyDialogComments"
              :key="entry.id || `${entry.at}-${entry.text}-${index}`"
              class="history-dialog__item"
            >
              <div class="history-dialog__rail" aria-hidden="true">
                <span class="history-dialog__dot">{{ index + 1 }}</span>
              </div>
              <article class="history-dialog__panel">
                <header class="history-dialog__panel-head">
                  <span class="history-dialog__badge">Update {{ index + 1 }}</span>
                  <time class="history-dialog__when" :datetime="entry.at || undefined">
                    {{ formatCommentDateTime(entry.at) }}
                  </time>
                </header>
                <p v-if="entry.updatedBy" class="history-dialog__by">
                  Updated by <strong>{{ entry.updatedBy }}</strong>
                </p>
                <div class="history-dialog__range-row">
                  <div class="history-dialog__chip">
                    <span>From</span>
                    <strong>{{ formatPlanLabel(entry.fromPlan) }}</strong>
                  </div>
                  <span class="history-dialog__arrow" aria-hidden="true">→</span>
                  <div class="history-dialog__chip history-dialog__chip--to">
                    <span>To</span>
                    <strong>{{ formatPlanLabel(entry.toPlan) }}</strong>
                  </div>
                </div>
                <blockquote class="history-dialog__quote">
                  <p>{{ entry.text }}</p>
                </blockquote>
              </article>
            </li>
          </ol>

          <div class="history-dialog__footer">
            <mc-button
              type="button"
              appearance="primary"
              variant="filled"
              fit="medium"
              label="Close"
              @click="closeHistoryDialog"
            />
          </div>
        </div>
      </mc-dialog>

      <mc-dialog
        :open="reasonDialogOpen"
        heading="Comment for Plan update"
        dimension="small"
        showclosebutton
        @closing="cancelReasonDialog"
      >
        <div class="reason-dialog">
          <p class="reason-dialog__lead">
            <template v-if="pendingPlanChanges.length > 1">
              {{ reasonStepIndex + 1 }} of {{ pendingPlanChanges.length }} —
            </template>
            Plan for <strong>{{ currentPendingPlanChange?.taskName || 'this stage' }}</strong> was
            already saved. Add a comment before saving this update. Earlier comments stay on this
            stage.
          </p>
          <p v-if="currentPendingPlanChange" class="reason-dialog__range">
            {{ formatPlanLabel(currentPendingPlanChange.fromPlan) }}
            →
            {{ formatPlanLabel(currentPendingPlanChange.toPlan) }}
          </p>
          <div
            v-if="currentStageCommentHistory.length"
            class="reason-dialog__history"
          >
            <p class="reason-dialog__history-title">Previous comments</p>
            <ul class="reason-dialog__history-list">
              <li
                v-for="entry in currentStageCommentHistory"
                :key="entry.id || `${entry.at}-${entry.text}`"
              >
                <span class="reason-dialog__history-meta">
                  {{ formatCommentHistoryMeta(entry) }}
                </span>
                <span>{{ entry.text }}</span>
              </li>
            </ul>
          </div>
          <label class="reason-dialog__field">
            <span>Comment</span>
            <textarea
              v-model="reasonText"
              class="reason-dialog__input"
              rows="4"
              maxlength="500"
              placeholder="Why is this Plan timeline being updated?"
            />
          </label>
          <p v-if="reasonError" class="reason-dialog__error">{{ reasonError }}</p>
          <div class="reason-dialog__actions">
            <mc-button
              type="button"
              appearance="neutral"
              variant="outlined"
              fit="medium"
              label="Cancel"
              @click="cancelReasonDialog"
            />
            <mc-button
              type="button"
              appearance="primary"
              variant="filled"
              fit="medium"
              :label="reasonStepIndex + 1 < pendingPlanChanges.length ? 'Next' : 'Save'"
              :disabled="saving"
              @click="confirmReasonDialog"
            />
          </div>
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
import { getCurrentUserEmail } from '../auth/azureAuth.js'
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

const hasPlanData = (plan) => Boolean(cloneRange(plan))

const makeCommentId = () =>
  `c-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`

const currentUpdaterLabel = () => {
  const email = String(getCurrentUserEmail() || '').trim()
  return email || 'unknown'
}

const cloneComments = (comments) => {
  if (!Array.isArray(comments)) return []
  return comments
    .map((entry) => {
      if (!entry || typeof entry !== 'object') return null
      const text = String(entry.text || '').trim()
      if (!text) return null
      const id = entry.id != null && String(entry.id).trim() ? String(entry.id).trim() : null
      const updatedBy = String(entry.updatedBy || entry.updated_by || '').trim() || null
      return {
        id,
        at: entry.at ? String(entry.at) : new Date().toISOString(),
        text,
        updatedBy,
        fromPlan: cloneRange(entry.fromPlan),
        toPlan: cloneRange(entry.toPlan)
      }
    })
    .filter(Boolean)
}

const cloneTasks = (rows) =>
  rows.map((task) => ({
    id: task.id,
    name: task.name,
    standard: cloneRange(task.standard),
    plan: cloneRange(task.plan),
    actual: cloneRange(task.actual),
    completedAt: task.completedAt ?? null,
    actualStatus: task.actualStatus ?? null,
    comments: cloneComments(task.comments)
  }))

const makeTaskId = (name) => {
  const base =
    String(name || 'stage')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 40) || 'stage'
  return `${base}-${Date.now().toString(36)}`
}

/**
 * Plain JSON payload for PUT.
 * Optional draftCommentsByTaskId appends new Plan-change comments for this save only
 * (history on each task is kept; server also merges append-only).
 */
const serializeTasksForSave = (rows, draftCommentsByTaskId = {}) =>
  (rows || []).map((task) => {
    const taskId = String(task.id || '').trim()
    const rawDraft = draftCommentsByTaskId[taskId]
    const draftList = !rawDraft ? [] : Array.isArray(rawDraft) ? rawDraft : [rawDraft]
    return {
      id: taskId,
      name: String(task.name || '').trim(),
      standard: cloneRange(task.standard),
      plan: cloneRange(task.plan),
      actual: cloneRange(task.actual),
      completedAt: task.completedAt ? String(task.completedAt) : null,
      comments: [...cloneComments(task.comments), ...cloneComments(draftList)]
    }
  })

const cloneMeta = (source = {}) => ({
  total: source.total ?? ''
})

const formatAreasLabel = (areas) => {
  const list = Array.isArray(areas)
    ? areas.map((item) => String(item || '').trim()).filter(Boolean)
    : String(areas || '')
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean)
  return list.length ? list.join(', ') : '—'
}

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
const reasonDialogOpen = ref(false)
const reasonText = ref('')
const reasonError = ref('')
const pendingPlanChanges = ref([])
const reasonStepIndex = ref(0)
/** Draft comments collected at Save-time (applied only in PUT payload until success). */
const draftCommentsByTaskId = ref({})
const historyDialogOpen = ref(false)
const historyDialogTaskName = ref('')
const historyDialogComments = ref([])
const historyDialogCurrentPlan = ref(null)
const historyDialogStandard = ref(null)
const lastSavedTasks = ref([])
const fieldLabels = projectGanttFixture.fieldLabels
const weeks = ref(buildProjectGanttWeeks())
const barTypes = ref([...projectGanttBarTypes])
const notes = projectGanttFixture.notes
const todayWeek = projectGanttFixture.todayWeek
const tasks = ref(cloneTasks(projectGanttFixture.tasks))
const templateTasks = ref(cloneTasks(projectGanttFixture.tasks))
const meta = ref(cloneMeta(projectGanttFixture.meta))

const summaryMeta = computed(() => ({
  region: String(project.value?.region || '').trim() || '—',
  area: formatAreasLabel(project.value?.areas),
  total: meta.value.total ?? ''
}))

const currentPendingPlanChange = computed(
  () => pendingPlanChanges.value[reasonStepIndex.value] || null
)

const currentStageCommentHistory = computed(() => {
  const pending = currentPendingPlanChange.value
  if (!pending?.taskId) return []
  const task = tasks.value.find((row) => row.id === pending.taskId)
  return cloneComments(task?.comments)
})

const historyDialogHeading = computed(() => 'Plan comment history')

const backTo = computed(() => `/migration-dashboard/${route.params.id}`)

const pageTitle = computed(() =>
  project.value?.projectName ? `Gantt — ${project.value.projectName}` : 'Project Gantt'
)

const pageSubtitle = computed(() => {
  if (project.value) {
    const start = weeks.value?.[0]?.calendarWeek
    return start
      ? `${project.value.migrationRequestId} — Calendar weeks start at ${start} (intake week + 1).`
      : `${project.value.migrationRequestId} — edit Migration Key Steps Plan bars for this project.`
  }
  return 'Edit Migration Key Steps Plan bars for this project.'
})

const savedAtLabel = computed(() => {
  if (!savedAt.value) return ''
  try {
    return new Date(savedAt.value).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
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
  lastSavedTasks.value = cloneTasks(tasks.value)
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

const formatPlanLabel = (range) => {
  if (!range) return 'none'
  return `wk${String(range.startWeek).padStart(2, '0')}–wk${String(range.endWeek).padStart(2, '0')}`
}

const formatCommentHistoryMeta = (entry) => {
  const when = formatCommentDateTime(entry?.at)
  const by = entry?.updatedBy ? String(entry.updatedBy).trim() : ''
  const range =
    entry?.fromPlan || entry?.toPlan
      ? `${formatPlanLabel(entry.fromPlan)} → ${formatPlanLabel(entry.toPlan)}`
      : ''
  const parts = []
  if (when !== 'Unknown time') parts.push(when)
  if (by) parts.push(`by ${by}`)
  if (range) parts.push(range)
  return parts.join(' · ') || 'Previous'
}

const formatCommentDateTime = (iso) => {
  if (!iso) return 'Unknown time'
  try {
    const date = new Date(iso)
    if (Number.isNaN(date.getTime())) return String(iso)
    // Always English — project UI is en-US only.
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    })
  } catch {
    return String(iso)
  }
}

const applyTaskUpdate = (payload) => {
  const { id } = payload || {}
  if (!id) return
  const index = tasks.value.findIndex((task) => task.id === id)
  if (index < 0) return
  const current = tasks.value[index]

  let nextName = current.name
  const hasName = Object.prototype.hasOwnProperty.call(payload, 'name')
  if (hasName) {
    nextName = String(payload.name ?? '')
  }

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

  const nameChanged = hasName && nextName !== current.name
  const planChanged = !rangesEqual(current.plan, nextPlan)
  const completedChanged =
    hasCompletedAt && String(current.completedAt || '') !== String(nextCompletedAt || '')

  if (!nameChanged && !planChanged && !completedChanged) return

  let nextActual = current.actual
  let nextActualStatus = current.actualStatus
  let nextCompleted = current.completedAt || null

  if (hasCompletedAt || (planChanged && nextCompletedAt)) {
    const actualFields = refreshActualFromCompletion(current, nextCompletedAt, nextPlan)
    nextActual = actualFields.actual
    nextActualStatus = actualFields.actualStatus
    nextCompleted = actualFields.completedAt
  } else if (planChanged && current.actual && nextPlan) {
    nextActualStatus =
      current.actual.endWeek <= nextPlan.endWeek ? 'on_time' : 'late'
  }

  const next = [...tasks.value]
  next[index] = {
    ...current,
    name: nextName,
    plan: nextPlan,
    completedAt: nextCompleted,
    actual: nextActual,
    actualStatus: nextActualStatus
  }
  tasks.value = next
  isDirty.value = true
}

const onUpdateTask = (payload) => {
  applyTaskUpdate(payload)
}

/** Compare current Plans vs last saved: updates of already-saved Plans need a comment. */
const getPlanChangesRequiringReason = () => {
  const baselineById = new Map(lastSavedTasks.value.map((task) => [task.id, task]))
  const changes = []
  for (const task of tasks.value) {
    const saved = baselineById.get(task.id)
    const fromPlan = saved ? cloneRange(saved.plan) : null
    const toPlan = cloneRange(task.plan)
    if (!hasPlanData(fromPlan)) continue
    if (rangesEqual(fromPlan, toPlan)) continue
    changes.push({
      taskId: task.id,
      taskName: task.name,
      fromPlan,
      toPlan
    })
  }
  return changes
}

const draftCoversPlanChanges = (changes) => {
  if (!changes.length) return true
  const drafts = draftCommentsByTaskId.value || {}
  return changes.every((change) => {
    const entry = drafts[change.taskId]
    if (!entry?.text) return false
    return (
      rangesEqual(entry.fromPlan, change.fromPlan) &&
      rangesEqual(entry.toPlan, change.toPlan)
    )
  })
}

const resetReasonDialog = ({ clearDrafts = false } = {}) => {
  reasonDialogOpen.value = false
  reasonText.value = ''
  reasonError.value = ''
  pendingPlanChanges.value = []
  reasonStepIndex.value = 0
  if (clearDrafts) draftCommentsByTaskId.value = {}
}

const cancelReasonDialog = () => {
  // Keep typed drafts so a later Save can resume; discard only the open wizard.
  resetReasonDialog({ clearDrafts: false })
}

const confirmReasonDialog = async () => {
  const reason = String(reasonText.value || '').trim()
  if (!reason) {
    reasonError.value = 'Please enter a comment for this Plan update.'
    return
  }
  const pending = currentPendingPlanChange.value
  if (!pending?.taskId) {
    resetReasonDialog({ clearDrafts: true })
    return
  }

  draftCommentsByTaskId.value = {
    ...draftCommentsByTaskId.value,
    [pending.taskId]: {
      id: makeCommentId(),
      at: new Date().toISOString(),
      text: reason,
      updatedBy: currentUpdaterLabel(),
      fromPlan: cloneRange(pending.fromPlan),
      toPlan: cloneRange(pending.toPlan)
    }
  }

  const nextIndex = reasonStepIndex.value + 1
  if (nextIndex < pendingPlanChanges.value.length) {
    reasonStepIndex.value = nextIndex
    const nextChange = pendingPlanChanges.value[nextIndex]
    const existingDraft = draftCommentsByTaskId.value[nextChange?.taskId]
    reasonText.value =
      existingDraft &&
      rangesEqual(existingDraft.fromPlan, nextChange.fromPlan) &&
      rangesEqual(existingDraft.toPlan, nextChange.toPlan)
        ? existingDraft.text
        : ''
    reasonError.value = ''
    return
  }

  resetReasonDialog({ clearDrafts: false })
  await persistGantt()
}

const onDuplicateTask = ({ id } = {}) => {
  if (!id || !editMode.value) return
  const index = tasks.value.findIndex((task) => task.id === id)
  if (index < 0) return
  const source = tasks.value[index]
  const standard = cloneRange(source.standard)
  const duplicated = {
    id: makeTaskId(source.name),
    name: source.name,
    standard,
    plan: null,
    actual: null,
    completedAt: null,
    actualStatus: null,
    comments: []
  }
  const next = [...tasks.value]
  next.splice(index + 1, 0, duplicated)
  tasks.value = next
  isDirty.value = true
}

const onViewComments = ({ id } = {}) => {
  if (!id) return
  const task = tasks.value.find((row) => row.id === id)
  if (!task) return
  historyDialogTaskName.value = task.name || 'Stage'
  historyDialogComments.value = cloneComments(task.comments)
  historyDialogCurrentPlan.value = cloneRange(task.plan)
  historyDialogStandard.value = cloneRange(task.standard)
  historyDialogOpen.value = true
}

const closeHistoryDialog = () => {
  historyDialogOpen.value = false
  historyDialogTaskName.value = ''
  historyDialogComments.value = []
  historyDialogCurrentPlan.value = null
  historyDialogStandard.value = null
}

const onRemoveTask = ({ id } = {}) => {
  if (!id || !editMode.value) return
  if (tasks.value.length <= 1) return
  tasks.value = tasks.value.filter((task) => task.id !== id)
  isDirty.value = true
}

const onUpdateMeta = ({ key, value }) => {
  if (key !== 'total') return
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
  resetReasonDialog({ clearDrafts: true })
  closeHistoryDialog()
  project.value = null
  isDirty.value = false
  tasks.value = cloneTasks(projectGanttFixture.tasks)
  templateTasks.value = cloneTasks(projectGanttFixture.tasks)
  meta.value = cloneMeta(projectGanttFixture.meta)
  barTypes.value = [...projectGanttBarTypes]
  savedAt.value = null
  lastSavedTasks.value = []

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

const persistGantt = async () => {
  if (saving.value || loading.value) return
  saving.value = true
  try {
    const payload = {
      tasks: serializeTasksForSave(tasks.value, draftCommentsByTaskId.value),
      meta: cloneMeta(meta.value)
    }
    const { data } = await axios.put(
      `/api/migration-dashboard/projects/${route.params.id}/gantt/`,
      payload
    )
    applyGanttPayload(data || {})
    draftCommentsByTaskId.value = {}
    isDirty.value = false
    openResultDialog({
      heading: 'Saved',
      message: `Gantt saved (${tasks.value.length} stages). Refresh will keep your changes.`,
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

const openCommentDialogForChanges = (changes) => {
  pendingPlanChanges.value = changes
  reasonStepIndex.value = 0
  const first = changes[0]
  const existingDraft = draftCommentsByTaskId.value[first?.taskId]
  reasonText.value =
    existingDraft &&
    rangesEqual(existingDraft.fromPlan, first.fromPlan) &&
    rangesEqual(existingDraft.toPlan, first.toPlan)
      ? existingDraft.text
      : ''
  reasonError.value = ''
  reasonDialogOpen.value = true
}

const saveGantt = async () => {
  if (!editMode.value || saving.value || loading.value || reasonDialogOpen.value) return

  const changes = getPlanChangesRequiringReason()
  if (changes.length) {
    if (draftCoversPlanChanges(changes)) {
      await persistGantt()
      return
    }
    openCommentDialogForChanges(changes)
    return
  }

  draftCommentsByTaskId.value = {}
  await persistGantt()
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

.reason-dialog {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 4px 2px 8px;
}

.reason-dialog__lead {
  color: #334155;
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
}

.reason-dialog__range {
  color: #0070c0;
  font-size: 13px;
  font-weight: 600;
  margin: 0;
}

.reason-dialog__history {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
  max-height: 140px;
  overflow: auto;
  padding: 8px 10px;
}

.reason-dialog__history-title {
  margin: 0 0 6px;
  color: #64748b;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.reason-dialog__history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.reason-dialog__history-list li {
  color: #334155;
  font-size: 12px;
  line-height: 1.4;
}

.reason-dialog__history-meta {
  display: block;
  color: #64748b;
  font-size: 11px;
  font-weight: 600;
  margin-bottom: 2px;
}

.reason-dialog__field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
}

.reason-dialog__input {
  border: 1px solid rgba(15, 23, 42, 0.16);
  border-radius: 8px;
  color: #0f172a;
  font: inherit;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.45;
  min-height: 96px;
  padding: 10px 12px;
  resize: vertical;
  width: 100%;
}

.reason-dialog__input:focus {
  border-color: #0070c0;
  box-shadow: 0 0 0 2px rgba(0, 112, 192, 0.15);
  outline: none;
}

.reason-dialog__error {
  color: #b91c1c;
  font-size: 12px;
  margin: 0;
}

.reason-dialog__actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 4px;
  padding-top: 4px;
}

.history-dialog {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: min(760px, 100%);
  padding: 2px 2px 6px;
}

.history-dialog__hero {
  align-items: stretch;
  background:
    linear-gradient(135deg, rgba(66, 176, 213, 0.12), rgba(0, 112, 192, 0.08)),
    #f8fafc;
  border: 1px solid rgba(148, 163, 184, 0.35);
  border-radius: 14px;
  display: flex;
  gap: 16px;
  justify-content: space-between;
  padding: 16px 18px;
}

.history-dialog__hero-main {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.history-dialog__eyebrow {
  color: #0284c7;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  margin: 0;
  text-transform: uppercase;
}

.history-dialog__title {
  color: #0f172a;
  font-size: 1.25rem;
  font-weight: 700;
  line-height: 1.25;
  margin: 0;
}

.history-dialog__subtitle {
  color: #64748b;
  font-size: 12.5px;
  line-height: 1.45;
  margin: 2px 0 0;
}

.history-dialog__metrics {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 168px;
}

.history-dialog__metric {
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(148, 163, 184, 0.28);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 10px;
}

.history-dialog__metric span {
  color: #64748b;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.history-dialog__metric strong {
  color: #0f172a;
  font-size: 13px;
  font-weight: 700;
}

.history-dialog__empty {
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  border-radius: 12px;
  color: #64748b;
  font-size: 13px;
  line-height: 1.5;
  margin: 0;
  padding: 18px;
}

.history-dialog__timeline {
  display: flex;
  flex-direction: column;
  gap: 0;
  list-style: none;
  margin: 0;
  max-height: min(54vh, 520px);
  overflow: auto;
  padding: 4px 4px 8px 0;
}

.history-dialog__item {
  display: grid;
  gap: 12px;
  grid-template-columns: 28px minmax(0, 1fr);
  padding-bottom: 14px;
  position: relative;
}

.history-dialog__item:last-child {
  padding-bottom: 2px;
}

.history-dialog__rail {
  display: flex;
  justify-content: center;
  position: relative;
}

.history-dialog__rail::before {
  background: linear-gradient(#bae6fd, #e2e8f0);
  bottom: -14px;
  content: '';
  position: absolute;
  top: 28px;
  width: 2px;
}

.history-dialog__item:last-child .history-dialog__rail::before {
  display: none;
}

.history-dialog__dot {
  align-items: center;
  background: #0070c0;
  border: 2px solid #e0f2fe;
  border-radius: 999px;
  box-shadow: 0 0 0 3px rgba(0, 112, 192, 0.12);
  color: #fff;
  display: inline-flex;
  font-size: 11px;
  font-weight: 700;
  height: 26px;
  justify-content: center;
  position: relative;
  width: 26px;
  z-index: 1;
}

.history-dialog__panel {
  background: #fff;
  border: 1px solid rgba(148, 163, 184, 0.32);
  border-radius: 14px;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px 16px;
}

.history-dialog__panel-head {
  align-items: center;
  display: flex;
  gap: 10px;
  justify-content: space-between;
}

.history-dialog__badge {
  background: rgba(0, 112, 192, 0.1);
  border-radius: 999px;
  color: #0369a1;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  padding: 4px 10px;
}

.history-dialog__when {
  color: #64748b;
  font-size: 12px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.history-dialog__by {
  color: #475569;
  font-size: 12px;
  line-height: 1.4;
  margin: -2px 0 0;
}

.history-dialog__by strong {
  color: #0f172a;
  font-weight: 650;
}

.history-dialog__range-row {
  align-items: center;
  display: grid;
  gap: 10px;
  grid-template-columns: 1fr auto 1fr;
}

.history-dialog__chip {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 12px;
}

.history-dialog__chip--to {
  background: linear-gradient(180deg, #eff6ff, #f8fbff);
  border-color: #bfdbfe;
}

.history-dialog__chip span {
  color: #64748b;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.history-dialog__chip strong {
  color: #0f172a;
  font-size: 14px;
  font-weight: 700;
}

.history-dialog__arrow {
  color: #0070c0;
  font-size: 18px;
  font-weight: 700;
  line-height: 1;
}

.history-dialog__quote {
  background: #f8fafc;
  border-left: 3px solid #42b0d5;
  border-radius: 0 10px 10px 0;
  margin: 0;
  padding: 10px 12px;
}

.history-dialog__quote p {
  color: #1e293b;
  font-size: 14px;
  line-height: 1.55;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.history-dialog__footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 2px;
}

@media (max-width: 720px) {
  .history-dialog__hero {
    flex-direction: column;
  }

  .history-dialog__metrics {
    flex-direction: row;
    min-width: 0;
  }

  .history-dialog__metric {
    flex: 1;
  }

  .history-dialog__range-row {
    grid-template-columns: 1fr;
  }

  .history-dialog__arrow {
    justify-self: center;
    transform: rotate(90deg);
  }
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
