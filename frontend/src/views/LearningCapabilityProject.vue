<template>
  <div class="kt-page">
    <main class="kt-content">
      <p v-if="loading" class="feedback" role="status">Loading project data...</p>
      <p v-else-if="error && !project" class="feedback feedback--error" role="alert">{{ error }} <button type="button" @click="loadProject">Retry</button></p>
      <template v-else-if="project">
        <p v-if="error" class="feedback feedback--error" role="alert">{{ error }}</p>
        <p v-if="legacyDraftAvailable" class="note note--warning" role="status">
          This browser contains an older local draft that is not in the project database.
          <button type="button" class="inline-action" :disabled="!canEdit" @click="importLegacyDraft">Import browser draft</button>
          <button type="button" class="inline-action" @click="ignoreLegacyDraft">Continue without importing</button>
        </p>
        <p v-if="!canEdit" class="note note--warning">Only the assigned Project Migration Manager or a Platform Super Admin can save L&amp;D data.</p>
        <div class="kt-heading">
          <div>
            <RouterLink class="back-link" to="/migration-success-partners/learning-development">← L&amp;D Portfolio</RouterLink>
            <div class="title-row"><span class="execute-chip">Execute</span><h1>Knowledge Transfer</h1><span class="project-chip">{{ project.migrationRequestId }}</span></div>
          </div>
          <button type="button" class="kt-button" @click="exportKnowledgeTransfer">↓ Export</button>
        </div>
        <div class="project-context">
          <span>Project: <b>{{ project.projectName }}</b></span>
          <span>Region: <b>{{ project.region || '—' }}</b></span>
          <span>Area: <b>{{ project.areas?.join(', ') || '—' }}</b></span>
          <span>Product: <b>{{ project.products?.join(', ') || '—' }}</b></span>
        </div>

        <section class="summary-tiles" aria-label="Project learning summary">
          <article><span>Approved FTEs</span><b>{{ approvedFtes }}</b><small>From project resources</small></article>
          <article><span>Cohorts planned</span><b>{{ cohorts.length }}</b><small>{{ allocatedFtes }} of {{ approvedFtes }} FTE in cohorts</small></article>
        </section>

        <nav class="kt-tabs" aria-label="Knowledge transfer sections">
          <button v-for="tab in tabs" :key="tab.id" type="button" :class="{ active: activeTab === tab.id }" @click="activeTab = tab.id">
            {{ tab.label }}<small>{{ tab.caption }}</small>
          </button>
        </nav>

        <section v-if="activeTab === 'foundation'" class="kt-section">
          <p class="note">Cohorts are managed in TAA › Resources. Their names and FTE counts are read-only here; L&amp;D maintains the foundational training plan for each cohort.</p>
          <div class="allocation" :class="{ 'allocation--short': allocatedFtes < approvedFtes }">
            <span>FTE in cohorts</span><b>{{ allocatedFtes }} / {{ approvedFtes }}</b><span>{{ allocatedFtes >= approvedFtes ? 'All approved FTEs are allocated' : `${approvedFtes - allocatedFtes} FTE not yet assigned to a cohort` }}</span>
            <span class="allocation-track"><i :style="{ width: `${allocationPercent}%` }" /></span>
          </div>
          <div class="table-wrap">
            <table class="kt-table foundation-table">
              <thead>
                <tr class="group-heading"><th></th><th colspan="3">Cohort (from Resources)</th><th colspan="4">GSC L&amp;D input — Foundational training</th><th colspan="3">Readiness timeline (calculated)</th></tr>
                <tr><th>#</th><th>Cohort</th><th>FTE</th><th>Start date</th><th>Foundational (days)</th><th>L&amp;D Trainer</th><th>Training Details</th><th>Status</th><th>KT (days)</th><th>Total (days)</th><th>Timeline</th></tr>
              </thead>
              <tbody>
                <tr v-for="(cohort, index) in cohorts" :key="cohort.name">
                  <td class="read-only">{{ index + 1 }}</td><td class="read-only"><b>{{ cohort.name }}</b></td><td class="read-only number">{{ cohort.fte }}</td>
                  <td><input v-model="cohortPlan(cohort.name).start" type="date" :disabled="!canEdit" @change="markDirty" /></td>
                  <td><input v-model="cohortPlan(cohort.name).fdays" type="number" min="0" step="0.5" placeholder="0" :disabled="!canEdit" @input="markDirty" /></td>
                  <td><input v-model="cohortPlan(cohort.name).trainer" placeholder="Trainer name" :disabled="!canEdit" @input="markDirty" /></td>
                  <td><input v-model="cohortPlan(cohort.name).details" placeholder="Modules, schedule, location…" :disabled="!canEdit" @input="markDirty" /></td>
                  <td><select v-model="cohortPlan(cohort.name).status" :disabled="!canEdit" @change="markDirty"><option v-for="status in cohortStatuses" :key="status">{{ status }}</option></select></td>
                  <td class="calculated">{{ cohortKtDays(cohort.name) }}</td><td class="calculated">{{ totalTrainingDays(cohort.name) }}</td>
                  <td><div class="training-timeline" :title="`Foundational ${cohortPlan(cohort.name).fdays || 0} days; KT ${cohortKtDays(cohort.name)} days`"><i class="foundation-segment" :style="{ width: `${timelineWidth(cohortPlan(cohort.name).fdays)}%` }" /><i class="kt-segment" :style="{ width: `${timelineWidth(cohortKtDays(cohort.name))}%` }" /></div></td>
                </tr>
                <tr v-if="!cohorts.length"><td class="empty-state" colspan="11">No cohorts yet. Create cohorts in TAA › Resources › project › Create Cohort.</td></tr>
              </tbody>
            </table>
          </div>
          <div class="legend"><span><i class="foundation-segment" />Foundational (GSC L&amp;D)</span><span><i class="kt-segment" />Knowledge transfer (Area)</span></div>
        </section>

        <section v-else-if="activeTab === 'area'" class="kt-section">
          <p class="note">{{ processSource }} Select a cohort below; Area and L&amp;D update each cohort separately.</p>
          <p v-if="assessmentError" class="note note--warning" role="status">{{ assessmentError }} <button type="button" class="inline-action" @click="loadOpportunityProcesses(String(route.params.id))">Retry Opportunity Assessment</button></p>
          <div v-if="cohorts.length" class="cohort-tabs">
            <button v-for="cohort in cohorts" :key="cohort.name" type="button" :class="{ active: selectedCohort === cohort.name }" @click="selectedCohort = cohort.name">
              {{ cohort.name }}<small>{{ cohort.fte }} FTE · {{ updatedProcessCount(cohort.name) }} / {{ processes.length }} L3 updated</small>
            </button>
          </div>
          <template v-if="selectedCohort">
            <div class="toolbar">
              <label>L2<select v-model="filters.l2"><option value="">All</option><option v-for="value in l2Options" :key="value">{{ value }}</option></select></label>
              <label>Training delivered by<select v-model="filters.deliveredBy"><option value="">All</option><option v-for="value in deliveredByOptions" :key="value">{{ value }}</option></select></label>
              <label>Training material<select v-model="filters.material"><option value="">All</option><option v-for="value in materialOptions" :key="value">{{ value }}</option></select></label>
              <button type="button" class="kt-button kt-button--primary" @click="applyFilters">View</button><button type="button" class="kt-button" @click="clearAreaFilters">Clear All</button>
              <span class="toolbar-spacer" />
              <label v-if="cohorts.length > 1" class="copy-control">Copy from cohort<select v-model="copySource"><option value="">Choose cohort…</option><option v-for="cohort in otherCohorts" :key="cohort.name" :value="cohort.name">{{ cohort.name }}</option></select></label>
              <button v-if="cohorts.length > 1" type="button" class="kt-button" :disabled="!canEdit || !copySource" @click="copyCohortEntries">Copy</button>
              <button type="button" class="kt-button" :disabled="!canEdit" @click="expandAll">Expand all</button><button type="button" class="kt-button" :disabled="!canEdit" @click="collapseAll">Collapse all</button>
            </div>
            <div class="table-wrap">
              <table class="kt-table area-table">
                <thead><tr class="group-heading"><th colspan="3">Process</th><th colspan="6">Area input — Knowledge Transfer</th></tr><tr><th></th><th>L2</th><th>L3 / L4</th><th>Training delivered by</th><th>Training material</th><th>KT duration (days)</th><th>Delivery mode</th><th>Trainer / SME</th><th>Remarks</th></tr></thead>
                <tbody>
                  <template v-for="process in visibleProcesses" :key="process.key">
                    <tr>
                      <td><button v-if="process.l4.length" type="button" class="expand-button" :disabled="!canEdit" :aria-label="`${processEntry(process).expanded ? 'Collapse' : 'Expand'} ${process.l3}`" @click="toggleProcess(process)">{{ processEntry(process).expanded ? '▾' : '▸' }}</button></td>
                      <td class="read-only">{{ process.l2 }}</td><td class="read-only"><b>{{ process.l3 }}</b></td>
                      <td v-if="!processEntry(process).expanded"><select v-model="processEntry(process).deliveredBy" :disabled="!canEdit" @change="markDirty"><option value="">—</option><option v-for="value in deliveredByOptions" :key="value">{{ value }}</option></select></td>
                      <td v-if="!processEntry(process).expanded"><select v-model="processEntry(process).material" :disabled="!canEdit" @change="markDirty"><option value="">—</option><option v-for="value in materialOptions" :key="value">{{ value }}</option></select></td>
                      <td v-if="!processEntry(process).expanded"><input v-model="processEntry(process).days" type="number" min="0" step="0.5" placeholder="0" :disabled="!canEdit" @input="markDirty" /></td>
                      <td v-if="!processEntry(process).expanded"><select v-model="processEntry(process).mode" :disabled="!canEdit" @change="markDirty"><option value="">—</option><option v-for="value in deliveryModes" :key="value">{{ value }}</option></select></td>
                      <td v-if="!processEntry(process).expanded"><input v-model="processEntry(process).trainer" placeholder="Name" :disabled="!canEdit" @input="markDirty" /></td>
                      <td v-if="!processEntry(process).expanded"><input v-model="processEntry(process).remarks" :disabled="!canEdit" @input="markDirty" /></td>
                      <td v-if="processEntry(process).expanded" colspan="2" class="read-only">Captured at L4 level</td><td v-if="processEntry(process).expanded" class="calculated">{{ processKtDays(process) }}</td><td v-if="processEntry(process).expanded" colspan="3" />
                    </tr>
                    <tr v-for="child in processEntry(process).expanded ? process.l4 : []" :key="child" class="l4-row">
                      <td /><td /><td class="read-only indent">{{ child }}</td>
                      <td><select v-model="l4Entry(process, child).deliveredBy" :disabled="!canEdit" @change="markDirty"><option value="">—</option><option v-for="value in deliveredByOptions" :key="value">{{ value }}</option></select></td>
                      <td><select v-model="l4Entry(process, child).material" :disabled="!canEdit" @change="markDirty"><option value="">—</option><option v-for="value in materialOptions" :key="value">{{ value }}</option></select></td>
                      <td><input v-model="l4Entry(process, child).days" type="number" min="0" step="0.5" placeholder="0" :disabled="!canEdit" @input="markDirty" /></td>
                      <td><select v-model="l4Entry(process, child).mode" :disabled="!canEdit" @change="markDirty"><option value="">—</option><option v-for="value in deliveryModes" :key="value">{{ value }}</option></select></td>
                      <td><input v-model="l4Entry(process, child).trainer" placeholder="Name" :disabled="!canEdit" @input="markDirty" /></td>
                      <td><input v-model="l4Entry(process, child).remarks" :disabled="!canEdit" @input="markDirty" /></td>
                    </tr>
                  </template>
                  <tr v-if="!visibleProcesses.length"><td class="empty-state" colspan="9">No L3 processes match these filters.</td></tr>
                </tbody>
              </table>
            </div>
          </template>
          <p v-else class="empty-state">No cohorts yet. Create cohorts in TAA › Resources first.</p>
        </section>

        <section v-else class="kt-section">
          <p class="note">Enter one row per FTE in each cohort. Pass mark: 80%. Foundational scores are N/A when the cohort goes straight to KT. Attach one evidence file for the whole project.</p>
          <div v-if="cohorts.length" class="cohort-tabs">
            <button v-for="cohort in cohorts" :key="cohort.name" type="button" :class="{ active: selectedScoreCohort === cohort.name }" @click="selectedScoreCohort = cohort.name">
              {{ cohort.name }}<small>{{ scoreRows(cohort).length }} FTE · {{ scoreCompletion(cohort) }} scored</small>
            </button>
          </div>
          <template v-if="selectedScoreCohort">
            <section class="score-summary" aria-label="Training score summary">
              <article><b>{{ averageScore(selectedScoreCohort, 'foundation') }}</b><span>Avg Foundational score</span></article>
              <article><b>{{ averageScore(selectedScoreCohort, 'kt') }}</b><span>Avg KT score</span></article>
              <article><b>{{ scorePassCount(selectedScoreCohort) }} / {{ scoreRowsForSelected.length }}</b><span>Passed (80% pass mark)</span></article>
            </section>
            <div class="toolbar score-toolbar">
              <label>Result<select v-model="scoreFilter"><option value="">All</option><option>Pass</option><option>Fail</option><option>Pending</option></select></label>
              <span class="toolbar-spacer" />
              <button v-if="evidence?.url && !pendingEvidenceFile" type="button" class="evidence-link" @click="downloadEvidence">{{ evidence.name }}</button>
              <span v-else-if="evidence" class="evidence-link">{{ evidence.name }} · pending upload</span>
              <button type="button" class="kt-button" :disabled="!canEdit" @click="evidenceInput?.click()">{{ evidence ? 'Replace evidence' : 'Attach evidence' }}</button>
              <button v-if="evidence" type="button" class="kt-button kt-button--danger" :disabled="!canEdit" @click="removeEvidence">Remove</button>
              <input ref="evidenceInput" type="file" accept=".xlsx,.xls,.csv,.pdf,.msg,.eml,.docx" hidden @change="attachEvidence" />
              <button type="button" class="kt-button" :disabled="!canEdit" @click="scoreImportInput?.click()">↑ Import CSV</button><input ref="scoreImportInput" type="file" accept=".csv" hidden @change="importScores" />
              <button type="button" class="kt-button" @click="exportScores">↓ Export CSV</button>
            </div>
            <div class="table-wrap">
              <table class="kt-table score-table">
                <thead><tr class="group-heading"><th colspan="3">FTE</th><th colspan="2">Scores (%)</th><th>Outcome</th></tr><tr><th>#</th><th>FTE name</th><th>APMM ID</th><th>Foundational score</th><th>KT score</th><th>Result</th></tr></thead>
                <tbody>
                  <tr v-for="(row, index) in visibleScoreRows" :key="index">
                    <td class="read-only">{{ index + 1 }}</td><td><input v-model="row.name" :placeholder="`FTE ${index + 1} name`" :disabled="!canEdit" @input="markDirty" /></td><td><input v-model="row.apmm" placeholder="APMM ID" :disabled="!canEdit" @input="markDirty" /></td>
                    <td><span v-if="isStraightToKt(selectedScoreCohort)" class="na-label">N/A — straight to KT</span><input v-else v-model="row.foundation" type="number" min="0" max="100" placeholder="—" :disabled="!canEdit" @change="clampScore(row, 'foundation')" /></td>
                    <td><input v-model="row.kt" type="number" min="0" max="100" placeholder="—" :disabled="!canEdit" @change="clampScore(row, 'kt')" /></td>
                    <td><span class="result-pill" :class="`result-pill--${scoreResult(selectedScoreCohort, row).toLowerCase()}`">{{ scoreResult(selectedScoreCohort, row) }}</span></td>
                  </tr>
                  <tr v-if="!visibleScoreRows.length"><td class="empty-state" colspan="6">No FTEs match this result filter.</td></tr>
                </tbody>
              </table>
            </div>
          </template>
          <p v-else class="empty-state">No cohorts yet. Create cohorts in TAA › Resources first.</p>
        </section>

        <footer class="kt-footer">
          <span role="status">{{ dirty ? '● Unsaved changes' : success }}</span>
          <span class="toolbar-spacer" />
          <button type="button" class="kt-button" :disabled="loading" @click="reloadProject">↻ Reload</button>
          <button type="button" class="kt-button kt-button--primary" :disabled="!dirty || !canEdit || saving || (legacyDraftAvailable && !legacyDraftHandled)" @click="saveProject">{{ saving ? 'Saving…' : 'Save' }}</button>
        </footer>
        <div v-if="notice" class="kt-toast" role="status">{{ notice }}</div>
      </template>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { onBeforeRouteLeave, RouterLink, useRoute } from 'vue-router'
import axios from 'axios'
import { useTopbarBackLink } from '../composables/useTopbarBackLink.js'

useTopbarBackLink('/migration-success-partners/learning-development', 'Back to L&D')

const route = useRoute()
const project = ref(null)
const record = ref(null)
const loading = ref(false)
const error = ref('')
const success = ref('')
const dirty = ref(false)
const saving = ref(false)
const notice = ref('')
const activeTab = ref('foundation')
const selectedCohort = ref('')
const selectedScoreCohort = ref('')
const copySource = ref('')
const scoreFilter = ref('')
const evidence = ref(null)
const pendingEvidenceFile = ref(null)
const removeEvidencePending = ref(false)
const learningRecord = ref({ revision: 0, saved: false, evidence: null })
const learningAccess = ref({ edit: false })
const legacyDraft = ref(null)
const legacyDraftAvailable = ref(false)
const legacyDraftHandled = ref(true)
const evidenceInput = ref(null)
const scoreImportInput = ref(null)
const filters = reactive({ l2: '', deliveredBy: '', material: '' })
const appliedFilters = reactive({ l2: '', deliveredBy: '', material: '' })
const cohortStatuses = ['Planned', 'In Progress', 'Completed']
const deliveredByOptions = ['Area', 'GSC L&D', 'Not able to deliver']
const materialOptions = ['Ready', 'In Progress', 'Not Started']
const deliveryModes = ['Classroom', 'Virtual', 'Shadowing', 'Reverse shadowing', 'Self-paced']
const tabs = [
  { id: 'foundation', label: 'GSC L&D — Foundational Training', caption: 'Foundation per cohort' },
  { id: 'area', label: 'Area — Knowledge Transfer', caption: 'Training design & delivery per L3, per cohort' },
  { id: 'scores', label: 'Training Scores', caption: 'Scores per FTE' },
]
const sampleProcesses = [
  { l2: 'Order Management', l3: 'Create Order', l4: ['Review booking request', 'Check CMD data and create booking', 'Send booking confirmation'] },
  { l2: 'Order Management', l3: 'Amend Order', l4: ['Amend booking details', 'Amend cargo details'] },
  { l2: 'Order Management', l3: 'Cancel Order', l4: ['Cancel booking — customer request', 'Cancel booking — carrier initiated'] },
  { l2: 'Documentation', l3: 'Issue Transport Document', l4: ['Draft B/L creation', 'Final B/L release', 'Manifest submission'] },
  { l2: 'Billing & Invoicing', l3: 'Create Invoice', l4: ['Rate check', 'Invoice creation', 'Invoice dispute handling'] },
  { l2: 'Job Costing', l3: 'Job Costing — General', l4: ['Update cost accruals', 'Close job'] },
].map(item => ({ ...item, key: `${item.l2}|${item.l3}` }))
const processes = reactive([...sampleProcesses])
const processSource = ref('Sample data — no saved Opportunity Assessment tasks marked Migratable to GSC were found.')
const assessmentError = ref('')
const training = ref({ plans: {}, kt: {}, scores: {}, processCount: sampleProcesses.length })
const cohorts = computed(() => {
  const grouped = new Map()
  for (const row of record.value?.rows || []) {
    const name = String(row.cohort || '').trim()
    if (!name) continue
    if (!grouped.has(name)) grouped.set(name, [])
    grouped.get(name).push(row)
  }
  return [...grouped.entries()].map(([name, rows]) => ({ name, rows, fte: rows.length, members: rows }))
})
const approvedFtes = computed(() => Number(record.value?.source?.population ?? route.query.approvedFte ?? 0))
const allocatedFtes = computed(() => cohorts.value.reduce((sum, cohort) => sum + cohort.fte, 0))
const allocationPercent = computed(() => approvedFtes.value ? Math.min(100, allocatedFtes.value / approvedFtes.value * 100) : 0)
const l2Options = computed(() => [...new Set(processes.map(item => item.l2))])
const selectedScore = computed(() => cohorts.value.find(item => item.name === selectedScoreCohort.value))
const scoreRowsForSelected = computed(() => selectedScore.value ? scoreRows(selectedScore.value) : [])
const visibleProcesses = computed(() => processes.filter((process) =>
  (!appliedFilters.l2 || process.l2 === appliedFilters.l2) &&
  (!appliedFilters.deliveredBy || processMatches(process, 'deliveredBy', appliedFilters.deliveredBy)) &&
  (!appliedFilters.material || processMatches(process, 'material', appliedFilters.material))
))
const otherCohorts = computed(() => cohorts.value.filter(cohort => cohort.name !== selectedCohort.value))
const visibleScoreRows = computed(() => scoreRowsForSelected.value
  .map((row, index) => ({ row, index, result: scoreResult(selectedScoreCohort.value, row) }))
  .filter(item => !scoreFilter.value || item.result === scoreFilter.value)
  .map(item => item.row))
const storageId = computed(() => project.value?.migrationRequestId || String(route.query.project || route.params.id))
const legacyStorageKey = computed(() => `wpm_kt_v2_${storageId.value}`)
const legacyEvidenceKey = computed(() => `wpm_kt_evidence_${storageId.value}`)
const learningCapabilityUrl = computed(() => `/api/migration-dashboard/projects/${encodeURIComponent(route.params.id)}/learning-capability/`)
const canEdit = computed(() => Boolean(learningAccess.value.edit))
let noticeTimer
let hydrating = false

function cohortPlan(name) {
  training.value.plans[name] ||= { start: '', fdays: '', trainer: '', details: '', status: 'Planned' }
  return training.value.plans[name]
}
function cohortKtDays(name) {
  return processes.reduce((sum, process) => {
    const entry = processEntryFor(name, process)
    if (entry.expanded) return sum + process.l4.reduce((total, child) => total + (Number(l4EntryFor(name, process, child).days) || 0), 0)
    return sum + (entry.deliveredBy === 'Not able to deliver' ? 0 : Number(entry.days) || 0)
  }, 0)
}
function totalTrainingDays(name) { return (Number(cohortPlan(name).fdays) || 0) + cohortKtDays(name) }
function processKtDays(process) {
  const entry = processEntry(process)
  if (!entry.expanded) return Number(entry.days) || 0
  return process.l4.reduce((sum, child) => {
    const item = l4Entry(process, child)
    return sum + (item.deliveredBy === 'Not able to deliver' ? 0 : Number(item.days) || 0)
  }, 0)
}
function timelineWidth(days) {
  const max = Math.max(1, ...cohorts.value.map(cohort => totalTrainingDays(cohort.name)))
  return Math.min(100, (Number(days) || 0) / max * 100)
}
function processEntryFor(name, process) {
  training.value.kt[name] ||= {}
  training.value.kt[name][process.key] ||= { deliveredBy: '', material: '', days: '', mode: '', trainer: '', remarks: '', expanded: false, l4: {} }
  return training.value.kt[name][process.key]
}
function processEntry(process) { return processEntryFor(selectedCohort.value, process) }
function l4EntryFor(name, process, child) {
  const entry = processEntryFor(name, process)
  entry.l4[child] ||= { deliveredBy: entry.deliveredBy, material: entry.material, days: '', mode: entry.mode, trainer: entry.trainer, remarks: '' }
  return entry.l4[child]
}
function l4Entry(process, child) { return l4EntryFor(selectedCohort.value, process, child) }
function processMatches(process, key, value) {
  const parent = processEntry(process)
  const entries = parent.expanded ? process.l4.map(child => l4Entry(process, child)) : [parent]
  return entries.some(entry => entry[key] === value)
}
function applyFilters() { Object.assign(appliedFilters, filters) }
function clearAreaFilters() {
  Object.assign(filters, { l2: '', deliveredBy: '', material: '' })
  applyFilters()
}
function toggleProcess(process) {
  const entry = processEntry(process)
  if (entry.expanded && process.l4.some(child => {
    const row = l4Entry(process, child)
    return row.days || row.remarks
  }) && !window.confirm('Collapse to L3? L4 entries are kept.')) return
  entry.expanded = !entry.expanded
  markDirty()
}
function expandAll() {
  for (const process of processes) {
    if (!process.l4.length) continue
    const entry = processEntry(process)
    entry.expanded = true
    for (const child of process.l4) l4Entry(process, child)
  }
  markDirty()
}
function collapseAll() {
  for (const process of processes) processEntry(process).expanded = false
  markDirty()
}
function updatedProcessCount(name) {
  return processes.filter(process => {
    const entry = processEntryFor(name, process)
    return entry.expanded ? process.l4.every(child => l4EntryFor(name, process, child).deliveredBy) : Boolean(entry.deliveredBy)
  }).length
}
function copyCohortEntries() {
  if (!copySource.value) return
  training.value.kt[selectedCohort.value] = JSON.parse(JSON.stringify(training.value.kt[copySource.value] || {}))
  markDirty()
  showNotice(`Copied entries from ${copySource.value}.`)
}
function scoreRows(cohort) {
  training.value.scores[cohort.name] ||= []
  const rows = training.value.scores[cohort.name]
  while (rows.length < cohort.fte) rows.push({ name: '', apmm: '', foundation: '', kt: '' })
  rows.length = cohort.fte
  cohort.members.forEach((member, index) => {
    if (rows[index] && !rows[index].apmm && member.apmmId) rows[index].apmm = member.apmmId
  })
  return rows
}
function isStraightToKt(name) { return !(Number(cohortPlan(name).fdays) > 0) }
function scoreResult(name, row) {
  const required = isStraightToKt(name) ? [row.kt] : [row.foundation, row.kt]
  if (required.some(value => value === '' || value == null)) return 'Pending'
  return required.every(value => Number(value) >= 80) ? 'Pass' : 'Fail'
}
function scoreCompletion(cohort) {
  const rows = scoreRows(cohort)
  return `${rows.filter(row => scoreResult(cohort.name, row) !== 'Pending').length} / ${rows.length}`
}
function scorePassCount(name) { return scoreRowsFor(name).filter(row => scoreResult(name, row) === 'Pass').length }
function scoreRowsFor(name) { const cohort = cohorts.value.find(item => item.name === name); return cohort ? scoreRows(cohort) : [] }
function averageScore(name, key) {
  if (key === 'foundation' && isStraightToKt(name)) return 'N/A'
  const values = scoreRowsFor(name).map(row => row[key]).filter(value => value !== '' && value != null).map(Number)
  return values.length ? `${(values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(1)}%` : '—'
}
function clampScore(row, key) {
  if (row[key] !== '') row[key] = String(Math.max(0, Math.min(100, Number(row[key]) || 0)))
  markDirty()
}
function showNotice(message) {
  notice.value = message
  window.clearTimeout(noticeTimer)
  noticeTimer = window.setTimeout(() => { notice.value = '' }, 2600)
}
function markDirty() {
  if (!hydrating) {
    dirty.value = true
    success.value = ''
  }
}
function parseSavedState(saved) {
  const state = saved && typeof saved === 'object' && !Array.isArray(saved) ? saved : {}
  return {
    plans: state.plans && typeof state.plans === 'object' && !Array.isArray(state.plans) ? state.plans : {},
    kt: state.kt && typeof state.kt === 'object' && !Array.isArray(state.kt) ? state.kt : {},
    scores: state.scores && typeof state.scores === 'object' && !Array.isArray(state.scores) ? state.scores : {},
    processCount: Number.isInteger(state.processCount) ? state.processCount : processes.length,
  }
}
async function importLegacyDraft() {
  const draft = legacyDraft.value
  if (!draft || !canEdit.value) return
  let importedEvidence = null
  let importedFile = null
  if (draft.evidence && !draft.evidence.data) {
    error.value = 'The saved browser evidence does not contain file data and cannot be imported.'
    return
  }
  if (draft.evidence?.data) {
    try {
      const response = await fetch(draft.evidence.data)
      if (!response.ok) throw new Error('The saved browser evidence could not be opened.')
      const blob = await response.blob()
      if (blob.size > 5 * 1024 * 1024) throw new Error('The saved browser evidence is larger than 5 MB.')
      const name = String(draft.evidence.name || 'training-evidence')
      importedFile = new File([blob], name, { type: blob.type || 'application/octet-stream' })
      importedEvidence = { name, size: importedFile.size, pending: true }
    } catch (caught) {
      error.value = caught.message || 'Unable to import the browser evidence file.'
      return
    }
  }
  training.value = parseSavedState(draft.state)
  evidence.value = importedEvidence
  pendingEvidenceFile.value = importedFile
  removeEvidencePending.value = false
  legacyDraftAvailable.value = false
  legacyDraftHandled.value = true
  markDirty()
  showNotice('Browser draft loaded. Save it to store it in the project database.')
}
function ignoreLegacyDraft() {
  legacyDraftAvailable.value = false
  legacyDraftHandled.value = true
}
function loadLegacyBrowserDraft() {
  legacyDraft.value = null
  legacyDraftAvailable.value = false
  legacyDraftHandled.value = true
  try {
    const savedState = localStorage.getItem(legacyStorageKey.value)
    const savedEvidence = localStorage.getItem(legacyEvidenceKey.value)
    if (!savedState && !savedEvidence) return
    legacyDraft.value = {
      state: savedState ? JSON.parse(savedState) : {},
      evidence: savedEvidence ? JSON.parse(savedEvidence) : null,
    }
    legacyDraftAvailable.value = true
    legacyDraftHandled.value = false
  } catch (caught) {
    error.value = caught.message || 'An older browser draft could not be read.'
  }
}
function processesFromAssessment(state) {
  const taskRows = Array.isArray(state?.task) ? state.task : []
  const groupedRows = Array.isArray(state?.catGroups)
    ? state.catGroups.flatMap(group => Array.isArray(group.rows) ? group.rows : [])
    : []
  const catalogueRows = groupedRows.length ? groupedRows : Array.isArray(state?.cat) ? state.cat : []
  const grouped = new Map()
  for (const row of [...taskRows, ...catalogueRows]) {
    if (String(row.mig ?? row.mgsc ?? '').trim().toLowerCase() !== 'yes') continue
    const l2 = String(row.l2 || '').trim()
    const l3 = String(row.l3 || '').trim()
    if (!l2 || !l3) continue
    const key = `${l2}|${l3}`
    if (!grouped.has(key)) grouped.set(key, { key, l2, l3, l4: [] })
    const l4 = String(row.l4 || '').trim()
    const children = grouped.get(key).l4
    if (l4 && !children.includes(l4)) children.push(l4)
  }
  return [...grouped.values()]
}
async function loadOpportunityProcesses(projectId) {
  assessmentError.value = ''
  try {
    const { data } = await axios.get(`/api/migration-dashboard/projects/${encodeURIComponent(projectId)}/opportunity-assessment/task-scope/`)
    const loadedProcesses = processesFromAssessment(data.state)
    processes.splice(0, processes.length, ...(loadedProcesses.length ? loadedProcesses : sampleProcesses))
    processSource.value = loadedProcesses.length
      ? 'L3 processes are sourced from Opportunity Assessment tasks marked Migratable to GSC = Yes.'
      : 'Sample data — no Opportunity Assessment tasks are currently marked Migratable to GSC.'
  } catch (caught) {
    processes.splice(0, processes.length, ...sampleProcesses)
    processSource.value = 'Sample data is shown because Opportunity Assessment could not be loaded.'
    assessmentError.value = caught.response?.data?.error || 'Unable to load Opportunity Assessment processes.'
  }
}
async function loadProject() {
  const id = String(route.params.id || '')
  if (!id) {
    error.value = 'Project ID is missing from the route.'
    return
  }
  loading.value = true
  error.value = ''
  project.value = null
  try {
    const { data } = await axios.get(`/api/migration-dashboard/projects/${encodeURIComponent(id)}/resources/`)
    await loadOpportunityProcesses(id)
    const { data: learningData } = await axios.get(learningCapabilityUrl.value)
    project.value = data
    record.value = data
    learningRecord.value = learningData
    learningAccess.value = learningData.permissions || { edit: false }
    hydrating = true
    training.value = parseSavedState(learningData.state)
    evidence.value = learningData.evidence || null
    pendingEvidenceFile.value = null
    removeEvidencePending.value = false
    loadLegacyBrowserDraft()
    if (learningData.saved || error.value) {
      legacyDraftAvailable.value = false
      legacyDraftHandled.value = true
    }
    training.value.processCount = processes.length
    selectedCohort.value = cohorts.value[0]?.name || ''
    selectedScoreCohort.value = selectedCohort.value
    await nextTick()
    dirty.value = false
    hydrating = false
  } catch (caught) {
    error.value = caught.response?.data?.error || 'Unable to load project resources.'
  } finally {
    loading.value = false
  }
}
async function reloadProject() {
  if (dirty.value && !window.confirm('Discard unsaved Knowledge Transfer changes?')) return
  success.value = ''
  await loadProject()
}
async function saveProject() {
  saving.value = true
  error.value = ''
  try {
    const payload = new FormData()
    payload.append('state', JSON.stringify(training.value))
    payload.append('revision', String(learningRecord.value.revision || 0))
    if (pendingEvidenceFile.value) payload.append('evidence', pendingEvidenceFile.value)
    if (removeEvidencePending.value) payload.append('removeEvidence', 'true')
    const { data } = await axios.put(learningCapabilityUrl.value, payload)
    learningRecord.value = data
    learningAccess.value = data.permissions || learningAccess.value
    evidence.value = data.evidence || null
    pendingEvidenceFile.value = null
    removeEvidencePending.value = false
    legacyDraftAvailable.value = false
    legacyDraftHandled.value = true
    dirty.value = false
    success.value = 'Changes saved to the project database.'
    showNotice('Saved')
  } catch (caught) {
    error.value = caught.response?.data?.error || 'Unable to save L&D data to the project database.'
  } finally {
    saving.value = false
  }
}
function parseCsvLine(line) {
  const values = []
  let value = ''
  let quoted = false
  for (let index = 0; index < line.length; index += 1) {
    const character = line[index]
    if (quoted && character === '"' && line[index + 1] === '"') { value += '"'; index += 1 }
    else if (character === '"') quoted = !quoted
    else if (character === ',' && !quoted) { values.push(value); value = '' }
    else value += character
  }
  values.push(value)
  return values
}
function exportCsv(filename, rows) {
  const csv = rows.map(row => row.map(value => `"${String(value ?? '').replaceAll('"', '""')}"`).join(',')).join('\r\n')
  const url = URL.createObjectURL(new Blob(['\ufeff', csv], { type: 'text/csv;charset=utf-8' }))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
function exportScores() {
  const rows = [['Cohort', '#', 'FTE name', 'APMM ID', 'Foundational score', 'KT score', 'Result']]
  for (const cohort of cohorts.value) scoreRows(cohort).forEach((row, index) => rows.push([
    cohort.name, index + 1, row.name, row.apmm, isStraightToKt(cohort.name) ? 'N/A' : row.foundation, row.kt, scoreResult(cohort.name, row),
  ]))
  exportCsv(`Training_Scores_${storageId.value}.csv`, rows)
}
async function importScores(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  const text = (await file.text()).replace(/^\uFEFF/, '')
  const lines = text.split(/\r?\n/).filter(Boolean).map(parseCsvLine)
  const header = lines.shift() || []
  const column = name => header.findIndex(value => value.trim() === name)
  if (column('Cohort') < 0 || column('#') < 0) {
    showNotice('Import failed — export a score CSV first and use it as the template.')
    return
  }
  let updated = 0
  let skipped = 0
  for (const values of lines) {
    const cohort = cohorts.value.find(item => item.name === values[column('Cohort')]?.trim())
    const index = Number(values[column('#')]) - 1
    if (!cohort || !Number.isInteger(index) || index < 0 || index >= cohort.fte) { skipped += 1; continue }
    const row = scoreRows(cohort)[index]
    for (const [heading, key] of [['FTE name', 'name'], ['APMM ID', 'apmm'], ['Foundational score', 'foundation'], ['KT score', 'kt']]) {
      const position = column(heading)
      if (position < 0 || (key === 'foundation' && isStraightToKt(cohort.name))) continue
      const value = values[position]?.trim() || ''
      row[key] = ['foundation', 'kt'].includes(key) && value && value !== 'N/A'
        ? String(Math.max(0, Math.min(100, Number(value) || 0)))
        : value === 'N/A' ? '' : value
    }
    updated += 1
  }
  if (updated) markDirty()
  showNotice(`Import: ${updated} FTE updated${skipped ? `, ${skipped} rows skipped` : ''}.`)
}
function exportKnowledgeTransfer() {
  const rows = [['Cohort', 'FTE', 'Start date', 'Foundational days', 'L&D Trainer', 'Training Details', 'Status', 'KT days', 'Total days']]
  cohorts.value.forEach(cohort => rows.push([
    cohort.name, cohort.fte, cohortPlan(cohort.name).start, cohortPlan(cohort.name).fdays || 0, cohortPlan(cohort.name).trainer,
    cohortPlan(cohort.name).details, cohortPlan(cohort.name).status, cohortKtDays(cohort.name), totalTrainingDays(cohort.name),
  ]))
  rows.push([], ['Cohort', 'Level', 'L2', 'L3', 'L4', 'Training delivered by', 'Training material', 'KT duration (days)', 'Delivery mode', 'Trainer / SME', 'Remarks'])
  cohorts.value.forEach(cohort => processes.forEach(process => {
    const parent = processEntryFor(cohort.name, process)
    if (parent.expanded) process.l4.forEach(child => {
      const entry = l4EntryFor(cohort.name, process, child)
      rows.push([cohort.name, 'L4', process.l2, process.l3, child, entry.deliveredBy, entry.material, entry.days, entry.mode, entry.trainer, entry.remarks])
    })
    else rows.push([cohort.name, 'L3', process.l2, process.l3, '', parent.deliveredBy, parent.material, parent.days, parent.mode, parent.trainer, parent.remarks])
  }))
  exportCsv(`Knowledge_Transfer_${storageId.value}.csv`, rows)
}
function attachEvidence(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  if (file.size > 5 * 1024 * 1024) {
    showNotice('File is larger than 5 MB.')
    return
  }
  pendingEvidenceFile.value = file
  removeEvidencePending.value = false
  evidence.value = { name: file.name, size: file.size, pending: true }
  markDirty()
}
function removeEvidence() {
  if (!window.confirm('Remove the evidence file?')) return
  pendingEvidenceFile.value = null
  removeEvidencePending.value = Boolean(learningRecord.value.evidence)
  evidence.value = null
  markDirty()
}
async function downloadEvidence() {
  if (!evidence.value?.url) return
  try {
    const { data } = await axios.get(evidence.value.url, { responseType: 'blob' })
    const url = URL.createObjectURL(data)
    const link = document.createElement('a')
    link.href = url
    link.download = evidence.value.name
    link.click()
    URL.revokeObjectURL(url)
  } catch (caught) {
    error.value = caught.response?.data?.error || 'Unable to download the evidence file.'
  }
}
function beforeUnload(event) {
  if (!dirty.value) return
  event.preventDefault()
  event.returnValue = ''
}
onBeforeRouteLeave(() => !dirty.value || window.confirm('Discard unsaved Knowledge Transfer changes?'))
watch(() => route.params.id, loadProject)
onMounted(() => {
  window.addEventListener('beforeunload', beforeUnload)
  loadProject()
})
onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', beforeUnload)
  window.clearTimeout(noticeTimer)
})
</script>

<style scoped>
.kt-page { --ink: #101828; --muted: #667085; --line: #d9e1e8; --blue: #0073ab; background: #fff; color: var(--ink); flex: 1 0 auto; min-height: 100%; }
.kt-content { margin: 0 auto; max-width: 1580px; padding: 18px; }
.kt-heading, .title-row, .project-context, .toolbar, .kt-footer { align-items: center; display: flex; gap: 10px; }
.kt-heading { justify-content: space-between; margin-bottom: 12px; }
.back-link { color: var(--blue); font-size: 11px; font-weight: 600; text-decoration: none; }
.title-row { margin-top: 6px; }.title-row h1 { font-size: 20px; margin: 0; }
.execute-chip, .project-chip { background: #e1effa; border-radius: 12px; color: #005a87; font-size: 10px; font-weight: 700; padding: 4px 9px; }
.project-chip { background: #eef2f6; color: #344054; }
.project-context { background: #fbfcfd; border: 1px solid var(--line); border-radius: 7px; color: var(--muted); flex-wrap: wrap; font-size: 10px; margin-bottom: 12px; padding: 9px 12px; }
.project-context b { color: var(--ink); }.summary-tiles { display: grid; gap: 10px; grid-template-columns: repeat(2, minmax(0, 1fr)); margin-bottom: 12px; max-width: 560px; }
.summary-tiles article, .score-summary article { border: 1px solid var(--line); border-radius: 8px; display: grid; gap: 4px; padding: 10px 13px; }
.summary-tiles span, .score-summary span { color: var(--muted); font-size: 11px; }.summary-tiles b { font-size: 20px; }.summary-tiles small { color: var(--muted); font-size: 10px; }
.kt-tabs, .cohort-tabs { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0 12px; }
.kt-tabs button, .cohort-tabs button { background: #fff; border: 1px solid var(--line); border-bottom: 2px solid transparent; border-radius: 7px; cursor: pointer; display: flex; flex-direction: column; font: inherit; font-size: 11px; font-weight: 600; gap: 3px; padding: 8px 12px; text-align: left; }
.kt-tabs button.active, .cohort-tabs button.active { background: #eaf4fb; border-color: var(--blue); color: #005a87; }
.kt-tabs small, .cohort-tabs small { color: var(--muted); font-size: 9px; font-weight: 400; }
.kt-section { min-width: 0; }.note { background: #f2f8fc; border: 1px solid #b6d7ee; border-radius: 7px; font-size: 11px; margin: 0 0 10px; padding: 9px 12px; }.note--warning { background: #fff8ee; border-color: #f5c58c; }
.allocation { align-items: center; border: 1px solid var(--line); border-radius: 7px; display: grid; font-size: 10px; gap: 8px; grid-template-columns: auto auto minmax(90px, 1fr) auto; margin-bottom: 10px; padding: 8px 10px; }.allocation--short { background: #fff8ee; border-color: #f5c58c; }.allocation-track, .training-timeline { background: #eef0f2; border-radius: 5px; display: block; height: 8px; overflow: hidden; }.allocation-track i { background: #16a34a; display: block; height: 100%; }.allocation--short .allocation-track i { background: #f59e0b; }
.table-wrap { border: 1px solid var(--line); border-radius: 7px; overflow: auto; }.kt-table { border-collapse: collapse; font-size: 10px; min-width: 100%; width: 100%; }.kt-table th, .kt-table td { border-bottom: 1px solid #e7ebf0; border-right: 1px solid #edf0f3; padding: 5px 7px; vertical-align: middle; }.kt-table thead th { background: #f3f6f9; font-size: 10px; min-width: 105px; position: sticky; text-align: left; top: 0; white-space: nowrap; z-index: 1; }.kt-table thead .group-heading th { background: #e9f1f8; color: #005a87; top: 0; }.kt-table tbody tr:last-child td { border-bottom: 0; }.kt-table input, .kt-table select, .toolbar select { background: #fff; border: 1px solid #b9c3cd; border-radius: 4px; color: var(--ink); font: inherit; min-height: 28px; min-width: 90px; padding: 4px 6px; width: 100%; }.kt-table input:disabled, .kt-table select:disabled { background: #f7f8fa; color: #667085; }.foundation-table { min-width: 1450px; }.area-table { min-width: 1450px; }.score-table { min-width: 900px; }.read-only { background: #f7f8fa; }.number { font-weight: 700; text-align: right; }.calculated { background: #eef8f1; font-weight: 700; text-align: right; }.training-timeline { display: flex; min-width: 150px; }.training-timeline i { display: block; height: 100%; }.foundation-segment { background: #7c3aed; }.kt-segment { background: #0073ab; }.legend { color: var(--muted); display: flex; flex-wrap: wrap; font-size: 10px; gap: 14px; margin: 8px 0; }.legend span { align-items: center; display: inline-flex; gap: 5px; }.legend i { border-radius: 2px; display: inline-block; height: 9px; width: 9px; }
.toolbar { align-items: end; flex-wrap: wrap; margin: 10px 0; }.toolbar label { color: #344054; display: grid; font-size: 10px; font-weight: 700; gap: 4px; min-width: 140px; }.toolbar select { min-width: 150px; }.toolbar-spacer { flex: 1; }.copy-control { min-width: 150px; }.kt-button { align-items: center; background: #fff; border: 1px solid #b9c3cd; border-radius: 5px; color: #344054; cursor: pointer; display: inline-flex; font: 600 10px 'Maersk Text', sans-serif; gap: 5px; justify-content: center; min-height: 29px; padding: 0 10px; text-decoration: none; white-space: nowrap; }.kt-button:hover:not(:disabled) { background: #f3f8fa; }.kt-button:disabled { cursor: not-allowed; opacity: .5; }.kt-button--primary { background: var(--blue); border-color: var(--blue); color: #fff; }.kt-button--danger { color: #b42318; }.expand-button { background: none; border: 0; color: var(--blue); cursor: pointer; font-size: 15px; }.l4-row .indent { padding-left: 24px; }.empty-state { color: var(--muted); padding: 22px !important; text-align: center; white-space: normal !important; }
.score-summary { display: grid; gap: 10px; grid-template-columns: repeat(3, minmax(0, 1fr)); margin: 10px 0; max-width: 700px; }.score-summary b { font-size: 18px; }.score-summary article { align-content: center; grid-template-columns: 1fr; }.score-toolbar { align-items: end; }.evidence-link { background: none; border: 0; color: var(--blue); cursor: pointer; font: inherit; font-size: 10px; max-width: 200px; overflow: hidden; padding: 0; text-align: left; text-decoration: underline; text-overflow: ellipsis; white-space: nowrap; }.na-label { color: var(--muted); font-size: 10px; }.result-pill { border-radius: 10px; display: inline-block; font-size: 10px; padding: 3px 8px; }.result-pill--pass { background: #e3f5ea; color: #167a3e; }.result-pill--fail { background: #fde8e7; color: #b42318; }.result-pill--pending { background: #eef0f2; color: #475467; }
.inline-action { background: none; border: 0; color: var(--blue); cursor: pointer; font: inherit; font-weight: 700; }
.kt-footer { border-top: 1px solid var(--line); color: var(--muted); font-size: 10px; margin-top: 12px; padding: 10px 0; }.feedback { color: var(--muted); font-size: 11px; }.feedback--error { color: #b42318; }.feedback button { background: none; border: 0; color: var(--blue); cursor: pointer; font: inherit; font-weight: 700; }.kt-toast { background: #0b2a4a; border-radius: 7px; bottom: 20px; color: #fff; left: 50%; padding: 9px 15px; position: fixed; transform: translateX(-50%); z-index: 10; }
@media (max-width: 700px) { .kt-content { padding: 12px 10px; }.kt-heading { align-items: flex-end; }.title-row { align-items: flex-start; flex-wrap: wrap; }.title-row h1 { font-size: 17px; }.allocation { grid-template-columns: auto auto; }.allocation-track { grid-column: 1 / -1; grid-row: 2; }.summary-tiles { grid-template-columns: 1fr 1fr; }.score-summary { grid-template-columns: 1fr; }.toolbar-spacer { display: none; } }
</style>
