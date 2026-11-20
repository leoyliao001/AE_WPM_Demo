<template>
  <PageShell
    class="portfolio-page"
    title="Migration Manager Portfolio"
    subtitle="Select a migration manager to review assigned projects, delivery health, and key milestones."
    tag="Migration Portfolio"
    full-width
  >
    <div class="portfolio-content">
      <div class="portfolio-title-row">
        <div>
          <p class="portfolio-subtitle">Portfolio overview</p>
        </div>
        <button class="portfolio-button" type="button" :disabled="!filteredProjects.length" @click="exportCsv">
          ↓ Export
        </button>
      </div>

      <section class="manager-card" aria-label="Migration manager selection">
        <div class="manager-left">
          <div class="manager-avatar" aria-hidden="true">{{ managerInitials }}</div>
          <div class="manager-copy">
            <label for="manager-select">Migration Manager</label>
            <select id="manager-select" v-model="selectedManager">
              <option value="all">All managers</option>
              <option v-for="manager in managers" :key="manager" :value="manager">{{ manager }}</option>
            </select>
          </div>
        </div>
        <div class="manager-meta">
          <div><strong>{{ managerProjects.length }}</strong><span>Assigned projects</span></div>
          <div><strong>{{ managerRegion }}</strong><span>Primary region</span></div>
        </div>
      </section>

      <div v-if="loadError" class="portfolio-error" role="alert">
        <span>{{ loadError }}</span>
        <button class="portfolio-button" type="button" @click="loadProjects">Retry</button>
      </div>

      <section class="metrics" aria-label="Portfolio metrics">
        <article class="metric">
          <div class="metric-label">Assigned Projects</div>
          <div class="metric-value">{{ metrics.projectCount }}<span>projects</span></div>
          <div class="metric-foot">{{ metrics.activeCount }} currently active</div>
        </article>
        <article class="metric">
          <div class="metric-label">Total Scope</div>
          <div class="metric-value">{{ formatNumber(metrics.totalFte) }}<span>FTE</span></div>
          <div class="metric-foot">{{ formatNumber(metrics.averageFte) }} average per project</div>
        </article>
        <article class="metric metric--green">
          <div class="metric-label">On Track</div>
          <div class="metric-value">{{ metrics.onTrack }}<span>projects</span></div>
          <div class="metric-foot">{{ metrics.onTrackPercent }}% of portfolio</div>
        </article>
        <article class="metric metric--amber">
          <div class="metric-label">At Risk</div>
          <div class="metric-value">{{ metrics.atRisk }}<span>projects</span></div>
          <div class="metric-foot">Needs mitigation / attention</div>
        </article>
        <article class="metric metric--red">
          <div class="metric-label">Upcoming Go-Lives</div>
          <div class="metric-value">{{ metrics.upcomingGoLives }}<span>next 90 days</span></div>
          <div class="metric-foot">Based on target end date</div>
        </article>
      </section>

      <section class="toolbar" aria-label="Project filters">
        <div class="search-field">
          <input v-model="search" type="search" placeholder="Search project name or ID" aria-label="Search project name or ID" />
        </div>
        <select v-model="statusFilter" aria-label="Filter by RAG status">
          <option value="">All RAG statuses</option>
          <option value="On Track">On Track</option>
          <option value="At Risk">At Risk</option>
          <option value="Off Track">Off Track</option>
        </select>
        <select v-model="phaseFilter" aria-label="Filter by phase">
          <option value="">All phases</option>
          <option v-for="phase in phases" :key="phase" :value="phase">{{ phase }}</option>
        </select>
        <select v-model="regionFilter" aria-label="Filter by region">
          <option value="">All regions</option>
          <option v-for="region in regions" :key="region" :value="region">{{ region }}</option>
        </select>
        <button class="portfolio-button" type="button" @click="resetFilters">Reset</button>
      </section>

      <section class="table-card">
        <div class="table-head">
          <h2>Assigned Projects</h2>
          <span class="record-count">{{ filteredProjects.length }} projects</span>
        </div>
        <div v-if="loading" class="empty-state">Loading projects…</div>
        <div v-else-if="!filteredProjects.length" class="empty-state">
          No projects match the selected filters.
        </div>
        <div v-else class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th>Project Name</th>
                <th>Region</th>
                <th>Area</th>
                <th>Migration Type</th>
                <th>RAG</th>
                <th>Phase</th>
                <th>FTE</th>
                <th>Progress</th>
                <th>Request ID</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="project in filteredProjects"
                :key="project.id"
                tabindex="0"
                @click="openProject(project.id)"
                @keydown.enter="openProject(project.id)"
              >
                <td>{{ displayProducts(project) }}</td>
                <td><strong class="project-name">{{ project.projectName || '—' }}</strong></td>
                <td>{{ project.region || '—' }}</td>
                <td>{{ displayAreas(project) }}</td>
                <td>{{ project.migrationType || '—' }}</td>
                <td><span class="rag-pill" :class="ragClass(project)">{{ ragLabel(project) }}</span></td>
                <td>{{ phaseLabel(project) }}</td>
                <td><strong>{{ formatNumber(projectFte(project)) }}</strong></td>
                <td>
                  <div class="progress-track" aria-hidden="true">
                    <span :style="{ width: `${projectProgress(project)}%` }" />
                  </div>
                  <span class="progress-label">{{ projectProgress(project) }}%</span>
                </td>
                <td>{{ project.migrationRequestId || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <footer class="table-footer">
          <span><strong>Open a project:</strong> click any row to view details and track progress.</span>
          <span>Showing {{ filteredProjects.length }} of {{ managerProjects.length }} projects</span>
        </footer>
      </section>
    </div>
  </PageShell>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'
import { overallProgress } from '../utils/migrationDashboardProgress.js'

const router = useRouter()
const projects = ref([])
const loading = ref(false)
const loadError = ref('')
const selectedManager = ref('all')
const search = ref('')
const statusFilter = ref('')
const phaseFilter = ref('')
const regionFilter = ref('')
const phases = ['Initiate', 'Plan', 'Execute', 'Monitor & Control', 'Close & Realize Value']

const managers = computed(() => {
  const values = new Set(projects.value.map(project => project.owner).filter(Boolean))
  if (projects.value.some(project => !project.owner)) values.add('Unassigned')
  return [...values].sort((a, b) => a.localeCompare(b))
})
const managerProjects = computed(() => selectedManager.value === 'all'
  ? projects.value
  : projects.value.filter(project => (project.owner || 'Unassigned') === selectedManager.value))
const regions = computed(() => [...new Set(managerProjects.value.map(project => project.region).filter(Boolean))].sort())
const filteredProjects = computed(() => {
  const query = search.value.trim().toLowerCase()
  return managerProjects.value.filter(project => {
    if (statusFilter.value && ragLabel(project) !== statusFilter.value) return false
    if (phaseFilter.value && phaseLabel(project) !== phaseFilter.value) return false
    if (regionFilter.value && project.region !== regionFilter.value) return false
    return !query || `${project.projectName || ''} ${project.migrationRequestId || ''}`.toLowerCase().includes(query)
  })
})

const metrics = computed(() => {
  const totalFte = managerProjects.value.reduce((sum, project) => sum + projectFte(project), 0)
  const onTrack = managerProjects.value.filter(project => ragLabel(project) === 'On Track').length
  const now = new Date()
  const deadline = new Date(now)
  deadline.setDate(deadline.getDate() + 90)
  const upcomingGoLives = managerProjects.value.filter(project => {
    const raw = project.targetEndDate
    if (!raw) return false
    const date = new Date(`${raw}T00:00:00`)
    return !Number.isNaN(date.getTime()) && date >= new Date(now.toDateString()) && date <= deadline
  }).length
  return {
    projectCount: managerProjects.value.length,
    activeCount: managerProjects.value.filter(project => project.status !== 'completed').length,
    totalFte,
    averageFte: managerProjects.value.length ? totalFte / managerProjects.value.length : 0,
    onTrack,
    onTrackPercent: managerProjects.value.length ? Math.round(onTrack / managerProjects.value.length * 100) : 0,
    atRisk: managerProjects.value.filter(project => ragLabel(project) === 'At Risk').length,
    upcomingGoLives
  }
})

const managerInitials = computed(() => {
  const name = selectedManager.value === 'all' ? 'All Managers' : selectedManager.value
  return name.split(/[\s@._-]+/).filter(Boolean).slice(0, 2).map(part => part[0]).join('').toUpperCase() || 'MM'
})
const managerRegion = computed(() => {
  const counts = new Map()
  managerProjects.value.forEach(project => {
    if (project.region) counts.set(project.region, (counts.get(project.region) || 0) + 1)
  })
  return [...counts].sort((left, right) => right[1] - left[1])[0]?.[0] || '—'
})

function projectFte(project) {
  const value = Number.parseFloat(project.fteNumber)
  return Number.isFinite(value) ? value : 0
}

function ragLabel(project) {
  const status = String(project.status || '').toLowerCase()
  if (status === 'at_risk' || status.includes('risk')) return 'At Risk'
  if (status === 'off_track' || status.includes('off track') || status === 'delayed') return 'Off Track'
  return 'On Track'
}

function ragClass(project) {
  return ragLabel(project).toLowerCase().replaceAll(' ', '-')
}

function phaseLabel(project) {
  const status = String(project.status || '').toLowerCase()
  if (status === 'completed') return 'Close & Realize Value'
  if (status === 'planning') return 'Plan'
  if (status === 'in_progress' || status === 'at_risk') return 'Execute'
  return 'Initiate'
}

function projectProgress(project) {
  return Math.max(0, Math.min(100, overallProgress(project.status)))
}

function displayProducts(project) {
  return project.products?.length ? project.products.join(', ') : '—'
}

function displayAreas(project) {
  return project.areasPreview || (project.areasCount ? `${project.areasCount} areas` : '—')
}

function formatNumber(value) {
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 }).format(Number(value) || 0)
}

function resetFilters() {
  search.value = ''
  statusFilter.value = ''
  phaseFilter.value = ''
  regionFilter.value = ''
}

function openProject(id) {
  router.push({ path: '/toll-gates', query: { project: String(id), from: 'project-dashboard' } })
}

function exportCsv() {
  const columns = ['Request ID', 'Project Name', 'Region', 'Areas', 'Migration Type', 'RAG', 'Phase', 'FTE', 'Progress', 'Product']
  const rows = filteredProjects.value.map(project => [
    project.migrationRequestId, project.projectName, project.region, displayAreas(project),
    project.migrationType, ragLabel(project), phaseLabel(project), projectFte(project),
    `${projectProgress(project)}%`, displayProducts(project)
  ])
  const quote = value => `"${String(value ?? '').replaceAll('"', '""')}"`
  const csv = [columns, ...rows].map(row => row.map(quote).join(',')).join('\r\n')
  const link = document.createElement('a')
  const objectUrl = URL.createObjectURL(new Blob(['\ufeff', csv], { type: 'text/csv;charset=utf-8' }))
  link.href = objectUrl
  link.download = 'migration-manager-portfolio.csv'
  link.click()
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 0)
}

async function loadProjects() {
  loading.value = true
  loadError.value = ''
  try {
    const { data } = await axios.get('/api/migration-dashboard/projects/')
    projects.value = data.rows || []
  } catch (error) {
    loadError.value = error.response?.data?.error || 'Unable to load project portfolio.'
  } finally {
    loading.value = false
  }
}

onMounted(loadProjects)
</script>

<style scoped>
.portfolio-content { width: 100%; max-width: none; margin: 0; color: #15232d; font: 13px Arial, Helvetica, sans-serif; }
.portfolio-title-row { display: flex; justify-content: space-between; align-items: flex-end; margin: 0 0 14px; }
.portfolio-subtitle { margin: 0; color: #667985; }
.portfolio-button { height: 34px; padding: 0 14px; border: 1px solid #bfd0d8; border-radius: 6px; background: #fff; color: #20333f; font-weight: 700; cursor: pointer; }
.portfolio-button:disabled { opacity: .5; cursor: not-allowed; }
.manager-card { display: flex; justify-content: space-between; align-items: center; padding: 16px 18px; border: 1px solid #dfe5e8; border-radius: 12px; background: #fff; box-shadow: 0 2px 8px rgba(0,31,51,.04); }
.manager-left { display: flex; align-items: center; gap: 13px; }
.manager-avatar { display: grid; width: 42px; height: 42px; place-items: center; border-radius: 50%; background: #dff2f8; color: #006d93; font-size: 15px; font-weight: 800; }
.manager-copy label { display: block; color: #667985; font-size: 10px; font-weight: 700; letter-spacing: .6px; text-transform: uppercase; }
.manager-copy select { display: block; max-width: min(460px, 60vw); margin-top: 3px; border: 0; background: transparent; color: #15232d; font-size: 17px; font-weight: 700; }
.manager-meta { display: flex; gap: 34px; }
.manager-meta strong, .manager-meta span { display: block; }
.manager-meta strong { font-size: 14px; }
.manager-meta span { margin-top: 3px; color: #667985; font-size: 11px; }
.metrics { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; margin: 14px 0; }
.metric { position: relative; min-height: 92px; padding: 15px 16px; border: 1px solid #dfe5e8; border-radius: 10px; background: #fff; }
.metric::before { position: absolute; top: 15px; bottom: 15px; left: 0; width: 3px; border-radius: 3px; background: #42b0d5; content: ''; }
.metric--green::before { background: #318b4f; }
.metric--amber::before { background: #db8c00; }
.metric--red::before { background: #cf3e43; }
.metric-label { color: #667985; font-size: 10px; font-weight: 800; letter-spacing: .45px; text-transform: uppercase; }
.metric-value { margin-top: 8px; font-size: 27px; font-weight: 800; line-height: 1; }
.metric-value span { margin-left: 4px; color: #667985; font-size: 11px; font-weight: 400; }
.metric-foot { margin-top: 8px; color: #667985; font-size: 11px; }
.toolbar { display: flex; align-items: center; gap: 9px; margin-top: 4px; padding: 11px; border: 1px solid #dfe5e8; border-radius: 10px 10px 0 0; background: #fff; }
.search-field { flex: 1; min-width: 220px; }
.toolbar input, .toolbar select { height: 34px; padding: 0 10px; border: 1px solid #cfd9de; border-radius: 6px; background: #fff; color: #263842; }
.toolbar input { width: 100%; }
.toolbar select { max-width: 190px; }
.table-card { overflow: hidden; border: 1px solid #dfe5e8; border-top: 0; border-radius: 0 0 12px 12px; background: #fff; box-shadow: 0 2px 8px rgba(0,31,51,.04); }
.table-head, .table-footer { display: flex; justify-content: space-between; align-items: center; padding: 14px 16px 9px; }
.table-head h2 { margin: 0; font-size: 14px; }
.record-count { padding: 4px 9px; border-radius: 20px; background: #eef2f4; color: #50646f; font-size: 10px; font-weight: 700; }
.table-scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
th { padding: 11px 13px; border-block: 1px solid #dfe5e8; background: #f0f3f5; color: #334650; font-size: 10px; letter-spacing: .35px; text-align: left; text-transform: uppercase; white-space: nowrap; }
td { padding: 12px 13px; border-bottom: 1px solid #e7ecef; white-space: nowrap; }
tbody tr { cursor: pointer; }
tbody tr:hover, tbody tr:focus-visible { background: #f4fbfd; outline: none; }
.project-name { color: #003f61; }
.rag-pill { display: inline-flex; align-items: center; gap: 6px; padding: 5px 9px; border-radius: 16px; font-size: 10px; font-weight: 800; }
.rag-pill::before { width: 7px; height: 7px; border-radius: 50%; background: currentColor; content: ''; }
.on-track { background: #e6f5eb; color: #287b43; }
.at-risk { background: #fff1da; color: #a45f00; }
.off-track { background: #fde8e9; color: #b52f35; }
.progress-track { width: 94px; height: 6px; margin-bottom: 4px; overflow: hidden; border-radius: 10px; background: #e8edf0; }
.progress-track span { display: block; height: 100%; border-radius: 10px; background: #31a4ca; }
.progress-label { color: #667985; font-size: 11px; }
.table-footer { padding-top: 12px; color: #667985; font-size: 11px; }
.table-footer strong { color: #15232d; }
.empty-state { padding: 36px 20px; color: #667985; text-align: center; }
.portfolio-error { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 12px 14px; border: 1px solid #f0b4ae; border-radius: 8px; color: #b42318; }
@media (max-width: 1000px) { .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); } .manager-meta { display: none; } }
@media (max-width: 700px) { .toolbar { align-items: stretch; flex-wrap: wrap; } .search-field { flex-basis: 100%; } .toolbar select { flex: 1; max-width: none; min-width: 130px; } .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); } .table-footer { align-items: flex-start; flex-direction: column; gap: 8px; } .manager-copy select { max-width: calc(100vw - 130px); } }
@media (max-width: 420px) { .metrics { grid-template-columns: 1fr; } }
</style>
