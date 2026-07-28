<template>
  <div class="pga-page">
    <div class="pga-page-inner">
      <header class="pga-toolbar">
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
          <mc-tag appearance="info" fit="small" label="Project Gantt" />
          <h1 class="page-title">Project Gantt</h1>
          <span v-if="loaded" class="meta-pill">{{ rowCount }} tasks</span>
          <span v-if="loading" class="meta-pill meta-pill--loading">Loading…</span>
          <span v-else-if="error" class="meta-pill meta-pill--error">{{ error }}</span>
        </div>
        <div class="toolbar-right">
          <span v-if="isDirty" class="meta-pill meta-pill--pending">Unsaved changes</span>
          <mc-button
            appearance="primary"
            fit="small"
            :label="saving ? 'Saving…' : 'Save'"
            icon="mi-floppy-disk"
            :disabled="!loaded || loading || saving || !isDirty"
            @click="saveData"
          />
          <mc-button
            appearance="neutral"
            variant="plain"
            fit="small"
            label="Reload"
            icon="mi-arrow-clockwise"
            :disabled="!migrationId.trim() || loading || saving"
            @click="loadData"
          />
        </div>
      </header>

      <section class="lookup-bar">
        <mc-input
          class="lookup-input"
          label="Migration ID"
          fit="small"
          width="full-width"
          placeholder="Enter Migration ID, e.g. WPM_PRJ_20260724342173"
          :value="migrationId"
          @input="onMigrationIdInput"
          @keydown="onMigrationKeydown"
        />
        <mc-button
          appearance="primary"
          variant="filled"
          fit="small"
          label="Load"
          icon="mi-magnifying-glass"
          :disabled="!migrationId.trim() || loading || saving"
          @click="loadData"
        />
      </section>

      <mc-notification
        v-if="!loaded && !loading && !error"
        appearance="info"
        fit="medium"
        heading="Enter a Migration ID"
        body="Project Gantt data is scoped by Migration Request ID. Enter an ID and click Load to view or edit tasks."
      />

      <template v-if="loaded">
        <section class="meta-panel" aria-label="Project parameters">
          <div class="meta-panel__head">
            <h2>{{ projectName || migrationRequestId }}</h2>
            <p>{{ migrationRequestId }}</p>
          </div>
          <div class="meta-panel__grid">
            <label v-for="field in metaFields" :key="field.key" class="meta-field">
              <span>{{ field.label }}</span>
              <input
                :type="field.type"
                :value="meta[field.key]"
                @input="onMetaInput(field.key, field.type, $event)"
              />
            </label>
          </div>
        </section>

        <div
          id="pga-handsontable"
          ref="hotContainer"
          class="ht-theme-horizon handsontable-host"
          :class="{ 'is-hidden': loading && !hotReady }"
        />
      </template>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'
import axios from 'axios'
import Handsontable from 'handsontable'
import 'handsontable/styles/handsontable.min.css'
import 'handsontable/styles/ht-theme-horizon.min.css'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-tag'
import '@maersk-global/mds-components-core/mc-input'
import '@maersk-global/mds-components-core/mc-notification'
import {
  hasStoredColumnWidths,
  loadColumnWidths,
  persistColumnWidths,
  resolveColumnWidth
} from '../utils/handsontableColumnWidths.js'

const ALL_COLUMNS = [
  { key: 'task_id', label: 'Task ID', width: 180 },
  { key: 'name', label: 'Task Name', width: 280 },
  { key: 'startWeek', label: 'Start Week', width: 110 },
  { key: 'endWeek', label: 'End Week', width: 110 },
  { key: 'phaseId', label: 'Phase ID', width: 180 }
]

const ALL_KEYS = ALL_COLUMNS.map((c) => c.key)
const COLUMN_WIDTH_STORAGE_ID = 'project-gantt-attributes'

const metaFields = [
  { key: 'projectPhase', label: 'Project Phase', type: 'text' },
  { key: 'scope', label: 'Scope', type: 'text' },
  { key: 'migratableFte', label: 'Migratable FTE', type: 'number' },
  { key: 'learningCurve', label: 'Learning Curve', type: 'number' },
  { key: 'tlTmHc', label: 'TL/TM HC', type: 'number' },
  { key: 'mngrHc', label: 'Mngr. HC', type: 'number' },
  { key: 'totalWoBuffer', label: 'Total wo/buffer', type: 'number' },
  { key: 'total', label: 'Total', type: 'number' }
]

const defaultMeta = () =>
  Object.fromEntries(metaFields.map((field) => [field.key, '']))

const hotContainer = ref(null)
const hotInstance = shallowRef(null)
const hotReady = ref(false)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const loaded = ref(false)
const isDirty = ref(false)
const migrationId = ref('')
const migrationRequestId = ref('')
const projectName = ref('')
const meta = ref(defaultMeta())
const phaseOptions = ref([
  'opportunity',
  'onboarding',
  'gss-training',
  'knowledge-transfer',
  'volume-rampup',
  'hypercare',
  'closure'
])
const rowCount = ref(0)

const readInputValue = (event) => event?.target?.value ?? event?.detail?.value ?? ''

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

function onMigrationIdInput(event) {
  migrationId.value = readInputValue(event)
}

function onMigrationKeydown(event) {
  if (event?.key === 'Enter' || event?.detail?.key === 'Enter') {
    event.preventDefault?.()
    loadData()
  }
}

function onMetaInput(key, type, event) {
  const raw = event.target.value
  if (type === 'number') {
    meta.value = {
      ...meta.value,
      [key]: raw === '' ? '' : Number.isFinite(Number(raw)) ? Number(raw) : raw
    }
  } else {
    meta.value = { ...meta.value, [key]: raw }
  }
  isDirty.value = true
}

function buildColumns() {
  const storedWidths = loadColumnWidths(COLUMN_WIDTH_STORAGE_ID)
  return ALL_COLUMNS.map((col) => {
    const base = {
      data: col.key,
      width: resolveColumnWidth(col.width, col.key, storedWidths)
    }
    if (col.key === 'phaseId') {
      return {
        ...base,
        type: 'dropdown',
        source: phaseOptions.value,
        strict: true,
        allowInvalid: false
      }
    }
    if (col.key === 'startWeek' || col.key === 'endWeek') {
      return { ...base, type: 'numeric' }
    }
    return { ...base, type: 'text' }
  })
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
  if (!el) return 420
  const wasHidden = el.classList.contains('is-hidden')
  if (wasHidden) el.classList.remove('is-hidden')
  el.style.height = ''
  void el.offsetHeight
  let height = Math.floor(el.clientHeight || 0)
  if (height < 260) {
    const top = el.getBoundingClientRect().top || 160
    height = Math.max(Math.floor(window.innerHeight - top - 24), 260)
  }
  height = Math.max(height - 2, 260)
  el.style.height = `${height}px`
  if (wasHidden) el.classList.add('is-hidden')
  return height
}

function collectTasksFromHot() {
  const hot = hotInstance.value
  if (!hot || hot.isDestroyed) return []
  return (hot.getSourceData() || [])
    .filter((row) => !isBlankRow(row))
    .map((row) => ({
      id: normalizeCellValue(row.task_id) || null,
      task_id: normalizeCellValue(row.task_id),
      name: normalizeCellValue(row.name),
      startWeek: normalizeCellValue(row.startWeek),
      endWeek: normalizeCellValue(row.endWeek),
      phaseId: normalizeCellValue(row.phaseId) || 'opportunity'
    }))
}

function initHot(rows) {
  if (!hotContainer.value) return
  destroyHot()

  const data = rows.map((r) => {
    const row = emptyRow()
    ALL_KEYS.forEach((k) => {
      row[k] = r[k] ?? ''
    })
    row.id = r.id ?? r.task_id ?? null
    row.task_id = r.task_id || r.id || ''
    return row
  })
  for (let i = 0; i < 5; i += 1) data.push(emptyRow())

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
      isDirty.value = true
      rowCount.value = (this.getSourceData() || []).filter((row) => !isBlankRow(row)).length
    },
    afterCreateRow() {
      isDirty.value = true
    },
    afterRemoveRow() {
      isDirty.value = true
      rowCount.value = (this.getSourceData() || []).filter((row) => !isBlankRow(row)).length
    },
    afterInit() {
      requestAnimationFrame(() => {
        if (!this.isDestroyed) this.refreshDimensions()
      })
    }
  })

  hotInstance.value = hot
  hotReady.value = true
  rowCount.value = rows.length
}

function onResize() {
  if (!hotInstance.value || hotInstance.value.isDestroyed) return
  const height = syncTableHeight()
  hotInstance.value.updateSettings({ height })
  hotInstance.value.refreshDimensions()
}

async function loadData() {
  const mid = migrationId.value.trim()
  if (!mid) {
    error.value = 'Please enter a Migration ID.'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const { data } = await axios.get('/api/project-gantt-attributes/', {
      params: { migration_request_id: mid }
    })
    migrationRequestId.value = data.migration_request_id || mid
    projectName.value = data.project_name || ''
    meta.value = { ...defaultMeta(), ...(data.meta || {}) }
    if (Array.isArray(data.phase_options) && data.phase_options.length) {
      phaseOptions.value = data.phase_options
    }
    loaded.value = true
    isDirty.value = false
    await nextTick()
    initHot(data.rows || [])
  } catch (err) {
    loaded.value = false
    destroyHot()
    error.value =
      err?.response?.data?.error || 'Unable to load Project Gantt for this Migration ID.'
  } finally {
    loading.value = false
  }
}

async function saveData() {
  if (!loaded.value || saving.value) return
  saving.value = true
  error.value = ''
  try {
    const { data } = await axios.post('/api/project-gantt-attributes/data/', {
      migration_request_id: migrationRequestId.value || migrationId.value.trim(),
      meta: meta.value,
      tasks: collectTasksFromHot()
    })
    meta.value = { ...defaultMeta(), ...(data.meta || {}) }
    isDirty.value = false
    await nextTick()
    initHot(data.rows || [])
  } catch (err) {
    error.value = err?.response?.data?.error || 'Unable to save Project Gantt data.'
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  destroyHot()
})
</script>

<style scoped>
.pga-page {
  background: #fff;
  min-height: 100%;
  padding: 16px 18px 24px;
}

.pga-page-inner {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: calc(100vh - 120px);
}

.pga-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.back-link {
  text-decoration: none;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #161616;
}

.meta-pill {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: #f1f5f9;
  color: #64748b;
  font-size: 12px;
  font-weight: 600;
}

.meta-pill--loading,
.meta-pill--pending {
  background: rgba(0, 119, 184, 0.1);
  color: #0077b8;
}

.meta-pill--error {
  background: rgba(220, 38, 38, 0.1);
  color: #b91c1c;
  max-width: 420px;
}

.lookup-bar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: end;
}

.lookup-input {
  width: 100%;
}

.meta-panel {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 14px 16px;
  background: #f8fafc;
}

.meta-panel__head h2 {
  margin: 0 0 2px;
  font-size: 15px;
  color: #0f172a;
}

.meta-panel__head p {
  margin: 0 0 12px;
  color: #64748b;
  font-size: 12px;
}

.meta-panel__grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px 12px;
}

.meta-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
}

.meta-field input {
  min-height: 34px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 6px 10px;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
  background: #fff;
}

.handsontable-host {
  flex: 1;
  min-height: 320px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}

.handsontable-host.is-hidden {
  visibility: hidden;
  pointer-events: none;
}

@media (max-width: 900px) {
  .meta-panel__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
