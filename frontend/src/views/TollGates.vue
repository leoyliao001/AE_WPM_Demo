<template>
  <PageShell
    class="toll-gates-page-shell"
    title="Toll Gates"
    subtitle="Migration lifecycle grouped into the five PMI process groups — Initiating through Closing."
    back-to="/"
    full-width
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
          icon="mi-times-circle"
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
        Pick a project to see live progress.
      </span>
    </div>

    <section class="artefact-board" aria-label="Artefact Delivery Dashboard">
      <header class="artefact-board__head">
        <div>
          <p class="artefact-board__eyebrow">Project lifecycle</p>
          <h2 class="artefact-board__title">Artefact Delivery Dashboard</h2>
          <p class="artefact-board__sub">
            Five process groups · {{ artefactTotals.total }} key artefacts · live completion and RAG status
          </p>
        </div>

        <div class="artefact-board__meta">
          <div class="artefact-legend">
            <span class="artefact-legend__title">Status</span>
            <span
              v-for="legend in ARTEFACT_LEGEND"
              :key="legend.status"
              class="artefact-legend__item"
            >
              <span class="artefact-dot" :class="`artefact-dot--${legend.status}`" />
              {{ legend.label }}
            </span>
          </div>

          <div class="artefact-kpis">
            <div class="artefact-kpi artefact-kpi--info">
              <span class="artefact-kpi__icon artefact-kpi__icon--blue"><mc-icon icon="mi-chart-pie" size="22" /></span>
              <span class="artefact-kpi__copy">
              <span class="artefact-kpi__label">Overall completion</span>
              <strong class="artefact-kpi__value">{{ artefactTotals.pct }}%</strong>
              </span>
            </div>
            <div class="artefact-kpi artefact-kpi--info">
              <span class="artefact-kpi__icon artefact-kpi__icon--green"><mc-icon icon="mi-shield" size="22" /></span>
              <span class="artefact-kpi__copy">
              <span class="artefact-kpi__label">Artefacts secured</span>
              <strong class="artefact-kpi__value">{{ artefactTotals.secured }} / {{ artefactTotals.total }}</strong>
              </span>
            </div>
            <div class="artefact-kpi artefact-kpi--risk">
              <span class="artefact-kpi__icon artefact-kpi__icon--red"><mc-icon icon="mi-flag" size="22" /></span>
              <span class="artefact-kpi__copy">
              <span class="artefact-kpi__label">At risk</span>
              <strong class="artefact-kpi__value">{{ artefactTotals.atRiskStages }} stage{{ artefactTotals.atRiskStages === 1 ? '' : 's' }}</strong>
              </span>
            </div>
          </div>
        </div>
      </header>

      <div class="artefact-grid">
        <article
          v-for="stage in artefactStages"
          :key="stage.id"
          class="artefact-card"
          :class="`artefact-card--${stage.rag}`"
          :style="{ '--stage-color': stage.color }"
        >
          <header class="artefact-card__head">
            <span class="artefact-card__index">{{ stage.index }}</span>
            <span class="artefact-card__icon"><mc-icon :icon="stage.icon" size="22" /></span>
            <div>
              <h3 class="artefact-card__title">{{ stage.title }}</h3>
              <p class="artefact-card__caption">{{ stage.caption }}</p>
            </div>
            <span class="artefact-card__menu">...</span>
          </header>

          <div class="artefact-card__body">
            <div class="artefact-card__summary">
              <div class="artefact-card__ring" :style="{ '--pct': stage.pct, '--stage-color': stage.color }">
                <span class="artefact-card__ring-value">{{ stage.pct }}%</span>
              </div>
              <div class="artefact-card__rag">
                <strong class="artefact-card__pct">{{ stage.pct }}%</strong>
                <span class="artefact-rag">
                  <span class="artefact-dot" :class="`artefact-dot--rag-${stage.rag}`" />
                  {{ stage.rag.toUpperCase() }}
                </span>
              </div>
              <div class="artefact-card__count">
                <span>Artefacts</span>
                <strong>{{ stage.secured }} / {{ stage.items.length }}</strong>
              </div>
            </div>

            <ul :id="`artefact-list-${stage.id}`" class="artefact-list">
              <li
                v-for="item in stage.items.slice(0, isArtefactStageExpanded(stage.id) ? stage.items.length : 4)"
                :key="item.label"
                class="artefact-item"
                :class="`artefact-item--${item.status}`"
              >
                <button
                  v-if="item.source && TILE_ROUTES[item.source]"
                  type="button"
                  class="artefact-item__link"
                  :disabled="!canNavigate(item.source, 'tile')"
                  @click="goToStep(item.source, 'tile')"
                >
                  <span class="artefact-item__icon">
                    <mc-icon icon="mi-file" size="14" />
                  </span>
                  <span class="artefact-item__text">
                    <span class="artefact-item__label">{{ item.label }}</span>
                    <span class="artefact-item__status">{{ ARTEFACT_STATUS_LABEL[item.status] }}</span>
                  </span>
                  <span class="artefact-item__link-arrow" aria-hidden="true">›</span>
                </button>
                <template v-else>
                  <span class="artefact-item__icon">
                    <mc-icon icon="mi-file" size="14" />
                  </span>
                  <span class="artefact-item__text">
                    <span class="artefact-item__label">{{ item.label }}</span>
                    <span class="artefact-item__status">{{ ARTEFACT_STATUS_LABEL[item.status] }}</span>
                  </span>
                </template>
              </li>
            </ul>
            <button
              v-if="stage.items.length > 4"
              :aria-controls="`artefact-list-${stage.id}`"
              :aria-expanded="isArtefactStageExpanded(stage.id)"
              class="artefact-list__toggle"
              type="button"
              @click="toggleArtefactStage(stage.id)"
            >
              {{ isArtefactStageExpanded(stage.id) ? 'Show fewer' : `Show all ${stage.items.length} items` }}
            </button>
          </div>

          <footer class="artefact-card__foot">
            <span class="artefact-gate" :class="`artefact-gate--${stage.rag}`">{{ stage.gateLabel }}</span>
          </footer>
        </article>
      </div>

      <p class="artefact-board__note">
        <mc-icon icon="mi-information" size="14" />
        Completion is auto-calculated from artefact status (Secured only).
      </p>
    </section>

    <section class="quick-tools" aria-labelledby="quick-tools-title">
      <header class="quick-tools__head">
        <div>
          <h2 id="quick-tools-title" class="quick-tools__title">Project Artefacts</h2>
          <p class="quick-tools__sub">
            Access the tools used to prepare, plan and govern this migration.
          </p>
        </div>
      </header>

      <div class="quick-cards" aria-label="Project artefact shortcuts">
      <div
        v-for="(card, cardIndex) in quickCards"
        :key="card.id"
        class="quick-card"
        :class="[`quick-card--${stepState(card.id)}`, { 'quick-card--disabled': !canNavigate(card.id, 'tile') }]"
        :style="{ '--card-accent': card.accent }"
        :tabindex="canNavigate(card.id, 'tile') ? 0 : -1"
        role="button"
        :aria-disabled="!canNavigate(card.id, 'tile')"
        @click="goToStep(card.id, 'tile')"
        @keydown.enter.prevent="goToStep(card.id, 'tile')"
        @keydown.space.prevent="goToStep(card.id, 'tile')"
      >
        <div class="quick-card__main">
          <span class="quick-card__icon">
            <mc-icon :icon="card.icon" size="22" />
          </span>
          <span class="quick-card__index">{{ String(cardIndex + 1).padStart(2, '0') }}</span>
          <div class="quick-card__body">
            <h3 class="quick-card__title">{{ card.title }}</h3>
            <p class="quick-card__desc">{{ card.description }}</p>
          </div>
        </div>
        <div class="quick-card__foot">
          <span class="quick-card__status">
            <mc-icon v-if="stepState(card.id) === 'complete'" icon="mi-check" size="14" />
            <mc-icon v-else-if="stepState(card.id) === 'at_risk'" icon="mi-exclamation-triangle" size="14" />
            <mc-icon v-else icon="mi-clock" size="14" />
            {{ QUICK_STATUS_LABEL[stepState(card.id)] }}
          </span>
          <span class="quick-card__link">Open ›</span>
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

// Where each trackable step id navigates to once a project is selected.
const TILE_ROUTES = {
  intake: (id) => `/migration-dashboard/${id}`,
  business_case: (id) => `/migration-dashboard/${id}/business-case`,
  opportunity: (id) => `/migration-dashboard/${id}/opportunity-assessment`,
  approvals: () => '/approval-cycle',
  gantt: (id) => `/migration-dashboard/${id}/gantt`,
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
    map[task.id] = state
  }
  return map
})

const stepState = (stepId) => {
  if (!stepId || !selectedProjectId.value) return 'pending'
  return milestoneStateById.value[stepId] ?? ganttStateById.value[stepId] ?? 'pending'
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
  // `from` lets the destination page send the user back here instead of its default parent.
  router.push({ path: to, query: { from: 'toll-gates', project: id } })
}

const ARTEFACT_LEGEND = [
  { status: 'secured', label: 'Secured' },
  { status: 'in_progress', label: 'In progress' },
  { status: 'not_started', label: 'Not started' }
]

const ARTEFACT_STATUS_LABEL = {
  secured: 'Secured',
  in_progress: 'In progress',
  not_started: 'Not started'
}

const expandedArtefactStages = ref(new Set())

const isArtefactStageExpanded = (stageId) => expandedArtefactStages.value.has(stageId)

const toggleArtefactStage = (stageId) => {
  const expanded = new Set(expandedArtefactStages.value)
  if (expanded.has(stageId)) expanded.delete(stageId)
  else expanded.add(stageId)
  expandedArtefactStages.value = expanded
}

// `source` links an artefact to an existing tracked step id; artefacts without a
// source have no system of record yet and stay "Not started".
const ARTEFACT_STAGES = [
  {
    id: 'initiating',
    index: '01',
    title: 'Initiate',
    caption: 'Authorise & define',
    icon: 'mi-play-circle',
    color: '#2d8cff',
    items: [
      { label: 'Opportunity Assessment/Task details', source: 'opportunity' },
      { label: 'Scope Statement', source: null },
      { label: 'Stakeholder Registration', source: 'approvals' },
      { label: 'Business Case', source: 'business_case' },
      { label: 'Project Charter', source: 'intake' },
      { label: 'Tollgate Automation', source: null },
      { label: 'People Consultation & Compliance', source: null },
      { label: 'Resources', source: null },
      { label: 'Access & Enablement Requirements', source: null },
      { label: 'Business Impact Analysis', source: null },
      { label: 'Gantt', source: 'gantt' }
    ]
  },
  {
    id: 'planning',
    index: '02',
    title: 'Plan',
    caption: 'Build the roadmap',
    icon: 'mi-map',
    color: '#22b8b0',
    items: [
      { label: 'Integrated project plan', source: 'gantt' },
      { label: 'WBS & milestone schedule', source: 'gantt' },
      { label: 'RAID log & risk plan', source: null },
      { label: 'RACI & governance calendar', source: null }
    ]
  },
  {
    id: 'executing',
    index: '03',
    title: 'Execute',
    caption: 'Do the work',
    icon: 'mi-play-circle',
    color: '#9566ef',
    items: [
      { label: 'Deliverables / outputs', source: 'volume-transfer' },
      { label: 'Status updates & MoMs', source: 'knowledge-transfer' },
      { label: 'Updated RAID & action log', source: 'neo-training' },
      { label: 'Change requests', source: null }
    ]
  },
  {
    id: 'monitor-control',
    index: '04',
    title: 'Monitor & Control',
    caption: 'Track & correct',
    icon: 'mi-chart-bars-vertical',
    color: '#6dac39',
    items: [
      { label: 'Governance / status pack', source: 'hypercare' },
      { label: 'Dashboards & bowler charts', source: 'hypercare-exit' },
      { label: 'Change & decision logs', source: null },
      { label: 'Forecast & variance view', source: null }
    ]
  },
  {
    id: 'closing',
    index: '05',
    title: 'Close & Realise Value',
    caption: 'Finalise & learn',
    icon: 'mi-check-circle',
    color: '#2d8cff',
    items: [
      { label: 'Closure report & sign-off', source: 'sign-off' },
      { label: 'Benefits realisation plan', source: 'capacity-release' },
      { label: 'Lessons-learned log', source: null },
      { label: 'Handover pack', source: 'golive' }
    ]
  }
]

const artefactStatus = (source) => {
  if (!source || !selectedProjectId.value) return 'not_started'
  const state = stepState(source)
  if (state === 'complete') return 'secured'
  if (state === 'active' || state === 'at_risk') return 'in_progress'
  return 'not_started'
}

const ragFromPct = (pct) => (pct >= 80 ? 'green' : pct >= 40 ? 'amber' : 'red')
const gateLabelFromRag = (rag) =>
  rag === 'green' ? 'Gate passed' : rag === 'amber' ? 'Gate at risk' : 'Gate not met'

const artefactStages = computed(() =>
  ARTEFACT_STAGES.map((stage) => {
    const items = stage.items.map((item) => ({ ...item, status: artefactStatus(item.source) }))
    const secured = items.filter((item) => item.status === 'secured').length
    const pct = items.length ? Math.round((secured / items.length) * 100) : 0
    const rag = ragFromPct(pct)
    return { ...stage, items, secured, pct, rag, gateLabel: gateLabelFromRag(rag) }
  })
)

const artefactTotals = computed(() => {
  const stages = artefactStages.value
  const total = stages.reduce((sum, stage) => sum + stage.items.length, 0)
  const secured = stages.reduce((sum, stage) => sum + stage.secured, 0)
  return {
    total,
    secured,
    pct: total ? Math.round((secured / total) * 100) : 0,
    atRiskStages: stages.filter((stage) => stage.rag !== 'green').length
  }
})

const QUICK_STATUS_LABEL = {
  complete: 'Complete',
  active: 'In progress',
  at_risk: 'At risk',
  pending: 'Not started'
}

// Ids reuse TILE_ROUTES so cards open the existing destination for each artefact.
const quickCards = [
  {
    id: 'opportunity',
    title: 'Opportunity Assessment',
    description: 'Volume, task time and capacity analysis for the migration scope.',
    icon: 'mi-chart-bars-vertical',
    accent: '#0077B8'
  },
  {
    id: 'business_case',
    title: 'Business Case',
    description: 'Generate the draft memo, review it, then upload the signed-off version.',
    icon: 'mi-file',
    accent: '#42B0D5'
  },
  {
    id: 'gantt',
    title: 'Gantt Chart',
    description: 'Plan and track every migration task against the baseline schedule.',
    icon: 'mi-calendar',
    accent: '#F3880E'
  },
  {
    id: 'approvals',
    title: 'Approvals',
    description: 'Area Head, PMO, BPM, FBP, WPM, ELT and GSC Head decision cycle.',
    icon: 'mi-check-circle',
    accent: '#6DAA28'
  }
]

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

.artefact-board {
  background: #f1f5f8;
  border: 1px solid #e4ebf0;
  border-radius: 14px;
  margin-bottom: 28px;
  padding: 18px 20px 16px;
}

.artefact-board__head {
  align-items: flex-start;
  display: flex;
  flex-wrap: wrap;
  gap: 26px;
  justify-content: space-between;
  margin-bottom: 18px;
}

.artefact-board__eyebrow {
  color: #42b0d5;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  margin: 0;
  text-transform: uppercase;
}

.artefact-board__title {
  color: #10314f;
  font-family: 'Maersk Headline', 'Maersk Text', sans-serif;
  font-size: clamp(30px, 3vw, 44px);
  font-weight: 800;
  letter-spacing: -0.06em;
  line-height: 1.04;
  margin: 8px 0 0;
}

.artefact-board__sub {
  color: #7a8894;
  font-size: 13px;
  margin: 8px 0 0;
}

.artefact-board__meta {
  display: flex;
  flex-direction: column;
  gap: 12px;
  justify-content: center;
}

.artefact-legend {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  justify-content: flex-end;
}

.artefact-legend__title {
  color: #7a8894;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.artefact-legend__item {
  align-items: center;
  color: #10314f;
  display: inline-flex;
  font-size: 12.5px;
  font-weight: 600;
  gap: 7px;
}

.artefact-dot {
  border-radius: 999px;
  display: inline-block;
  flex-shrink: 0;
  height: 11px;
  width: 11px;
}

.artefact-dot--secured,
.artefact-dot--rag-green {
  background: #0e8a7d;
}

.artefact-dot--in_progress,
.artefact-dot--rag-amber {
  background: #eaa227;
}

.artefact-dot--not_started {
  background: #b8c4cf;
}

.artefact-dot--rag-red {
  background: #e05252;
}

.artefact-kpis {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(3, minmax(150px, 1fr));
}

.artefact-kpi {
  background: #fff;
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 10px;
  box-shadow: 0 2px 4px rgba(15, 23, 42, 0.04);
  min-width: 0;
  padding: 12px 14px 10px;
}

.artefact-kpi--risk {
  border-left: 3px solid #e05252;
}

.artefact-kpi__label {
  color: #7a8894;
  display: block;
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.artefact-kpi__value {
  color: #10314f;
  display: block;
  font-size: 20px;
  font-weight: 700;
  margin-top: 8px;
}

.artefact-kpi--risk .artefact-kpi__value {
  color: #c23b3b;
}

.artefact-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.artefact-card {
  background: #fff;
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(15, 23, 42, 0.05), 0 10px 22px rgba(15, 23, 42, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.artefact-card__head {
  align-items: center;
  background: linear-gradient(180deg, #0a2e4d 0%, #123a5e 100%);
  color: #fff;
  display: flex;
  gap: 12px;
  padding: 14px 16px;
}

.artefact-card__index {
  align-items: center;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.28);
  border-radius: 8px;
  display: inline-flex;
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 700;
  height: 30px;
  justify-content: center;
  width: 30px;
}

.artefact-card__title {
  font-size: 12.8px;
  font-weight: 700;
  letter-spacing: 0.04em;
  margin: 0;
}

.artefact-card__caption {
  color: rgba(255, 255, 255, 0.68);
  font-size: 11.5px;
  margin: 2px 0 0;
}

.artefact-card__body {
  flex: 1 1 auto;
  padding: 15px 14px 14px;
}

.artefact-card__rag {
  align-items: center;
  display: flex;
  justify-content: space-between;
}

.artefact-rag {
  align-items: center;
  color: #10314f;
  display: inline-flex;
  font-size: 12px;
  font-weight: 700;
  gap: 8px;
  letter-spacing: 0.06em;
}

.artefact-card__pct {
  color: #10314f;
  font-size: 22px;
  font-weight: 700;
}

.artefact-card__track {
  background: #eaeef2;
  border-radius: 999px;
  height: 6px;
  margin: 10px 0 14px;
  overflow: hidden;
}

.artefact-card__fill {
  background: #0e8a7d;
  border-radius: 999px;
  height: 100%;
  transition: width 0.3s ease;
}

.artefact-card--amber .artefact-card__fill {
  background: #eaa227;
}

.artefact-card--red .artefact-card__fill {
  background: #e05252;
}

.artefact-card__count {
  border-top: 1px solid rgba(22, 22, 22, 0.08);
  color: #7a8894;
  display: flex;
  font-size: 10.5px;
  font-weight: 700;
  justify-content: space-between;
  letter-spacing: 0.1em;
  margin: 0 0 12px;
  padding-top: 12px;
  text-transform: uppercase;
}

.artefact-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.artefact-list__toggle {
  background: transparent;
  border: 0;
  color: #0077b8;
  cursor: pointer;
  font: inherit;
  font-size: 11px;
  font-weight: 700;
  margin-top: 8px;
  padding: 4px 0;
  text-align: left;
}

.artefact-list__toggle:hover {
  color: #005f93;
  text-decoration: underline;
}

.artefact-list__toggle:focus-visible {
  border-radius: 3px;
  outline: 2px solid rgba(0, 119, 184, 0.45);
  outline-offset: 2px;
}

.artefact-item {
  align-items: flex-start;
  background: #f7f9fa;
  border: 1px solid rgba(22, 22, 22, 0.06);
  border-left: 3px solid #b8c4cf;
  border-radius: 8px;
  display: flex;
  gap: 10px;
  min-height: 48px;
  padding: 8px 10px;
}

.artefact-item__link {
  align-items: flex-start;
  background: transparent;
  border: 0;
  color: inherit;
  cursor: pointer;
  display: flex;
  font: inherit;
  gap: 10px;
  min-width: 0;
  padding: 0;
  text-align: left;
  width: 100%;
}

.artefact-item__link:disabled {
  cursor: not-allowed;
}

.artefact-item__link:not(:disabled):hover .artefact-item__label {
  color: #0077b8;
  text-decoration: underline;
}

.artefact-item__link:focus-visible {
  border-radius: 4px;
  outline: 2px solid rgba(0, 119, 184, 0.45);
  outline-offset: 3px;
}

.artefact-item__link-arrow {
  color: #0077b8;
  font-size: 19px;
  font-weight: 700;
  line-height: 1;
  margin-left: auto;
  opacity: 0;
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.artefact-item__link:not(:disabled):hover .artefact-item__link-arrow,
.artefact-item__link:not(:disabled):focus-visible .artefact-item__link-arrow {
  opacity: 1;
  transform: translateX(2px);
}

.artefact-item--secured {
  border-left-color: #0e8a7d;
}

.artefact-item--in_progress {
  border-left-color: #eaa227;
}

.artefact-item__icon {
  align-items: center;
  border-radius: 999px;
  color: #fff;
  display: inline-flex;
  flex-shrink: 0;
  height: 20px;
  justify-content: center;
  width: 20px;
}

.artefact-item--secured .artefact-item__icon {
  background: #0e8a7d;
}

.artefact-item--in_progress .artefact-item__icon {
  background: #eaa227;
}

.artefact-item--not_started .artefact-item__icon {
  background: #c3ccd6;
}

.artefact-item__text {
  min-width: 0;
}

.artefact-item__label {
  color: #10314f;
  display: block;
  font-size: 12.5px;
  font-weight: 600;
  line-height: 1.35;
}

.artefact-item--not_started .artefact-item__label {
  color: #97a4b0;
}

.artefact-item__status {
  color: #0e8a7d;
  display: block;
  font-size: 11px;
  margin-top: 3px;
}

.artefact-item--in_progress .artefact-item__status {
  color: #b8801a;
}

.artefact-item--not_started .artefact-item__status {
  color: #a8b3bd;
}

.artefact-card__foot {
  align-items: center;
  border-top: 1px solid rgba(22, 22, 22, 0.08);
  display: flex;
  gap: 10px;
  justify-content: space-between;
  padding: 10px 16px 12px;
}

.artefact-gate {
  background: #0e8a7d;
  border-radius: 6px;
  color: #fff;
  font-size: 11.5px;
  font-weight: 700;
  padding: 7px 12px;
}

.artefact-gate--amber {
  background: #eaa227;
}

.artefact-gate--red {
  background: #e05252;
}

.artefact-card__link {
  background: none;
  border: none;
  color: #0077b8;
  cursor: pointer;
  font-family: inherit;
  font-size: 12px;
  font-weight: 600;
  padding: 0;
}

.artefact-card__link:hover {
  text-decoration: underline;
}

@media (max-width: 1400px) {
  .artefact-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .artefact-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .artefact-board__meta {
    width: 100%;
  }

  .artefact-legend {
    justify-content: flex-start;
  }
}

@media (max-width: 620px) {
  .artefact-grid {
    grid-template-columns: 1fr;
  }
}

/* Reference treatment for the lifecycle dashboard only. */
.artefact-board {
  background: linear-gradient(135deg, #f8fbff 0%, #ffffff 58%, #f6f9ff 100%);
  border: 1px solid #e3eaf4;
  box-shadow: 0 12px 34px rgba(35, 86, 145, 0.09);
  padding: 30px 30px 24px;
}

.artefact-board__head {
  align-items: flex-start;
  margin-bottom: 24px;
}

.artefact-board__eyebrow {
  color: #1673df;
  font-size: 12px;
  letter-spacing: 0.08em;
}

.artefact-board__title {
  color: #102542;
  font-size: clamp(26px, 2.6vw, 38px);
  letter-spacing: -0.04em;
  margin-top: 10px;
}

.artefact-board__sub {
  color: #526885;
  font-size: 15px;
  margin-top: 12px;
}

.artefact-board__meta {
  gap: 18px;
}

.artefact-legend {
  gap: 22px;
}

.artefact-legend__item {
  color: #354967;
  font-size: 14px;
}

.artefact-kpis {
  gap: 16px;
}

.artefact-kpi {
  align-items: center;
  display: flex;
  gap: 14px;
  min-height: 86px;
  padding: 14px 16px;
}

.artefact-kpi__icon {
  align-items: center;
  border-radius: 50%;
  display: inline-flex;
  flex-shrink: 0;
  height: 42px;
  justify-content: center;
  width: 42px;
}

.artefact-kpi__icon--blue {
  background: #edf4ff;
  color: #237ee9;
}

.artefact-kpi__icon--green {
  background: #edf9f3;
  color: #25a779;
}

.artefact-kpi__icon--red {
  background: #fff0f0;
  color: #ed4a4a;
}

.artefact-kpi__copy {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.artefact-kpi__label {
  color: #647694;
  font-size: 11px;
  letter-spacing: 0.02em;
}

.artefact-kpi__value {
  color: #102542;
  font-size: 24px;
  line-height: 1;
  margin: 0;
}

.artefact-grid {
  gap: 22px;
}

.artefact-card {
  border: 1px solid #e5ebf3;
  border-radius: 12px;
  box-shadow: 0 8px 20px rgba(35, 63, 100, 0.08);
  position: relative;
}

.artefact-card::before {
  background: var(--stage-color);
  content: '';
  height: 3px;
  left: 0;
  position: absolute;
  right: 0;
  top: 0;
  z-index: 1;
}

.artefact-card--red { --stage-color: #2d8cff; }
.artefact-card--amber { --stage-color: #22b8b0; }
.artefact-card--green { --stage-color: #6dac39; }

.artefact-card__head {
  align-items: center;
  background: #fff;
  color: #102542;
  gap: 12px;
  min-height: 86px;
  padding: 20px 18px 12px;
}

.artefact-card__index {
  background: color-mix(in srgb, var(--stage-color) 12%, white);
  border: 0;
  border-radius: 8px;
  color: color-mix(in srgb, var(--stage-color) 80%, #102542);
  height: 38px;
  width: 38px;
}

.artefact-card__icon {
  align-items: center;
  background: color-mix(in srgb, var(--stage-color) 12%, white);
  border-radius: 50%;
  color: var(--stage-color);
  display: inline-flex;
  flex-shrink: 0;
  height: 42px;
  justify-content: center;
  width: 42px;
}

.artefact-card__title {
  color: #102542;
  font-size: 14px;
  letter-spacing: 0;
}

.artefact-card__caption {
  color: #62728b;
  font-size: 12px;
  margin-top: 5px;
}

.artefact-card__menu {
  color: #8795ad;
  font-size: 19px;
  letter-spacing: 2px;
  line-height: 1;
  margin-left: auto;
  margin-top: -14px;
}

.artefact-card__body {
  padding: 8px 22px 16px;
}

.artefact-card__summary {
  align-items: center;
  border-bottom: 1px solid #edf0f5;
  display: grid;
  gap: 12px;
  grid-template-columns: 62px minmax(0, 1fr) auto;
  padding: 6px 0 16px;
}

.artefact-card__ring {
  align-items: center;
  background: conic-gradient(var(--stage-color) calc(var(--pct) * 1%), #e8edf3 0);
  border-radius: 50%;
  display: flex;
  height: 58px;
  justify-content: center;
  position: relative;
  width: 58px;
}

.artefact-card__ring::after {
  background: #fff;
  border-radius: 50%;
  content: '';
  height: 44px;
  position: absolute;
  width: 44px;
}

.artefact-card__ring-value {
  color: #102542;
  font-size: 0;
  position: relative;
  z-index: 1;
}

.artefact-card__rag {
  align-items: flex-start;
  flex-direction: column;
  gap: 4px;
  justify-content: center;
}

.artefact-card__pct {
  color: #102542;
  font-size: 24px;
  line-height: 1;
}

.artefact-rag {
  color: #e44848;
  font-size: 12px;
  gap: 6px;
}

.artefact-card__count {
  border: 0;
  display: flex;
  flex-direction: column;
  gap: 7px;
  margin: 0;
  padding: 0;
  text-align: right;
}

.artefact-card__count span {
  color: #647694;
  font-size: 10px;
}

.artefact-card__count strong {
  color: #354967;
  font-size: 14px;
}

.artefact-list {
  gap: 7px;
  margin-top: 14px;
}

.artefact-item {
  align-items: center;
  background: #fbfcfe;
  border: 1px solid #edf0f5;
  border-left: 0;
  border-radius: 7px;
  min-height: 45px;
  padding: 7px 10px;
}

.artefact-item__icon,
.artefact-item--not_started .artefact-item__icon {
  background: transparent;
  color: var(--stage-color);
  height: 20px;
  width: 20px;
}

.artefact-item__label,
.artefact-item--not_started .artefact-item__label {
  color: #354967;
  font-size: 12px;
}

.artefact-item__status,
.artefact-item--not_started .artefact-item__status {
  color: #7d8ba2;
  font-size: 10px;
  margin-top: 3px;
}

.artefact-card__foot {
  background: #fff;
  padding: 12px 22px 15px;
}

.artefact-gate {
  background: #fff5f5;
  border: 1px solid #ffd8d8;
  border-radius: 6px;
  color: #e44848;
  font-size: 11px;
  padding: 9px 12px;
}

.artefact-card__link {
  color: #1673df;
  font-size: 12px;
}

.artefact-board__note {
  align-items: center;
  color: #687993;
  display: flex;
  font-size: 12px;
  gap: 7px;
  justify-content: center;
  margin: 24px 0 0;
}

.artefact-board__note mc-icon {
  color: #287fe0;
}

.quick-tools {
  margin-bottom: 24px;
}

.quick-tools__head {
  margin-bottom: 14px;
}

.quick-tools__eyebrow {
  color: #1673df;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  margin: 0 0 6px;
  text-transform: uppercase;
}

.quick-tools__title {
  color: #102542;
  font-family: 'Maersk Headline', 'Maersk Text', sans-serif;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.1;
  margin: 0;
}

.quick-tools__sub {
  color: #71819a;
  font-size: 13px;
  line-height: 1.5;
  margin: 6px 0 0;
}

.quick-cards {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-bottom: 28px;
}

.quick-card {
  --card-accent: #0077b8;
  background: #fff;
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-top: 3px solid var(--card-accent);
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(15, 23, 42, 0.05), 0 10px 22px rgba(15, 23, 42, 0.06);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px 20px;
  transition: box-shadow 0.22s ease, transform 0.22s ease, border-color 0.22s ease;
}

.quick-card:hover:not(.quick-card--disabled) {
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.08), 0 20px 40px rgba(0, 63, 110, 0.14);
  transform: translateY(-3px);
}

.quick-card:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--card-accent) 35%, white);
  outline-offset: 2px;
}

.quick-card--disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.quick-card__icon {
  align-items: center;
  background: color-mix(in srgb, var(--card-accent) 12%, white);
  border-radius: 10px;
  color: var(--card-accent);
  display: inline-flex;
  height: 42px;
  justify-content: center;
  width: 42px;
}

.quick-card__body {
  flex: 1 1 auto;
  min-width: 0;
}

.quick-card__title {
  color: #10314f;
  font-family: 'Maersk Headline', 'Maersk Text', sans-serif;
  font-size: 16.5px;
  font-weight: 700;
  margin: 0 0 6px;
}

.quick-card__desc {
  color: #7a8894;
  font-size: 12.5px;
  line-height: 1.5;
  margin: 0;
}

.quick-card__foot {
  align-items: center;
  border-top: 1px solid rgba(22, 22, 22, 0.08);
  display: flex;
  justify-content: space-between;
  padding-top: 12px;
}

.quick-card__status {
  align-items: center;
  color: #7a8894;
  display: inline-flex;
  font-size: 12px;
  font-weight: 600;
  gap: 6px;
}

.quick-card--complete .quick-card__status {
  color: #0e8a7d;
}

.quick-card--active .quick-card__status {
  color: #b8801a;
}

.quick-card--at_risk .quick-card__status {
  color: #c23b3b;
}

.quick-card__link {
  color: var(--card-accent);
  font-size: 12px;
  font-weight: 700;
}

.quick-cards {
  align-items: stretch;
  column-gap: 24px;
  position: relative;
}

.quick-card {
  border-top: 0;
  min-height: 160px;
  padding: 18px 20px 14px;
  position: relative;
}

.quick-card::after {
  background: linear-gradient(90deg, rgba(45, 140, 255, 0.35), rgba(45, 140, 255, 0.08));
  content: '';
  height: 1px;
  position: absolute;
  right: -24px;
  top: 50%;
  width: 24px;
}

.quick-card::before {
  display: none;
}

.quick-card:last-child::after,
.quick-card:last-child::before {
  display: none;
}

.quick-card__main {
  align-items: flex-start;
  display: flex;
  gap: 12px;
  min-height: 94px;
}

.quick-card__icon {
  border-radius: 50%;
  flex-shrink: 0;
  height: 56px;
  width: 56px;
}

.quick-card__index {
  color: var(--card-accent);
  font-size: 14px;
  font-weight: 800;
  line-height: 1.2;
  margin-left: -2px;
  margin-top: 1px;
}

.quick-card__body {
  min-width: 0;
}

.quick-card__title {
  font-size: 16px;
  line-height: 1.15;
  margin: 0 0 7px;
}

.quick-card__desc {
  font-size: 12px;
  line-height: 1.45;
}

.quick-card__foot {
  padding-top: 10px;
}

.quick-card__status {
  background: color-mix(in srgb, var(--card-accent) 12%, white);
  border-radius: 999px;
  color: var(--card-accent);
  font-size: 11px;
  padding: 4px 8px;
}

.quick-card--complete .quick-card__status {
  background: #e9f7ed;
  color: #3b9c59;
}

.quick-card--pending .quick-card__status {
  background: #f2f3f5;
  color: #68717e;
}

.quick-card__link {
  font-size: 12px;
}

@media (max-width: 1100px) {
  .quick-cards {
    gap: 18px;
  }

  .quick-card::after,
  .quick-card::before {
    display: none;
  }
}

@media (max-width: 1100px) {
  .quick-cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 620px) {
  .quick-cards {
    grid-template-columns: 1fr;
  }
}

/* Extend the lifecycle dashboard language to the supporting Toll Gates panels. */
.project-picker {
  align-items: center;
  background: #f7faff;
  border: 1px solid #e5edf7;
  border-radius: 12px;
  display: flex;
  gap: 14px;
  margin-bottom: 24px;
  padding: 12px 16px;
}

.project-picker__label {
  color: #354967;
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
}

.project-picker__combobox {
  min-width: min(320px, 38vw);
}

.project-picker__input {
  background: #fff;
  border-color: #dce6f1;
  border-radius: 8px;
  color: #102542;
  font-size: 13px;
  height: 38px;
}

.project-picker__input::placeholder {
  color: #94a2b7;
}

.project-picker__hint {
  color: #71819a;
  font-size: 12px;
}

.quick-cards {
  gap: 18px;
  margin-bottom: 24px;
}

.quick-card {
  background: linear-gradient(145deg, #fff 0%, #fbfdff 100%);
  border: 1px solid #e4ebf4;
  border-top: 3px solid var(--card-accent);
  border-radius: 12px;
  box-shadow: 0 7px 18px rgba(35, 63, 100, 0.07);
  gap: 14px;
  padding: 16px 18px;
}

.quick-card__icon {
  background: color-mix(in srgb, var(--card-accent) 11%, white);
  border-radius: 50%;
  height: 40px;
  width: 40px;
}

.quick-card__title {
  color: #102542;
  font-size: 15px;
}

.quick-card__desc {
  color: #71819a;
}

.quick-card__foot {
  border-top-color: #edf0f5;
}

@media (min-width: 721px) {
  .toll-gates-page-shell :deep(.page-content) {
    padding-top: 14px;
    padding-bottom: 40px;
  }

  .toll-gates-page-shell :deep(.back-link) {
    margin-bottom: 8px;
  }

  .toll-gates-page-shell :deep(.header-main) {
    margin-bottom: 10px;
  }

  .toll-gates-page-shell :deep(.page-title) {
    font-size: clamp(28px, 3vw, 36px);
    line-height: 1;
    margin: 6px 0 4px;
  }

  .toll-gates-page-shell :deep(.page-subtitle) {
    font-size: 13px;
    line-height: 1.35;
  }

  .project-picker {
    gap: 10px;
    margin-bottom: 12px;
    padding: 8px 12px;
  }

  .project-picker__label {
    font-size: 12px;
  }

  .project-picker__input {
    height: 34px;
  }

  .project-picker__hint {
    font-size: 11px;
  }

  .artefact-board {
    margin-bottom: 20px;
    padding: 8px 16px 7px;
  }

  .artefact-board__head {
    align-items: center;
    gap: 14px;
    margin-bottom: 6px;
  }

  .artefact-board__title {
    font-size: clamp(21px, 1.9vw, 26px);
    letter-spacing: -0.04em;
    margin-top: 1px;
  }

  .artefact-board__sub {
    font-size: 11px;
    margin-top: 2px;
  }

  .artefact-board__meta {
    align-items: stretch;
    display: flex;
    flex-direction: column;
    gap: 5px;
    min-width: min(100%, 500px);
  }

  .artefact-legend {
    gap: 8px;
  }

  .artefact-kpis {
    gap: 6px;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .artefact-kpi {
    align-items: center;
    display: grid;
    gap: 4px 8px;
    grid-template-columns: minmax(0, 1fr) 26px;
    min-height: 0;
    padding: 6px 8px;
  }

  .artefact-kpi__copy {
    display: flex;
    flex-direction: column;
    grid-column: 1;
    grid-row: 1;
  }

  .artefact-kpi__icon {
    grid-column: 2;
    grid-row: 1;
    height: 26px;
    width: 26px;
  }

  .artefact-kpi__icon mc-icon {
    height: 15px;
    width: 15px;
  }

  .artefact-kpi__label {
    order: 2;
    font-size: 9px;
    letter-spacing: 0.05em;
    line-height: 1.2;
  }

  .artefact-kpi__value {
    font-size: 17px;
    line-height: 1.1;
    margin-top: 2px;
    order: 1;
  }

  .artefact-board__note {
    margin-top: 8px;
  }
}

@media (max-width: 720px) {
  .project-picker {
    align-items: stretch;
    flex-direction: column;
  }

  .project-picker__combobox {
    min-width: 0;
    width: 100%;
  }
}
</style>
