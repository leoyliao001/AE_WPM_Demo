<template>
  <div class="fpo-page">
    <div class="fpo-page-inner">
      <header class="fpo-toolbar">
        <div class="toolbar-left">
          <router-link class="back-link" to="/">
            <mc-button
              appearance="neutral"
              variant="plain"
              fit="small"
              label="Back"
              icon="mi-arrow-left"
            />
          </router-link>
          <mc-tag appearance="info" fit="small" label="FPO Mapping" />
          <h1 class="page-title">FPO Extended Mapping</h1>
          <span class="meta-pill">{{ rowCount }} rows</span>
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
        <span>Loading FPO mapping…</span>
      </div>

      <div
        id="fpo-handsontable"
        ref="hotContainer"
        class="ht-theme-main handsontable-host"
        :class="{ 'is-hidden': loading && !hotReady }"
      />
    </div>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'
import axios from 'axios'
import Handsontable from 'handsontable'
import 'handsontable/styles/handsontable.min.css'
import 'handsontable/styles/ht-theme-main.min.css'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-tag'
import '@maersk-global/mds-components-core/mc-loading-indicator'

/** Cascade columns — dropdown only, no free text */
const CASCADE_KEYS = [
  'l1',
  'gpl',
  'l2',
  'sfpo',
  'num_business_policy',
  'l3',
  'fpo',
  'risk_link',
  'control_link',
  'l4',
  'activity_type',
  'sub_process_call_activity',
  'activity_type_2',
  'assigned_models_from_l5'
]

/** Full Excel / DB column set */
const ALL_COLUMNS = [
  { key: 'l1', label: 'L1', width: 200 },
  { key: 'gpl', label: 'GPL', width: 120 },
  { key: 'l2', label: 'L2', width: 180 },
  { key: 'sfpo', label: 'SFPO', width: 120 },
  { key: 'num_business_policy', label: '# of Business Policy', width: 110 },
  { key: 'l3', label: 'L3', width: 200 },
  { key: 'fpo', label: 'FPO', width: 120 },
  { key: 'risk_link', label: 'Risk Link', width: 160 },
  { key: 'control_link', label: 'Control Link', width: 120 },
  { key: 'l4', label: 'L4', width: 220 },
  { key: 'activity_type', label: 'Activity Type', width: 140 },
  { key: 'sub_process_call_activity', label: 'Sub-Process/Call Activity', width: 180 },
  { key: 'activity_type_2', label: 'Activity Type (L5)', width: 140 },
  { key: 'assigned_models_from_l5', label: 'Assigned Models from L5', width: 180 },
  { key: 'process_level', label: 'Process Level', width: 90 },
  { key: 'process_grouping', label: 'Process Grouping', width: 110 },
  { key: 'last_change', label: 'Last change', width: 140 },
  { key: 'guid', label: 'GUID', width: 220 },
  { key: 'connect_link', label: 'Connect Link', width: 160 },
  { key: 'num_automated_activities', label: '# of Automated activities', width: 110 },
  { key: 'num_system_supported_activities', label: '# of System Supported activities', width: 120 },
  { key: 'num_manual_activities', label: '# of Manual activities', width: 110 },
  { key: 'num_undefined_activities', label: '# of Undefined activities', width: 110 },
  { key: 'num_sub_process_activities', label: '# of Sub-Process activities', width: 110 },
  { key: 'num_ms_office_activities', label: '# of MS-Office activities', width: 110 },
  { key: 'num_touchpoint_external_parties', label: '# of Touchpoint with External parties', width: 120 },
  { key: 'num_risks', label: '# of Risks', width: 80 },
  { key: 'num_controls', label: '# of Controls', width: 90 },
  { key: 'num_manual_controls', label: '# of Manual Controls', width: 100 },
  { key: 'num_business_rules', label: '# of Business Rules', width: 100 },
  { key: 'report_generation_date', label: 'Report Generation Date', width: 120 },
  { key: 'sharepoint_link_sop', label: 'Sharepoint Link(SOP)', width: 180 }
]

const ALL_KEYS = ALL_COLUMNS.map((c) => c.key)
const CASCADE_SET = new Set(CASCADE_KEYS)

const CLEAR_FROM = {
  l1: [
    'gpl',
    'l2',
    'sfpo',
    'num_business_policy',
    'l3',
    'fpo',
    'risk_link',
    'control_link',
    'l4',
    'activity_type',
    'sub_process_call_activity',
    'activity_type_2',
    'assigned_models_from_l5'
  ],
  l2: [
    'sfpo',
    'num_business_policy',
    'l3',
    'fpo',
    'risk_link',
    'control_link',
    'l4',
    'activity_type',
    'sub_process_call_activity',
    'activity_type_2',
    'assigned_models_from_l5'
  ],
  l3: [
    'fpo',
    'risk_link',
    'control_link',
    'l4',
    'activity_type',
    'sub_process_call_activity',
    'activity_type_2',
    'assigned_models_from_l5'
  ],
  l4: [
    'activity_type',
    'sub_process_call_activity',
    'activity_type_2',
    'assigned_models_from_l5'
  ],
  sub_process_call_activity: ['activity_type_2', 'assigned_models_from_l5']
}

const hotContainer = ref(null)
const hotInstance = shallowRef(null)
const cascade = shallowRef({ l1_list: [], by_l1: {} })
const loading = ref(false)
const hotReady = ref(false)
const error = ref('')
const rowCount = ref(0)

const emptyRow = () => Object.fromEntries(ALL_KEYS.map((k) => [k, '']))

function getL1Node(l1) {
  if (!l1) return null
  return cascade.value.by_l1?.[l1] || null
}

function getL2Node(l1, l2) {
  const n1 = getL1Node(l1)
  if (!n1 || !l2) return null
  return n1.by_l2?.[l2] || null
}

function getL3Node(l1, l2, l3) {
  const n2 = getL2Node(l1, l2)
  if (!n2 || !l3) return null
  return n2.by_l3?.[l3] || null
}

function getL4Node(l1, l2, l3, l4) {
  const n3 = getL3Node(l1, l2, l3)
  if (!n3 || !l4) return null
  return n3.by_l4?.[l4] || null
}

function getSubNode(l1, l2, l3, l4, sub) {
  const n4 = getL4Node(l1, l2, l3, l4)
  if (!n4 || !sub) return null
  return n4.by_sub_process?.[sub] || null
}

function optionsFor(prop, rowData) {
  const { l1, l2, l3, l4, sub_process_call_activity: sub } = rowData || {}

  switch (prop) {
    case 'l1':
      return cascade.value.l1_list || []
    case 'gpl': {
      const n1 = getL1Node(l1)
      return n1?.gpl ? [n1.gpl] : []
    }
    case 'l2':
      return getL1Node(l1)?.l2_list || []
    case 'sfpo': {
      const n2 = getL2Node(l1, l2)
      return n2?.sfpo ? [n2.sfpo] : []
    }
    case 'num_business_policy': {
      const n2 = getL2Node(l1, l2)
      return n2?.num_business_policy ? [n2.num_business_policy] : []
    }
    case 'l3':
      return getL2Node(l1, l2)?.l3_list || []
    case 'fpo': {
      const n3 = getL3Node(l1, l2, l3)
      return n3?.fpo ? [n3.fpo] : []
    }
    case 'risk_link': {
      const n3 = getL3Node(l1, l2, l3)
      return n3?.risk_link ? [n3.risk_link] : []
    }
    case 'control_link': {
      const n3 = getL3Node(l1, l2, l3)
      return n3?.control_link ? [n3.control_link] : []
    }
    case 'l4':
      return getL3Node(l1, l2, l3)?.l4_list || []
    case 'activity_type':
      return getL4Node(l1, l2, l3, l4)?.activity_type_list || []
    case 'sub_process_call_activity':
      return getL4Node(l1, l2, l3, l4)?.sub_process_list || []
    case 'activity_type_2': {
      const leaf = getSubNode(l1, l2, l3, l4, sub)
      return leaf?.activity_type_2 ? [leaf.activity_type_2] : []
    }
    case 'assigned_models_from_l5': {
      const leaf = getSubNode(l1, l2, l3, l4, sub)
      return leaf?.assigned_models_from_l5 ? [leaf.assigned_models_from_l5] : []
    }
    default:
      return []
  }
}

function makeDropdownSource(prop) {
  return function source(_query, callback) {
    // Ignore typed query — list is always the full cascade options (no free-text filter path)
    const hot = this.instance
    const visualRow = this.row
    const physicalRow =
      typeof hot.toPhysicalRow === 'function' ? hot.toPhysicalRow(visualRow) : visualRow
    const rowData = hot.getSourceDataAtRow(physicalRow) || emptyRow()
    callback(optionsFor(prop, rowData))
  }
}

function makeValidator(prop) {
  return function validator(value, callback) {
    if (value === null || value === undefined || value === '') {
      callback(true)
      return
    }
    const hot = this.instance
    const visualRow = this.row
    const physicalRow =
      typeof hot.toPhysicalRow === 'function' ? hot.toPhysicalRow(visualRow) : visualRow
    const rowData = { ...(hot.getSourceDataAtRow(physicalRow) || emptyRow()) }
    callback(optionsFor(prop, rowData).includes(value))
  }
}

function applyCascadeFill(hot, visualRow, physicalRow, changedProp) {
  const data = { ...(hot.getSourceDataAtRow(physicalRow) || emptyRow()) }
  const updates = []

  const pushClear = (fields) => {
    fields.forEach((field) => {
      if (data[field]) {
        updates.push([visualRow, field, ''])
        data[field] = ''
      }
    })
  }

  if (CLEAR_FROM[changedProp]) {
    pushClear(CLEAR_FROM[changedProp])
  }

  if (changedProp === 'l1') {
    const n1 = getL1Node(data.l1)
    if (n1?.gpl) {
      updates.push([visualRow, 'gpl', n1.gpl])
      data.gpl = n1.gpl
    }
  }

  if (changedProp === 'l2') {
    const n2 = getL2Node(data.l1, data.l2)
    if (n2) {
      if (n2.sfpo) {
        updates.push([visualRow, 'sfpo', n2.sfpo])
        data.sfpo = n2.sfpo
      }
      if (n2.num_business_policy) {
        updates.push([visualRow, 'num_business_policy', n2.num_business_policy])
        data.num_business_policy = n2.num_business_policy
      }
    }
  }

  if (changedProp === 'l3') {
    const n3 = getL3Node(data.l1, data.l2, data.l3)
    if (n3) {
      if (n3.fpo) {
        updates.push([visualRow, 'fpo', n3.fpo])
        data.fpo = n3.fpo
      }
      if (n3.risk_link) {
        updates.push([visualRow, 'risk_link', n3.risk_link])
        data.risk_link = n3.risk_link
      }
      if (n3.control_link) {
        updates.push([visualRow, 'control_link', n3.control_link])
        data.control_link = n3.control_link
      }
    }
  }

  if (changedProp === 'l4') {
    const n4 = getL4Node(data.l1, data.l2, data.l3, data.l4)
    if (n4?.activity_type_list?.length === 1) {
      updates.push([visualRow, 'activity_type', n4.activity_type_list[0]])
    }
  }

  if (changedProp === 'sub_process_call_activity') {
    const leaf = getSubNode(
      data.l1,
      data.l2,
      data.l3,
      data.l4,
      data.sub_process_call_activity
    )
    if (leaf) {
      if (leaf.activity_type_2) {
        updates.push([visualRow, 'activity_type_2', leaf.activity_type_2])
      }
      if (leaf.assigned_models_from_l5) {
        updates.push([visualRow, 'assigned_models_from_l5', leaf.assigned_models_from_l5])
      }
    }
  }

  if (updates.length) {
    hot.setDataAtRowProp(updates, 'cascade')
  }
}

function buildColumns() {
  return ALL_COLUMNS.map((col) => {
    if (CASCADE_SET.has(col.key)) {
      return {
        data: col.key,
        type: 'dropdown',
        strict: true,
        allowInvalid: false,
        filter: false,
        visibleRows: 12,
        trimDropdown: false,
        source: makeDropdownSource(col.key),
        validator: makeValidator(col.key),
        width: col.width
      }
    }

    return {
      data: col.key,
      type: 'text',
      width: col.width
    }
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
  if (!el) return 480
  const top = el.getBoundingClientRect().top
  const height = Math.max(window.innerHeight - top - 12, 360)
  el.style.height = `${height}px`
  return height
}

function initHot(rows) {
  if (!hotContainer.value) return
  destroyHot()

  const data = rows.map((r) => {
    const row = emptyRow()
    ALL_KEYS.forEach((k) => {
      row[k] = r[k] ?? ''
    })
    return row
  })

  for (let i = 0; i < 5; i += 1) {
    data.push(emptyRow())
  }

  const tableHeight = syncTableHeight()

  const hot = new Handsontable(hotContainer.value, {
    data,
    columns: buildColumns(),
    colHeaders: ALL_COLUMNS.map((c) => c.label),
    rowHeaders: true,
    height: tableHeight,
    width: '100%',
    stretchH: 'none',
    autoWrapRow: false,
    autoWrapCol: false,
    textEllipsis: true,
    wordWrap: false,
    autoRowSize: false,
    manualColumnResize: true,
    manualRowResize: true,
    filters: true,
    dropdownMenu: true,
    multiColumnSorting: true,
    contextMenu: {
      items: {
        row_above: { name: 'Insert row above' },
        row_below: { name: 'Insert row below' },
        remove_row: { name: 'Remove row' },
        undo: { name: 'Undo' },
        redo: { name: 'Redo' },
        alignment: { name: 'Alignment' }
      }
    },
    minSpareRows: 1,
    licenseKey: 'non-commercial-and-evaluation',
    className: 'htLeft htMiddle',
    beforeKeyDown(event) {
      const sel = this.getSelectedLast()
      if (!sel) return
      const prop = this.colToProp(sel[1])
      if (!CASCADE_SET.has(prop)) return

      // Allow navigation / confirm / clear / open editor — block free typing
      if (event.ctrlKey || event.metaKey || event.altKey) return
      const allowed = new Set([
        'ArrowUp',
        'ArrowDown',
        'ArrowLeft',
        'ArrowRight',
        'Tab',
        'Enter',
        'Escape',
        'Delete',
        'Backspace',
        'Home',
        'End',
        'F2',
        'PageUp',
        'PageDown'
      ])
      if (allowed.has(event.key)) return
      if (event.key.length === 1) {
        event.preventDefault()
        event.stopImmediatePropagation()
      }
    },
    afterChange(changes, source) {
      if (!changes || source === 'cascade' || source === 'loadData') return
      if (!['edit', 'CopyPaste.paste', 'Autofill.fill'].includes(source)) return

      const handled = new Set()
      changes.forEach(([visualRow, prop]) => {
        if (
          !CLEAR_FROM[prop] &&
          !['l1', 'l2', 'l3', 'l4', 'sub_process_call_activity'].includes(prop)
        ) {
          return
        }
        const key = `${visualRow}|${prop}`
        if (handled.has(key)) return
        handled.add(key)

        const physicalRow =
          typeof this.toPhysicalRow === 'function'
            ? this.toPhysicalRow(visualRow)
            : visualRow
        applyCascadeFill(this, visualRow, physicalRow, prop)
      })
    },
    afterInit() {
      requestAnimationFrame(() => {
        if (!this.isDestroyed) {
          this.refreshDimensions()
        }
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
    const { data } = await axios.get('/api/fpo-mapping/')
    cascade.value = data.cascade || { l1_list: [], by_l1: {} }
    rowCount.value = data.count || 0
    await nextTick()
    initHot(data.rows || [])
  } catch (e) {
    console.error(e)
    error.value = e?.response?.data?.detail || e.message || 'Failed to load FPO mapping'
    destroyHot()
  } finally {
    loading.value = false
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
.fpo-page {
  background: #fff;
  min-height: calc(100vh - 56px);
}

.fpo-page-inner {
  box-sizing: border-box;
  margin: 0;
  max-width: none;
  padding: 8px 10px 8px;
  width: 100%;
}

.fpo-toolbar {
  align-items: center;
  border-bottom: 1px solid #c0c4cc;
  display: flex;
  gap: 12px;
  justify-content: space-between;
  margin-bottom: 8px;
  min-height: 44px;
  padding: 4px 2px 8px;
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
  font-size: 18px;
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

.meta-pill--loading {
  color: #0077b8;
}

.meta-pill--error {
  background: #fff5f5;
  border-color: #f5c2c2;
  color: #b42318;
}

.table-loading {
  align-items: center;
  color: #6c757d;
  display: flex;
  flex-direction: column;
  gap: 12px;
  justify-content: center;
  min-height: 360px;
}

.handsontable-host {
  box-sizing: border-box;
  min-height: 360px;
  overflow: hidden;
  position: relative;
  width: 100%;
}

.handsontable-host.is-hidden {
  display: none;
}

/* —— OverView-like dense spreadsheet chrome —— */
:deep(#fpo-handsontable .ht-root-wrapper) {
  height: 100% !important;
}

:deep(#fpo-handsontable .ht_master .wtHolder) {
  overflow: auto !important;
}

:deep(#fpo-handsontable .ht_clone_inline_start .wtHolder),
:deep(#fpo-handsontable .ht_clone_top .wtHolder),
:deep(#fpo-handsontable .ht_clone_top_inline_start_corner .wtHolder) {
  overflow: hidden !important;
}

:deep(#fpo-handsontable .handsontable),
:deep(#fpo-handsontable .htCore td),
:deep(#fpo-handsontable .htCore th) {
  font-family: 'Maersk Text', sans-serif !important;
  font-size: 11px !important;
}

:deep(#fpo-handsontable .htCore thead th),
:deep(#fpo-handsontable .ht_clone_top th),
:deep(#fpo-handsontable .ht_clone_top_inline_start_corner th) {
  background: #f5f5f5 !important;
  border-color: #e0e0e0 !important;
  color: #161616 !important;
  font-weight: 600 !important;
  white-space: nowrap;
}

:deep(#fpo-handsontable .htCore tbody td) {
  border-color: #e0e0e0 !important;
  box-sizing: border-box;
  overflow: hidden !important;
  vertical-align: middle;
}

:deep(#fpo-handsontable .htCore tbody tr:nth-child(even) td) {
  border-bottom: 1px solid #e0e0e0 !important;
}

:deep(#fpo-handsontable .htCore tbody tr:nth-child(odd) td) {
  border-bottom: 1px dashed #e0e0e0 !important;
}

:deep(#fpo-handsontable .htCore tbody tr:hover td) {
  background: rgba(0, 119, 184, 0.04);
}

:deep(#fpo-handsontable .handsontableInput),
:deep(#fpo-handsontable .handsontableInputHolder textarea),
:deep(#fpo-handsontable .listbox) {
  font-family: 'Maersk Text', sans-serif !important;
  font-size: 11px !important;
}

:deep(#fpo-handsontable .htDropdownMenu),
:deep(#fpo-handsontable .htFiltersMenuCondition),
:deep(#fpo-handsontable .htFiltersMenuValue) {
  font-size: 11px;
}

@media (max-width: 900px) {
  .fpo-page-inner {
    padding: 6px 6px 8px;
  }

  .page-title {
    font-size: 16px;
  }
}
</style>
