<template>
  <PageShell title="Resources" :show-heading="false" :back-to="backTo" :back-label="backLabel" back-link-to-topbar full-width>
    <div class="pa-page pa-resources-page">
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
              <mc-button v-if="record.frozen && record.permissions.reopen" appearance="primary" label="Unlock Resources" :disabled="!!busy" @click="openUnlockDialog" />
              <mc-button v-if="!record.frozen && (record.permissions.edit || record.permissions.area)" appearance="neutral" variant="outlined" label="Save draft" :disabled="!!busy || cohortMode" @click="save()" />
              <mc-button v-if="!record.frozen && record.permissions.edit" appearance="primary" label="Confirm resources" :disabled="!!busy || cohortMode || !ready" @click="save('submit')" />
            </div>
          </div>
          <div class="pa-project-meta"><strong>{{ record.projectName }}</strong><span>{{ record.migrationRequestId }}</span><span>{{ record.products.join(', ') || 'No product' }} / {{ record.region }}</span><span>{{ dirty ? 'Unsaved changes' : record.updatedAt ? `Last saved ${dateTime(record.updatedAt)}` : 'Not yet saved' }}</span></div>
          <div class="pa-tabs" role="tablist" aria-label="Resource views"><button v-for="item in tabs" :key="item.id" role="tab" :aria-selected="tab === item.id" @click="selectTab(item.id)">{{ item.label }}</button></div>
          <div class="pa-metrics">
            <article v-for="metric in metrics" :key="metric.label" class="pa-metric" :class="[`pa-metric--${metric.tone}`, { 'pa-metric--risk': metric.risk && metric.value > 0 }]">
              <span class="pa-metric-icon" aria-hidden="true"><mc-icon :icon="metric.icon" color="var(--pa-metric-accent)" size="24" /></span>
              <div class="pa-metric-content"><span class="pa-metric-label">{{ metric.label }}<mc-icon class="pa-metric-info" icon="mi-information" size="14" :title="metric.note" :aria-label="metric.note" role="img" /></span><strong>{{ metric.value }}</strong></div>
            </article>
            <article v-if="tab !== 'area'" class="pa-jl-card" aria-label="Job level scope summary">
              <h2 class="pa-jl-card__title">JL</h2>
              <div class="pa-jl-card__levels">
                <div v-for="level in jlSummary" :key="level.name" class="pa-jl-card__level" :class="`pa-jl-card__level--${level.tone}`">
                  <span>{{ level.name }}</span>
                  <strong>{{ level.selected }}<span>/{{ level.total ?? '—' }}</span></strong>
                </div>
              </div>
              <p class="pa-jl-card__caption">Selected / Scope Statement</p>
            </article>
          </div>
        </header>
        <section v-if="tab === 'execution' && canEdit" class="pa-panel pa-cohort-panel" aria-label="Cohort management">
          <div class="pa-section-heading">
            <div>
              <p class="pa-eyebrow">Execution grouping</p>
              <div class="pa-cohort-title">
                <h2>Cohorts</h2>
                <span class="pa-cohort-help">
                  <button type="button" class="pa-cohort-help__trigger" aria-describedby="pa-cohort-help-tooltip">Cohort guide</button>
                  <span id="pa-cohort-help-tooltip" class="pa-cohort-help__tooltip" role="tooltip">
                    <strong>What cohorts do</strong>
                    <p>Cohorts group resource positions that belong to the same hiring or onboarding group. Positions stay as separate resource rows.</p>
                    <strong>How to create one</strong>
                    <ol>
                      <li>Select <b>Create Cohort</b> and enter a cohort name.</li>
                      <li>Tick one or more unassigned positions in the Execution table.</li>
                      <li>Select <b>Create Cohort</b> again. The cohort is saved to this project automatically.</li>
                    </ol>
                    <strong>Manage cohorts</strong>
                    <p>Each position can belong to one cohort. Rename updates all its positions; Delete only unassigns them. Use the cohort table headings to expand or collapse groups.</p>
                  </span>
                </span>
              </div>
            </div>
            <button type="button" class="pa-text-button" :disabled="cohortMode || !unassignedRows.length || !!busy" @click="startCohortCreation">+ Create Cohort</button>
          </div>
          <div v-if="cohorts.length" class="pa-cohort-list">
            <div v-for="(cohort, index) in cohorts" :key="cohort.name" class="pa-cohort-chip" :style="{ '--cohort-accent': cohortColor(index) }">
              <span><strong>{{ cohort.name }}</strong><small>{{ cohort.rows.length }} position{{ cohort.rows.length === 1 ? '' : 's' }}</small></span>
              <button type="button" :disabled="!!busy" :aria-label="`Rename ${cohort.name}`" @click="renameCohort(cohort.name)">Rename</button>
              <button type="button" :disabled="!!busy" :aria-label="`Delete ${cohort.name}`" @click="deleteCohort(cohort)">Delete</button>
            </div>
          </div>
          <p class="pa-note">{{ assignedRowCount }} / {{ record.rows.length }} positions assigned · {{ unassignedRows.length }} not yet in a cohort</p>
          <div v-if="cohortMode" class="pa-cohort-builder">
            <label>Cohort name<input v-model="cohortDraftName" maxlength="120" aria-label="Cohort name" /></label>
            <span>Select resource positions in the Execution table below.</span>
            <strong>{{ cohortSelection.length }} position{{ cohortSelection.length === 1 ? '' : 's' }} selected</strong>
            <div>
              <button type="button" class="pa-text-button" :disabled="!!busy" @click="cancelCohortCreation">Cancel</button>
              <button type="button" class="pa-cohort-create" :disabled="!!busy || !cohortDraftName.trim() || !cohortSelection.length" @click="createCohort">Create Cohort</button>
            </div>
          </div>
        </section>
        <section v-if="!record.frozen && submitBlockers.length" class="pa-submit-readiness" aria-live="polite">
          <strong>Resources cannot be confirmed yet</strong>
          <ul>
            <li v-for="blocker in submitBlockers" :key="blocker.key">
              {{ blocker.message }}
              <router-link v-if="blocker.to" :to="blocker.to" class="pa-link">Open Scope</router-link>
            </li>
          </ul>
        </section>
        <div v-if="record.sourceChanged" class="pa-feedback">Scope changed since the last save. Reconcile resource positions with the current locked FTE before confirming.</div>
        <div v-if="record.frozen" class="pa-feedback pa-feedback--error">
          <template v-if="record.migrationManagers.length">
            Submitted Resources are locked. Contact this project's assigned Migration Manager
            <template v-for="(manager, index) in record.migrationManagers" :key="manager">
              <a class="pa-link" :href="`mailto:${manager}`">{{ manager }}</a>{{ index < record.migrationManagers.length - 1 ? ', ' : '' }}
            </template>
            or a platform administrator to request an unlock.
          </template>
          <template v-else>
            Submitted Resources are locked. No Migration Manager is assigned to this project. Contact a platform administrator to request an unlock.
          </template>
        </div>
        <section class="pa-panel">
          <div class="pa-section-heading"><div><p class="pa-eyebrow">{{ tab === 'execution' ? 'Project coordination' : tab === 'area' ? 'Sending area' : 'Recruitment & onboarding' }}</p><h2>{{ tabs.find(item => item.id === tab).label }}</h2></div>
            <div class="pa-actions">
              <mc-button v-if="tab === 'execution' && canEdit" appearance="neutral" variant="outlined" label="Add position" :disabled="cohortMode" @click="addRow" />
              <mc-button v-if="tab === 'execution' && canEdit" appearance="neutral" variant="outlined" label="Import Excel" :disabled="cohortMode" @click="fileInput.click()" />
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
          <div class="pa-scroll"><table class="pa-table pa-resource-table">
            <thead><tr><th class="pa-column--select"><input type="checkbox" aria-label="Select visible resource rows" :checked="allVisibleRowsSelected" :disabled="cohortMode && !cohortSelectableRows.length" @change="selectVisibleRows($event.target.checked)" /></th><th v-for="column in columns" :key="column.key" :class="`pa-column--${column.key}`">{{ column.label }}</th><th class="pa-column--action">Action</th></tr></thead>
            <tbody>
              <template v-for="group in tableGroups" :key="group.key">
                <tr v-if="group.showHeader" class="pa-cohort-group" :class="{ 'pa-cohort-group--collapsed': group.collapsed }" @click="toggleCohortGroup(group.key)">
                  <td :colspan="columns.length + 2">
                    <span class="pa-cohort-group__arrow">{{ group.collapsed ? '▸' : '▾' }}</span>
                    <strong v-if="group.unassigned">Not in a cohort</strong>
                    <strong v-else class="pa-cohort-tag" :style="{ '--cohort-accent': cohortColor(group.index) }">{{ group.name }}</strong>
                    <b>{{ group.rows.length }} position{{ group.rows.length === 1 ? '' : 's' }}</b>
                    <span v-if="!group.unassigned" class="pa-cohort-group__summary">{{ cohortSummary(group.rows) }}</span>
                    <span class="pa-cohort-group__toggle">{{ group.collapsed ? 'Expand' : 'Collapse' }}</span>
                  </td>
                </tr>
                <template v-if="!group.collapsed">
                  <tr v-for="row in group.rows" :key="row.id">
              <td class="pa-column--select"><input type="checkbox" :checked="cohortMode ? cohortSelection.includes(row.id) : selected.includes(row.id)" :disabled="cohortMode && Boolean(String(row.cohort || '').trim())" :aria-label="`Select position ${row.gscPid || row.id}`" @change="toggleRowSelection(row, $event.target.checked)" /></td>
              <td v-for="column in columns" :key="column.key" :class="`pa-column--${column.key}`">
                <template v-if="column.key === 'hiringStatus' && tab === 'execution'">
                  <select v-if="activeHiringStatusId === row.id" v-model="row.hiringStatus" aria-label="Hiring Status" @change="activeHiringStatusId = ''" @blur="activeHiringStatusId = ''">
                    <option v-for="status in record.hiringStatuses" :key="status" :value="status">{{ status }}</option>
                  </select>
                  <button v-else type="button" class="pa-status pa-hiring-status" :class="{
                    'pa-status--at_risk': row.hiringStatus === 'At Risk',
                    'pa-status--confirmed': row.hiringStatus === 'Onboarded',
                    'pa-status--in_progress': row.hiringStatus === 'In Progress',
                    'pa-status--pending': row.hiringStatus === 'Pending',
                    'pa-status--not_applicable': row.hiringStatus === 'Not Applicable',
                  }" :disabled="!canEdit || row.hiringType === 'Efficiency'" @click="editHiringStatus(row)">{{ row.hiringStatus }}</button>
                </template>
                <mc-select v-else-if="column.options && cellEditable(row, column.key)" :label="column.label" hiddenlabel fit="small" width="full-width" listsearch optionsheight="260px" :value.prop="row[column.key]" :aria-label="column.label" @optionselected="selectCellOption(row, column.key, $event)">
                  <mc-option value="">Select</mc-option><mc-option v-for="option in column.options" :key="option" :value="option" :disabled="column.key === 'jobLevel' && option === 'JL4' && !jl4Available">{{ option }}</mc-option>
                </mc-select>
                <input v-else-if="cellEditable(row, column.key)" v-model="row[column.key]" :type="column.date ? 'date' : 'text'" :aria-label="column.label" maxlength="500" />
                <span v-else>{{ row[column.key] || '—' }}</span>
              </td>
              <td class="pa-column--action"><span v-if="tab === 'area'" class="pa-status">{{ row.areaLockedAt ? 'Submitted' : 'Draft' }}</span><button v-else-if="tab === 'execution'" class="pa-text-button" :disabled="!canEdit || !!row.areaLockedAt" @click="removeRow(row)">Remove</button><span v-else>Synced to Execution</span></td>
                  </tr>
                </template>
              </template>
              <tr v-if="!visibleRows.length"><td :colspan="columns.length + 2" class="pa-empty">{{ record.rows.length ? 'No matching positions.' : 'No positions yet. Add a position or import the Execution sheet from an exported workbook.' }}</td></tr>
            </tbody>
          </table></div>
          <div class="pa-section-heading" style="margin-top: 18px"><span class="pa-note">{{ visibleRows.length }} visible · {{ selected.length }} selected · {{ record.rows.length }} total</span><a v-if="selected.length" class="pa-link" :href="reminderLink">Compose reminder for selected positions</a></div>
          <div v-if="tab === 'area' && areaSubmitted && canEditArea" class="pa-field"><label>Reason to reopen submitted Area details<textarea v-model="areaReason" maxlength="2000" rows="2" /></label><mc-button appearance="neutral" variant="outlined" label="Reopen Area details" :disabled="!areaReason.trim()" @click="reopenArea" /></div>
        </section>
        <details class="pa-audit"><summary>Audit history · {{ record.auditLog.length }} events</summary><div class="pa-scroll"><table class="pa-table"><thead><tr><th>Revision</th><th>Action</th><th>User</th><th>Timestamp</th><th>Reason</th><th>Changes</th></tr></thead><tbody>
          <tr v-for="entry in [...record.auditLog].reverse()" :key="entry.revision">
            <td>{{ entry.revision }}</td><td>{{ auditActionLabel(entry.action) }}</td><td>{{ entry.by }}</td><td>{{ dateTime(entry.at) }}</td><td>{{ entry.reason || '—' }}</td>
            <td class="pa-audit-changes">
              <details v-if="entry.action === 'reopen' && entry.unlockChanges?.length">
                <summary>{{ entry.unlockChanges.length }} saved change event{{ entry.unlockChanges.length === 1 ? '' : 's' }} after unlock</summary>
                <div v-for="(update, index) in entry.unlockChanges" :key="`${update.revision}-${index}`" class="pa-audit-change-event">
                  <strong>Revision {{ update.revision }} · {{ auditActionLabel(update.action) }} · {{ update.by }}</strong>
                  <ul><li v-for="(change, changeIndex) in update.changes" :key="`${change.type}-${change.field || changeIndex}`">{{ auditChangeText(change) }}</li></ul>
                </div>
              </details>
              <span v-else-if="entry.action === 'reopen'">No changes saved after this unlock.</span>
              <details v-else-if="entry.changes?.length">
                <summary>{{ entry.changes.length }} change{{ entry.changes.length === 1 ? '' : 's' }}</summary>
                <ul><li v-for="(change, index) in entry.changes" :key="`${change.type}-${change.field || index}`">{{ auditChangeText(change) }}</li></ul>
              </details>
              <span v-else>—</span>
            </td>
          </tr>
        </tbody></table></div></details>
      </template>
      <mc-dialog :open="unlockDialogOpen" heading="Unlock Resources" dimension="small" showclosebutton @closing="closeUnlockDialog">
        <p>Unlocking returns Resources to draft. Enter a reason; it will be saved in the audit history.</p>
        <label class="unlock-dialog__field">
          <span>Reason for unlocking <span aria-hidden="true">*</span></span>
          <textarea v-model="unlockReason" rows="4" maxlength="2000" required />
        </label>
        <p v-if="unlockReasonError" class="unlock-dialog__error" role="alert">{{ unlockReasonError }}</p>
        <div class="unlock-dialog__actions">
          <mc-button type="button" appearance="neutral" variant="outlined" label="Cancel" :disabled="!!busy" @click="closeUnlockDialog" />
          <mc-button type="button" appearance="primary" label="Unlock Resources" :disabled="!!busy" @click="confirmUnlock" />
        </div>
      </mc-dialog>
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
import '@maersk-global/mds-components-core/mc-icon'
import '@maersk-global/mds-components-core/mc-select'
import '@maersk-global/mds-components-core/mc-option'
import '@maersk-global/mds-components-core/mc-dialog'
import '../styles/projectArtefacts.css'

const { record, projectId, backTo, backLabel, loading, busy, error, success, dirty, editable, load, save } = useProjectArtefact('resources')
const tab = ref('execution')
const tabs = [{ id: 'execution', label: 'Execution' }, { id: 'area', label: 'Area' }, { id: 'hr', label: 'HR / TAA' }]
const query = ref('')
const siteFilter = ref('')
const statusFilter = ref('')
const selected = ref([])
const cohortMode = ref(false)
const cohortDraftName = ref('')
const cohortSelection = ref([])
const collapsedCohortGroups = ref(new Set())
const areaReason = ref('')
const unlockDialogOpen = ref(false)
const unlockReason = ref('')
const unlockReasonError = ref('')
const fileInput = ref(null)
const activeHiringStatusId = ref('')
const canEdit = computed(() => editable.value && record.value.permissions.edit)
const canEditArea = computed(() => editable.value && record.value.permissions.area)
const sites = computed(() => [...new Set([...(record.value?.sites || []), ...(record.value?.rows || []).map(row => row.site)].filter(Boolean))])
const resourceRows = computed(() => record.value?.rows || [])
const executionRows = computed(() => resourceRows.value)
const areaRows = computed(() => resourceRows.value)
const hrRows = computed(() => resourceRows.value.filter(row => row.hiringType !== 'Efficiency'))
const approvedFtes = computed(() => record.value?.businessCase?.locked ? record.value.businessCase.population : null)
const countRows = (rows, predicate) => rows.filter(predicate).length
const onboarded = rows => countRows(rows, row => row.actualDoj && row.apmmId)
const atRisk = rows => countRows(rows, row => row.hiringStatus === 'At Risk')
const jobLevels = ['JL1', 'JL2', 'JL3', 'JL4']
const scopeFinalFteByLevel = computed(() => record.value?.source?.finalFteByLevel || {})
const jl4Available = computed(() => Number(scopeFinalFteByLevel.value.JL4) > 0)
const jlSummary = computed(() => jobLevels.map((name, index) => ({
  name,
  selected: countRows(resourceRows.value, row => row.jobLevel === name),
  total: scopeFinalFteByLevel.value[name] ?? null,
  tone: index === 1 ? 'cool' : 'warm',
})))
const metricCards = {
  execution: () => [
    {
      label: 'Approved FTEs',
      value: approvedFtes.value ?? '—',
      note: approvedFtes.value != null ? 'Population from the locked Business Case' : 'Locked Business Case population',
      icon: 'mi-people', tone: 'green',
    },
    {
      label: 'Efficiency/Backfill',
      value: `${countRows(executionRows.value, row => row.hiringType === 'Efficiency')} / ${countRows(executionRows.value, row => row.hiringType === 'Backfill')}`,
      note: 'Execution rows counted by Hiring Type: Efficiency / Backfill',
      icon: 'mi-lightning', tone: 'teal',
    },
    { label: 'Onboarding Completed', value: onboarded(executionRows.value), note: 'Execution rows with both Actual DOJ and APMM ID filled', icon: 'mi-user-circle', tone: 'purple' },
    { label: 'AT Risk', value: atRisk(hrRows.value), note: 'Non-Efficiency rows with Hiring Status set to At Risk', icon: 'mi-exclamation-triangle', tone: 'red', risk: true },
    {
      label: 'Area PIDs Received',
      value: `${countRows(areaRows.value, row => row.areaPid && row.areaApmmId && row.releaseDate)} / ${approvedFtes.value ?? '—'}`,
      note: 'Rows with Area PID, Area APMM ID and Release Date filled / locked Business Case population',
      icon: 'mi-file', tone: 'blue',
    },
  ],
  area: () => [
    {
      label: 'Area PIDs Received',
      value: `${countRows(areaRows.value, row => areaColumns.every(column => String(row[column.key] ?? '').trim()))} / ${approvedFtes.value ?? '—'}`,
      note: 'Rows with all 6 Area fields filled / locked Business Case population',
    },
  ],
  hr: () => [
    {
      label: 'Hiring Required',
      value: `${countRows(executionRows.value, row => row.hiringType === 'External' || row.hiringType === 'IJP')} / ${record.value?.source?.population ?? '—'}`,
      note: 'Execution rows with Hiring Type External or IJP / confirmed Scope population',
    },
    {
      label: 'Efficiency/Backfill FTEs',
      value: countRows(executionRows.value, row => row.hiringType === 'Efficiency'),
      note: 'Execution rows counted with Hiring Type set to Efficiency',
    },
    {
      label: 'Onboarding Completed',
      value: `${countRows(hrRows.value, row => row.hiringStatus === 'Onboarded')} / ${countRows(executionRows.value, row => row.hiringType === 'External' || row.hiringType === 'IJP')}`,
      note: 'Non-Efficiency rows with Hiring Status Onboarded / Execution rows with Hiring Type External or IJP',
    },
    { label: 'AT Risk', value: atRisk(hrRows.value), note: 'Non-Efficiency rows with Hiring Status set to At Risk', risk: true },
  ],
}
const metrics = computed(() => (metricCards[tab.value] || metricCards.execution)())
const baseColumns = computed(() => [
  { key: 'cohort', label: 'Cohort' },
  { key: 'site', label: 'GSC Site', options: [...new Set([...record.value.siteOptions, ...sites.value])] }, { key: 'hiringType', label: 'Hiring Type', options: record.value.hiringTypes },
  { key: 'language', label: 'Language', options: record.value.languages }, { key: 'pidCreationDate', label: 'PID Creation Date', date: true },
  { key: 'gscPid', label: 'GSC PID' },
])
const jobLevelColumn = { key: 'jobLevel', label: 'JL', options: ['JL1', 'JL2', 'JL3', 'JL4'] }
const hrColumns = computed(() => [
  { key: 'requisitionId', label: 'Requisition ID' }, { key: 'hiringStatus', label: 'Hiring Status', options: record.value.hiringStatuses },
  { key: 'remarks', label: 'Remarks' }, { key: 'tentativeDoj', label: 'Tentative DOJ', date: true },
  { key: 'actualDoj', label: 'Actual DOJ', date: true }, { key: 'apmmId', label: 'APMM ID' },
])
const executionColumns = computed(() => [
  ...baseColumns.value,
  { key: 'deletedPid', label: 'Deleted PID for Efficiency' },
  hrColumns.value.find(column => column.key === 'requisitionId'),
  jobLevelColumn,
  ...hrColumns.value.filter(column => column.key !== 'requisitionId'),
])
const areaColumns = [
  { key: 'region', label: 'Region' }, { key: 'area', label: 'Area' }, { key: 'country', label: 'Country' },
  { key: 'areaPid', label: 'Area PID' }, { key: 'areaApmmId', label: 'Area APMM ID' }, { key: 'releaseDate', label: 'Release Date', date: true },
]
const columns = computed(() => tab.value === 'area' ? areaColumns : tab.value === 'hr' ? [...baseColumns.value, ...hrColumns.value] : executionColumns.value)
const visibleRows = computed(() => (record.value?.rows || []).filter(row =>
  (tab.value !== 'hr' || row.hiringType !== 'Efficiency') && (!siteFilter.value || row.site === siteFilter.value) &&
  (!statusFilter.value || row.hiringStatus === statusFilter.value) && Object.values(row).join(' ').toLowerCase().includes(query.value.toLowerCase())))
const cohorts = computed(() => {
  const groupedRows = new Map()
  for (const row of resourceRows.value) {
    const name = String(row.cohort || '').trim()
    if (!name) continue
    if (!groupedRows.has(name)) groupedRows.set(name, [])
    groupedRows.get(name).push(row)
  }
  return [...groupedRows.entries()].map(([name, rows]) => ({ name, rows }))
})
const unassignedRows = computed(() => resourceRows.value.filter(row => !String(row.cohort || '').trim()))
const assignedRowCount = computed(() => resourceRows.value.length - unassignedRows.value.length)
const cohortSelectableRows = computed(() => visibleRows.value.filter(row => !String(row.cohort || '').trim()))
const allVisibleRowsSelected = computed(() => {
  const rows = cohortMode.value ? cohortSelectableRows.value : visibleRows.value
  const selection = cohortMode.value ? cohortSelection.value : selected.value
  return rows.length > 0 && rows.every(row => selection.includes(row.id))
})
const tableGroups = computed(() => {
  if (tab.value !== 'execution' || cohortMode.value || !cohorts.value.length) {
    return [{ key: 'all', rows: visibleRows.value, showHeader: false, collapsed: false }]
  }
  const groups = cohorts.value.flatMap((cohort, index) => {
    const rows = visibleRows.value.filter(row => String(row.cohort || '').trim() === cohort.name)
    if (!rows.length) return []
    const key = `cohort:${cohort.name}`
    return [{ key, name: cohort.name, rows, index, showHeader: true, collapsed: collapsedCohortGroups.value.has(key) }]
  })
  const unassigned = visibleRows.value.filter(row => !String(row.cohort || '').trim())
  if (unassigned.length) {
    const key = 'cohort:unassigned'
    groups.push({ key, name: 'Not in a cohort', rows: unassigned, unassigned: true, showHeader: true, collapsed: collapsedCohortGroups.value.has(key) })
  }
  return groups
})
const cohortPalette = ['#0073ab', '#7c3aed', '#16a34a', '#f59e0b', '#dc2626', '#0f766e']
const ready = computed(() => record.value?.source.ready && record.value.rows.length === record.value.source.population &&
  record.value.rows.every(row => row.site && row.language && row.gscPid && row.pidCreationDate && row.areaLockedAt && row.actualDoj && row.apmmId &&
    (row.hiringType === 'Efficiency' ? row.deletedPid : row.hiringStatus === 'Onboarded' && row.requisitionId)))
const submitBlockers = computed(() => {
  const current = record.value
  if (!current) return []

  const blockers = []
  if (!current.permissions.edit) {
    blockers.push({
      key: 'permission',
      message: 'Your account does not have Resources edit permission. Ask the Requestor, locked WPM Focal, or Resources administrator to confirm.',
    })
  }
  if (busy.value) blockers.push({ key: 'busy', message: 'Wait for the current save to finish.' })
  if (cohortMode.value) blockers.push({ key: 'cohort', message: 'Finish or cancel Cohort creation before confirming.' })

  if (!current.source.ready) {
    blockers.push({
      key: 'scope',
      message: 'Submit and lock the Scope Statement before confirming Resources.',
      to: `/migration-dashboard/${projectId.value}/scope-statement`,
    })
  } else if (current.rows.length !== current.source.population) {
    blockers.push({
      key: 'population',
      message: `Resource positions: ${current.rows.length} of ${current.source.population}. Add or remove positions to match the locked Scope FTE.`,
    })
  }

  const positionNames = rows => {
    const names = rows.slice(0, 3).map(row => row.gscPid || row.id)
    return `${names.join(', ')}${rows.length > names.length ? ` and ${rows.length - names.length} more` : ''}`
  }
  const addMissingFieldBlocker = (key, label, predicate) => {
    const rows = current.rows.filter(predicate)
    if (rows.length) {
      blockers.push({
        key,
        message: `${label} is missing for ${rows.length} position${rows.length === 1 ? '' : 's'}: ${positionNames(rows)}.`,
      })
    }
  }

  addMissingFieldBlocker('site', 'GSC Site', row => !row.site)
  addMissingFieldBlocker('language', 'Language', row => !row.language)
  addMissingFieldBlocker('gsc-pid', 'GSC PID', row => !row.gscPid)
  addMissingFieldBlocker('pid-date', 'PID Creation Date', row => !row.pidCreationDate)
  addMissingFieldBlocker('area', 'Area details submission', row => !row.areaLockedAt)
  addMissingFieldBlocker('actual-doj', 'Actual DOJ', row => !row.actualDoj)
  addMissingFieldBlocker('apmm-id', 'APMM ID', row => !row.apmmId)
  addMissingFieldBlocker('efficiency-pid', 'Deleted PID for Efficiency', row => row.hiringType === 'Efficiency' && !row.deletedPid)
  addMissingFieldBlocker('onboarded', 'Hiring Status Onboarded and Requisition ID', row =>
    row.hiringType !== 'Efficiency' && (row.hiringStatus !== 'Onboarded' || !row.requisitionId))

  return blockers
})
const reminderLink = computed(() => `mailto:${encodeURIComponent(record.value?.requestor || '')}?subject=${encodeURIComponent(`Resource update: ${record.value?.migrationRequestId}`)}&body=${encodeURIComponent(`Please review these ${selected.value.length} resource positions:\n${record.value?.rows.filter(row => selected.value.includes(row.id)).map(row => `${row.gscPid || row.id} - ${row.site} - ${row.hiringType}`).join('\n')}\n${location.href}`)}`)
const dateTime = value => new Date(value).toLocaleString('en-GB')
const auditActionLabel = action => ({
  save: 'Save changes',
  submit: 'Confirm Resources',
  reopen: 'Unlock Resources',
  submit_area: 'Submit Area details',
  reopen_area: 'Unlock Area details',
}[action] || action)
function auditChangeText(change) {
  if (change.type === 'status') return `${change.label}: ${change.from || '—'} → ${change.to || '—'}`
  if (change.type === 'position_added') return `Added position ${change.position} (${change.positionId})`
  if (change.type === 'position_removed') return `Removed position ${change.position} (${change.positionId})`
  return `${change.position} · ${change.field}: ${change.from || '—'} → ${change.to || '—'}`
}
function selectCellOption(row, key, event) {
  const value = event.detail?.value ?? event.currentTarget.value
  if (row[key] === value) return
  row[key] = value
  if (key === 'hiringType') changeHiringType(row)
}
function cellEditable(row, key) {
  if (key === 'cohort') return false
  if (tab.value === 'area') return canEditArea.value && !row.areaLockedAt
  if (!canEdit.value) return false
  if (tab.value === 'hr') return hrColumns.value.some(column => column.key === key)
  return baseColumns.value.some(column => column.key === key) || key === 'jobLevel' || key === 'hiringStatus' ||
    key === 'remarks' ||
    (row.hiringType === 'Efficiency' && ['deletedPid', 'actualDoj', 'apmmId'].includes(key)) ||
    (row.hiringType !== 'Efficiency' && ['requisitionId', 'tentativeDoj', 'actualDoj', 'apmmId'].includes(key))
}
function editHiringStatus(row) {
  if (canEdit.value && row.hiringType !== 'Efficiency') activeHiringStatusId.value = row.id
}
function newRow() {
  return Object.fromEntries([
    ...baseColumns.value, ...hrColumns.value, ...areaColumns, { key: 'deletedPid' }, jobLevelColumn,
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
function selectVisibleRows(checked) {
  if (!cohortMode.value) {
    selectAll(checked)
    return
  }
  const ids = new Set(cohortSelection.value)
  cohortSelectableRows.value.forEach(row => checked ? ids.add(row.id) : ids.delete(row.id))
  cohortSelection.value = [...ids]
}
function toggleRowSelection(row, checked) {
  if (cohortMode.value) {
    if (String(row.cohort || '').trim()) return
    const ids = new Set(cohortSelection.value)
    checked ? ids.add(row.id) : ids.delete(row.id)
    cohortSelection.value = [...ids]
    return
  }
  const ids = new Set(selected.value)
  checked ? ids.add(row.id) : ids.delete(row.id)
  selected.value = [...ids]
}
function nextCohortName() {
  const names = new Set(cohorts.value.map(cohort => cohort.name.toLocaleLowerCase()))
  let suffix = 1
  while (names.has(`cohort ${suffix}`)) suffix += 1
  return `Cohort ${suffix}`
}
function startCohortCreation() {
  if (!canEdit.value || !unassignedRows.value.length) return
  tab.value = 'execution'
  selected.value = []
  cohortSelection.value = []
  cohortDraftName.value = nextCohortName()
  cohortMode.value = true
}
function cancelCohortCreation() {
  cohortMode.value = false
  cohortSelection.value = []
  cohortDraftName.value = ''
}
function selectTab(tabId) {
  if (cohortMode.value && tabId !== 'execution') cancelCohortCreation()
  tab.value = tabId
}
function cohortColor(index) {
  return cohortPalette[index % cohortPalette.length]
}
function cohortSummary(rows) {
  const recruitmentRows = rows.filter(row => !['Efficiency', 'Backfill'].includes(row.hiringType))
  const onboarded = recruitmentRows.filter(row => row.hiringStatus === 'Onboarded').length
  return `Onboarded ${onboarded} / ${recruitmentRows.length} · Efficiency / Backfill ${rows.length - recruitmentRows.length}`
}
function toggleCohortGroup(key) {
  const collapsed = new Set(collapsedCohortGroups.value)
  collapsed.has(key) ? collapsed.delete(key) : collapsed.add(key)
  collapsedCohortGroups.value = collapsed
}
async function createCohort() {
  const name = cohortDraftName.value.trim()
  if (!name) {
    error.value = 'Enter a cohort name.'
    return
  }
  if (cohorts.value.some(cohort => cohort.name.toLocaleLowerCase() === name.toLocaleLowerCase())) {
    error.value = 'A cohort with this name already exists.'
    return
  }
  const selectedIds = new Set(cohortSelection.value)
  const rows = resourceRows.value.filter(row => selectedIds.has(row.id) && !String(row.cohort || '').trim())
  if (!rows.length || rows.length !== selectedIds.size) {
    error.value = 'Select one or more positions that are not already in a cohort.'
    return
  }
  error.value = ''
  success.value = ''
  rows.forEach(row => { row.cohort = name })
  if (!await save()) {
    rows.forEach(row => { row.cohort = '' })
    return
  }
  cancelCohortCreation()
  success.value = `${name} created with ${rows.length} position${rows.length === 1 ? '' : 's'}.`
}
async function renameCohort(cohortName) {
  const name = window.prompt('Rename cohort', cohortName)
  if (name === null) return
  const nextName = name.trim()
  if (!nextName) {
    error.value = 'Enter a cohort name.'
    return
  }
  if (cohorts.value.some(cohort => cohort.name !== cohortName && cohort.name.toLocaleLowerCase() === nextName.toLocaleLowerCase())) {
    error.value = 'A cohort with this name already exists.'
    return
  }
  const rows = resourceRows.value.filter(row => String(row.cohort || '').trim() === cohortName)
  if (!rows.length || nextName === cohortName) return
  error.value = ''
  success.value = ''
  rows.forEach(row => { row.cohort = nextName })
  if (!await save()) {
    rows.forEach(row => { row.cohort = cohortName })
    return
  }
  success.value = `${cohortName} renamed to ${nextName}.`
}
async function deleteCohort(cohort) {
  if (!window.confirm(`Delete "${cohort.name}"? Its ${cohort.rows.length} position${cohort.rows.length === 1 ? '' : 's'} will become unassigned. The resource positions will not be deleted.`)) return
  error.value = ''
  success.value = ''
  cohort.rows.forEach(row => { row.cohort = '' })
  if (!await save()) {
    cohort.rows.forEach(row => { row.cohort = cohort.name })
    return
  }
  success.value = `${cohort.name} deleted; its positions are unassigned.`
}
async function reopenArea() {
  if (await save('reopen_area', { reason: areaReason.value })) areaReason.value = ''
}
function openUnlockDialog() {
  unlockReason.value = ''
  unlockReasonError.value = ''
  unlockDialogOpen.value = true
}
function closeUnlockDialog() {
  unlockDialogOpen.value = false
  unlockReason.value = ''
  unlockReasonError.value = ''
}
async function confirmUnlock() {
  const reason = unlockReason.value.trim()
  if (!reason) {
    unlockReasonError.value = 'Enter a reason to unlock Resources.'
    return
  }
  unlockReasonError.value = ''
  if (await save('reopen', { reason })) closeUnlockDialog()
}
function exportData() {
  error.value = ''
  try {
    const execution = executionColumns.value
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
    const allowed = [...baseColumns.value, { key: 'deletedPid', label: 'Deleted PID for Efficiency' }, jobLevelColumn]
    const required = allowed.filter(column => !['cohort', 'jobLevel'].includes(column.key))
    if (required.some(column => !(column.label in rows[0]))) throw new Error('Execution sheet is missing required column headers.')
    const updated = record.value.rows.map(row => ({ ...row }))
    const ids = new Set()
    for (const data of rows) {
      const id = String(data['Position ID'] || crypto.randomUUID())
      if (ids.has(id)) throw new Error('Duplicate Position ID in the workbook.')
      ids.add(id)
      let row = updated.find(item => item.id === id)
      if (!row) { row = { ...newRow(), id }; updated.push(row) }
      for (const column of allowed) {
        if (column.label in data) row[column.key] = String(data[column.label]).trim()
      }
      if (!record.value.hiringTypes.includes(row.hiringType)) throw new Error('Invalid hiring type in workbook.')
      if (row.language && !record.value.languages.includes(row.language)) throw new Error('Invalid language in workbook.')
      if (row.jobLevel && !jobLevels.includes(row.jobLevel)) throw new Error('Invalid JL value in workbook. Choose JL1, JL2, JL3 or JL4.')
      if (row.jobLevel === 'JL4' && !jl4Available.value) throw new Error('JL4 cannot be imported because Scope has no positive JL4 final agreement.')
      changeHiringType(row)
    }
    if (updated.length > 1000) throw new Error('The project can have at most 1000 resource rows.')
    record.value.rows = updated
    success.value = `${rows.length} Execution rows imported into the draft. HR and Area values are preserved. Save draft to persist.`
  } catch (caught) { error.value = `Unable to import: ${caught.message}` }
}
</script>

<style scoped>
.unlock-dialog__field { color: #526d7f; display: flex; flex-direction: column; font-size: 12px; gap: 7px; margin-top: 18px; }
.unlock-dialog__field textarea { border: 1px solid #cedce4; border-radius: 6px; box-sizing: border-box; color: var(--pa-ink); font: inherit; font-size: 13px; padding: 9px 10px; resize: vertical; width: 100%; }
.unlock-dialog__field textarea:focus { outline: 2px solid #42b0d5; outline-offset: 1px; }
.unlock-dialog__error { color: #a3332c; font-size: 12px; margin: 8px 0 0; }
.unlock-dialog__actions { display: flex; gap: 8px; justify-content: flex-end; }
.pa-audit-changes { min-width: 260px; }
.pa-audit-changes summary { color: #0073ab; cursor: pointer; }
.pa-audit-changes ul { margin: 6px 0; padding-left: 18px; }
.pa-audit-change-event { margin-top: 8px; }
.pa-audit-change-event strong { color: #344054; font-size: 11px; }
.pa-cohort-panel { margin-bottom: 12px; }
.pa-cohort-panel .pa-section-heading { margin-bottom: 10px; }
.pa-cohort-title { align-items: center; display: flex; gap: 9px; }
.pa-cohort-title h2 { margin: 0; }
.pa-cohort-help { display: inline-block; margin-bottom: -6px; padding-bottom: 6px; position: relative; z-index: 20; }
.pa-cohort-help__trigger { background: #e8f4fa; border: 0; border-radius: 12px; color: #0073ab; cursor: help; font-size: 9px; font-weight: 700; padding: 4px 8px; }
.pa-cohort-help__trigger:focus-visible { outline: 2px solid #0073ab; outline-offset: 2px; }
.pa-cohort-help__tooltip { background: #0b2a4a; border-radius: 7px; box-shadow: 0 8px 24px rgba(16, 24, 40, .2); color: #fff; display: none; font-size: 10px; font-weight: 400; left: 0; line-height: 1.5; padding: 12px 14px; position: absolute; text-align: left; top: 100%; width: min(360px, calc(100vw - 48px)); z-index: 30; }
.pa-cohort-help:hover .pa-cohort-help__tooltip,.pa-cohort-help:focus-within .pa-cohort-help__tooltip { display: block; }
.pa-cohort-help__tooltip strong { display: block; font-size: 10px; }
.pa-cohort-help__tooltip p { color: #e3edf5; font-size: 10px; line-height: 1.5; margin: 4px 0 9px; }
.pa-cohort-help__tooltip ol { margin: 4px 0 9px; padding-left: 18px; }
.pa-cohort-help__tooltip li { margin: 3px 0; }
.pa-cohort-list { display: flex; flex-wrap: wrap; gap: 8px; }
.pa-cohort-chip { align-items: center; background: #f7fafc; border: 1px solid #dfe5eb; border-left: 3px solid var(--cohort-accent); border-radius: 6px; display: flex; gap: 8px; padding: 6px 9px; }
.pa-cohort-chip > span { display: flex; flex-direction: column; gap: 2px; min-width: 90px; }
.pa-cohort-chip strong { color: #164b69; font-size: 11px; }
.pa-cohort-chip small { color: var(--muted); font-size: 9px; }
.pa-cohort-chip button { background: transparent; border: 0; color: #0073ab; cursor: pointer; font-size: 10px; padding: 3px; }
.pa-cohort-chip button:disabled { cursor: not-allowed; opacity: .5; }
.pa-cohort-panel > .pa-note { margin: 8px 0 0; }
.pa-cohort-builder { align-items: end; border-top: 1px solid #e3e8ed; display: flex; flex-wrap: wrap; gap: 12px; margin-top: 12px; padding-top: 12px; }
.pa-cohort-builder label { color: #344054; display: flex; flex-direction: column; font-size: 10px; font-weight: 700; gap: 4px; }
.pa-cohort-builder input { border: 1px solid #c8d1d9; border-radius: 5px; font: inherit; height: 30px; min-width: 190px; padding: 0 8px; }
.pa-cohort-builder > span,.pa-cohort-builder > strong { color: var(--muted); font-size: 10px; }
.pa-cohort-builder > div { display: flex; gap: 8px; margin-left: auto; }
.pa-cohort-create { background: #0073ab; border: 1px solid #0073ab; border-radius: 5px; color: white; cursor: pointer; font-size: 10px; font-weight: 700; padding: 7px 12px; }
.pa-cohort-create:disabled { cursor: not-allowed; opacity: .5; }
.pa-cohort-group { background: #f4f7fa; cursor: pointer; }
.pa-cohort-group:hover { background: #edf4f8; }
.pa-cohort-group td { color: #344054; font-size: 10px; }
.pa-cohort-group__arrow { color: #0073ab; display: inline-block; margin-right: 7px; width: 10px; }
.pa-cohort-group td > b { margin-left: 9px; }
.pa-cohort-tag { background: #e8f4fa; border-radius: 10px; color: var(--cohort-accent); padding: 3px 8px; }
.pa-cohort-group__summary,.pa-cohort-group__toggle { color: var(--muted); margin-left: 12px; }
.pa-cohort-group__toggle { float: right; }
@media (max-width: 700px) {
  .pa-cohort-builder > div { margin-left: 0; width: 100%; }
  .pa-cohort-builder > div button:last-child { margin-left: auto; }
}
</style>
