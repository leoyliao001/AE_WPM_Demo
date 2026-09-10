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
              <span class="artefact-kpi__label">Overall completion</span>
              <strong class="artefact-kpi__value">{{ artefactTotals.pct }}%</strong>
            </div>
            <div class="artefact-kpi artefact-kpi--info">
              <span class="artefact-kpi__label">Artefacts secured</span>
              <strong class="artefact-kpi__value">{{ artefactTotals.secured }} / {{ artefactTotals.total }}</strong>
            </div>
            <div class="artefact-kpi artefact-kpi--risk">
              <span class="artefact-kpi__label">At risk</span>
              <strong class="artefact-kpi__value">{{ artefactTotals.atRiskStages }} stage{{ artefactTotals.atRiskStages === 1 ? '' : 's' }}</strong>
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
        >
          <header class="artefact-card__head">
            <span class="artefact-card__index">{{ stage.index }}</span>
            <div>
              <h3 class="artefact-card__title">{{ stage.title }}</h3>
              <p class="artefact-card__caption">{{ stage.caption }}</p>
            </div>
          </header>

          <div class="artefact-card__body">
            <div class="artefact-card__rag">
              <span class="artefact-rag">
                <span class="artefact-dot" :class="`artefact-dot--rag-${stage.rag}`" />
                {{ stage.rag.toUpperCase() }}
              </span>
              <strong class="artefact-card__pct">{{ stage.pct }}%</strong>
            </div>
            <div class="artefact-card__track">
              <div class="artefact-card__fill" :style="{ width: `${stage.pct}%` }" />
            </div>

            <p class="artefact-card__count">
              <span>Artefacts</span>
              <span>{{ stage.secured }}/{{ stage.items.length }}</span>
            </p>

            <ul class="artefact-list">
              <li
                v-for="item in stage.items"
                :key="item.label"
                class="artefact-item"
                :class="`artefact-item--${item.status}`"
              >
                <span class="artefact-item__icon">
                  <mc-icon v-if="item.status === 'secured'" icon="mi-check" size="14" />
                  <mc-icon v-else-if="item.status === 'in_progress'" icon="mi-exclamation-circle" size="14" />
                  <mc-icon v-else icon="mi-minus" size="14" />
                </span>
                <span class="artefact-item__text">
                  <span class="artefact-item__label">{{ item.label }}</span>
                  <span class="artefact-item__status">{{ ARTEFACT_STATUS_LABEL[item.status] }}</span>
                </span>
              </li>
            </ul>
          </div>

          <footer class="artefact-card__foot">
            <span class="artefact-gate" :class="`artefact-gate--${stage.rag}`">{{ stage.gateLabel }}</span>
            <button type="button" class="artefact-card__link" @click="scrollToPhase(stage.id)">
              View stage ›
            </button>
          </footer>
        </article>
      </div>
    </section>

    <section class="quick-cards" aria-label="Project artefact shortcuts">
      <div
        v-for="card in quickCards"
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
        <span class="quick-card__icon">
          <mc-icon :icon="card.icon" size="22" />
        </span>
        <div class="quick-card__body">
          <h3 class="quick-card__title">{{ card.title }}</h3>
          <p class="quick-card__desc">{{ card.description }}</p>
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
    </section>

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
      :id="`phase-${phase.id}`"
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
  // `from` lets the destination page send the user back here instead of its default parent.
  router.push({ path: to, query: { from: 'toll-gates', project: id } })
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

// `source` links an artefact to an existing tracked step id; artefacts without a
// source have no system of record yet and stay "Not started".
const ARTEFACT_STAGES = [
  {
    id: 'initiating',
    index: '01',
    title: 'Initiating',
    caption: 'Authorise & define',
    items: [
      { label: 'Project Charter / mandate', source: 'intake' },
      { label: 'Business case', source: 'business_case' },
      { label: 'Stakeholder register', source: 'approvals' },
      { label: 'High-level scope statement', source: 'opportunity' }
    ]
  },
  {
    id: 'planning',
    index: '02',
    title: 'Planning',
    caption: 'Build the roadmap',
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
    title: 'Executing',
    caption: 'Do the work',
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
    title: 'Closing',
    caption: 'Finalise & learn',
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

const scrollToPhase = (phaseId) => {
  document.getElementById(`phase-${phaseId}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const QUICK_STATUS_LABEL = {
  complete: 'Complete',
  active: 'In progress',
  at_risk: 'At risk',
  pending: 'Not started'
}

// Ids reuse TILE_ROUTES so clicking a card opens the same page as the stepper below.
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
  background: #f6f8fa;
  border: 1px solid rgba(22, 22, 22, 0.07);
  border-radius: 16px;
  margin-bottom: 28px;
  padding: 24px;
}

.artefact-board__head {
  align-items: flex-start;
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  justify-content: space-between;
  margin-bottom: 22px;
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
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin: 6px 0 0;
}

.artefact-board__sub {
  color: #7a8894;
  font-size: 13px;
  margin: 6px 0 0;
}

.artefact-board__meta {
  display: flex;
  flex-direction: column;
  gap: 12px;
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
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.artefact-kpi {
  background: #fff;
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-left: 4px solid #42b0d5;
  border-radius: 8px;
  min-width: 168px;
  padding: 12px 18px;
}

.artefact-kpi--risk {
  border-left-color: #e05252;
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
  font-size: 22px;
  font-weight: 700;
  margin-top: 4px;
}

.artefact-kpi--risk .artefact-kpi__value {
  color: #c23b3b;
}

.artefact-grid {
  display: grid;
  gap: 16px;
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
  background: #123a5e;
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
  font-size: 13.5px;
  font-weight: 700;
  letter-spacing: 0.04em;
  margin: 0;
  text-transform: uppercase;
}

.artefact-card__caption {
  color: rgba(255, 255, 255, 0.68);
  font-size: 11.5px;
  margin: 2px 0 0;
}

.artefact-card__body {
  flex: 1 1 auto;
  padding: 16px;
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

.artefact-item {
  align-items: flex-start;
  background: #f7f9fa;
  border: 1px solid rgba(22, 22, 22, 0.06);
  border-left: 3px solid #b8c4cf;
  border-radius: 8px;
  display: flex;
  gap: 10px;
  padding: 10px 12px;
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
  padding: 12px 16px;
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
