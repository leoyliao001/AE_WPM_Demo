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
                  ? 'View mode — turn on Edit to change summary or Gantt bars.'
                  : isDirty
                    ? 'Unsaved changes — edit summary or bars, then Save.'
                    : savedAt
                      ? `Saved plan · last update ${savedAtLabel}`
                      : 'Using fixed Migration Key Steps — edit week bars, then Save for this project.'
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
          :phases="phases"
          :meta="meta"
          :field-labels="fieldLabels"
          :today-week="todayWeek"
          @update-task="onUpdateTask"
          @update-meta="onUpdateMeta"
          @add-phase="onAddPhase"
          @remove-phase="onRemovePhase"
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
import { projectGanttFixture, buildProjectGanttWeeks, mergeGanttPhases } from '../data/projectGanttFixture.js'
import '@maersk-global/mds-components-core/mc-notification'
import '@maersk-global/mds-components-core/mc-tag'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-dialog'
import '@maersk-global/mds-components-core/mc-icon'
const cloneTasks = (rows) =>
  rows.map((task) => ({
    id: task.id,
    name: task.name,
    startWeek: task.startWeek,
    endWeek: task.endWeek,
    phaseId: task.phaseId || 'opportunity'
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
const customPhases = ref([])
const phases = computed(() => mergeGanttPhases(customPhases.value))
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
      : `${project.value.migrationRequestId} — edit fixed Migration Key Steps week bars for this project.`
  }
  return 'Edit fixed Migration Key Steps week bars for this project.'
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
  if (Array.isArray(data?.customPhases)) {
    customPhases.value = data.customPhases.map((phase) => ({
      id: String(phase.id),
      label: String(phase.label),
      color: String(phase.color || '#64748B'),
      custom: true
    }))
  } else if (Array.isArray(data?.phases)) {
    customPhases.value = data.phases
      .filter((phase) => phase?.custom)
      .map((phase) => ({
        id: String(phase.id),
        label: String(phase.label),
        color: String(phase.color || '#64748B'),
        custom: true
      }))
  }
  savedAt.value = data?.updated_at || null
}

const mergeSavedMeta = (savedMeta) => {
  const base = cloneMeta(projectGanttFixture.meta)
  if (!savedMeta || typeof savedMeta !== 'object') return base
  return cloneMeta({ ...base, ...savedMeta })
}

const onUpdateTask = ({ id, startWeek, endWeek, phaseId }) => {
  const index = tasks.value.findIndex((task) => task.id === id)
  if (index < 0) return
  const current = tasks.value[index]
  const nextPhaseId = phaseId || current.phaseId || 'opportunity'
  if (
    current.startWeek === startWeek &&
    current.endWeek === endWeek &&
    current.phaseId === nextPhaseId
  ) {
    return
  }
  const next = [...tasks.value]
  next[index] = {
    ...current,
    startWeek,
    endWeek,
    phaseId: nextPhaseId
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

const onAddPhase = ({ id, label, color }) => {
  const phaseId = String(id || '').trim()
  const phaseLabel = String(label || '').trim()
  if (!phaseId || !phaseLabel) return
  if (customPhases.value.some((phase) => phase.id === phaseId)) return
  customPhases.value = [
    ...customPhases.value,
    {
      id: phaseId,
      label: phaseLabel,
      color: String(color || '#64748B'),
      custom: true
    }
  ]
  isDirty.value = true
}

const onRemovePhase = ({ id }) => {
  const phaseId = String(id || '').trim()
  if (!phaseId) return
  if (!customPhases.value.some((phase) => phase.id === phaseId)) return
  customPhases.value = customPhases.value.filter((phase) => phase.id !== phaseId)
  // Reassign bars that used the removed status.
  let tasksChanged = false
  const nextTasks = tasks.value.map((task) => {
    if (task.phaseId !== phaseId) return task
    tasksChanged = true
    return { ...task, phaseId: 'opportunity' }
  })
  if (tasksChanged) tasks.value = nextTasks
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
  customPhases.value = []
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
        meta: meta.value,
        customPhases: customPhases.value.map((phase) => ({
          id: phase.id,
          label: phase.label,
          color: phase.color
        }))
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
