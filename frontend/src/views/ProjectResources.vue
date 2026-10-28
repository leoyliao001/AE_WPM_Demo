<template>
  <PageShell title="Resources" :show-heading="false" :back-to="backTo" back-label="Back to Toll Gates" full-width>
    <div class="pa-page">
      <div v-if="loading" class="pa-panel" role="status">Loading project resources...</div>
      <div v-if="error" class="pa-feedback pa-feedback--error" role="alert">{{ error }} <button v-if="!record" class="pa-text-button" @click="load">Retry</button></div>
      <div v-if="success" class="pa-feedback pa-feedback--success" role="status">{{ success }}</div>
      <template v-if="record && !loading">
        <header class="pa-hero">
          <div class="pa-heading">
            <div><p class="pa-eyebrow">Initiate / People &amp; capacity</p><h1>Resources</h1><span class="pa-status" :class="`pa-status--${record.status}`">{{ record.status.replaceAll('_', ' ') }}</span></div>
            <div class="pa-actions">
              <router-link class="pa-link" to="/resources">All resource projects</router-link>
              <mc-button appearance="neutral" variant="outlined" label="Export" :disabled="!!busy" @click="exportData" />
              <mc-button v-if="!record.frozen && (record.permissions.edit || record.permissions.area)" appearance="neutral" variant="outlined" label="Save draft" :disabled="!!busy" @click="save()" />
              <mc-button v-if="!record.frozen && record.permissions.edit" appearance="primary" label="Confirm resources" :disabled="!!busy || !ready" @click="save('submit')" />
            </div>
          </div>
          <div class="pa-project-meta"><strong>{{ record.projectName }}</strong><span>{{ record.migrationRequestId }}</span><span>{{ record.products.join(', ') || 'No product' }} / {{ record.region }}</span><span>{{ dirty ? 'Unsaved changes' : record.updatedAt ? `Last saved ${dateTime(record.updatedAt)}` : 'Not yet saved' }}</span></div>
          <div class="pa-metrics">
            <article class="pa-metric"><span>Scope capacity</span><strong>{{ record.source.population ?? '—' }} <small>FTE</small></strong><small>Locked final Scope FTE</small></article>
            <article class="pa-metric"><span>Resource positions</span><strong>{{ record.rows.length }}</strong><small>One row per project FTE</small></article>
            <article class="pa-metric"><span>Onboarding completed</span><strong>{{ onboarded }}</strong><small>Actual DOJ and APMM ID recorded</small></article>
            <article class="pa-metric" :class="{ 'pa-metric--risk': atRisk }"><span>At risk</span><strong>{{ atRisk }}</strong><small>Across all hiring positions</small></article>
            <article class="pa-metric"><span>Area PIDs submitted</span><strong>{{ areaSubmitted }} / {{ record.rows.length }}</strong><small>Submitted Area records are read-only</small></article>
          </div>
        </header>
        <div v-if="!record.source.ready" class="pa-feedback">Complete and submit Scope before confirming Resources. Draft positions can be prepared now. <router-link class="pa-link" :to="`/migration-dashboard/${projectId}/scope-statement`">Open Scope</router-link></div>
        <div v-if="record.sourceChanged" class="pa-feedback">Scope changed since the last save. Reconcile resource positions with the current locked FTE before confirming.</div>
        <div v-if="record.frozen" class="pa-feedback">Confirmed resources are frozen. Reopen with a reason before making changes.</div>
        <div class="pa-tabs" role="tablist" aria-label="Resource views"><button v-for="item in tabs" :key="item.id" role="tab" :aria-selected="tab === item.id" @click="tab = item.id">{{ item.label }}</button></div>
        <section class="pa-panel">
          <div class="pa-section-heading"><div><p class="pa-eyebrow">{{ tab === 'execution' ? 'Project coordination' : tab === 'area' ? 'Sending area' : 'Recruitment & onboarding' }}</p><h2>{{ tabs.find(item => item.id === tab).label }}</h2></div>
            <div class="pa-actions">
              <mc-button v-if="tab === 'execution' && canEdit" appearance="neutral" variant="outlined" label="Add position" @click="addRow" />
              <mc-button v-if="tab === 'execution' && canEdit" appearance="neutral" variant="outlined" label="Import Excel" @click="fileInput.click()" />
              <input ref="fileInput" type="file" accept=".xlsx" hidden @change="importData" />
              <mc-button v-if="tab === 'area' && canEditArea" appearance="primary" label="Submit Area details" :disabled="!record.rows.length" @click="save('submit_area')" />
            </div>
          </div>
          <p v-if="tab === 'execution'">Maintain GSC site, hiring type, language and PID details here. Hiring and onboarding fields sync from HR / TAA. For Efficiency, Actual DOJ means the date the FTE is onboarded onto this project.</p>
          <p v-else-if="tab === 'area'">Intake location is prefilled for new positions. Enter Area PID, Area APMM ID and release date, then submit to secure the sending-area details.</p>
          <p v-else>HR / TAA updates are saved to the same positions and reflected in Execution. Efficiency positions do not require recruitment; their Actual DOJ and APMM ID are maintained in Execution.</p>
          <p class="pa-note">Execution and HR / TAA editing: Requestor, locked WPM Focal or Resources administrator. Area editing: the same users or a locked Area POC. Other Project Team members have read-only access. Reminder links open an email draft to the project Requestor.</p>
          <div class="pa-toolbar">
            <input v-model="query" type="search" placeholder="Search positions, PID, APMM ID..." aria-label="Search resources" />
            <select v-model="siteFilter" aria-label="Filter GSC site"><option value="">All GSC sites</option><option v-for="site in sites" :key="site">{{ site }}</option></select>
            <select v-model="statusFilter" aria-label="Filter hiring status"><option value="">All statuses</option><option v-for="status in [...record.hiringStatuses, 'Not Applicable']" :key="status">{{ status }}</option></select>
            <button class="pa-text-button" @click="resetFilters">Reset filters</button>
          </div>
          <div class="pa-scroll"><table class="pa-table">
            <thead><tr><th><input type="checkbox" aria-label="Select visible resource rows" :checked="visibleRows.length > 0 && visibleRows.every(row => selected.includes(row.id))" @change="selectAll($event.target.checked)" /></th><th v-for="column in columns" :key="column.key">{{ column.label }}</th><th>Action</th></tr></thead>
            <tbody><tr v-for="row in visibleRows" :key="row.id">
              <td><input v-model="selected" type="checkbox" :value="row.id" :aria-label="`Select position ${row.gscPid || row.id}`" /></td>
              <td v-for="column in columns" :key="column.key">
                <select v-if="column.options && cellEditable(row, column.key)" v-model="row[column.key]" :aria-label="column.label" @change="column.key === 'hiringType' && changeHiringType(row)">
                  <option value="">Select</option><option v-for="option in column.options" :key="option">{{ option }}</option>
                </select>
                <input v-else-if="cellEditable(row, column.key)" v-model="row[column.key]" :type="column.date ? 'date' : 'text'" :aria-label="column.label" maxlength="500" />
                <span v-else-if="column.key === 'hiringStatus'" class="pa-status" :class="{ 'pa-status--at_risk': row.hiringStatus === 'At Risk', 'pa-status--confirmed': row.hiringStatus === 'Onboarded' }">{{ row.hiringStatus }}</span>
                <span v-else>{{ row[column.key] || '—' }}</span>
              </td>
              <td><span v-if="tab === 'area'" class="pa-status">{{ row.areaLockedAt ? 'Submitted' : 'Draft' }}</span><button v-else-if="tab === 'execution'" class="pa-text-button" :disabled="!canEdit || !!row.areaLockedAt" @click="removeRow(row)">Remove</button><span v-else>Synced to Execution</span></td>
            </tr><tr v-if="!visibleRows.length"><td :colspan="columns.length + 2" class="pa-empty">{{ record.rows.length ? 'No matching positions.' : 'No positions yet. Add a position or import the Execution sheet from an exported workbook.' }}</td></tr></tbody>
          </table></div>
          <div class="pa-section-heading" style="margin-top: 18px"><span class="pa-note">{{ visibleRows.length }} visible · {{ selected.length }} selected · {{ record.rows.length }} total</span><a v-if="selected.length" class="pa-link" :href="reminderLink">Compose reminder for selected positions</a></div>
          <div v-if="tab === 'area' && areaSubmitted && canEditArea" class="pa-field"><label>Reason to reopen submitted Area details<textarea v-model="areaReason" maxlength="2000" rows="2" /></label><mc-button appearance="neutral" variant="outlined" label="Reopen Area details" :disabled="!areaReason.trim()" @click="reopenArea" /></div>
        </section>
        <section v-if="record.frozen && record.permissions.edit" class="pa-panel"><h2>Reopen Resources</h2><label class="pa-field">Revision reason<textarea v-model="reason" maxlength="2000" rows="2" /></label><mc-button appearance="neutral" variant="outlined" label="Reopen" :disabled="!!busy || !reason.trim()" @click="reopen" /></section>
        <details class="pa-audit"><summary>Audit history · {{ record.auditLog.length }} events</summary><div class="pa-scroll"><table class="pa-table"><thead><tr><th>Revision</th><th>Action</th><th>User</th><th>Timestamp</th><th>Reason</th></tr></thead><tbody><tr v-for="entry in [...record.auditLog].reverse()" :key="entry.revision"><td>{{ entry.revision }}</td><td>{{ entry.action }}</td><td>{{ entry.by }}</td><td>{{ dateTime(entry.at) }}</td><td>{{ entry.reason }}</td></tr></tbody></table></div></details>
      </template>
    </div>
  </PageShell>
</template>

<script setup>
import { computed, ref } from 'vue'
import { read, utils } from 'xlsx'
import PageShell from '../components/PageShell.vue'
import { useProjectArtefact } from '../composables/useProjectArtefact.js'
import { exportArtefact } from '../utils/projectArtefactExport.js'
import '@maersk-global/mds-components-core/mc-button'
import '../styles/projectArtefacts.css'

const { record, projectId, backTo, loading, busy, error, success, dirty, editable, load, save } = useProjectArtefact('resources')
const tab = ref('execution')
const tabs = [{ id: 'execution', label: 'Execution' }, { id: 'area', label: 'Area' }, { id: 'hr', label: 'HR / TAA' }]
const query = ref('')
const siteFilter = ref('')
const statusFilter = ref('')
const selected = ref([])
const reason = ref('')
const areaReason = ref('')
const fileInput = ref(null)
const canEdit = computed(() => editable.value && record.value.permissions.edit)
const canEditArea = computed(() => editable.value && record.value.permissions.area)
const sites = computed(() => [...new Set([...(record.value?.sites || []), ...(record.value?.rows || []).map(row => row.site)].filter(Boolean))])
const onboarded = computed(() => record.value?.rows.filter(row => row.actualDoj && row.apmmId).length || 0)
const atRisk = computed(() => record.value?.rows.filter(row => row.hiringStatus === 'At Risk').length || 0)
const areaSubmitted = computed(() => record.value?.rows.filter(row => row.areaLockedAt).length || 0)
const baseColumns = computed(() => [
  { key: 'site', label: 'GSC Site', options: [...new Set([...record.value.siteOptions, ...sites.value])] }, { key: 'hiringType', label: 'Hiring Type', options: record.value.hiringTypes },
  { key: 'language', label: 'Language', options: record.value.languages }, { key: 'pidCreationDate', label: 'PID Creation Date', date: true },
  { key: 'gscPid', label: 'GSC PID' },
])
const hrColumns = computed(() => [
  { key: 'requisitionId', label: 'Requisition ID' }, { key: 'hiringStatus', label: 'Hiring Status', options: record.value.hiringStatuses },
  { key: 'remarks', label: 'Remarks' }, { key: 'tentativeDoj', label: 'Tentative DOJ', date: true },
  { key: 'actualDoj', label: 'Actual DOJ', date: true }, { key: 'apmmId', label: 'APMM ID' },
])
const areaColumns = [
  { key: 'region', label: 'Region' }, { key: 'area', label: 'Area' }, { key: 'country', label: 'Country' },
  { key: 'areaPid', label: 'Area PID' }, { key: 'areaApmmId', label: 'Area APMM ID' }, { key: 'releaseDate', label: 'Release Date', date: true },
]
const columns = computed(() => tab.value === 'area' ? areaColumns : tab.value === 'hr' ? [...baseColumns.value, ...hrColumns.value] :
  [...baseColumns.value, { key: 'deletedPid', label: 'Deleted PID for Efficiency' }, ...hrColumns.value])
const visibleRows = computed(() => (record.value?.rows || []).filter(row =>
  (tab.value !== 'hr' || row.hiringType !== 'Efficiency') && (!siteFilter.value || row.site === siteFilter.value) &&
  (!statusFilter.value || row.hiringStatus === statusFilter.value) && Object.values(row).join(' ').toLowerCase().includes(query.value.toLowerCase())))
const ready = computed(() => record.value?.source.ready && record.value.rows.length === record.value.source.population &&
  record.value.rows.every(row => row.site && row.language && row.gscPid && row.pidCreationDate && row.areaLockedAt && row.actualDoj && row.apmmId &&
    (row.hiringType === 'Efficiency' ? row.deletedPid : row.hiringStatus === 'Onboarded' && row.requisitionId)))
const reminderLink = computed(() => `mailto:${encodeURIComponent(record.value?.requestor || '')}?subject=${encodeURIComponent(`Resource update: ${record.value?.migrationRequestId}`)}&body=${encodeURIComponent(`Please review these ${selected.value.length} resource positions:\n${record.value?.rows.filter(row => selected.value.includes(row.id)).map(row => `${row.gscPid || row.id} - ${row.site} - ${row.hiringType}`).join('\n')}\n${location.href}`)}`)
const dateTime = value => new Date(value).toLocaleString('en-GB')
function cellEditable(row, key) {
  if (tab.value === 'area') return canEditArea.value && !row.areaLockedAt
  if (!canEdit.value) return false
  if (tab.value === 'hr') return hrColumns.value.some(column => column.key === key)
  return baseColumns.value.some(column => column.key === key) || (row.hiringType === 'Efficiency' && ['deletedPid', 'actualDoj', 'apmmId'].includes(key))
}
function newRow() {
  return Object.fromEntries([
    ...baseColumns.value, ...hrColumns.value, ...areaColumns, { key: 'deletedPid' },
  ].map(column => [column.key, '']).concat([
    ['id', crypto.randomUUID()], ['site', record.value.sites.length === 1 ? record.value.sites[0] : ''],
    ['hiringType', 'External'], ['language', 'English'], ['hiringStatus', 'Pending'],
    ['region', record.value.region], ['area', record.value.areas.length === 1 ? record.value.areas[0] : ''],
    ['country', record.value.countries.length === 1 ? record.value.countries[0] : ''],
    ['areaLockedAt', ''], ['areaLockedBy', ''],
  ]))
}
function addRow() { record.value.rows.push(newRow()) }
function changeHiringType(row) {
  if (row.hiringType === 'Efficiency') {
    row.hiringStatus = 'Not Applicable'; row.requisitionId = ''; row.tentativeDoj = ''
  } else if (row.hiringStatus === 'Not Applicable') row.hiringStatus = 'Pending'
}
function removeRow(row) {
  if (!window.confirm('Remove this draft resource position?')) return
  record.value.rows = record.value.rows.filter(item => item.id !== row.id)
  selected.value = selected.value.filter(id => id !== row.id)
}
function resetFilters() { query.value = ''; siteFilter.value = ''; statusFilter.value = ''; selected.value = [] }
function selectAll(checked) {
  const ids = new Set(selected.value)
  visibleRows.value.forEach(row => checked ? ids.add(row.id) : ids.delete(row.id))
  selected.value = [...ids]
}
async function reopenArea() {
  if (await save('reopen_area', { reason: areaReason.value })) areaReason.value = ''
}
async function reopen() {
  if (await save('reopen', { reason: reason.value })) reason.value = ''
}
function exportData() {
  error.value = ''
  try {
    const execution = [...baseColumns.value, { key: 'deletedPid', label: 'Deleted PID for Efficiency' }, ...hrColumns.value]
    exportArtefact(record.value, 'resources', [
      ['Execution', [['Position ID', ...execution.map(column => column.label)], ...record.value.rows.map(row => [row.id, ...execution.map(column => row[column.key])])]],
      ['Area', [['Position ID', ...areaColumns.map(column => column.label), 'Submitted at', 'Submitted by'], ...record.value.rows.map(row => [row.id, ...areaColumns.map(column => row[column.key]), row.areaLockedAt, row.areaLockedBy])]],
      ['HR TAA', [['Position ID', ...hrColumns.value.map(column => column.label)], ...record.value.rows.filter(row => row.hiringType !== 'Efficiency').map(row => [row.id, ...hrColumns.value.map(column => row[column.key])])]],
    ])
    success.value = 'Excel export generated. All resource positions are included.'
  } catch (caught) { error.value = `Unable to export: ${caught.message}` }
}
async function importData(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  error.value = ''
  success.value = ''
  if (!file.name.toLowerCase().endsWith('.xlsx') || file.size > 5 * 1024 * 1024) { error.value = 'Choose an XLSX workbook no larger than 5 MB.'; return }
  try {
    const workbook = read(await file.arrayBuffer(), { type: 'array' })
    if (!workbook.Sheets.Execution) throw new Error('Use an exported Resources workbook with an Execution sheet.')
    const rows = utils.sheet_to_json(workbook.Sheets.Execution, { defval: '', raw: false })
    if (!rows.length || rows.length > 1000) throw new Error('Import requires 1–1000 rows.')
    const allowed = [...baseColumns.value, { key: 'deletedPid', label: 'Deleted PID for Efficiency' }]
    if (allowed.some(column => !(column.label in rows[0]))) throw new Error('Execution sheet is missing required column headers.')
    const updated = record.value.rows.map(row => ({ ...row }))
    const ids = new Set()
    for (const data of rows) {
      const id = String(data['Position ID'] || crypto.randomUUID())
      if (ids.has(id)) throw new Error('Duplicate Position ID in the workbook.')
      ids.add(id)
      let row = updated.find(item => item.id === id)
      if (!row) { row = { ...newRow(), id }; updated.push(row) }
      for (const column of allowed) row[column.key] = String(data[column.label]).trim()
      if (!record.value.hiringTypes.includes(row.hiringType)) throw new Error('Invalid hiring type in workbook.')
      if (row.language && !record.value.languages.includes(row.language)) throw new Error('Invalid language in workbook.')
      changeHiringType(row)
    }
    if (updated.length > 1000) throw new Error('The project can have at most 1000 resource rows.')
    record.value.rows = updated
    success.value = `${rows.length} Execution rows imported into the draft. HR and Area values are preserved. Save draft to persist.`
  } catch (caught) { error.value = `Unable to import: ${caught.message}` }
}
</script>
