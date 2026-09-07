<template>
  <PageShell
    title="Toll Gates"
    subtitle="Migration lifecycle grouped into the five PMI process groups — Initiating through Closing."
    tag="Governance"
    back-to="/"
  >
    <div class="project-picker">
      <label class="project-picker__label" for="tg-project-search">Show progress for project</label>
      <div class="project-picker__combobox" ref="comboboxEl">
        <input
          id="tg-project-search"
          class="project-picker__input"
          type="text"
          autocomplete="off"
          role="combobox"
          :aria-expanded="suggestionsOpen"
          placeholder="Search by ID, project name, requestor…"
          :disabled="loadingProjects"
          v-model="searchTerm"
          @focus="suggestionsOpen = true"
          @input="suggestionsOpen = true"
          @keydown.down.prevent="moveHighlight(1)"
          @keydown.up.prevent="moveHighlight(-1)"
          @keydown.enter.prevent="selectHighlighted()"
          @keydown.esc="suggestionsOpen = false"
        />
        <mc-button
          v-if="selectedProjectId"
          class="project-picker__clear"
          appearance="neutral"
          variant="plain"
          fit="small"
          icon="mi-cross"
          @click="clearSelection"
        />
        <ul v-if="suggestionsOpen && filteredProjects.length" class="project-picker__suggestions">
          <li
            v-for="(p, index) in filteredProjects"
            :key="p.id"
            class="project-picker__suggestion"
            :class="{ 'project-picker__suggestion--active': index === highlightIndex }"
            @mousedown.prevent="selectProject(p)"
            @mouseenter="highlightIndex = index"
          >
            <span class="project-picker__suggestion-id">#{{ p.id }}</span>
            <span class="project-picker__suggestion-name">{{ p.projectName }}</span>
            <span class="project-picker__suggestion-meta">{{ p.requestor }} · {{ formatStatusLabel(p.status) }}</span>
          </li>
        </ul>
        <div
          v-else-if="suggestionsOpen && searchTerm.trim() && !loadingProjects"
          class="project-picker__suggestions project-picker__suggestions--empty"
        >
          No matching projects.
        </div>
      </div>
      <span v-if="loadingProject" class="project-picker__hint">Loading progress…</span>
      <span v-else-if="projectError" class="project-picker__hint project-picker__hint--error">{{ projectError }}</span>
      <span v-else-if="!selectedProjectId" class="project-picker__hint">
        Search and pick a project to see live progress for each step below.
      </span>
    </div>

    <div v-if="selectedProjectId && !loadingProject && !projectError" class="overall-progress">
      <div class="overall-progress__ring" :style="{ '--pct': overallTotals.pct }">
        <span class="overall-progress__value">{{ overallTotals.pct }}%</span>
      </div>
      <div class="overall-progress__text">
        <strong>Overall toll gate completion</strong>
        <span>{{ overallTotals.complete }} of {{ overallTotals.total }} tracked steps complete</span>
      </div>
    </div>

    <section
      v-for="phase in phases"
      :key="phase.id"
      class="phase-section"
      :style="{ '--phase-accent': phase.accent }"
    >
      <div class="phase-head">
        <span class="phase-index">{{ phase.index }}</span>
        <span class="phase-icon">
          <mc-icon :icon="phase.icon" size="22" />
        </span>
        <div class="phase-head__text">
          <h2>{{ phase.title }}</h2>
          <p v-if="phase.description">{{ phase.description }}</p>
        </div>
        <div v-if="selectedProjectId && phaseTotals(phase).total" class="phase-progress">
          <strong>{{ phaseTotals(phase).complete }}/{{ phaseTotals(phase).total }}</strong>
          <span>steps complete</span>
          <div class="phase-progress__track">
            <div
              class="phase-progress__fill"
              :style="{ width: `${phaseTotals(phase).pct}%` }"
            />
          </div>
        </div>
      </div>

      <div class="phase-groups">
        <div v-if="phase.tiles.length" class="phase-group">
          <h3>Dashboard tiles</h3>
          <div class="tg-stepper">
            <div
              v-for="(tile, index) in phase.tiles"
              :key="tile.label"
              class="tg-stepper__item"
              :class="[`tg-stepper__item--${stepState(tile.id)}`, { 'tg-stepper__item--clickable': canNavigate(tile.id, 'tile') }]"
              @click="goToStep(tile.id, 'tile')"
            >
              <div
                v-if="index > 0"
                class="tg-stepper__connector"
                :class="{ 'tg-stepper__connector--complete': isConnectorComplete(phase.tiles, index) }"
              />
              <div class="tg-stepper__node">
                <mc-icon v-if="stepState(tile.id) === 'complete'" icon="mi-check" size="14" />
                <mc-icon v-else-if="stepState(tile.id) === 'at_risk'" icon="mi-exclamation-triangle" size="14" />
                <mc-icon v-else icon="mi-clock" size="14" />
              </div>
              <span class="tg-stepper__label">{{ tile.label }}</span>
            </div>
          </div>
        </div>

        <div v-if="phase.ganttSteps.length" class="phase-group">
          <h3>Gantt steps</h3>
          <div class="tg-stepper tg-stepper--wrap">
            <div
              v-for="(step, index) in phase.ganttSteps"
              :key="step.label"
              class="tg-stepper__item"
              :class="[`tg-stepper__item--${stepState(step.id)}`, { 'tg-stepper__item--clickable': canNavigate(step.id, 'gantt') }]"
              @click="goToStep(step.id, 'gantt')"
            >
              <div
                v-if="index > 0"
                class="tg-stepper__connector"
                :class="{ 'tg-stepper__connector--complete': isConnectorComplete(phase.ganttSteps, index) }"
              />
              <div class="tg-stepper__node">
                <mc-icon v-if="stepState(step.id) === 'complete'" icon="mi-check" size="14" />
                <mc-icon v-else-if="stepState(step.id) === 'at_risk'" icon="mi-exclamation-triangle" size="14" />
                <mc-icon v-else icon="mi-clock" size="14" />
              </div>
              <span class="tg-stepper__label">{{ step.label }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  </PageShell>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'
import { formatStatusLabel } from '../utils/migrationDashboardProgress.js'
import '@maersk-global/mds-components-core/mc-icon'
import '@maersk-global/mds-components-core/mc-tag'
import '@maersk-global/mds-components-core/mc-button'

const route = useRoute()
const router = useRouter()

const projects = ref([])
const loadingProjects = ref(false)
const selectedProjectId = ref(String(route.query.project || ''))
const project = ref(null)
const ganttTasks = ref([])
const ganttSaved = ref(false)
const oaHasRows = ref(false)
const loadingProject = ref(false)
const projectError = ref('')

const comboboxEl = ref(null)
const searchTerm = ref('')
const suggestionsOpen = ref(false)
const highlightIndex = ref(0)

const filteredProjects = computed(() => {
  const term = searchTerm.value.trim().toLowerCase()
  const pool = projects.value
  if (!term) return pool.slice(0, 20)
  return pool
    .filter((p) => {
      const idMatch = String(p.id).includes(term)
      const nameMatch = (p.projectName || '').toLowerCase().includes(term)
      const reqIdMatch = (p.migrationRequestId || '').toLowerCase().includes(term)
      const requestorMatch = (p.requestor || '').toLowerCase().includes(term)
      return idMatch || nameMatch || reqIdMatch || requestorMatch
    })
    .slice(0, 20)
})

const selectProject = (p) => {
  selectedProjectId.value = String(p.id)
  searchTerm.value = `#${p.id} · ${p.projectName}`
  suggestionsOpen.value = false
}

const clearSelection = () => {
  selectedProjectId.value = ''
  searchTerm.value = ''
  suggestionsOpen.value = false
}

const moveHighlight = (delta) => {
  if (!filteredProjects.value.length) return
  suggestionsOpen.value = true
  const max = filteredProjects.value.length - 1
  highlightIndex.value = Math.min(max, Math.max(0, highlightIndex.value + delta))
}

const selectHighlighted = () => {
  const match = filteredProjects.value[highlightIndex.value]
  if (match) selectProject(match)
}

const onDocumentClick = (event) => {
  if (comboboxEl.value && !comboboxEl.value.contains(event.target)) {
    suggestionsOpen.value = false
  }
}

// Tile ids match milestone ids from migrationDashboardProgress.js; Gantt step ids
// match TEMPLATE_TASKS ids in backend/api/views/project_gantt.py.
const phases = [
  {
    id: 'initiating',
    index: 1,
    title: 'Initiating',
    icon: 'mi-file-arrows-square',
    accent: '#0077B8',
    description: 'Intake, sign-off on the opportunity, and every approval needed before planning begins.',
    tiles: [
      { id: 'intake', label: 'Project Charter' },
      { id: 'business_case', label: 'Business Case' },
      { id: 'opportunity', label: 'Opportunity assessment' },
      { id: 'approvals', label: 'Approvals' }
    ],
    ganttSteps: [
      { id: 'business-case', label: 'Business case' },
      { id: 'fbp-approval', label: 'FBP approval' },
      { id: 'functional-head', label: 'Functional head approval' },
      { id: 'elt-approval', label: 'ELT approval' },
      { id: 'gsc-head', label: 'GSC head-1 approval' },
      { id: 'pid-approval', label: 'PID approval' },
      { id: 'hiring-request', label: 'Hiring request approval' }
    ]
  },
  {
    id: 'planning',
    index: 2,
    title: 'Planning',
    icon: 'mi-chart-bars-vertical',
    accent: '#42B0D5',
    description: 'Build the migration schedule, capture risks, and line up training ahead of execution.',
    tiles: [
      { id: 'gantt', label: 'Gantt' },
      { id: null, label: 'Risk Register' },
      { id: 'training', label: 'Training' }
    ],
    ganttSteps: []
  },
  {
    id: 'executing',
    index: 3,
    title: 'Executing',
    icon: 'mi-monitor',
    accent: '#F3880E',
    description: 'Deliver the L&D training stage, knowledge transfer, and ramp-up of transferred volume.',
    tiles: [],
    ganttSteps: [
      { id: 'neo-training', label: 'NEO + GSC L&D business & training stage' },
      { id: 'knowledge-transfer', label: 'Knowledge Transfer + System Training + Assessments' },
      { id: 'volume-transfer', label: 'Volume Transfer/Ramp-up stage' }
    ]
  },
  {
    id: 'monitor-control',
    index: 4,
    title: 'Monitor & Control',
    icon: 'mi-exclamation-triangle',
    accent: '#6DAA28',
    description: 'Track stability through Hypercare and confirm exit success criteria are met.',
    tiles: [],
    ganttSteps: [
      { id: 'hypercare', label: 'Hypercare stage' },
      { id: 'hypercare-exit', label: 'Hypercare Exit Success Criteria Review' }
    ]
  },
  {
    id: 'closing',
    index: 5,
    title: 'Closing',
    icon: 'mi-flag',
    accent: '#E85454',
    description: 'Recommend sign-off and release the capacity that migration frees up.',
    tiles: [{ id: 'golive', label: 'Go-live' }],
    ganttSteps: [
      { id: 'sign-off', label: 'Migration Sign-off recommendation' },
      { id: 'capacity-release', label: 'Recommended soonest Capacity Release' }
    ]
  }
]

// Where each trackable step id navigates to once a project is selected.
const TILE_ROUTES = {
  intake: (id) => `/migration-dashboard/${id}`,
  business_case: (id) => `/migration-dashboard/${id}/business-case`,
  opportunity: (id) => `/migration-dashboard/${id}/opportunity-assessment`,
  approvals: () => '/approval-cycle',
  gantt: (id) => `/migration-dashboard/${id}/gantt`,
  training: () => '/ld-dashboard'
}

const milestoneStateById = computed(() => {
  if (!project.value) return {}
  const p = project.value
  // Real completion signals already tracked elsewhere in the app, rather than
  // the coarse project.status index (which barely changes after intake).
  return {
    intake: 'complete',
    business_case: p.businessCaseSubmissionDate ? 'complete' : 'pending',
    opportunity: oaHasRows.value ? 'complete' : 'pending',
    approvals: ganttStateById.value['hiring-request'] === 'complete' ? 'complete' : 'pending',
    gantt: ganttSaved.value ? 'complete' : 'pending',
    training: ganttStateById.value['neo-training'] === 'complete' ? 'complete' : 'pending',
    golive: p.status === 'completed' ? 'complete' : 'pending'
  }
})

const ganttStateById = computed(() => {
  const map = {}
  for (const task of ganttTasks.value) {
    let state = 'pending'
    if (task.completedAt) state = 'complete'
    else if (task.actualStatus === 'late') state = 'at_risk'
    else if (task.plan) state = 'active'
    map[task.id] = state
  }
  return map
})

const stepState = (stepId) => {
  if (!stepId || !selectedProjectId.value) return 'pending'
  return milestoneStateById.value[stepId] ?? ganttStateById.value[stepId] ?? 'pending'
}

const isConnectorComplete = (steps, index) => {
  const prev = steps[index - 1]
  if (!prev) return false
  const state = stepState(prev.id)
  return state === 'complete' || state === 'active'
}

const canNavigate = (stepId, kind) => {
  if (!selectedProjectId.value || !stepId) return false
  if (kind === 'tile') return typeof TILE_ROUTES[stepId] === 'function'
  return true
}

const goToStep = (stepId, kind) => {
  if (!canNavigate(stepId, kind)) return
  const id = selectedProjectId.value
  const to = kind === 'tile' ? TILE_ROUTES[stepId](id) : `/migration-dashboard/${id}/gantt`
  router.push(to)
}

const phaseTotals = (phase) => {
  const trackable = [...phase.tiles, ...phase.ganttSteps].filter((s) => s.id)
  const total = trackable.length
  const complete = trackable.filter((s) => stepState(s.id) === 'complete').length
  const pct = total ? Math.round((complete / total) * 100) : 0
  return { total, complete, pct }
}

const overallTotals = computed(() => {
  const trackable = phases.flatMap((ph) => [...ph.tiles, ...ph.ganttSteps]).filter((s) => s.id)
  const total = trackable.length
  const complete = trackable.filter((s) => stepState(s.id) === 'complete').length
  const pct = total ? Math.round((complete / total) * 100) : 0
  return { total, complete, pct }
})

const loadProjects = async () => {
  loadingProjects.value = true
  try {
    const { data } = await axios.get('/api/migration-dashboard/projects/')
    projects.value = data.rows || []
  } catch {
    projects.value = []
  } finally {
    loadingProjects.value = false
  }
}

const loadProjectData = async (id) => {
  project.value = null
  ganttTasks.value = []
  ganttSaved.value = false
  oaHasRows.value = false
  projectError.value = ''
  if (!id) return
  loadingProject.value = true
  try {
    const [detailRes, ganttRes] = await Promise.all([
      axios.get(`/api/migration-dashboard/projects/${id}/`),
      axios.get(`/api/migration-dashboard/projects/${id}/gantt/`)
    ])
    project.value = detailRes.data
    ganttTasks.value = ganttRes.data.tasks || []
    ganttSaved.value = !!ganttRes.data.saved
  } catch (error) {
    projectError.value = error?.response?.data?.error ?? 'Unable to load progress for this project.'
  } finally {
    loadingProject.value = false
  }

  // Best-effort: Opportunity Assessment is requestor-only, so a 403 here just
  // means "can't verify" — leave it pending rather than failing the page.
  try {
    const { data } = await axios.get(`/api/migration-dashboard/projects/${id}/opportunity-assessment/`)
    oaHasRows.value = !!data.has_existing_rows
  } catch {
    oaHasRows.value = false
  }
}

watch(selectedProjectId, (id) => {
  router.replace({ query: { ...route.query, project: id || undefined } })
  loadProjectData(id)
})

watch(searchTerm, () => {
  highlightIndex.value = 0
})

onMounted(async () => {
  document.addEventListener('mousedown', onDocumentClick)
  await loadProjects()
  if (selectedProjectId.value) {
    loadProjectData(selectedProjectId.value)
    const match = projects.value.find((p) => String(p.id) === selectedProjectId.value)
    if (match) searchTerm.value = `#${match.id} · ${match.projectName}`
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('mousedown', onDocumentClick)
})
</script>

<style scoped>
.project-picker {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 20px;
}

.project-picker__label {
  font-size: 13px;
  font-weight: 600;
  color: #56626c;
}

.project-picker__select {
  border: 1px solid #d7dde3;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 14px;
  min-width: 280px;
  color: #161616;
}

.project-picker__combobox {
  position: relative;
  min-width: 320px;
  display: flex;
  align-items: center;
}

.project-picker__input {
  width: 100%;
  border: 1px solid #d7dde3;
  border-radius: 8px;
  padding: 8px 36px 8px 12px;
  font-size: 14px;
  color: #161616;
}

.project-picker__input:focus {
  outline: none;
  border-color: #0077b8;
  box-shadow: 0 0 0 3px rgba(0, 119, 184, 0.12);
}

.project-picker__clear {
  position: absolute;
  right: 2px;
}

.project-picker__suggestions {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  z-index: 20;
  background: #fff;
  border: 1px solid #d7dde3;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(22, 22, 22, 0.12);
  max-height: 280px;
  overflow-y: auto;
  padding: 4px;
  margin: 0;
  list-style: none;
}

.project-picker__suggestions--empty {
  padding: 10px 12px;
  font-size: 13px;
  color: #9aa5ae;
  font-style: italic;
}

.project-picker__suggestion {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
}

.project-picker__suggestion--active,
.project-picker__suggestion:hover {
  background: #eef6fb;
}

.project-picker__suggestion-id {
  font-weight: 700;
  font-size: 12px;
  color: #0077b8;
  flex-shrink: 0;
}

.project-picker__suggestion-name {
  font-size: 13px;
  color: #161616;
  flex: 1 1 auto;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-picker__suggestion-meta {
  font-size: 11px;
  color: #9aa5ae;
  flex-shrink: 0;
}

.project-picker__hint {
  font-size: 13px;
  color: #7a8894;
}

.project-picker__hint--error {
  color: #e85454;
}

.overall-progress {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  border: 1px solid #e4e9ef;
  border-radius: 12px;
  margin-bottom: 20px;
  background: linear-gradient(135deg, rgba(0, 119, 184, 0.05) 0%, rgba(66, 176, 213, 0.04) 100%);
}

.overall-progress__ring {
  --pct: 0;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  flex-shrink: 0;
  background: conic-gradient(#0077b8 calc(var(--pct) * 1%), #e4e9ef 0);
  display: flex;
  align-items: center;
  justify-content: center;
}

.overall-progress__ring::before {
  content: '';
  position: absolute;
}

.overall-progress__value {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  color: #161616;
}

.overall-progress__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 13px;
  color: #56626c;
}

.overall-progress__text strong {
  font-size: 15px;
  color: #161616;
}

.phase-section {
  border: 1px solid #e4e9ef;
  border-left: 4px solid var(--phase-accent, #0077b8);
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 20px;
  background: #fff;
}

.phase-head {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 16px;
}

.phase-index {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--phase-accent, #0077b8);
  color: #fff;
  font-weight: 700;
  font-size: 13px;
  flex-shrink: 0;
}

.phase-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--phase-accent, #0077b8);
  flex-shrink: 0;
}

.phase-head__text {
  flex: 1 1 auto;
}

.phase-head__text h2 {
  margin: 0 0 4px;
  font-size: 18px;
}

.phase-head__text p {
  margin: 0;
  color: #56626c;
  font-size: 14px;
}

.phase-progress {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  min-width: 140px;
  font-size: 12px;
  color: #56626c;
}

.phase-progress strong {
  font-size: 15px;
  color: #161616;
}

.phase-progress__track {
  width: 120px;
  height: 5px;
  border-radius: 999px;
  background: #e4e9ef;
  overflow: hidden;
}

.phase-progress__fill {
  height: 100%;
  background: var(--phase-accent, #0077b8);
  border-radius: 999px;
  transition: width 0.3s ease;
}

.phase-groups {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}

.phase-group h3 {
  margin: 0 0 14px;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #7a8894;
}

.tg-stepper {
  display: flex;
  gap: 0;
  overflow-x: auto;
  padding-bottom: 4px;
}

.tg-stepper--wrap {
  flex-wrap: wrap;
  row-gap: 20px;
}

.tg-stepper__item {
  align-items: center;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 96px;
  max-width: 130px;
  position: relative;
  padding: 0 4px;
}

.tg-stepper__item--clickable {
  cursor: pointer;
}

.tg-stepper__connector {
  background: #d7dde3;
  height: 2px;
  left: calc(-50% + 16px);
  position: absolute;
  top: 15px;
  width: calc(100% - 32px);
  z-index: 0;
}

.tg-stepper__connector--complete {
  background: #6daa28;
}

.tg-stepper__node {
  align-items: center;
  background: #fff;
  border: 2px solid #d7dde3;
  border-radius: 999px;
  color: #6c757d;
  display: flex;
  height: 32px;
  justify-content: center;
  position: relative;
  width: 32px;
  z-index: 1;
  flex-shrink: 0;
}

.tg-stepper__item--complete .tg-stepper__node {
  background: #eef8e8;
  border-color: #6daa28;
  color: #6daa28;
}

.tg-stepper__item--active .tg-stepper__node {
  background: #0077b8;
  border-color: #0077b8;
  color: #fff;
  box-shadow: 0 0 0 4px rgba(0, 119, 184, 0.15);
}

.tg-stepper__item--at_risk .tg-stepper__node {
  background: #fff5f5;
  border-color: #e85454;
  color: #e85454;
}

.tg-stepper__label {
  color: #6c757d;
  font-size: 11px;
  font-weight: 500;
  line-height: 1.3;
  text-align: center;
}

.tg-stepper__item--complete .tg-stepper__label {
  color: #5a9420;
}

.tg-stepper__item--active .tg-stepper__label {
  color: #0077b8;
  font-weight: 600;
}

.tg-stepper__item--at_risk .tg-stepper__label {
  color: #e85454;
  font-weight: 600;
}
</style>
