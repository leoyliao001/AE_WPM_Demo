<template>
  <div class="migration-team-page">
    <div class="migration-team-page-inner">
      <header class="migration-team-toolbar">
        <div class="toolbar-left">
          <router-link class="back-link" to="/project-attributes">
            <mc-button appearance="neutral" variant="plain" fit="small" label="Back" icon="mi-arrow-left" />
          </router-link>
          <mc-tag appearance="info" fit="small" label="Project Attributes" />
          <h1 class="page-title">Migration Team</h1>
          <span class="meta-pill">{{ rowCount }} rows</span>
          <span v-if="loading" class="meta-pill">Loading…</span>
        </div>
        <div class="toolbar-right">
          <span v-if="pendingCount" class="meta-pill meta-pill--pending">{{ pendingCount }} pending</span>
          <mc-button
            appearance="neutral"
            variant="outlined"
            fit="small"
            label="Add row"
            :disabled="loading || saving || deleting"
            @click="addRow"
          />
          <mc-button
            appearance="primary"
            fit="small"
            :label="saving ? 'Saving…' : 'Save'"
            icon="mi-floppy-disk"
            :disabled="loading || saving || deleting || pendingCount === 0"
            :title="saving ? 'Saving changes…' : 'Ctrl + S'"
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

      <p v-if="error" class="migration-team-error" role="alert">{{ error }}</p>
      <div v-if="loading && !hotReady" class="table-loading">
        <mc-loading-indicator size="large" />
        <span>Loading Migration Team…</span>
      </div>
      <div
        id="migration-team-handsontable"
        ref="hotContainer"
        class="ht-theme-horizon handsontable-host"
        :class="{ 'is-hidden': loading && !hotReady }"
      />
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
import {
  hasStoredColumnWidths,
  loadColumnWidths,
  persistColumnWidths,
  resolveColumnWidth
} from '../utils/handsontableColumnWidths.js'

const ROLE_OPTIONS = ['Manager', 'Member']
const ALL_COLUMNS = [
  { key: 'role', label: 'Role', width: 220 },
  { key: 'email', label: 'Email', width: 320 }
]
const ALL_KEYS = ALL_COLUMNS.map((column) => column.key)
const COLUMN_WIDTH_STORAGE_ID = 'migration-team'

const hotContainer = ref(null)
const hotInstance = shallowRef(null)
const hotReady = ref(false)
const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const error = ref('')
const rowCount = ref(0)
const allChanges = ref([])
const pendingCount = computed(() => allChanges.value.length)

function emptyRow() {
  return { id: null, _cid: crypto.randomUUID(), role: '', email: '' }
}

function normalizeCellValue(value) {
  return value == null ? '' : String(value).trim()
}

function isBlankRow(row) {
  return ALL_KEYS.every((key) => !normalizeCellValue(row[key]))
}

function trackChangedRow(hot, visualRow) {
  const physicalRow =
    typeof hot.toPhysicalRow === 'function' ? hot.toPhysicalRow(visualRow) : visualRow
  const source = hot.getSourceDataAtRow(physicalRow)
  if (!source) return
  if (!source._cid && (source.id == null || source.id === '')) source._cid = crypto.randomUUID()

  const snapshot = { id: source.id ?? null, _cid: source._cid }
  ALL_KEYS.forEach((key) => {
    snapshot[key] = normalizeCellValue(source[key])
  })
  const key = snapshot.id != null ? `id:${snapshot.id}` : `cid:${snapshot._cid}`
  allChanges.value = [
    ...allChanges.value.filter((row) => {
      const rowKey = row.id != null ? `id:${row.id}` : `cid:${row._cid}`
      return rowKey !== key
    }),
    snapshot
  ]
}

function destroyHot() {
  if (hotInstance.value && !hotInstance.value.isDestroyed) hotInstance.value.destroy()
  hotInstance.value = null
  hotReady.value = false
}

function syncTableHeight() {
  const element = hotContainer.value
  if (!element) return 480
  const wasHidden = element.classList.contains('is-hidden')
  if (wasHidden) element.classList.remove('is-hidden')
  element.style.height = ''
  void element.offsetHeight
  let height = Math.floor(element.clientHeight || 0)
  if (height < 280) {
    const top = element.getBoundingClientRect().top || 120
    height = Math.max(Math.floor(window.innerHeight - top - 24), 280)
  }
  height = Math.max(height - 2, 280)
  element.style.height = `${height}px`
  if (wasHidden) element.classList.add('is-hidden')
  return height
}

function initHot(rows) {
  if (!hotContainer.value) return
  destroyHot()
  allChanges.value = []

  const data = rows.map((row) => ({
    id: row.id,
    _cid: crypto.randomUUID(),
    role: row.role ?? '',
    email: row.email ?? ''
  }))
  for (let index = 0; index < 5; index += 1) data.push(emptyRow())

  const widths = loadColumnWidths(COLUMN_WIDTH_STORAGE_ID)
  const stretchH = hasStoredColumnWidths(COLUMN_WIDTH_STORAGE_ID) ? 'none' : 'all'
  const hot = new Handsontable(hotContainer.value, {
    data,
    columns: [
      {
        data: 'role',
        type: 'dropdown',
        source: ROLE_OPTIONS,
        strict: true,
        allowInvalid: false,
        width: resolveColumnWidth(ALL_COLUMNS[0].width, 'role', widths)
      },
      {
        data: 'email',
        type: 'text',
        width: resolveColumnWidth(ALL_COLUMNS[1].width, 'email', widths)
      }
    ],
    colHeaders: ALL_COLUMNS.map((column) => column.label),
    rowHeaders: false,
    height: syncTableHeight(),
    width: '100%',
    stretchH,
    autoWrapRow: false,
    autoWrapCol: false,
    autoRowSize: false,
    manualColumnResize: true,
    manualRowResize: true,
    filters: true,
    dropdownMenu: ['filter_by_condition', 'filter_by_value', 'filter_action_bar'],
    multiColumnSorting: true,
    minSpareRows: 1,
    contextMenu: {
      items: {
        row_above: { name: 'Insert row above' },
        row_below: { name: 'Insert row below' },
        remove_row: { name: 'Remove row' },
        sp1: '---------',
        undo: { name: 'Undo' },
        redo: { name: 'Redo' }
      }
    },
    afterColumnResize() {
      persistColumnWidths(this, COLUMN_WIDTH_STORAGE_ID, ALL_KEYS)
      if (this.getSettings()?.stretchH !== 'none') this.updateSettings({ stretchH: 'none' })
    },
    afterChange(changes, source) {
      if (!changes || source === 'loadData' || source === 'api') return
      if (!['edit', 'Autofill.fill', 'CopyPaste.paste', 'UndoRedo.undo', 'UndoRedo.redo'].includes(source)) return
      const changedRows = new Set(changes.map(([visualRow]) => visualRow))
      changedRows.forEach((visualRow) => trackChangedRow(this, visualRow))
    },
    beforeRemoveRow(_index, amount, physicalRows) {
      if (deleting.value) return false
      const ids = []
      for (let index = 0; index < amount; index += 1) {
        const row = this.getSourceDataAtRow(physicalRows[index])
        if (row?.id != null && row.id !== '') ids.push(row.id)
      }
      if (!ids.length) return true
      if (!window.confirm(`Permanently delete ${ids.length} saved row(s)? This cannot be undone.`)) {
        return false
      }
      void deleteRows(ids)
      return false
    },
    afterInit() {
      requestAnimationFrame(() => {
        if (!this.isDestroyed) this.refreshDimensions()
      })
    },
    licenseKey: 'non-commercial-and-evaluation',
    themeName: 'ht-theme-horizon',
    className: 'htLeft htMiddle',
    headerClassName: 'htLeft'
  })
  hotInstance.value = hot
  hotReady.value = true
}

function addRow() {
  const hot = hotInstance.value
  if (!hot || hot.isDestroyed) return
  hot.alter('insert_row_below', Math.max(0, hot.countRows() - 1))
  const row = hot.countRows() - 2
  hot.selectCell(Math.max(0, row), 0)
  hot.getActiveEditor()?.beginEditing()
}

function onResize() {
  const hot = hotInstance.value
  if (!hot || hot.isDestroyed) return
  hot.updateSettings({ height: syncTableHeight() })
  hot.refreshDimensions()
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await axios.get('/api/migration-team/')
    rowCount.value = data.count || 0
    await nextTick()
    initHot(data.rows || [])
  } catch (requestError) {
    console.error(requestError)
    error.value =
      requestError?.response?.data?.error ||
      requestError?.response?.data?.detail ||
      requestError.message ||
      'Failed to load Migration Team.'
    destroyHot()
  } finally {
    loading.value = false
    await nextTick()
    onResize()
  }
}

async function saveData() {
  if (saving.value || deleting.value || !allChanges.value.length) return
  const uniqueData = [...new Map(
    allChanges.value.map((row) => [row.id != null ? `id:${row.id}` : `cid:${row._cid}`, row])
  ).values()]
    .filter((row) => !isBlankRow(row))
    .map((row) => ({ id: row.id, role: row.role, email: row.email }))

  if (!uniqueData.length) {
    error.value = 'Add a role and email before saving.'
    return
  }

  saving.value = true
  error.value = ''
  try {
    const { data } = await axios.post('/api/migration-team/data/', { uniqueData })
    const errors = data.errors || []
    allChanges.value = []
    await loadData()
    if (errors.length) error.value = errors.map((item) => item.error).join(' ')
  } catch (requestError) {
    console.error(requestError)
    const rowErrors = requestError?.response?.data?.errors
    error.value =
      (Array.isArray(rowErrors) && rowErrors.map((item) => item.error).join(' ')) ||
      requestError?.response?.data?.error ||
      requestError?.response?.data?.detail ||
      requestError.message ||
      'Save failed.'
  } finally {
    saving.value = false
  }
}

async function deleteRows(ids) {
  if (deleting.value) return
  deleting.value = true
  error.value = ''
  try {
    const { data } = await axios.delete('/api/migration-team/data/delete/', {
      data: { removedIds: ids }
    })
    allChanges.value = []
    await loadData()
    if (data.error_count) error.value = data.errors.map((item) => item.error).join(' ')
  } catch (requestError) {
    console.error(requestError)
    error.value =
      requestError?.response?.data?.error ||
      requestError?.response?.data?.detail ||
      requestError.message ||
      'Delete failed.'
  } finally {
    deleting.value = false
  }
}

function handleGlobalKeydown(event) {
  if (!(event.ctrlKey || event.metaKey) || !['s', 'S'].includes(event.key)) return
  event.preventDefault()
  saveData()
}

onMounted(() => {
  void loadData()
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
.migration-team-page {
  background: #f3f4f6;
  box-sizing: border-box;
  display: flex;
  flex: 1;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.migration-team-page-inner {
  box-sizing: border-box;
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
  padding: 10px 12px 12px;
  width: 100%;
}

.migration-team-toolbar {
  align-items: center;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  display: flex;
  flex-shrink: 0;
  gap: 8px;
  justify-content: space-between;
  margin-bottom: 8px;
  min-height: 52px;
  padding: 6px 10px;
}

.toolbar-left, .toolbar-right {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.page-title { color: #172b4d; font-size: 19px; margin: 0 4px; }
.meta-pill { color: #52616b; font-size: 13px; white-space: nowrap; }
.meta-pill--pending { color: #8a5700; }
.back-link { text-decoration: none; }
.migration-team-error { color: #b42318; margin: 4px 2px 10px; }

.handsontable-host {
  flex: 1;
  min-height: 280px;
  overflow: hidden;
}

.handsontable-host.is-hidden { visibility: hidden; }

.table-loading {
  align-items: center;
  color: #52616b;
  display: flex;
  gap: 10px;
  justify-content: center;
  min-height: 160px;
}

@media (max-width: 760px) {
  .migration-team-toolbar { align-items: flex-start; flex-direction: column; }
  .toolbar-right { width: 100%; }
}
</style>
