<template>
  <PageShell
    title="Scope Statements"
    subtitle="Saved scope statement data and its Migration Intake project context."
    tag="Project Attributes"
    back-to="/project-attributes"
    back-label="Back to Admin"
    full-width
  >
    <div class="scope-database-toolbar">
      <label class="search-field">
        <span>Filter records</span>
        <input v-model="query" type="search" placeholder="Project, request ID, requestor…" />
      </label>
      <span class="row-count">{{ filteredRows.length }} visible · {{ savedCount }} saved</span>
      <span v-if="pendingCount" class="pending-count">{{ pendingCount }} pending</span>
      <mc-button
        appearance="neutral"
        variant="outlined"
        fit="small"
        label="Add row"
        icon="mi-plus"
        :disabled="loading || busy"
        @click="addRow"
      />
      <mc-button
        appearance="primary"
        fit="small"
        label="Save"
        icon="mi-floppy-disk"
        :disabled="loading || busy || pendingCount === 0"
        @click="saveData"
      />
      <mc-button
        appearance="neutral"
        variant="outlined"
        fit="small"
        label="Delete selected"
        icon="mi-trash"
        :disabled="loading || busy || selectedIds.length === 0"
        @click="deleteSelected"
      />
      <mc-button
        appearance="neutral"
        variant="outlined"
        fit="small"
        label="Reload"
        icon="mi-arrow-clockwise"
        :disabled="loading || busy"
        @click="reloadData"
      />
    </div>

    <div v-if="success" class="success-message" role="status">{{ success }}</div>
    <mc-notification
      v-if="error"
      appearance="error"
      fit="medium"
      heading="Unable to load Scope Statements"
      :body="error"
    />
    <div v-else-if="loading" class="table-state">Loading saved Scope Statements…</div>
    <div v-else-if="!filteredRows.length" class="table-state">
      {{ rows.length ? 'No rows match this filter.' : 'No Scope Statements have been saved yet. Add a row to link an existing Migration Request ID.' }}
    </div>
    <div v-else class="table-scroll" role="region" aria-label="Saved Scope Statements" tabindex="0">
      <table class="scope-database-table">
        <thead>
          <tr>
            <th class="selection-cell" scope="col">Select</th>
            <th v-for="column in columns" :key="column.key" scope="col">{{ column.label }}</th>
            <th scope="col">Open</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in filteredRows" :key="row._rowKey" :class="{ 'is-pending': isRowPending(row) }">
            <td class="selection-cell">
              <input
                v-if="row.statement_id"
                v-model="selectedIds"
                type="checkbox"
                :value="row.statement_id"
                :aria-label="`Select ${row.migration_request_id} for deletion`"
              />
              <button v-else type="button" class="discard-row" @click="discardNewRow(row._rowKey)">Discard</button>
            </td>
            <td v-for="column in columns" :key="column.key" :title="rawCell(row[column.key])">
              <textarea
                v-if="['scope_text', 'out_of_scope', 'assumptions', 'waves'].includes(column.key) && canEditCell(row, column)"
                v-model="row[column.key]"
                rows="2"
                :maxlength="column.key === 'scope_text' ? 2000 : undefined"
                :aria-label="column.label"
                :placeholder="column.key === 'waves' ? '[{&quot;name&quot;:&quot;Wave name&quot;,&quot;date&quot;:&quot;YYYY-MM-DD&quot;,&quot;fte&quot;:0}]' : undefined"
              />
              <input
                v-else-if="canEditCell(row, column)"
                v-model="row[column.key]"
                :type="isNumericColumn(column.key) ? 'number' : 'text'"
                :min="isNumericColumn(column.key) ? 0 : undefined"
                :step="column.key.endsWith('_final_fte') ? 1 : 0.0001"
                :aria-label="column.label"
              />
              <span v-else>{{ displayCell(row, column) }}</span>
            </td>
            <td>
              <router-link v-if="row.statement_id"
                class="open-project-link"
                :to="`/migration-dashboard/${row.project_id}/scope-statement?from=admin&project=${row.project_id}`"
              >Open</router-link>
              <span v-else>New</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </PageShell>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'
import { useUnsavedChanges } from '../composables/useUnsavedChanges.js'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-notification'

const columns = ref([])
const rows = ref([])
const query = ref('')
const loading = ref(false)
const busy = ref(false)
const error = ref('')
const success = ref('')
const selectedIds = ref([])
const originalSnapshots = ref({})

const editableColumns = computed(() => columns.value.filter((column) => column.editable))

const filteredRows = computed(() => {
  const term = query.value.trim().toLowerCase()
  if (!term) return rows.value
  return rows.value.filter((row) =>
    columns.value.some((column) => String(row[column.key] ?? '').toLowerCase().includes(term))
  )
})

const pendingRows = computed(() => rows.value.filter(isRowPending))
const pendingCount = computed(() => pendingRows.value.length)
const savedCount = computed(() => rows.value.filter((row) => row.statement_id).length)
const { canLeave } = useUnsavedChanges(computed(() => pendingCount.value > 0), computed(() => busy.value || loading.value))

function rowSnapshot(row) {
  return JSON.stringify(editableColumns.value.map((column) => [column.key, row[column.key] ?? '']))
}

function isRowPending(row) {
  if (!row.statement_id) {
    return editableColumns.value.some((column) => String(row[column.key] ?? '').trim() !== '')
  }
  return rowSnapshot(row) !== originalSnapshots.value[row._rowKey]
}

function canEditCell(row, column) {
  if (busy.value || loading.value || !column.editable || row.scope_status === 'submitted') return false
  if (column.editable === 'new') return !row.statement_id
  const lockedLevel = column.key.match(/^(jl\d+)_(agreed_fte|not_agreed_fte|final_fte)$/)?.[1]
  return !lockedLevel || !row[`${lockedLevel}_locked_at`]
}

function isNumericColumn(key) {
  return key === 'ambition_fte' || /_(agreed_fte|not_agreed_fte|final_fte)$/.test(key)
}

function rawCell(value) {
  return value === null || value === undefined ? '' : String(value)
}

function displayCell(row, column) {
  const value = row[column.key]
  if (value === null || value === undefined || value === '') return '—'
  if (column.key === 'audit_log') {
    try {
      const entries = JSON.parse(value)
      return `${entries.length} event${entries.length === 1 ? '' : 's'}`
    } catch {
      return String(value)
    }
  }
  if (column.key.endsWith('_evidence')) {
    try {
      const files = JSON.parse(value)
      return files.length ? files.map((file) => file.name).join(', ') : '—'
    } catch {
      return String(value)
    }
  }
  return String(value)
}

function addRow() {
  query.value = ''
  const row = {
    statement_id: null,
    project_id: null,
    scope_status: 'draft',
    _rowKey: `new-${crypto.randomUUID()}`
  }
  columns.value.forEach((column) => { row[column.key] = '' })
  rows.value.push(row)
}

function discardNewRow(rowKey) {
  rows.value = rows.value.filter((row) => row._rowKey !== rowKey)
}

function buildSavePayload(row) {
  const payload = {
    statement_id: row.statement_id,
    migration_request_id: row.migration_request_id,
    scope_text: row.scope_text,
    out_of_scope: row.out_of_scope ?? '',
    assumptions: row.assumptions ?? '',
    waves: row.waves || '[]'
  }
  for (const level of ['jl2', 'jl3', 'jl4']) {
    payload[`${level}_agreed_fte`] = row[`${level}_agreed_fte`]
    payload[`${level}_not_agreed_fte`] = row[`${level}_not_agreed_fte`]
    payload[`${level}_final_fte`] = row[`${level}_final_fte`]
  }
  return payload
}

function apiErrorMessage(caught, fallback) {
  const response = caught?.response?.data
  if (Array.isArray(response?.errors) && response.errors.length) {
    return response.errors.map((item) => item.error || JSON.stringify(item)).join(' ')
  }
  return response?.error || response?.detail || caught?.message || fallback
}

async function saveData() {
  if (!pendingRows.value.length || busy.value || loading.value) return
  busy.value = true
  error.value = ''
  success.value = ''
  try {
    const { data } = await axios.post('/api/migration-dashboard/scope-statements/data/', {
      uniqueData: pendingRows.value.map(buildSavePayload)
    })
    success.value = `Created ${data.created_count}; updated ${data.updated_count}.`
    const saveErrors = data.error_count ? data.errors.map((item) => item.error).join(' ') : ''
    await loadData()
    if (saveErrors) error.value = saveErrors
  } catch (caught) {
    error.value = apiErrorMessage(caught, 'Unable to save Scope Statement records.')
  } finally {
    busy.value = false
  }
}

async function deleteSelected() {
  if (!selectedIds.value.length || busy.value || loading.value) return
  const confirmed = window.confirm(
    'Delete the selected Scope Statement records and their evidence files? This cannot be undone.'
  )
  if (!confirmed) return

  busy.value = true
  error.value = ''
  success.value = ''
  try {
    const { data } = await axios.delete('/api/migration-dashboard/scope-statements/data/delete/', {
      data: { removedIds: selectedIds.value }
    })
    success.value = `Deleted ${data.deleted_count} Scope Statement record(s).`
    const deleteErrors = data.error_count ? data.errors.map((item) => item.error).join(' ') : ''
    selectedIds.value = []
    await loadData()
    if (deleteErrors) error.value = deleteErrors
  } catch (caught) {
    error.value = apiErrorMessage(caught, 'Unable to delete Scope Statement records.')
  } finally {
    busy.value = false
  }
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await axios.get('/api/migration-dashboard/scope-statements/')
    columns.value = data.columns || []
    rows.value = (data.rows || []).map((row) => ({
      ...row,
      _rowKey: `statement-${row.statement_id}`
    }))
    originalSnapshots.value = Object.fromEntries(
      rows.value.map((row) => [row._rowKey, rowSnapshot(row)])
    )
    selectedIds.value = []
  } catch (caught) {
    error.value = caught?.response?.data?.error || caught?.response?.data?.detail || caught.message
  } finally {
    loading.value = false
  }
}

function reloadData() {
  if (canLeave()) loadData()
}

onMounted(loadData)
</script>

<style scoped>
.scope-database-toolbar {
  display: flex;
  align-items: end;
  flex-wrap: wrap;
  gap: 14px;
  margin-bottom: 18px;
}

.pending-count {
  margin-bottom: 9px;
  color: #945200;
  font-size: 13px;
  font-weight: 600;
}

.success-message {
  padding: 10px 12px;
  border-left: 3px solid #21845b;
  background: #edf8f1;
  color: #155f3d;
  font-size: 13px;
}

.search-field {
  display: grid;
  gap: 5px;
  color: #526270;
  font-size: 12px;
}

.search-field input {
  width: min(360px, 72vw);
  min-height: 38px;
  padding: 7px 10px;
  border: 1px solid #bbc7cf;
  border-radius: 4px;
  background: #fff;
  color: #1d2b34;
  font: inherit;
  font-size: 14px;
}

.row-count {
  margin: 0 auto 9px 0;
  color: #5f6f79;
  font-size: 13px;
}

.table-state {
  padding: 28px 14px;
  border-top: 1px solid #d8e0e5;
  color: #526270;
}

.table-scroll {
  max-width: 100%;
  overflow: auto;
  border: 1px solid #d4dde3;
  background: #fff;
}

.scope-database-table {
  width: max-content;
  min-width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 12px;
}

.scope-database-table th,
.scope-database-table td {
  max-width: 300px;
  min-width: 90px;
  padding: 9px 11px;
  overflow: hidden;
  border-right: 1px solid #e0e6ea;
  border-bottom: 1px solid #e0e6ea;
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.scope-database-table td input,
.scope-database-table td textarea {
  width: 100%;
  min-width: 110px;
  padding: 5px 6px;
  border: 1px solid #9baeb8;
  border-radius: 3px;
  background: #fff;
  color: #1d2b34;
  font: inherit;
}

.scope-database-table td textarea {
  min-width: 220px;
  resize: vertical;
}

.scope-database-table .selection-cell {
  position: sticky;
  left: 0;
  z-index: 2;
  min-width: 72px;
  background: #fff;
}

.scope-database-table th.selection-cell {
  z-index: 3;
  background: #eef3f5;
}

.scope-database-table tr.is-pending td {
  background: #fff9e8;
}

.discard-row {
  border: 0;
  background: transparent;
  color: #8d3232;
  cursor: pointer;
  font: inherit;
}

.scope-database-table th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: #eef3f5;
  color: #243641;
  font-weight: 650;
}

.scope-database-table tbody tr:hover td {
  background: #f4f8f8;
}

.open-project-link {
  color: #006b73;
  font-weight: 600;
}
</style>