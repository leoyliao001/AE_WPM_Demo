<template>
  <div class="gsc-page">
    <div class="gsc-page-inner">
      <header class="gsc-toolbar">
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
          <mc-tag appearance="info" fit="small" label="GSC Site Mapping" />
          <h1 class="page-title">GSC Site Mapping</h1>
          <span class="meta-pill">{{ rowCount }} rows</span>
          <button
            type="button"
            class="meta-pill meta-pill--help"
            @click="helpDialogOpen = true"
          >
            How to use
          </button>
          <span v-if="loading" class="meta-pill meta-pill--loading">Loading…</span>
          <span v-else-if="error" class="meta-pill meta-pill--error">{{ error }}</span>
        </div>
        <div class="toolbar-right">
          <span v-if="pendingCount" class="meta-pill meta-pill--pending">
            {{ pendingCount }} pending
          </span>
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
        <span>Loading GSC Site Mapping…</span>
      </div>

      <div
        id="gsc-handsontable"
        ref="hotContainer"
        class="ht-theme-horizon handsontable-host"
        :class="{ 'is-hidden': loading && !hotReady }"
      />

      <mc-dialog
        :open="helpDialogOpen"
        heading="GSC Site Mapping — User Guide"
        dimension="medium"
        showclosebutton
        @closing="helpDialogOpen = false"
      >
        <div class="help-dialog-body">
          <section class="help-section">
            <h3>What this table is for</h3>
            <p>
              Maintain <strong>Region</strong>, <strong>Area</strong>,
              <strong>Supporting GSC Sites</strong>, and <strong>All options</strong>. Edit cells,
              add or remove rows, then click <strong>Save</strong>.
            </p>
          </section>
          <section class="help-section">
            <h3>Edit and save</h3>
            <ul>
              <li>Edit any cell directly. Pending changes are tracked until you Save.</li>
              <li>Use the context menu to insert or remove rows.</li>
              <li>Press <strong>Ctrl + S</strong> (Cmd + S on Mac) to save.</li>
              <li>Use column filters via the ⋮ menu on each header.</li>
            </ul>
          </section>
        </div>
      </mc-dialog>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'
import axios from 'axios'
import Handsontable from 'handsontable'
import 'handsontable/styles/handsontable.min.css'
import 'handsontable/styles/ht-theme-horizon.min.css'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-tag'
import '@maersk-global/mds-components-core/mc-loading-indicator'
import '@maersk-global/mds-components-core/mc-dialog'
import {
  hasStoredColumnWidths,
  loadColumnWidths,
  persistColumnWidths,
  resolveColumnWidth
} from '../utils/handsontableColumnWidths.js'

const ALL_COLUMNS = [
  { key: 'region', label: 'Region', width: 120 },
  { key: 'area', label: 'Area', width: 120 },
  { key: 'supporting_gsc_sites', label: 'Supporting GSC Sites', width: 280 },
  { key: 'all_options', label: 'All options', width: 200 }
]

const ALL_KEYS = ALL_COLUMNS.map((c) => c.key)
const COLUMN_WIDTH_STORAGE_ID = 'gsc-site-mapping'

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
const helpDialogOpen = ref(false)

const pendingCount = computed(() => allChanges.value.length)

function emptyRow() {
  const row = { id: null, _cid: crypto.randomUUID() }
  ALL_KEYS.forEach((key) => {
    row[key] = ''
  })
  return row
}

function normalizeCellValue(value) {
  if (value === null || value === undefined) return ''
  return String(value).replace(/\r\n/g, '\n').trim()
}

function isBlankRow(item) {
  return ALL_KEYS.every((key) => !normalizeCellValue(item[key]))
}

function trackChangedRow(hot, visualRow) {
  const physicalRow =
    typeof hot.toPhysicalRow === 'function' ? hot.toPhysicalRow(visualRow) : visualRow
  const src = hot.getSourceDataAtRow(physicalRow)
  if (!src) return

  if (!src._cid && (src.id == null || src.id === '')) {
    src._cid = crypto.randomUUID()
  }

  const snapshot = {
    id: src.id ?? null,
    _cid: src._cid
  }
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

  const data = rows.map((r) => {
    const row = emptyRow()
    ALL_KEYS.forEach((k) => {
      row[k] = r[k] ?? ''
    })
    row.id = r.id ?? null
    return row
  })

  for (let i = 0; i < 5; i += 1) {
    data.push(emptyRow())
  }

  const tableHeight = syncTableHeight()
  // Prefer saved widths over stretch-to-fill once the user has customized columns.
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
        copy: {
          name: 'Copy',
          callback() {
            this.getPlugin('copyPaste')?.copyCellsOnly()
          }
        },
        copy_with_column_headers: {
          name: 'Copy with headers',
          callback() {
            this.getPlugin('copyPaste')?.copyWithColumnHeaders()
          },
          disabled() {
            return !this.getSelectedLast()
          }
        },
        cut: {
          name: 'Cut',
          callback() {
            this.getPlugin('copyPaste')?.cut()
          }
        },
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
      if (!['edit', 'Autofill.fill', 'CopyPaste.paste', 'UndoRedo.undo', 'UndoRedo.redo'].includes(source)) {
        return
      }
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

      const confirmed = confirm(
        'The rows will be deleted permanently and can not be restored. Continue?'
      )
      if (!confirmed) return false
      if (idsToRemove.length === 0) return true

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
    const { data } = await axios.post('/api/gsc-site-mapping/data/', { uniqueData })
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
    console.error(e)
    const msg =
      e?.response?.data?.error ||
      e?.response?.data?.detail ||
      e.message ||
      'Save failed'
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
    const { data } = await axios.delete('/api/gsc-site-mapping/data/delete/', {
      data: { removedIds: idsToRemove }
    })
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
    console.error(e)
    const msg =
      e?.response?.data?.error ||
      e?.response?.data?.detail ||
      e.message ||
      'Delete failed'
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
    const { data } = await axios.get('/api/gsc-site-mapping/')
    rowCount.value = data.count || 0
    await nextTick()
    initHot(data.rows || [])
  } catch (e) {
    console.error(e)
    error.value = e?.response?.data?.detail || e.message || 'Failed to load GSC Site Mapping'
    destroyHot()
  } finally {
    loading.value = false
    await nextTick()
    onResize()
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
.gsc-page {
  background: #f3f4f6;
  box-sizing: border-box;
  display: flex;
  flex: 1;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.gsc-page-inner {
  box-sizing: border-box;
  display: flex;
  flex: 1;
  flex-direction: column;
  margin: 0;
  max-width: none;
  min-height: 0;
  padding: 10px 12px 12px;
  width: 100%;
}

.gsc-toolbar {
  align-items: center;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  display: flex;
  flex-shrink: 0;
  gap: 8px;
  justify-content: space-between;
  margin-bottom: 8px;
  min-height: 0;
  padding: 4px 10px;
}

.toolbar-left,
.toolbar-right {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 10px;
}

.back-link {
  display: inline-flex;
  text-decoration: none;
}

.page-title {
  color: #161616;
  font-family: 'Maersk Headline', 'Maersk Text', sans-serif;
  font-size: 16px;
  font-weight: 400;
  letter-spacing: -0.01em;
  margin: 0;
}

.meta-pill {
  background: #f6f7f9;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  color: #425466;
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
}

.meta-pill--help {
  background: #eef6fb;
  border-color: #b8d9eb;
  color: #0077b8;
  cursor: pointer;
  font-family: 'Maersk Text', sans-serif;
}

.meta-pill--help:hover {
  background: #dceef8;
  border-color: #0077b8;
}

.meta-pill--loading {
  color: #0077b8;
}

.meta-pill--error {
  background: #fdecec;
  border-color: #f5c2c2;
  color: #c4000a;
  max-width: 360px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta-pill--pending {
  background: #fff6e8;
  border-color: #f5d5a6;
  color: #b35c00;
}

.help-dialog-body {
  color: #161616;
  font-size: 14px;
  line-height: 1.55;
  max-height: 60vh;
  overflow-y: auto;
  padding: 4px 0;
}

.help-section {
  margin-bottom: 20px;
}

.help-section:last-child {
  margin-bottom: 0;
}

.help-section h3 {
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 8px;
}

.help-section p,
.help-section ul {
  margin: 0;
}

.help-section ul {
  padding-left: 20px;
}

.table-loading {
  align-items: center;
  color: #6c757d;
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 12px;
  justify-content: center;
  min-height: 240px;
}

.handsontable-host {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  width: 100%;
}

.handsontable-host.is-hidden {
  display: none;
}
</style>
