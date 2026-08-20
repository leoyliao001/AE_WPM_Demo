<template>
  <div class="aw-page">
    <div class="aw-page-inner">
      <header class="aw-toolbar">
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
          <mc-tag appearance="info" fit="small" label="Approval Workflow" />
          <mc-tag appearance="neutral" fit="small" label="Read-only" />
          <h1 class="page-title">Approval Workflow</h1>
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
          <mc-button
            appearance="neutral"
            variant="plain"
            fit="small"
            label="Reload"
            icon="mi-arrow-clockwise"
            :disabled="loading"
            @click="loadData"
          />
        </div>
      </header>

      <div v-if="loading && !hotReady" class="table-loading">
        <mc-loading-indicator size="large" />
        <span>Loading approval workflow…</span>
      </div>

      <div
        id="aw-handsontable"
        ref="hotContainer"
        class="ht-theme-horizon handsontable-host"
        :class="{ 'is-hidden': loading && !hotReady }"
      />

      <mc-dialog
        :open="helpDialogOpen"
        heading="Approval Workflow — User Guide"
        dimension="medium"
        showclosebutton
        @closing="helpDialogOpen = false"
      >
        <div class="help-dialog-body">
          <section class="help-section">
            <h3>What this table is for</h3>
            <p>
              Browse <strong>Approval Workflow</strong> statuses for each
              <code>migration_request_id</code> (Area Head, PMO, BPM, FBP, WPM, GSC Head, ELT).
              Rows are synced automatically from upstream systems.
            </p>
          </section>
          <section class="help-section">
            <h3>Read-only</h3>
            <ul>
              <li>You can filter, sort, resize columns, and copy cells.</li>
              <li>Editing, inserting, and deleting rows are disabled.</li>
              <li>Use <strong>Reload</strong> to refresh the latest synced data.</li>
            </ul>
          </section>
        </div>
      </mc-dialog>
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
import '@maersk-global/mds-components-core/mc-loading-indicator'
import '@maersk-global/mds-components-core/mc-dialog'
import {
  hasStoredColumnWidths,
  loadColumnWidths,
  persistColumnWidths,
  resolveColumnWidth
} from '../utils/handsontableColumnWidths.js'

const ALL_COLUMNS = [
  { key: 'migration_request_id', label: 'migration_request_id', width: 200 },
  { key: 'business_case_submitted_date', label: 'Business case submitted date', width: 200 },
  { key: 'area_head_approval_trigger_date', label: 'Area Head Approval Trigger Date', width: 220 },
  { key: 'area_head_comments', label: 'Area Head comments', width: 220 },
  { key: 'area_head_final_date', label: 'Area Head FinalDate', width: 170 },
  { key: 'area_head_status', label: 'Area Head Status', width: 150 },
  { key: 'pmo_review_comment', label: 'PMO Review Comment', width: 200 },
  { key: 'pmo_review_date', label: 'PMO Review Date', width: 160 },
  { key: 'pmo_status', label: 'PMO Status', width: 130 },
  { key: 'bpm_budget_status', label: 'BPM Budget Status', width: 160 },
  { key: 'bpm_comment', label: 'BPM Comment', width: 200 },
  { key: 'bpm_review_date', label: 'BPM Review Date', width: 160 },
  { key: 'fbp_review_date', label: 'FBP Review Date', width: 160 },
  { key: 'fbp_comment', label: 'FBP Comment', width: 200 },
  { key: 'fbp_status', label: 'FBP Status', width: 130 },
  { key: 'wpm_review_date', label: 'WPM Review Date', width: 160 },
  { key: 'wpm_review_comment', label: 'WPM Review Comment', width: 200 },
  { key: 'wpm_review_status', label: 'WPM Review Status', width: 160 },
  { key: 'gsc_head_date', label: 'GSC Head Date', width: 150 },
  { key: 'gsc_head_comment', label: 'GSC Head Comment', width: 200 },
  { key: 'gsc_head_status', label: 'GSC Head Status', width: 150 },
  { key: 'elt_date', label: 'ELT Date', width: 150 },
  { key: 'elt_comment', label: 'ELT Comment', width: 200 },
  { key: 'elt_status', label: 'ELT Status', width: 130 }
]

const ALL_KEYS = ALL_COLUMNS.map((c) => c.key)
const COLUMN_WIDTH_STORAGE_ID = 'approval-workflow'

const hotContainer = ref(null)
const hotInstance = shallowRef(null)
const hotReady = ref(false)
const loading = ref(false)
const error = ref('')
const rowCount = ref(0)
const helpDialogOpen = ref(false)

function buildColumns() {
  const storedWidths = loadColumnWidths(COLUMN_WIDTH_STORAGE_ID)
  return ALL_COLUMNS.map((col) => ({
    data: col.key,
    type: 'text',
    readOnly: true,
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

  const data = rows.map((r) => {
    const row = { id: r.id ?? null }
    ALL_KEYS.forEach((k) => {
      row[k] = r[k] ?? ''
    })
    return row
  })

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
    readOnly: true,
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
    minSpareRows: 0,
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
        }
      }
    },
    licenseKey: 'non-commercial-and-evaluation',
    themeName: 'ht-theme-horizon',
    className: 'htLeft htMiddle',
    headerClassName: 'htLeft',
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

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await axios.get('/api/approval-workflow/')
    rowCount.value = data.count || 0
    await nextTick()
    initHot(data.rows || [])
  } catch (e) {
    console.error(e)
    error.value = e?.response?.data?.error || e?.response?.data?.detail || e.message || 'Failed to load'
    destroyHot()
  } finally {
    loading.value = false
    await nextTick()
    onResize()
  }
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  destroyHot()
})
</script>

<style scoped>
.aw-page {
  background: #f3f4f6;
  box-sizing: border-box;
  display: flex;
  flex: 1;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.aw-page-inner {
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

.aw-toolbar {
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
