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
      <mc-notification
        v-if="saveMessage"
        :appearance="saveAppearance"
        fit="medium"
        :heading="saveHeading"
        :body="saveMessage"
      />

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
                      : tasks.length
                        ? 'Tasks from Opportunity Assessment — edit week bars, then Save for this project.'
                        : 'No Opportunity Assessment tasks yet — submit OA tasks to generate Migration Key Steps.'
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
              label="Reset from OA"
              :disabled="saving || loading || !editMode || !oaTasks.length"
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
        />

        <aside v-for="note in notes" :key="note.title" class="gantt-notes">
          <h3>{{ note.title }}</h3>
          <ul>
            <li v-for="item in note.items" :key="item">{{ item }}</li>
          </ul>
        </aside>
      </section>
    </template>
  </PageShell>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'
import ProjectGanttChart from '../components/ProjectGanttChart.vue'
import { projectGanttFixture } from '../data/projectGanttFixture.js'
import '@maersk-global/mds-components-core/mc-notification'
import '@maersk-global/mds-components-core/mc-tag'
import '@maersk-global/mds-components-core/mc-button'

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
const saveMessage = ref('')
const saveAppearance = ref('success')
const saveHeading = ref('Saved')
const savedAt = ref(null)
const isDirty = ref(false)
const editMode = ref(false)

const fieldLabels = projectGanttFixture.fieldLabels
const weeks = projectGanttFixture.weeks
const phases = projectGanttFixture.phases
const notes = projectGanttFixture.notes
const todayWeek = projectGanttFixture.todayWeek
const tasks = ref([])
const oaTasks = ref([])
const meta = ref(cloneMeta(projectGanttFixture.meta))

const backTo = computed(() => `/migration-dashboard/${route.params.id}`)

const pageTitle = computed(() =>
  project.value?.projectName ? `Gantt — ${project.value.projectName}` : 'Project Gantt'
)

const pageSubtitle = computed(() => {
  if (project.value) {
    return `${project.value.migrationRequestId} — Migration Key Steps follow Opportunity Assessment tasks.`
  }
  return 'Migration Key Steps follow Opportunity Assessment tasks.'
})

const savedAtLabel = computed(() => {
  if (!savedAt.value) return ''
  try {
    return new Date(savedAt.value).toLocaleString()
  } catch {
    return savedAt.value
  }
})

const applyGanttPayload = (data) => {
  const nextTasks = Array.isArray(data?.tasks) ? data.tasks : []
  const nextOa = Array.isArray(data?.oa_tasks) ? data.oa_tasks : nextTasks
  tasks.value = cloneTasks(nextTasks)
  oaTasks.value = cloneTasks(nextOa)
  if (data?.meta && typeof data.meta === 'object') {
    meta.value = mergeSavedMeta(data.meta)
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
  saveMessage.value = ''
}

const onUpdateMeta = ({ key, value }) => {
  if (!(key in meta.value)) return
  if (meta.value[key] === value) return
  meta.value = { ...meta.value, [key]: value }
  isDirty.value = true
  saveMessage.value = ''
}

const resetToTemplate = () => {
  tasks.value = cloneTasks(oaTasks.value)
  meta.value = cloneMeta(projectGanttFixture.meta)
  isDirty.value = true
  saveMessage.value = ''
}

const loadAll = async () => {
  loading.value = true
  loadError.value = ''
  saveMessage.value = ''
  project.value = null
  isDirty.value = false
  tasks.value = []
  oaTasks.value = []
  meta.value = cloneMeta(projectGanttFixture.meta)
  savedAt.value = null

  try {
    const [projectRes, ganttRes] = await Promise.all([
      axios.get(`/api/migration-dashboard/projects/${route.params.id}/`),
      axios.get(`/api/migration-dashboard/projects/${route.params.id}/gantt/`)
    ])
    project.value = projectRes.data
    applyGanttPayload(ganttRes.data || {})
  } catch (error) {
    loadError.value =
      error?.response?.data?.error ?? 'Unable to load this project Gantt. Please try again.'
  } finally {
    loading.value = false
  }
}

const saveGantt = async () => {
  saving.value = true
  saveMessage.value = ''
  try {
    const { data } = await axios.put(
      `/api/migration-dashboard/projects/${route.params.id}/gantt/`,
      { tasks: tasks.value, meta: meta.value }
    )
    applyGanttPayload(data || {})
    isDirty.value = false
    saveAppearance.value = 'success'
    saveHeading.value = 'Saved'
    saveMessage.value = 'Gantt plan and project parameters saved for this project.'
  } catch (error) {
    saveAppearance.value = 'error'
    saveHeading.value = 'Save failed'
    saveMessage.value =
      error?.response?.data?.error ?? 'Unable to save Gantt. Please try again.'
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
</style>
