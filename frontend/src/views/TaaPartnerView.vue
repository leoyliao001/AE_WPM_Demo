<template>
  <div class="partner-dashboard taa-page">
    <main class="taa-content">
      <div class="taa-crumb"><RouterLink to="/migration-success-partners">TAA</RouterLink><span aria-hidden="true">›</span><b>TAA View</b><span class="updated">Live project data</span></div>
      <h1>TAA View</h1>
      <p v-if="loading" class="taa-feedback" role="status">Loading project portfolio...</p>
      <p v-else-if="error" class="taa-feedback taa-feedback--error" role="alert">{{ error }} <button type="button" @click="loadProjects">Retry</button></p>

      <section class="taa-metrics" aria-label="Talent acquisition metrics">
        <article class="taa-metric"><span class="taa-icon taa-icon--blue">▦</span><div><strong>Approved Projects</strong><b>{{ approvedProjects.length }}</b><small>Projects with approved FTEs</small></div></article>
        <article class="taa-metric"><span class="taa-icon taa-icon--green">♙</span><div><strong>Approved FTEs</strong><b>{{ approvedFtes }}</b><small>FTEs in approved projects</small></div></article>
        <article class="taa-metric"><span class="taa-icon taa-icon--amber">◷</span><div><strong>Pipeline Projects</strong><b>{{ pipelineProjects.length }}</b><small>Awaiting approval</small></div></article>
        <article class="taa-metric taa-metric--amber"><span class="taa-icon taa-icon--amber">♧</span><div><strong>Pipeline FTEs</strong><b>{{ pipelineFtes }}</b><small>FTEs in pipeline projects</small></div></article>
      </section>

      <section class="taa-charts" aria-label="Talent acquisition portfolio charts">
        <article class="taa-panel timeline-panel">
          <h2>Onboarding Timeline <small>PID creation → tentative joining month</small></h2>
          <div class="timeline">
            <div class="timeline-axis"><span></span><span v-for="month in timelineMonths" :key="month.key">{{ month.label }}</span></div>
            <div v-for="project in visibleTimelineProjects" :key="project.id" class="timeline-row">
              <span class="timeline-name" :title="project.name">{{ project.name }}</span>
              <span class="timeline-track"><i v-if="project.hiringStart && project.joinDate" class="timeline-bar timeline-bar--hiring" :style="barStyle(project.hiringStart, project.joinDate)" /><i v-if="project.joinDate" class="timeline-marker" :style="markerStyle(project.joinDate)" /></span>
            </div>
            <p v-if="!visibleTimelineProjects.length" class="timeline-empty">No saved tentative joining dates.</p>
          </div>
          <div class="taa-legend"><span><i class="legend-hiring" />PID creation to tentative joining</span><span><i class="legend-marker" />Tentative joining month</span></div>
        </article>

        <article class="taa-panel progress-panel">
          <h2>Hiring Progress <small>Saved resource rows</small></h2>
          <div v-for="stage in hiringStages" :key="stage.label" class="hiring-stage"><span>{{ stage.label }}</span><span class="stage-track"><i :style="{ width: `${stage.percent}%`, background: stage.color }" /></span><b>{{ stage.value }} / {{ resourceRows }}</b></div>
          <p>{{ resourceRows }} saved resource rows</p>
        </article>

        <article class="taa-panel hiring-status-panel">
          <h2>Hiring Status <small>Saved resource rows</small></h2>
          <div class="hiring-status">
            <div class="hiring-donut" :style="hiringDonutStyle"><span><b>{{ resourceRows }}</b>Resource<br />rows</span></div>
            <ul><li v-for="item in hiringStatuses" :key="item.label"><i :style="{ background: item.color }" /><span>{{ item.label }}</span><b>{{ item.value }}</b></li></ul>
          </div>
        </article>
      </section>

      <section class="taa-filters" aria-label="Filter projects">
        <label>Product<select v-model="filters.product"><option value="">All</option><option v-for="item in products" :key="item">{{ item }}</option></select></label>
        <label>Region<select v-model="filters.region"><option value="">All</option><option v-for="item in regions" :key="item">{{ item }}</option></select></label>
        <label>Area<select v-model="filters.area"><option value="">All</option><option v-for="item in areas" :key="item">{{ item }}</option></select></label>
        <label>GSC Site<select v-model="filters.site"><option value="">All</option><option v-for="item in sites" :key="item">{{ item }}</option></select></label>
        <label>Project Status<select v-model="filters.status"><option value="">All</option><option v-for="item in statuses" :key="item">{{ item }}</option></select></label>
      </section>
      <section class="taa-tools">
        <label class="taa-search"><span class="sr-only">Search by project name</span><input v-model="filters.search" type="search" placeholder="Search by Project name" /></label>
        <div><button type="button" class="taa-button" @click="clearFilters">Reset</button><button type="button" class="taa-button" @click="exportProjects">Export</button><button type="button" class="taa-button taa-button--primary" :disabled="!selectedProject" @click="openSelected">Open Project</button></div>
      </section>

      <div class="taa-table-wrap">
        <table class="taa-table">
          <thead><tr><th class="check-cell"><input v-model="allSelected" type="checkbox" aria-label="Select all projects" /></th><th>Project Name</th><th>Project ID</th><th>Product</th><th>Region</th><th>Area</th><th>GSC Site</th><th>Approved FTEs</th><th>Pipeline FTEs</th><th>Tentative Joining Month</th><th>Project Status</th><th>Action</th></tr></thead>
          <tbody><tr v-for="project in paginatedProjects" :key="project.id" :class="{ 'taa-row--selected': selectedIds.has(project.id) }">
            <td class="check-cell"><input :checked="selectedIds.has(project.id)" type="checkbox" :aria-label="`Select ${project.name}`" @change="toggleProject(project.id)" /></td>
            <td><strong>{{ project.name }}</strong></td><td>{{ project.requestId }}</td><td>{{ project.products.join(', ') }}</td><td>{{ project.region }}</td><td>{{ project.areas.join(', ') }}</td><td>{{ project.sites.join(', ') }}</td><td>{{ project.approved ?? '—' }}</td><td>{{ project.pipeline ?? '—' }}</td><td>{{ project.joinMonth }}</td>
            <td><span class="project-status" :class="`project-status--${project.status.toLowerCase()}`">{{ project.status }}</span></td><td><button class="view-button" type="button" @click="openProject(project)">View</button></td>
          </tr><tr v-if="!filteredProjects.length"><td colspan="12" class="empty-state">No projects match these filters.</td></tr></tbody>
        </table>
      </div>
      <footer class="taa-table-footer"><span>{{ selectedIds.size }} rows selected</span><span>Showing {{ pageStart }}-{{ pageEnd }} of {{ filteredProjects.length }} records</span><div class="pagination"><button type="button" aria-label="Previous page" title="Previous page" :disabled="currentPage === 1" @click="currentPage -= 1">‹</button><b aria-live="polite">{{ currentPage }} / {{ pageCount }}</b><button type="button" aria-label="Next page" title="Next page" :disabled="currentPage === pageCount" @click="currentPage += 1">›</button></div></footer>
      <div v-if="notice" class="taa-toast" role="status">{{ notice }}</div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import axios from 'axios'

const projects = ref([])
const loading = ref(false)
const error = ref('')
const statuses = ['Approved', 'Pipeline', 'Not locked']
const filters = reactive({ search: '', product: '', region: '', area: '', site: '', status: '' })
const selectedIds = ref(new Set())
const notice = ref('')
const currentPage = ref(1)
const pageSize = 10
const products = computed(() => [...new Set(projects.value.flatMap(project => project.products))].sort())
const regions = computed(() => [...new Set(projects.value.map(project => project.region).filter(Boolean))].sort())
const areas = computed(() => [...new Set(projects.value.flatMap(project => project.areas))].sort())
const sites = computed(() => [...new Set(projects.value.flatMap(project => project.sites))].sort())
const filteredProjects = computed(() => projects.value.filter((project) => {
  const query = filters.search.trim().toLowerCase()
  return (!query || `${project.name} ${project.requestId}`.toLowerCase().includes(query)) && (!filters.product || project.products.includes(filters.product)) && (!filters.region || project.region === filters.region) && (!filters.area || project.areas.includes(filters.area)) && (!filters.site || project.sites.includes(filters.site)) && (!filters.status || project.status === filters.status)
}))
const pageCount = computed(() => Math.max(1, Math.ceil(filteredProjects.value.length / pageSize)))
const paginatedProjects = computed(() => filteredProjects.value.slice((currentPage.value - 1) * pageSize, currentPage.value * pageSize))
const pageStart = computed(() => filteredProjects.value.length ? (currentPage.value - 1) * pageSize + 1 : 0)
const pageEnd = computed(() => Math.min(currentPage.value * pageSize, filteredProjects.value.length))
const approvedProjects = computed(() => filteredProjects.value.filter((project) => project.status === 'Approved'))
const pipelineProjects = computed(() => filteredProjects.value.filter((project) => project.status === 'Pipeline'))
const approvedFtes = computed(() => approvedProjects.value.reduce((sum, project) => sum + (project.approved ?? 0), 0))
const pipelineFtes = computed(() => pipelineProjects.value.reduce((sum, project) => sum + (project.pipeline ?? 0), 0))
const resourceRows = computed(() => filteredProjects.value.reduce((sum, project) => sum + project.resourceSummary.total, 0))
const hiringStatusColors = { Onboarded: '#16a34a', 'In Progress': '#0073ab', 'At Risk': '#dc2626', Pending: '#cbd5df', 'Not Applicable': '#98a5b3' }
const hiringStatuses = computed(() => Object.entries(hiringStatusColors).map(([label, color]) => ({
  label,
  color,
  value: filteredProjects.value.reduce((sum, project) => sum + (project.resourceSummary.hiringStatusCounts[label] || 0), 0)
})))
const visibleTimelineProjects = computed(() => filteredProjects.value.filter(project => project.joinDate).slice(0, 8))
const selectedProject = computed(() => filteredProjects.value.find((project) => selectedIds.value.has(project.id)))
const allSelected = computed({
  get: () => filteredProjects.value.length > 0 && filteredProjects.value.every((project) => selectedIds.value.has(project.id)),
  set: (checked) => { selectedIds.value = checked ? new Set(filteredProjects.value.map((project) => project.id)) : new Set() }
})
watch(filteredProjects, () => { currentPage.value = 1 })
const hiringStages = computed(() => [
  { label: 'GSC PIDs created', value: filteredProjects.value.reduce((sum, project) => sum + project.resourceSummary.pidCreated, 0), percent: resourceRows.value ? filteredProjects.value.reduce((sum, project) => sum + project.resourceSummary.pidCreated, 0) / resourceRows.value * 100 : 0, color: '#0073ab' },
  { label: 'Requisitions raised', value: filteredProjects.value.reduce((sum, project) => sum + project.resourceSummary.requisitionsRaised, 0), percent: resourceRows.value ? filteredProjects.value.reduce((sum, project) => sum + project.resourceSummary.requisitionsRaised, 0) / resourceRows.value * 100 : 0, color: '#7c3aed' },
  { label: 'Onboarded', value: filteredProjects.value.reduce((sum, project) => sum + project.resourceSummary.onboarded, 0), percent: resourceRows.value ? filteredProjects.value.reduce((sum, project) => sum + project.resourceSummary.onboarded, 0) / resourceRows.value * 100 : 0, color: '#16a34a' }
])
const hiringDonutStyle = computed(() => {
  let stop = 0
  const segments = hiringStatuses.value.map((status) => {
    const start = stop
    stop += resourceRows.value ? status.value / resourceRows.value * 100 : 0
    return `${status.color} ${start}% ${stop}%`
  })
  return { background: resourceRows.value ? `conic-gradient(${segments.join(',')})` : '#e8edf1' }
})
const now = new Date()
const timelineStart = new Date(now.getFullYear(), now.getMonth() - 2, 1)
const timelineEnd = new Date(now.getFullYear(), now.getMonth() + 6, 1)
const timelineMonths = Array.from({ length: 8 }, (_, index) => {
  const date = new Date(now.getFullYear(), now.getMonth() - 2 + index, 1)
  return { key: date.toISOString(), label: date.toLocaleDateString('en-GB', { month: 'short', year: '2-digit' }) }
})

function monthDate(value) { return value ? `${value}-01` : '' }
function monthLabel(value) {
  if (!value) return '—'
  return new Date(`${value}-01T00:00:00`).toLocaleDateString('en-GB', { month: 'short', year: '2-digit' })
}
function firstMonth(months) { return Object.keys(months || {}).sort()[0] || '' }
function datePosition(value) {
  if (!value) return 0
  const timestamp = new Date(`${value}T00:00:00`).getTime()
  return Math.max(0, Math.min(100, (timestamp - timelineStart.getTime()) / (timelineEnd.getTime() - timelineStart.getTime()) * 100))
}
function barStyle(start, end) { const left = datePosition(start); return { left: `${left}%`, width: `${Math.max(0, datePosition(end) - left)}%` } }
function markerStyle(date) { return { left: `${datePosition(date)}%` } }
function toggleProject(id) {
  const next = new Set(selectedIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  selectedIds.value = next
}
function clearFilters() {
  Object.assign(filters, { search: '', product: '', region: '', area: '', site: '', status: '' })
  selectedIds.value = new Set()
}
function showNotice(message) {
  notice.value = message
  window.clearTimeout(showNotice.timer)
  showNotice.timer = window.setTimeout(() => { notice.value = '' }, 2400)
}
function openProject(project) { showNotice(`${project.name} - project workspace is not available in this demo.`) }
function openSelected() { if (selectedProject.value) openProject(selectedProject.value) }
function exportProjects() {
  const headings = ['Project Name', 'Project ID', 'Product', 'Region', 'Area', 'GSC Site', 'Approved FTEs', 'Pipeline FTEs', 'Tentative Joining Month', 'Project Status']
  const rows = filteredProjects.value.map((project) => [project.name, project.requestId, project.products.join(', '), project.region, project.areas.join(', '), project.sites.join(', '), project.approved ?? '', project.pipeline ?? '', project.joinMonth, project.status])
  const csv = [headings, ...rows].map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(',')).join('\r\n')
  const link = document.createElement('a')
  link.href = URL.createObjectURL(new Blob(['\ufeff', csv], { type: 'text/csv;charset=utf-8' }))
  link.download = 'TAA_Project_Portfolio.csv'
  link.click()
  URL.revokeObjectURL(link.href)
  showNotice('Portfolio exported.')
}

async function loadProjects() {
  loading.value = true
  error.value = ''
  try {
    const response = await axios.get('/api/migration-dashboard/resources/')
    projects.value = response.data.rows.map(row => {
      const summary = row.resourceSummary || {}
      const startMonth = firstMonth(summary.pidCreationMonths)
      const joinMonth = firstMonth(summary.tentativeDojMonths)
      return {
        id: row.projectId,
        requestId: row.migrationRequestId || row.projectId,
        name: row.projectName,
        products: row.products || [],
        region: row.region || '',
        areas: row.areas || [],
        sites: row.sites || [],
        approved: row.approvedFte,
        pipeline: row.pipelineFte,
        status: row.approvalStatus,
        joinMonth: monthLabel(joinMonth),
        hiringStart: monthDate(startMonth),
        joinDate: monthDate(joinMonth),
        resourceSummary: {
          total: summary.total || 0,
          hiringStatusCounts: summary.hiringStatusCounts || {},
          pidCreated: summary.pidCreated || 0,
          requisitionsRaised: summary.requisitionsRaised || 0,
          onboarded: summary.onboarded || 0,
        },
      }
    })
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
.taa-top { align-items: center; background: #fff; border-bottom: 1px solid var(--line); display: flex; gap: 22px; height: 47px; padding: 0 18px; }
.taa-brand { align-items: center; color: #102d49; display: flex; flex: 0 0 210px; gap: 9px; text-decoration: none; }.taa-logo { align-items: center; background: #0073ab; border-radius: 5px; color: #fff; display: flex; font-size: 17px; font-weight: 800; height: 28px; justify-content: center; width: 28px; }.taa-brand b, .taa-brand small { display: block; }.taa-brand b { font-size: 12px; }.taa-brand small { color: var(--muted); font-size: 9px; margin-top: 2px; }
.global-search { flex: 1; max-width: 520px; }.global-search input, .taa-search input { background: #fff; border: 1px solid #cbd5df; border-radius: 6px; color: #344054; font: 11px 'Maersk Text', sans-serif; height: 30px; padding: 0 10px; width: 100%; }.taa-user { align-items: center; display: flex; font-size: 10px; gap: 8px; margin-left: auto; }.notification { font-size: 20px; position: relative; }.notification i { align-items: center; background: #dc2626; border-radius: 50%; color: #fff; display: flex; font-size: 8px; font-style: normal; height: 14px; justify-content: center; position: absolute; right: -5px; top: -3px; width: 14px; }
.avatar { align-items: center; background: #0b2a4a; border-radius: 50%; color: #fff; display: flex; font-size: 9px; height: 24px; justify-content: center; width: 24px; }
.taa-content { margin: 0 auto; max-width: 1580px; padding: 12px 18px 42px; position: relative; }.taa-crumb { align-items: center; border-bottom: 1px solid #e6ebef; color: var(--muted); display: flex; font-size: 9px; gap: 5px; padding-bottom: 9px; }.taa-crumb a { color: #12648d; text-decoration: none; }.taa-crumb b { color: #164b69; }.updated { margin-left: auto; }.taa-content > h1 { font-size: 21px; margin: 11px 0 10px; }
.taa-metrics { display: grid; gap: 9px; grid-template-columns: repeat(4, minmax(0, 1fr)); margin-bottom: 10px; }.taa-metric { align-items: center; border: 1px solid #dfe5eb; border-radius: 8px; box-shadow: 0 2px 5px rgba(16,24,40,.05); display: flex; gap: 10px; min-height: 76px; min-width: 0; padding: 10px 12px; }.taa-metric--amber { background: #fff8ed; border-color: #ffd198; }.taa-metric > div { min-width: 0; }.taa-metric strong, .taa-metric small { display: block; }.taa-metric strong { font-size: 10px; }.taa-metric b { display: block; font-size: 20px; line-height: 1.1; margin: 3px 0; }.taa-metric small { color: var(--muted); font-size: 9px; }
.taa-icon { align-items: center; border-radius: 9px; display: flex; flex: 0 0 35px; font-size: 19px; height: 35px; justify-content: center; }.taa-icon--blue { background: #e1effa; color: #0b5cad; }.taa-icon--green { background: #e3f5ea; color: #167a3e; }.taa-icon--amber { background: #fff0cf; color: #9a6200; }
.taa-charts { display: grid; gap: 9px; grid-template-columns: minmax(0, 1.5fr) minmax(240px, 1fr) minmax(230px, .88fr); margin-bottom: 12px; }.taa-panel { border: 1px solid #dfe5eb; border-radius: 7px; box-shadow: 0 1px 3px rgba(16,24,40,.04); min-width: 0; padding: 10px 11px; }.taa-panel h2 { font-size: 11px; margin: 0 0 11px; }.taa-panel h2 small { color: var(--muted); font-size: 9px; font-weight: 400; margin-left: 4px; }
.timeline { min-width: 360px; }.timeline-axis, .timeline-row { display: grid; grid-template-columns: minmax(112px, 1.35fr) repeat(8, minmax(0, 1fr)); }.timeline-axis { border-bottom: 1px solid #dfe5eb; color: var(--muted); font-size: 8px; padding-bottom: 4px; }.timeline-axis span:not(:first-child) { border-left: 1px solid #edf0f3; padding-left: 3px; }.timeline-row { align-items: center; height: 18px; }.timeline-name { font-size: 8px; overflow: hidden; padding-right: 5px; text-overflow: ellipsis; white-space: nowrap; }.timeline-track { border-left: 1px solid #edf0f3; height: 100%; position: relative; }.timeline-track::after { border-bottom: 1px dashed #edf0f3; content: ''; left: 0; position: absolute; right: 0; top: 50%; }.timeline-bar { border-radius: 4px; height: 7px; position: absolute; top: 5px; z-index: 1; }.timeline-bar--hiring { background: #0073ab; }.timeline-bar--ramp { background: #16a34a; }.timeline-bar--pipeline { background: repeating-linear-gradient(45deg, #c7d2dc 0 3px, #e9eef2 3px 6px); }.timeline-marker { background: #0b2a4a; height: 8px; position: absolute; top: 4px; transform: translateX(-50%) rotate(45deg); width: 8px; z-index: 2; }.timeline-marker--pipeline { background: #98a5b3; }
.taa-legend { display: flex; flex-wrap: wrap; gap: 6px 10px; margin-top: 8px; }.taa-legend span { align-items: center; color: var(--muted); display: inline-flex; font-size: 8px; gap: 4px; }.taa-legend i { border-radius: 2px; display: inline-block; height: 7px; width: 8px; }.legend-hiring { background: #0073ab; }.legend-ramp { background: #16a34a; }.legend-pipeline { background: repeating-linear-gradient(45deg, #c7d2dc 0 2px, #e9eef2 2px 4px); }.legend-marker { background: #0b2a4a; transform: rotate(45deg); }
.hiring-stage { align-items: center; display: grid; gap: 8px; grid-template-columns: minmax(100px, 1fr) minmax(70px, 1.6fr) 48px; margin: 14px 0; }.hiring-stage span:first-child { font-size: 9px; }.hiring-stage > b { font-size: 9px; text-align: right; }.stage-track { background: #edf0f2; border-radius: 5px; height: 8px; overflow: hidden; }.stage-track i { border-radius: inherit; display: block; height: 100%; }.progress-panel p { color: var(--muted); font-size: 8px; margin: 16px 0 0; }
.hiring-status { align-items: center; display: flex; gap: 14px; justify-content: center; min-height: 145px; }.hiring-donut { align-items: center; border-radius: 50%; display: flex; flex: 0 0 112px; height: 112px; justify-content: center; position: relative; width: 112px; }.hiring-donut::before { background: #fff; border-radius: 50%; content: ''; inset: 17px; position: absolute; }.hiring-donut span { font-size: 8px; line-height: 1.3; position: relative; text-align: center; z-index: 1; }.hiring-donut b { display: block; font-size: 16px; margin-bottom: 3px; }.hiring-status ul { display: grid; gap: 9px; list-style: none; margin: 0; padding: 0; }.hiring-status li { align-items: center; display: grid; font-size: 9px; gap: 6px; grid-template-columns: 8px minmax(86px, 1fr) 18px; }.hiring-status li i { border-radius: 50%; height: 7px; width: 7px; }.hiring-status li b { font-size: 9px; }
.taa-filters { align-items: end; display: flex; flex-wrap: wrap; gap: 7px; margin: 8px 0; }.taa-filters label { color: #344054; display: flex; flex-direction: column; font-size: 9px; font-weight: 700; gap: 3px; min-width: 112px; }.taa-filters select { background: #fff; border: 1px solid #c8d1d9; border-radius: 5px; color: #344054; font: 10px 'Maersk Text', sans-serif; height: 28px; padding: 0 7px; }
.taa-tools { align-items: center; display: flex; gap: 8px; justify-content: space-between; margin-bottom: 7px; }.taa-search { width: 265px; }.taa-tools > div { display: flex; gap: 6px; }.taa-button { background: #fff; border: 1px solid #c8d1d9; border-radius: 5px; color: #344054; cursor: pointer; font: 600 10px 'Maersk Text', sans-serif; height: 29px; padding: 0 12px; }.taa-button:hover:not(:disabled) { background: #f3f8fa; border-color: #8cbcd0; }.taa-button:disabled { cursor: not-allowed; opacity: .5; }.taa-button--primary { background: #0073ab; border-color: #0073ab; color: #fff; }
.taa-table-wrap { border: 1px solid #dfe5eb; border-radius: 7px; overflow: auto; }.taa-table { border-collapse: collapse; font-size: 9px; min-width: 1030px; width: 100%; }.taa-table th { background: #f4f7fa; border-bottom: 1px solid #dfe5eb; color: #344054; font-size: 8px; padding: 8px 6px; text-align: left; white-space: nowrap; }.taa-table td { border-bottom: 1px solid #edf0f3; height: 37px; padding: 5px 6px; white-space: nowrap; }.taa-table tbody tr:last-child td { border-bottom: 0; }.taa-table tbody tr:hover { background: #f9fbfc; }.taa-table .taa-row--selected { background: #eff8fc; }.check-cell { text-align: center !important; width: 28px; }.check-cell input { accent-color: #0073ab; height: 13px; width: 13px; }.taa-table td strong { color: #154d71; font-size: 9px; }.project-status { background: #e3f5ea; border-radius: 10px; color: #167a3e; display: inline-block; font-size: 8px; font-weight: 700; padding: 3px 7px; }.project-status--pipeline { background: #fff0cf; color: #9a6200; }.view-button { background: none; border: 0; color: #0073ab; cursor: pointer; font: 700 9px 'Maersk Text', sans-serif; }.view-button:hover { text-decoration: underline; }.empty-state { color: var(--muted); height: 56px !important; text-align: center; }
.taa-table-footer { align-items: center; background: #fff; border: 1px solid #e3e8ed; border-radius: 6px; bottom: 0; display: flex; font-size: 9px; gap: 16px; justify-content: flex-end; margin-top: 7px; min-height: 34px; padding: 5px 8px; }.taa-table-footer > span:first-child { color: var(--muted); margin-right: auto; }.pagination { align-items: center; display: flex; gap: 5px; }.pagination button, .pagination b { align-items: center; background: #fff; border: 1px solid #d2dae2; border-radius: 4px; display: inline-flex; font-size: 9px; height: 23px; justify-content: center; width: 23px; }.pagination b { background: #0073ab; border-color: #0073ab; color: #fff; min-width: 46px; padding: 0 6px; white-space: nowrap; width: auto; }.pagination button:disabled { color: #98a5b3; }.taa-toast { background: #0b2a4a; border-radius: 6px; bottom: 48px; color: #fff; font-size: 11px; left: 50%; padding: 9px 14px; position: fixed; transform: translateX(-50%); z-index: 20; }.sr-only { height: 1px; margin: -1px; overflow: hidden; position: absolute; clip: rect(0,0,0,0); white-space: nowrap; width: 1px; }
.timeline-track { grid-column: 2 / -1; }
@media (max-width: 1100px) { .taa-charts { grid-template-columns: 1fr 1fr; }.timeline-panel { grid-column: 1 / -1; }.taa-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 700px) { .taa-top { gap: 10px; padding: 0 10px; }.taa-brand { flex-basis: auto; }.global-search { display: none; }.taa-user { font-size: 0; }.taa-content { padding: 10px 10px 36px; }.updated { font-size: 8px; }.taa-charts { grid-template-columns: 1fr; }.timeline-panel { grid-column: auto; }.timeline { overflow: hidden; }.taa-filters label { flex: 1 1 30%; min-width: 90px; }.taa-search { flex: 1; width: auto; }.taa-tools { align-items: stretch; flex-direction: column; }.taa-tools > div { justify-content: flex-end; }.hiring-status { justify-content: flex-start; }.taa-table-footer { flex-wrap: wrap; justify-content: center; }.taa-table-footer > span:first-child { flex-basis: 100%; text-align: center; } }
</style>