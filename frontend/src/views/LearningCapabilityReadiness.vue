<template>
  <div class="partner-dashboard ld-page">
    <main class="dashboard-content">
      <header class="page-heading">
        <div><h1>Learning &amp; Capability Readiness</h1><p>Foundational training and knowledge transfer across approved migrations</p></div>
        <label class="select-field region-field">Region<select v-model="filters.region"><option value="">All Regions</option><option v-for="item in regions" :key="item">{{ item }}</option></select></label>
      </header>
      <p v-if="loading" class="data-feedback" role="status">Loading project portfolio...</p>
      <p v-else-if="error" class="data-feedback data-feedback--error" role="alert">{{ error }} <button type="button" @click="loadProjects">Retry</button></p>

      <section class="metric-grid" aria-label="Learning and development metrics">
        <article class="metric"><span class="metric-icon metric-icon--blue">▦</span><div><strong>Active Migrations</strong><b>{{ activeMigrations }}</b><small>Approved or pipeline projects</small></div></article>
        <article class="metric"><span class="metric-icon metric-icon--green">♙</span><div><strong>Approved FTEs</strong><b>{{ approvedFtes }}</b><small>{{ regionsInView }} project regions in view</small></div></article>
        <article class="metric metric--amber"><span class="metric-icon metric-icon--amber">◷</span><div><strong>Pipeline FTEs</strong><b>{{ pipelineFtes }}</b><small>Awaiting approval - plan ahead</small></div></article>
        <article class="metric"><span class="metric-ring metric-ring--empty"><span>—</span></span><div><strong>Avg. L&amp;D Readiness</strong><small>Not tracked in project data</small></div></article>
        <article class="metric"><span class="metric-icon metric-icon--red">△</span><div><strong>Capability Gaps</strong><b>—</b><small>Not tracked in project data</small></div></article>
        <article class="metric"><span class="metric-icon metric-icon--violet">▣</span><div><strong>Approved Target Ends</strong><b>{{ upcomingTargetEnds }}</b><small>Next 90 days</small></div></article>
      </section>

      <section class="chart-grid" aria-label="Learning and development portfolio charts">
        <article class="panel timeline-panel">
          <h2>Project Target Window <small>{{ timelineProjects.length }} projects with dates</small></h2>
          <div class="timeline">
            <div class="timeline-axis"><span></span><span v-for="month in timelineMonths" :key="month.key">{{ month.label }}</span></div>
            <div v-for="project in timelineProjects" :key="project.id" class="timeline-row">
              <span class="timeline-name" :title="project.name">{{ project.name }}</span>
              <span class="timeline-track"><i v-if="project.start && project.go" class="timeline-bar timeline-bar--foundation" :style="barStyle(project.start, project.go)" /><i v-if="project.go" class="timeline-marker" :style="markerStyle(project.go)" /></span>
            </div>
            <p v-if="!timelineProjects.length" class="chart-empty">No project target dates available.</p>
          </div>
          <div class="legend"><span><i class="legend-foundation" />Project target window</span><span><i class="legend-go-live" />Target end date</span></div>
        </article>

        <article class="panel readiness-panel">
          <h2>L&amp;D Readiness by Stage</h2>
          <p class="untracked-state">Not tracked in the project database.</p>
        </article>

        <article class="panel status-panel">
          <h2>Migration Status</h2>
          <div class="status-chart"><div class="status-donut" :style="statusDonutStyle"><span><b>{{ filteredProjects.length }}</b><small>Projects</small></span></div><ul><li v-for="item in statusCounts" :key="item.name"><i :class="`status-dot status-dot--${item.key}`" /><span>{{ item.name }}</span><b>{{ item.count }}</b></li></ul></div>
        </article>
      </section>

      <section class="table-tools" aria-label="Filter projects">
        <label class="search-field">Search<input v-model="filters.search" type="search" placeholder="Search by project name or ID" /></label>
        <label class="select-field">Product<select v-model="filters.product"><option value="">All Products</option><option v-for="item in products" :key="item">{{ item }}</option></select></label>
        <label class="select-field">Area<select v-model="filters.area"><option value="">All Areas</option><option v-for="item in areas" :key="item">{{ item }}</option></select></label>
        <label class="select-field">Status<select v-model="filters.status"><option value="">All Statuses</option><option v-for="item in statuses" :key="item">{{ item }}</option></select></label>
        <button class="tool-button" type="button" @click="clearFilters">Clear All</button>
        <span class="tool-spacer" />
        <button class="tool-button tool-button--export" type="button" @click="exportProjects">↓ Export</button>
      </section>

      <div class="data-table-wrap">
        <table class="data-table">
          <thead><tr><th>Project</th><th>Product</th><th>Region</th><th>Area</th><th>GSC Site</th><th>Approved FTE</th><th>Pipeline FTE</th><th>Cohorts</th><th>Target Start</th><th>Target End</th><th>L&amp;D Readiness</th><th>Status</th></tr></thead>
          <tbody>
            <tr v-for="project in paginatedProjects" :key="project.id">
              <td><strong>{{ project.name }}</strong><small>{{ project.id }}</small></td><td>{{ project.products.join(', ') }}</td><td>{{ project.region }}</td><td>{{ project.areas.join(', ') }}</td><td>{{ project.sites.join(', ') }}</td><td>{{ project.fte ?? '—' }}</td><td>{{ project.pipe ?? '—' }}</td><td>—</td><td>{{ formatDate(project.start) }}</td><td>{{ formatDate(project.go) }}</td>
              <td>Not tracked</td><td><span class="status-label" :class="`status-label--${projectStatus(project).key}`"><i />{{ projectStatus(project).label }}</span></td>
            </tr>
            <tr v-if="!filteredProjects.length"><td class="empty-state" colspan="12">No projects match these filters.</td></tr>
          </tbody>
        </table>
      </div>
      <footer class="table-summary"><span>Showing {{ pageStart }}-{{ pageEnd }} of {{ filteredProjects.length }} projects</span><div class="ld-pagination"><button type="button" aria-label="Previous page" title="Previous page" :disabled="currentPage === 1" @click="currentPage -= 1">‹</button><b aria-live="polite">{{ currentPage }} / {{ pageCount }}</b><button type="button" aria-label="Next page" title="Next page" :disabled="currentPage === pageCount" @click="currentPage += 1">›</button></div></footer>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import axios from 'axios'

const today = new Date()
const projects = ref([])
const loading = ref(false)
const error = ref('')
const currentPage = ref(1)
const pageSize = 10
const statusColors = { Approved: '#16a34a', Pipeline: '#f59e0b', 'Not locked': '#98a5b3' }
const filters = reactive({ search: '', region: '', product: '', area: '', status: '' })
const regions = computed(() => [...new Set(projects.value.map(project => project.region).filter(Boolean))].sort())
const products = computed(() => [...new Set(projects.value.flatMap(project => project.products))].sort())
const areas = computed(() => [...new Set(projects.value.flatMap(project => project.areas))].sort())
const statuses = Object.keys(statusColors)
const filteredProjects = computed(() => projects.value.filter((project) => {
  const search = filters.search.trim().toLowerCase()
  return (!search || `${project.name} ${project.id}`.toLowerCase().includes(search)) && (!filters.region || project.region === filters.region) && (!filters.product || project.products.includes(filters.product)) && (!filters.area || project.areas.includes(filters.area)) && (!filters.status || projectStatus(project).label === filters.status)
}))
const pageCount = computed(() => Math.max(1, Math.ceil(filteredProjects.value.length / pageSize)))
const paginatedProjects = computed(() => filteredProjects.value.slice((currentPage.value - 1) * pageSize, currentPage.value * pageSize))
const pageStart = computed(() => filteredProjects.value.length ? (currentPage.value - 1) * pageSize + 1 : 0)
const pageEnd = computed(() => Math.min(currentPage.value * pageSize, filteredProjects.value.length))
const approvedFtes = computed(() => filteredProjects.value.reduce((sum, project) => sum + (project.approvedFte ?? 0), 0))
const pipelineFtes = computed(() => filteredProjects.value.reduce((sum, project) => sum + (project.pipelineFte ?? 0), 0))
const regionsInView = computed(() => new Set(filteredProjects.value.map((project) => project.region)).size)
const activeMigrations = computed(() => filteredProjects.value.filter(project => ['Approved', 'Pipeline'].includes(project.approvalStatus)).length)
const timelineProjects = computed(() => filteredProjects.value.filter(project => project.start || project.go))
const upcomingTargetEnds = computed(() => filteredProjects.value.filter(project => {
  if (project.approvalStatus !== 'Approved' || !project.targetEndDate) return false
  const date = new Date(`${project.targetEndDate}T00:00:00`)
  const horizon = new Date(today)
  horizon.setDate(horizon.getDate() + 90)
  return date >= today && date <= horizon
}).length)
const statusCounts = computed(() => Object.entries(statusColors).map(([name]) => ({ name, key: name.toLowerCase().replace(' ', '-'), count: filteredProjects.value.filter((project) => projectStatus(project).label === name).length })))
const statusDonutStyle = computed(() => {
  let stop = 0
  const segments = statusCounts.value.map((item) => {
    const start = stop
    stop += filteredProjects.value.length ? item.count / filteredProjects.value.length * 100 : 0
    return `${statusColors[item.name]} ${start}% ${stop}%`
  })
  return { background: filteredProjects.value.length ? `conic-gradient(${segments.join(',')})` : '#e8edf1' }
})
watch(filteredProjects, () => { currentPage.value = 1 })
const timelineMonths = computed(() => Array.from({ length: 6 }, (_, index) => {
  const date = new Date(today.getFullYear(), today.getMonth() - 2 + index, 1)
  return { key: date.toISOString(), label: date.toLocaleDateString('en-GB', { month: 'short', year: '2-digit' }) }
}))
const timelineStart = new Date(today.getFullYear(), today.getMonth() - 2, 1)
const timelineEnd = new Date(today.getFullYear(), today.getMonth() + 4, 1)

function projectStatus(project) {
  const label = project.approvalStatus
  return { label, key: label.toLowerCase().replace(' ', '-') }
}
function datePosition(value) {
  if (!value) return 0
  const timestamp = new Date(`${value}T00:00:00`).getTime()
  return Math.max(0, Math.min(100, (timestamp - timelineStart.getTime()) / (timelineEnd.getTime() - timelineStart.getTime()) * 100))
}
function barStyle(start, end) { const left = datePosition(start); return { left: `${left}%`, width: `${Math.max(0, datePosition(end) - left)}%` } }
function markerStyle(date) { return { left: `${datePosition(date)}%` } }
function formatDate(value) { return value ? new Date(`${value}T00:00:00`).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : '—' }
function clearFilters() { Object.assign(filters, { search: '', region: '', product: '', area: '', status: '' }) }
function exportProjects() {
  const headings = ['Project', 'Project ID', 'Product', 'Region', 'Area', 'GSC Site', 'Approved FTE', 'Pipeline FTE', 'Cohorts', 'Target Start', 'Target End', 'L&D Readiness', 'Status']
  const rows = filteredProjects.value.map((project) => [project.name, project.id, project.products.join(', '), project.region, project.areas.join(', '), project.sites.join(', '), project.approvedFte ?? '', project.pipelineFte ?? '', 'Not tracked', project.start, project.go, 'Not tracked', projectStatus(project).label])
  const csv = [headings, ...rows].map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(',')).join('\r\n')
  const link = document.createElement('a')
  link.href = URL.createObjectURL(new Blob(['\ufeff', csv], { type: 'text/csv;charset=utf-8' }))
  link.download = 'LD_Readiness_Portfolio.csv'
  link.click()
  URL.revokeObjectURL(link.href)
}

async function loadProjects() {
  loading.value = true
  error.value = ''
  try {
    const response = await axios.get('/api/migration-dashboard/resources/')
    projects.value = response.data.rows.map(row => ({
      id: row.migrationRequestId || row.projectId,
      name: row.projectName,
      products: row.products || [],
      region: row.region || '',
      areas: row.areas || [],
      sites: row.sites || [],
      approvalStatus: row.approvalStatus,
      approvedFte: row.approvedFte,
      pipelineFte: row.pipelineFte,
      targetEndDate: row.targetEndDate,
      start: row.targetStartDate,
      go: row.targetEndDate,
    }))
  } catch (caught) {
    error.value = caught.response?.data?.error || 'Unable to load project portfolio.'
  } finally {
    loading.value = false
  }
}

onMounted(loadProjects)
</script>

<style scoped>
.partner-dashboard { --ink: #101828; --muted: #667085; --line: #d9e1e8; --blue: #0073ab; background: #fff; color: var(--ink); flex: 1 0 auto; min-height: 100%; }
.partner-top { align-items: center; background: #fff; border-bottom: 1px solid var(--line); display: flex; gap: 14px; height: 46px; padding: 0 18px; }
.partner-brand { align-items: center; color: #111827; display: flex; gap: 8px; text-decoration: none; }
.brand-mark { align-items: center; background: #42b0d5; border-radius: 4px; color: #fff; display: inline-flex; font-size: 17px; height: 27px; justify-content: center; width: 27px; }
.brand-name { font-size: 14px; font-weight: 900; letter-spacing: .3px; }
.product-name { border-left: 1px solid var(--line); display: flex; flex-direction: column; line-height: 1.2; padding-left: 14px; }
.product-name strong { font-size: 12px; }.product-name small { color: var(--muted); font-size: 10px; margin-top: 2px; }
.partner-role { color: var(--blue); font-size: 11px; font-weight: 700; margin-left: auto; }
.partner-user { align-items: center; display: flex; font-size: 11px; font-weight: 600; gap: 7px; }
.avatar { align-items: center; background: #0b2a4a; border-radius: 50%; color: #fff; display: inline-flex; font-size: 9px; height: 24px; justify-content: center; width: 24px; }
.dashboard-content { margin: 0 auto; max-width: 1580px; padding: 13px 18px 26px; }
.page-heading { align-items: end; display: flex; gap: 18px; justify-content: space-between; margin-bottom: 10px; }
.page-heading h1 { font-size: 20px; line-height: 1.2; margin: 0 0 3px; }.page-heading p { color: var(--muted); font-size: 11px; margin: 0; }
.data-feedback { color: var(--muted); font-size: 11px; margin: 0 0 8px; }.data-feedback--error { color: #b42318; }.data-feedback button { background: none; border: 0; color: var(--blue); cursor: pointer; font: inherit; font-weight: 700; }
.select-field, .search-field { color: #344054; display: flex; flex-direction: column; font-size: 10px; font-weight: 700; gap: 4px; min-width: 0; }
.select-field select, .search-field input { background: #fff; border: 1px solid #c8d1d9; border-radius: 5px; color: #344054; font: 11px 'Maersk Text', sans-serif; height: 29px; min-width: 0; padding: 0 8px; }
.region-field { width: 136px; }
.metric-grid { display: grid; gap: 8px; grid-template-columns: repeat(6, minmax(0, 1fr)); margin-bottom: 10px; }
.metric { align-items: center; border: 1px solid #dfe5eb; border-radius: 7px; display: flex; gap: 9px; min-height: 70px; min-width: 0; padding: 9px 10px; }
.metric--amber { background: #fff8ed; border-color: #ffd198; }
.metric > div { min-width: 0; }.metric strong, .metric small { display: block; }.metric strong { font-size: 10px; line-height: 1.25; }.metric b { display: block; font-size: 19px; line-height: 1.1; margin: 2px 0; }.metric small { color: var(--muted); font-size: 9px; line-height: 1.25; }
.metric-icon { align-items: center; border-radius: 8px; display: flex; flex: 0 0 34px; font-size: 19px; height: 34px; justify-content: center; }
.metric-icon--blue { background: #e1effa; color: #0b5cad; }.metric-icon--green { background: #e3f5ea; color: #167a3e; }.metric-icon--amber { background: #fff0cf; color: #9a6200; }.metric-icon--red { background: #fde8e7; color: #dc2626; }.metric-icon--violet { background: #ece3fb; color: #7c3aed; }
.metric-ring, .status-donut { align-items: center; border-radius: 50%; display: flex; flex: 0 0 38px; height: 38px; justify-content: center; position: relative; width: 38px; }
.metric-ring { background: conic-gradient(#16a34a var(--value), #e8edf1 0); }.metric-ring::before { background: #fff; border-radius: 50%; content: ''; inset: 4px; position: absolute; }.metric-ring span { font-size: 9px; font-weight: 800; position: relative; z-index: 1; }
.metric-ring--empty { background: #e8edf1; }
.chart-grid { display: grid; gap: 9px; grid-template-columns: minmax(0, 1.4fr) minmax(240px, .95fr) minmax(220px, .8fr); margin-bottom: 10px; }
.panel { border: 1px solid #dfe5eb; border-radius: 7px; min-width: 0; padding: 9px 10px; }
.panel h2 { font-size: 11px; line-height: 1.2; margin: 0 0 9px; }
.panel h2 small { color: var(--muted); font-size: 9px; font-weight: 400; margin-left: 5px; }
.timeline { min-width: 350px; }.timeline-axis, .timeline-row { display: grid; grid-template-columns: minmax(110px, 1.3fr) repeat(6, minmax(0, 1fr)); }
.timeline-axis { border-bottom: 1px solid #dfe5eb; color: var(--muted); font-size: 8px; padding-bottom: 4px; }.timeline-axis span:not(:first-child) { border-left: 1px solid #edf0f3; padding-left: 4px; }
.timeline-row { align-items: center; height: 20px; }.timeline-name { font-size: 8px; overflow: hidden; padding-right: 5px; text-overflow: ellipsis; white-space: nowrap; }
.timeline-track { border-left: 1px solid #edf0f3; height: 100%; position: relative; }.timeline-track::after { border-bottom: 1px dashed #edf0f3; content: ''; left: 0; position: absolute; right: 0; top: 50%; }
.timeline-bar { border-radius: 4px; height: 8px; position: absolute; top: 6px; z-index: 1; }.timeline-bar--foundation { background: #7c3aed; }.timeline-bar--transfer { background: #42b0d5; }.timeline-marker { background: #0b2a4a; height: 9px; position: absolute; top: 5px; transform: translateX(-50%) rotate(45deg); width: 9px; z-index: 2; }
.legend { display: flex; flex-wrap: wrap; gap: 7px 12px; margin-top: 7px; }.legend span { align-items: center; color: var(--muted); display: inline-flex; font-size: 8px; gap: 4px; }.legend i { border-radius: 2px; display: inline-block; height: 7px; width: 7px; }.legend-foundation { background: #7c3aed; }.legend-transfer { background: #42b0d5; }.legend-go-live { background: #0b2a4a; transform: rotate(45deg); }
.stage-row { align-items: center; display: grid; gap: 7px; grid-template-columns: minmax(90px, 1fr) minmax(70px, 1.8fr) 28px; margin: 10px 0; }.stage-row > span:first-child { font-size: 9px; }.stage-row > b { font-size: 9px; text-align: right; }
.untracked-state, .chart-empty { color: var(--muted); font-size: 10px; margin: 18px 0; text-align: center; }
.status-chart { align-items: center; display: grid; gap: 12px; grid-template-columns: 96px minmax(0, 1fr); min-height: 118px; }
.status-donut { flex-basis: auto; height: 96px; width: 96px; }
.status-donut::before { background: #fff; border-radius: 50%; content: ''; inset: 17px; position: absolute; }
.status-donut span { align-items: center; display: flex; flex-direction: column; font-size: 9px; line-height: 1.2; position: relative; z-index: 1; }
.status-donut b { font-size: 16px; margin-bottom: 3px; }
.status-donut small { color: var(--muted); font-size: 8px; }
.status-chart ul { display: grid; gap: 9px; list-style: none; margin: 0; min-width: 0; padding: 0; }
.status-chart li { align-items: center; display: grid; font-size: 9px; gap: 6px; grid-template-columns: 8px minmax(0, 1fr) auto; list-style: none; }
.status-chart li b { font-size: 9px; text-align: right; }
.status-dot { border-radius: 50%; height: 7px; width: 7px; }
.status-dot--approved { background: #16a34a; }
.status-dot--pipeline { background: #f59e0b; }
.status-dot--not-locked { background: #98a5b3; }
.timeline-track { grid-column: 2 / -1; }
.bar-track, .readiness-track { background: #edf0f2; border-radius: 5px; display: block; height: 8px; overflow: hidden; }.stage-fill { border-radius: inherit; display: block; height: 100%; }.stage-fill--0 { background: #42b0d5; }.stage-fill--1 { background: #37a8c9; }.stage-fill--2 { background: #4ab6d1; }.stage-fill--3 { background: #3ca9c8; }.stage-fill--4 { background: #6bc1d6; }
.status-dot--pipeline, .status-label--pipeline i { background: #f59e0b; }.status-dot--not-locked, .status-label--not-locked i { background: #98a5b3; }
.table-tools { align-items: end; display: flex; flex-wrap: wrap; gap: 7px; margin: 10px 0 7px; }.search-field { width: 205px; }.table-tools .select-field { width: 128px; }.tool-button { background: #fff; border: 1px solid #c8d1d9; border-radius: 5px; color: #344054; cursor: pointer; font: 600 10px 'Maersk Text', sans-serif; height: 29px; padding: 0 10px; }.tool-button:hover { background: #f3f8fa; border-color: #8cbcd0; }.tool-spacer { flex: 1; }.tool-button--export { min-width: 70px; }
.data-table-wrap { border: 1px solid #dfe5eb; border-radius: 7px; overflow: auto; }.data-table { border-collapse: collapse; font-size: 9px; min-width: 1020px; width: 100%; }.data-table th { background: #f4f7fa; border-bottom: 1px solid #dfe5eb; color: #344054; font-size: 9px; font-weight: 700; padding: 8px 7px; text-align: left; white-space: nowrap; }.data-table td { border-bottom: 1px solid #edf0f3; height: 39px; padding: 5px 7px; white-space: nowrap; }.data-table tbody tr:last-child td { border-bottom: 0; }.data-table td strong, .data-table td small { display: block; }.data-table td strong { color: #154d71; font-size: 9px; }.data-table td small { color: var(--muted); font-size: 8px; margin-top: 2px; }.readiness-value { display: inline-block; font-weight: 700; margin-right: 8px; width: 30px; }.readiness-track { display: inline-block; height: 6px; vertical-align: middle; width: 62px; }.readiness-track i { background: #16a34a; border-radius: inherit; display: block; height: 100%; }.status-label { align-items: center; display: inline-flex; gap: 5px; }.status-label--at-risk i { background: #f59e0b; }.status-label--delayed i { background: #dc2626; }.empty-state { color: var(--muted); height: 60px !important; text-align: center; }.table-summary { color: var(--muted); font-size: 9px; margin: 6px 0 0; }
@media (max-width: 1050px) { .metric-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }.chart-grid { grid-template-columns: 1fr 1fr; }.timeline-panel { grid-column: 1 / -1; } }
@media (max-width: 700px) { .partner-top { gap: 8px; padding: 0 10px; }.brand-name { font-size: 11px; }.product-name { padding-left: 8px; }.partner-role { font-size: 9px; }.partner-user { font-size: 0; }.dashboard-content { padding: 12px 10px 24px; }.page-heading { align-items: start; flex-direction: column; }.region-field { width: 100%; }.metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }.chart-grid { grid-template-columns: 1fr; }.timeline-panel { grid-column: auto; }.table-tools { align-items: stretch; }.search-field, .table-tools .select-field { flex: 1 1 140px; width: auto; }.tool-spacer { display: none; }.status-panel { min-height: 175px; } }
.readiness-panel { display: flex; flex-direction: column; }
.readiness-panel .untracked-state { align-items: center; display: flex; flex: 1; justify-content: center; margin: 0; }
.table-summary { align-items: center; color: var(--muted); display: flex; font-size: 9px; justify-content: space-between; margin: 6px 0 0; }
.ld-pagination { align-items: center; display: flex; gap: 5px; }
.ld-pagination button, .ld-pagination b { align-items: center; background: #fff; border: 1px solid #d2dae2; border-radius: 4px; display: inline-flex; font-size: 9px; height: 23px; justify-content: center; width: 23px; }
.ld-pagination b { background: #0073ab; border-color: #0073ab; color: #fff; min-width: 46px; padding: 0 6px; white-space: nowrap; width: auto; }
.ld-pagination button:disabled { color: #98a5b3; }
</style>