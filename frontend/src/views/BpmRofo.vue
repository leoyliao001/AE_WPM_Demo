<template>
  <div class="bpm-page">
    <div class="bpm-page-inner">
      <header class="bpm-toolbar">
        <div class="toolbar-left">
          <router-link class="back-link" to="/project-attributes">
            <mc-button
              appearance="neutral"
              variant="plain"
              fit="small"
              label="Back"
              icon="mi-arrow-left"
            />
          </router-link>
          <mc-tag appearance="info" fit="small" label="BPM ROFO" />
          <h1 class="page-title">BPM ROFO</h1>
          <span class="meta-pill">{{ rowCount }} rows</span>
          <label class="year-picker">
            <span>Year</span>
            <select :value="selectedYear" @change="onYearChange">
              <option v-for="year in yearOptions" :key="year" :value="year">{{ year }}</option>
            </select>
          </label>
          <span v-if="loading" class="meta-pill meta-pill--loading">Loading…</span>
          <span v-else-if="error" class="meta-pill meta-pill--error">{{ error }}</span>
        </div>
        <div class="toolbar-right">
          <span v-if="pendingCount" class="meta-pill meta-pill--pending">{{ pendingCount }} pending</span>
          <mc-button
            v-if="isAdmin"
            appearance="neutral"
            variant="plain"
            fit="small"
            label="Field Mapping"
            icon="mi-information"
            title="Excel header to database field (admin only)"
            @click="mappingDialogOpen = true"
          />
          <mc-button
            appearance="neutral"
            variant="outlined"
            fit="small"
            label="Download Template"
            icon="mi-arrow-to-bottom"
            title="Download an empty Excel template with the expected headers"
            @click="downloadTemplate"
          />
          <label class="upload-box">
            <input ref="uploadInput" type="file" accept=".xlsx,.xls,.csv" @change="handleUpload" />
            <span>Upload Excel</span>
          </label>
          <mc-button
            appearance="primary"
            fit="small"
            :label="saving ? 'Saving…' : 'Save'"
            icon="mi-floppy-disk"
            :disabled="loading || saving || deleting || pendingCount === 0"
            :title="saving ? saveProgressMessage : 'Ctrl + S'"
            @click="saveData"
          />
          <mc-button
            appearance="neutral"
            variant="plain"
            fit="small"
            label="Reload"
            icon="mi-arrow-clockwise"
            :disabled="loading || saving || deleting"
            @click="loadData"
          />
        </div>
      </header>

      <div v-if="loading && !hotReady" class="table-loading">
        <mc-loading-indicator size="large" />
        <span>Loading BPM ROFO…</span>
      </div>

      <div
        id="bpm-rofo-handsontable"
        ref="hotContainer"
        class="ht-theme-horizon handsontable-host"
        :class="{ 'is-hidden': loading && !hotReady }"
      />

      <mc-dialog
        :open="mappingDialogOpen"
        heading="Field Mapping — BPM ROFO"
        dimension="large"
        showclosebutton
        @closing="mappingDialogOpen = false"
      >
        <div class="mapping-dialog-body">
          <p class="mapping-summary">
            How the importer reads an uploaded sheet. {{ mappingRows.length }} columns reported by the API<span v-if="mappingHiddenCount">, {{ mappingHiddenCount }} not rendered in the grid</span>.
          </p>
          <table class="mapping-table">
            <thead>
              <tr>
                <th>Excel header</th>
                <th>Database field</th>
                <th>Also accepted</th>
                <th>On upload</th>
                <th>In grid</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in mappingRows" :key="row.key">
                <td>{{ row.label }}</td>
                <td><code>{{ row.key }}</code></td>
                <td class="mapping-aliases">{{ row.alsoAccepted.join(', ') || '—' }}</td>
                <td>{{ row.computed ? 'derived' : 'mapped' }}</td>
                <td :class="{ 'mapping-drift': !row.inGrid }">{{ row.inGrid ? 'shown' : 'not shown' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </mc-dialog>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'
import axios from 'axios'
import Handsontable from 'handsontable'
import * as XLSX from 'xlsx'
import 'handsontable/styles/handsontable.min.css'
import 'handsontable/styles/ht-theme-horizon.min.css'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-tag'
import '@maersk-global/mds-components-core/mc-loading-indicator'
import '@maersk-global/mds-components-core/mc-dialog'
import { fetchMyAttributesAccess } from '../utils/attributesAccess.js'
import { createRowPicker, describeMapping } from '../utils/bpmUploadMapping.js'
import {
  hasStoredColumnWidths,
  loadColumnWidths,
  persistColumnWidths,
  resolveColumnWidth
} from '../utils/handsontableColumnWidths.js'

const ALL_COLUMNS = [
  { key: 'status', label: 'Status', width: 100 },
  { key: 'country', label: 'Country', width: 140 },
  { key: 'region', label: 'Region', width: 120 },
  { key: 'area', label: 'Area', width: 160 },
  { key: 'gsc_site', label: 'GSC Site to be Offshored', width: 160 },
  { key: 'function', label: 'Function', width: 160 },
  { key: 'function_id_description', label: 'Function ID + Description', width: 200 },
  { key: 'product', label: 'Product', width: 180 },
  { key: 'cost_center', label: 'Cost Center', width: 140 },
  { key: 'pid', label: 'PID', width: 120 },
  { key: 'project_name', label: 'Project Name', width: 220 },
  { key: 'part_not_part_of_rofo', label: 'Part/Not part of ROFO', width: 180 },
  { key: 'gsc_leader', label: 'GSC Leaders', width: 160 },
  { key: 'gsc1_leader', label: 'GSC-1 Leaders', width: 160 },
  { key: 'bpm_owner', label: 'BPM Owner', width: 180 },
  { key: 'bu', label: 'BU', width: 100 },
  { key: 'frontline_staff_cost_per_fte', label: 'Frontline Staff Cost per FTE', width: 180 },
  { key: 'gsc_staff_cost_per_fte', label: 'GSC Staff Cost per FTE', width: 180 },
  { key: 'project_cost', label: 'Project Cost', width: 140 },
  { key: 'x_column', label: 'X', width: 80 },
  { key: 'base_pids', label: 'Base PIDs', width: 140 },
  { key: 'positions_to_be_offshored_in_gsc', label: 'Positions to be Offshored in GSC', width: 180 },
  { key: 'positions_to_be_released_in_frontline', label: 'Positions to be Released in Frontline', width: 200 },
  { key: 'rofo_value', label: 'ROFO Value', width: 150 },
  { key: 'year', label: 'Year', width: 100 },
  { key: 'onboarding_month', label: 'Onboarding Month', width: 180 },
  { key: 'notes', label: 'Notes', width: 260 }
]

const ALL_KEYS = ALL_COLUMNS.map((c) => c.key)
const COLUMN_WIDTH_BY_KEY = new Map(ALL_COLUMNS.map((c) => [c.key, c.width]))

// Header spellings the importer still honours beyond a column's own label and
// field key, for spreadsheets written before the download template existed.
const UPLOAD_HEADER_ALIASES = {
  project_name: ['project'],
  product: ['product_name'],
  onboarding_month: ['onboarding'],
  bpm_owner: ['owner'],
  gsc1_leader: ['gsc_1_leader'],
  notes: ['comment'],
  positions_to_be_offshored_in_gsc: ['positions_to_be_offshored', 'positions'],
  rofo_value: ['rofo', 'value']
}

// Filled by the logic in handleUpload rather than a straight header match.
const UPLOAD_COMPUTED_KEYS = ['positions_to_be_offshored_in_gsc', 'rofo_value', 'year']
const DEFAULT_TEMPLATE_WIDTH = 140
const COLUMN_WIDTH_STORAGE_ID = 'bpm-rofo'

const hotContainer = ref(null)
const hotInstance = shallowRef(null)
const hotReady = ref(false)
const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const error = ref('')
const rowCount = ref(0)
const allChanges = ref([])
const saveProgressMessage = ref('')
const uploadInput = ref(null)
const serverColumns = ref([])
const isAdmin = ref(false)
const mappingDialogOpen = ref(false)
const currentYear = new Date().getFullYear()
const selectedYear = ref(currentYear)

const yearOptions = computed(() => {
  const years = []
  for (let i = -2; i <= 2; i += 1) {
    years.push(currentYear + i)
  }
  return years
})
const pendingCount = computed(() => allChanges.value.length)

// Headers for the upload template follow the column list the API reports, so a
// backend field change shows up in the template without a frontend edit.
// ALL_COLUMNS is only the fallback for when the first load has not landed yet.
const templateColumns = computed(() => {
  const fromServer = serverColumns.value
    .filter((col) => col && col.key)
    .map((col) => ({
      key: col.key,
      label: col.label || col.key,
      width: COLUMN_WIDTH_BY_KEY.get(col.key) || DEFAULT_TEMPLATE_WIDTH
    }))
  return fromServer.length ? fromServer : ALL_COLUMNS
})

const mappingRows = computed(() =>
  describeMapping(templateColumns.value, {
    aliases: UPLOAD_HEADER_ALIASES,
    computedKeys: UPLOAD_COMPUTED_KEYS,
    gridKeys: ALL_KEYS
  })
)
const mappingHiddenCount = computed(() => mappingRows.value.filter((row) => !row.inGrid).length)

function normalizeCellValue(value) {
  if (value === null || value === undefined) return ''
  return String(value).replace(/\r\n/g, '\n').trim()
}

function emptyRow() {
  const row = { id: null, _cid: crypto.randomUUID() }
  ALL_KEYS.forEach((key) => {
    row[key] = key === 'year' ? selectedYear.value : ''
  })
  return row
}

function isBlankRow(item) {
  return ALL_KEYS.every((key) => !normalizeCellValue(item[key]))
}

function trackChangedRow(hot, visualRow) {
  const physicalRow = typeof hot.toPhysicalRow === 'function' ? hot.toPhysicalRow(visualRow) : visualRow
  const src = hot.getSourceDataAtRow(physicalRow)
  if (!src) return

  if (!src._cid && (src.id == null || src.id === '')) {
    src._cid = crypto.randomUUID()
  }

  const snapshot = { id: src.id ?? null, _cid: src._cid }
  ALL_KEYS.forEach((key) => {
    snapshot[key] = normalizeCellValue(src[key])
  })

  const key = snapshot.id != null && snapshot.id !== '' ? `id:${snapshot.id}` : `cid:${snapshot._cid}`
  const next = allChanges.value.filter((item) => {
    const itemKey = item.id != null && item.id !== '' ? `id:${item.id}` : `cid:${item._cid}`
    return itemKey !== key
  })
  next.push(snapshot)
  allChanges.value = next
}

function buildColumns() {
  const storedWidths = loadColumnWidths(COLUMN_WIDTH_STORAGE_ID)
  return ALL_COLUMNS.map((col) => ({
    data: col.key,
    type: 'text',
    width: resolveColumnWidth(col.width, col.key, storedWidths)
  }))
}

function destroyHot() {
  if (hotInstance.value && !hotInstance.value.isDestroyed) {
    hotInstance.value.destroy()
  }
  hotInstance.value = null
  hotReady.value = false
}

function syncTableHeight() {
  const el = hotContainer.value
  if (!el) return 480

  const wasHidden = el.classList.contains('is-hidden')
  if (wasHidden) el.classList.remove('is-hidden')
  el.style.height = ''
  void el.offsetHeight

  let height = Math.floor(el.clientHeight || 0)
  if (height < 280) {
    const top = el.getBoundingClientRect().top || 120
    height = Math.max(Math.floor(window.innerHeight - top - 24), 280)
  }
  height = Math.max(height - 2, 280)
  el.style.height = `${height}px`
  if (wasHidden) el.classList.add('is-hidden')
  return height
}

function initHot(rows) {
  if (!hotContainer.value) return
  destroyHot()
  allChanges.value = []

  const data = rows.map((row) => {
    const out = emptyRow()
    ALL_KEYS.forEach((key) => {
      out[key] = row[key] ?? (key === 'year' ? selectedYear.value : '')
    })
    out.id = row.id ?? null
    return out
  })

  for (let i = 0; i < 5; i += 1) {
    data.push(emptyRow())
  }

  const tableHeight = syncTableHeight()
  const stretchH = hasStoredColumnWidths(COLUMN_WIDTH_STORAGE_ID) ? 'none' : 'all'

  const hot = new Handsontable(hotContainer.value, {
    data,
    columns: buildColumns(),
    colHeaders: ALL_COLUMNS.map((c) => c.label),
    rowHeaders: false,
    height: tableHeight,
    width: '100%',
    stretchH,
    autoWrapRow: false,
    autoWrapCol: false,
    textEllipsis: true,
    wordWrap: false,
    autoRowSize: false,
    manualColumnResize: true,
    manualRowResize: true,
    filters: true,
    dropdownMenu: ['filter_by_condition', 'filter_by_value', 'filter_action_bar'],
    multiColumnSorting: true,
    copyPaste: {
      copyColumnHeaders: true,
      copyColumnHeadersOnly: true
    },
    afterColumnResize() {
      persistColumnWidths(this, COLUMN_WIDTH_STORAGE_ID, ALL_KEYS)
      if (this.getSettings()?.stretchH !== 'none') {
        this.updateSettings({ stretchH: 'none' })
      }
    },
    contextMenu: {
      items: {
        row_above: { name: 'Insert row above' },
        row_below: { name: 'Insert row below' },
        remove_row: { name: 'Remove row' },
        sp1: '---------',
        copy: { name: 'Copy', callback() { this.getPlugin('copyPaste')?.copyCellsOnly() } },
        cut: { name: 'Cut', callback() { this.getPlugin('copyPaste')?.cut() } },
        sp2: '---------',
        undo: { name: 'Undo' },
        redo: { name: 'Redo' }
      }
    },
    minSpareRows: 1,
    licenseKey: 'non-commercial-and-evaluation',
    themeName: 'ht-theme-horizon',
    className: 'htLeft htMiddle',
    headerClassName: 'htLeft',
    afterChange(changes, source) {
      if (!changes || source === 'loadData' || source === 'api') return
      if (!['edit', 'Autofill.fill', 'CopyPaste.paste', 'UndoRedo.undo', 'UndoRedo.redo'].includes(source)) return
      const touchedRows = new Set()
      changes.forEach(([visualRow]) => touchedRows.add(visualRow))
      touchedRows.forEach((visualRow) => trackChangedRow(this, visualRow))
    },
    beforeRemoveRow(index, amount, physicalRows) {
      if (deleting.value) {
        alert('Delete in progress, please wait…')
        return false
      }

      const idsToRemove = []
      for (let i = 0; i < amount; i += 1) {
        const rowData = this.getSourceDataAtRow(physicalRows[i])
        const rowId = rowData?.id
        if (rowId != null && rowId !== '') {
          idsToRemove.push(rowId)
        }
      }

      if (idsToRemove.length === 0) return true
      const confirmed = confirm('The rows will be deleted permanently. Continue?')
      if (!confirmed) return false

      void runDeleteRows(idsToRemove)
      return false
    },
    afterInit() {
      requestAnimationFrame(() => {
        if (!this.isDestroyed) this.refreshDimensions()
      })
    }
  })

  hotInstance.value = hot
  hotReady.value = true
}

function onResize() {
  if (!hotInstance.value || hotInstance.value.isDestroyed) return
  const height = syncTableHeight()
  hotInstance.value.updateSettings({ height })
  hotInstance.value.refreshDimensions()
}

async function saveData() {
  if (saving.value || deleting.value) return
  if (allChanges.value.length === 0) {
    alert('No changes to save.')
    return
  }

  const deduped = new Map()
  allChanges.value.forEach((item) => {
    const key = item.id != null && item.id !== '' ? `id:${item.id}` : `cid:${item._cid}`
    deduped.set(key, item)
  })

  const uniqueData = [...deduped.values()]
    .filter((item) => !isBlankRow(item))
    .map((item) => {
      const payload = { id: item.id ?? null }
      ALL_KEYS.forEach((k) => {
        payload[k] = item[k] ?? ''
      })
      return payload
    })

  if (uniqueData.length === 0) {
    alert('No valid rows to save.')
    return
  }

  saving.value = true
  saveProgressMessage.value = `Saving ${uniqueData.length} row(s)…`
  error.value = ''

  try {
    const { data } = await axios.post('/api/bpm-rofo/data/', { uniqueData })
    const created = data.created_count || 0
    const updated = data.updated_count || 0
    const errCount = data.error_count || 0
    if (errCount > 0) {
      alert(`Saved with errors: created ${created}, updated ${updated}, errors ${errCount}.`)
    } else {
      alert(`Saved: created ${created}, updated ${updated}.`)
    }
    allChanges.value = []
    await loadData()
  } catch (e) {
    const msg = e?.response?.data?.error || e?.response?.data?.detail || e.message || 'Save failed'
    error.value = msg
    alert(`Save failed: ${msg}`)
  } finally {
    saving.value = false
    saveProgressMessage.value = ''
  }
}

async function runDeleteRows(idsToRemove) {
  if (deleting.value) return
  deleting.value = true
  error.value = ''
  try {
    const { data } = await axios.delete('/api/bpm-rofo/data/delete/', { data: { removedIds: idsToRemove } })
    const deletedCount = data.deleted_count || 0
    const errCount = data.error_count || 0
    if (errCount > 0) {
      alert(`Delete done: deleted ${deletedCount}, errors ${errCount}.`)
    } else {
      alert(`Delete done: deleted ${deletedCount} row(s).`)
    }
    allChanges.value = []
    await loadData()
  } catch (e) {
    const msg = e?.response?.data?.error || e?.response?.data?.detail || e.message || 'Delete failed'
    error.value = msg
    alert(`Delete failed: ${msg}`)
  } finally {
    deleting.value = false
  }
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await axios.get('/api/bpm-rofo/', { params: { year: selectedYear.value } })
    rowCount.value = data.count || 0
    serverColumns.value = Array.isArray(data.columns) ? data.columns : []
    await nextTick()
    initHot(data.rows || [])
  } catch (e) {
    error.value = e?.response?.data?.detail || e.message || 'Failed to load BPM ROFO'
    destroyHot()
  } finally {
    loading.value = false
    await nextTick()
    onResize()
  }
}

function onYearChange(event) {
  selectedYear.value = Number(event.target.value || currentYear)
  void loadData()
}

function downloadTemplate() {
  try {
    const columns = templateColumns.value
    const worksheet = XLSX.utils.aoa_to_sheet([columns.map((c) => c.label)])
    worksheet['!cols'] = columns.map((c) => ({ wch: Math.max(12, Math.round((c.width || DEFAULT_TEMPLATE_WIDTH) / 8)) }))
    const workbook = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(workbook, worksheet, 'BPM ROFO')
    XLSX.writeFile(workbook, `bpm-rofo-template-${selectedYear.value}.xlsx`)
  } catch (e) {
    const msg = e?.message || 'Failed to generate template'
    error.value = msg
    alert(`Download template failed: ${msg}`)
  }
}

async function handleUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return

  try {
    const arrayBuffer = await file.arrayBuffer()
    const workbook = XLSX.read(arrayBuffer, { type: 'array' })
    const sheet = workbook.Sheets[workbook.SheetNames[0]]
    const rows = XLSX.utils.sheet_to_json(sheet, { defval: '', raw: false })
    const columns = templateColumns.value
    const uniqueData = rows
      .map((row) => {
        const pick = createRowPicker(row, columns, UPLOAD_HEADER_ALIASES)
        const item = {}
        columns.forEach((col) => {
          item[col.key] = pick(col.key)
        })
        // The offshored-position count and the BPM ROFO value are the same
        // figure, so either header fills both fields.
        const positions = pick('positions_to_be_offshored_in_gsc') || pick('rofo_value')
        item.positions_to_be_offshored_in_gsc = positions
        item.rofo_value = positions
        item.year = pick('year') || selectedYear.value
        return item
      })
      .filter((item) => item.project_name || item.product || item.onboarding_month || item.rofo_value)

    if (!uniqueData.length) {
      alert('No valid rows found in the uploaded Excel file.')
      return
    }

    const { data } = await axios.post('/api/bpm-rofo/data/', { uniqueData })
    if (data.error_count > 0) {
      alert(`Upload completed with ${data.error_count} errors.`)
    } else {
      alert(`Uploaded ${data.success_count} row(s).`)
    }
    uploadInput.value = ''
    await loadData()
  } catch (e) {
    const msg = e?.response?.data?.error || e?.response?.data?.detail || e.message || 'Upload failed'
    error.value = msg
    alert(`Upload failed: ${msg}`)
  }
}

function handleGlobalKeydown(event) {
  if (!(event.ctrlKey || event.metaKey)) return
  if (event.key !== 's' && event.key !== 'S') return
  event.preventDefault()
  saveData()
}

onMounted(() => {
  loadData()
  fetchMyAttributesAccess().then((access) => {
    isAdmin.value = !!access?.is_super_admin
  })
  window.addEventListener('resize', onResize)
  document.addEventListener('keydown', handleGlobalKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  document.removeEventListener('keydown', handleGlobalKeydown)
  destroyHot()
})
</script>

<style scoped>
.bpm-page {
  background: #f3f4f6;
  box-sizing: border-box;
  display: flex;
  flex: 1;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}
.bpm-page-inner {
  box-sizing: border-box;
  display: flex;
  flex: 1;
  flex-direction: column;
  padding: 10px 12px 12px;
  width: 100%;
}
.bpm-toolbar {
  align-items: center;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
  padding: 6px 10px;
}
.toolbar-left, .toolbar-right {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.page-title {
  font-size: 1.3rem;
  margin: 0;
}
.meta-pill {
  background: #f3f4f6;
  border-radius: 999px;
  color: #111827;
  font-size: 0.75rem;
  padding: 4px 10px;
}
.meta-pill--error { background: #fee2e2; color: #991b1b; }
.meta-pill--loading { background: #e0f2fe; color: #075985; }
.meta-pill--pending { background: #fef3c7; color: #92400e; }
.year-picker {
  align-items: center;
  display: inline-flex;
  gap: 6px;
  font-size: 0.8rem;
}
.year-picker select {
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 6px 10px;
}
.upload-box {
  align-items: center;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  color: #1d4ed8;
  cursor: pointer;
  display: inline-flex;
  font-size: 0.8rem;
  padding: 7px 12px;
}
.upload-box input {
  display: none;
}
.table-loading {
  align-items: center;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 8px;
  padding: 24px;
}
.handsontable-host {
  flex: 1;
  min-height: 320px;
}
:deep(.handsontable) {
  width: 100% !important;
}
.mapping-dialog-body { display: flex; flex-direction: column; gap: 12px; }
.mapping-summary { margin: 0; font-size: 13px; color: #4a5568; line-height: 1.6; }
.mapping-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.mapping-table th,
.mapping-table td { padding: 6px 10px; text-align: left; border-bottom: 1px solid #e2e8f0; vertical-align: top; }
.mapping-table th { font-weight: 600; color: #00243d; background: #f7fafc; position: sticky; top: 0; }
.mapping-table code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; color: #2d3748; }
.mapping-aliases { color: #718096; font-size: 12px; }
.mapping-drift { color: #b7791f; font-weight: 600; }
</style>
