<template>
  <div class="oa-page">
    <div class="oa-page-inner">
      <header class="oa-toolbar">
        <div class="toolbar-left">
          <router-link class="back-link" :to="backTo">
            <mc-button
              appearance="neutral"
              variant="plain"
              fit="small"
              label="Back"
              icon="mi-arrow-left"
            />
          </router-link>
          <mc-tag appearance="info" fit="small" label="Opportunity Assessment" />
          <h1 class="page-title">Task-level Scoping</h1>
          <span class="meta-pill">{{ migrationRequestId || '—' }}</span>
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
            appearance="neutral"
            variant="outlined"
            fit="small"
            :label="downloading ? 'Preparing…' : 'Download template'"
            icon="mi-arrow-down"
            :disabled="loading || downloading || uploading || !migrationRequestId"
            @click="downloadTemplate"
          />
          <mc-button
            appearance="neutral"
            variant="outlined"
            fit="small"
            :label="uploading ? 'Uploading…' : 'Bulk upload'"
            icon="mi-arrow-up"
            :disabled="loading || downloading || uploading || !migrationRequestId"
            @click="triggerUpload"
          />
          <input
            ref="fileInput"
            class="file-input-hidden"
            type="file"
            accept=".xlsx,.xlsm,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            @change="onFileSelected"
          />
          <mc-button
            v-if="hasExistingRows || hotReady"
            appearance="neutral"
            variant="outlined"
            fit="small"
            label="Add new"
            icon="mi-plus"
            :disabled="loading || saving || deleting || uploading || setupDialogOpen"
            @click="openSetupDialog('append')"
          />
          <mc-button
            appearance="primary"
            fit="small"
            :label="saving ? 'Saving…' : 'Save'"
            icon="mi-floppy-disk"
            :disabled="loading || saving || deleting || pendingCount === 0"
            title="Ctrl + S"
            @click="saveData"
          />
          <mc-button
            appearance="neutral"
            variant="plain"
            fit="small"
            label="Reload"
            icon="mi-arrow-clockwise"
            :disabled="loading || saving || deleting || uploading"
            @click="loadData"
          />
        </div>
      </header>

      <div class="oa-banner" role="note">
        <strong>migration_request_id reminder:</strong>
        This page is locked to
        <code>{{ migrationRequestId || '—' }}</code>.
        The downloaded Excel template pre-fills this ID — do not change column A.
        Bulk upload will reject any row whose
        <code>migration_request_id</code> does not match.
      </div>

      <div v-if="loading && !hotReady" class="table-loading">
        <mc-loading-indicator size="large" />
        <span>Loading opportunity assessment…</span>
      </div>

      <div
        v-else-if="!hotReady && !hasExistingRows"
        class="table-empty"
      >
        <p>No assessment rows yet for this migration.</p>
        <mc-button
          appearance="primary"
          fit="medium"
          label="Generate rows"
          icon="mi-plus"
          :disabled="setupDialogOpen"
          @click="openSetupDialog('create')"
        />
      </div>

      <div
        id="oa-handsontable"
        ref="hotContainer"
        class="ht-theme-horizon handsontable-host"
        :class="{ 'is-hidden': (loading && !hotReady) || !hotReady }"
      />

      <mc-dialog
        :open="helpDialogOpen"
        heading="Opportunity Assessment — User Guide"
        dimension="large"
        showclosebutton
        @closing="helpDialogOpen = false"
      >
        <div class="help-dialog-body">
          <section class="help-section">
            <h3>What this page is for</h3>
            <p>
              This page captures <strong>task-level Opportunity Assessment</strong> for the current
              migration project. Each row describes one task under the process taxonomy
              (<strong>L1 → L2 → L3 → L4</strong>), plus scoping fields such as owner, complexity,
              volume, and FTE calculation.
            </p>
            <p>
              Data is scoped to
              <code>{{ migrationRequestId || '—' }}</code>
              and is not shared with other projects.
            </p>
          </section>

          <section class="help-section help-section--warn">
            <h3>migration_request_id (critical)</h3>
            <ul>
              <li>
                This page is locked to
                <code>{{ migrationRequestId || '—' }}</code>.
              </li>
              <li>
                Column <strong>migration_request_id</strong> and <strong>Product</strong> are
                read-only in the online grid (pre-filled from Intake / setup).
              </li>
              <li>
                When you download the Excel template, column A is pre-filled with the same ID —
                <strong>do not change it</strong>.
              </li>
              <li>
                Bulk upload rejects any filled row whose
                <code>migration_request_id</code> does not exactly match this page.
              </li>
            </ul>
          </section>

          <section class="help-section">
            <h3>1) Online update (edit in the grid)</h3>
            <ul>
              <li>
                The grid shows exactly the number of rows you generated (or loaded). Use
                <strong>Add new</strong> to append more rows — there are no spare blank rows.
              </li>
              <li>
                <strong>L1 → L2 → L3 → L4</strong> — cascading dropdowns only. Start with L1; each
                level filters the next. Free typing is blocked on these columns.
              </li>
              <li>
                Changing L1 clears L2/L3/L4; changing L2 clears L3/L4; changing L3 clears L4.
              </li>
              <li>
                Other columns (Owner, Location, Task Name, Description, Complexity, Volume, FTE,
                etc.) are free-text fields you can type or paste into.
              </li>
              <li>
                Edits are tracked as <strong>pending</strong> until you click
                <strong>Save</strong> (or press <strong>Ctrl+S</strong>).
              </li>
              <li>
                <strong>Reload</strong> refreshes from the database and discards unsaved pending
                changes.
              </li>
              <li>
                Right-click → <strong>Remove row</strong> deletes a saved row (with confirmation).
                Unsaved blank rows are removed locally only.
              </li>
              <li>
                Use the column header <strong>⋮</strong> menu to filter or sort when reviewing large
                lists.
              </li>
            </ul>
          </section>

          <section class="help-section">
            <h3>2) Download template</h3>
            <ul>
              <li>
                Click <strong>Download template</strong> to get an Excel file prepared for this
                project.
              </li>
              <li>
                The file includes an <strong>Instructions</strong> sheet and a
                <strong>Scope</strong> data sheet.
              </li>
              <li>
                Column A (<code>migration_request_id</code>) is already filled for 200 rows with
                <code>{{ migrationRequestId || '—' }}</code>.
              </li>
              <li>
                Excel also has <strong>L1 → L2 → L3 → L4</strong> cascading dropdowns (same hierarchy
                as the online grid). Select L1 first, then L2, then L3, then L4.
              </li>
              <li>
                Complexity has a simple Low / Medium / High dropdown in Excel for convenience.
              </li>
              <li>
                Fill only the rows you need; leave unused rows blank.
              </li>
            </ul>
          </section>

          <section class="help-section">
            <h3>3) Bulk upload</h3>
            <ul>
              <li>
                After filling the Excel template offline, click <strong>Bulk upload</strong> and
                select the completed <code>.xlsx</code> file.
              </li>
              <li>
                Before the file picker opens, confirm that every filled row keeps
                <code>migration_request_id = {{ migrationRequestId || '—' }}</code>.
              </li>
              <li>
                The server validates each non-empty row:
                <ul>
                  <li>Matching ID → imported into this project’s table</li>
                  <li>Wrong / empty ID → rejected (shown in the result dialog)</li>
                </ul>
              </li>
              <li>
                If <strong>all</strong> rows fail ID validation, nothing is imported and a clear
                error dialog is shown.
              </li>
              <li>
                Recommended flow:
                <strong>Download template</strong> → fill in Excel →
                <strong>Bulk upload</strong> → review the grid → adjust online if needed →
                <strong>Save</strong> only for extra online edits.
              </li>
              <li>
                Tip: always download the template from <em>this</em> project page so the ID and
                cascade lists stay correct.
              </li>
            </ul>
          </section>

          <section class="help-section">
            <h3>Online update vs bulk upload</h3>
            <ul>
              <li>
                <strong>Online update</strong> — best for small edits, quick fixes, or reviewing
                rows already in the database. Remember to click <strong>Save</strong>.
              </li>
              <li>
                <strong>Bulk upload</strong> — best for entering many tasks offline in Excel, then
                importing them in one go.
              </li>
              <li>
                Both methods are bound to the same
                <code>migration_request_id</code>; they do not mix data across projects.
              </li>
            </ul>
          </section>
        </div>

        <div slot="footer" class="help-dialog-footer">
          <mc-button
            type="button"
            appearance="primary"
            variant="filled"
            fit="medium"
            label="Got it"
            @click="helpDialogOpen = false"
          />
        </div>
      </mc-dialog>

      <mc-dialog
        :open="setupDialogOpen"
        :heading="setupMode === 'append' ? 'Add new assessment rows' : 'Generate assessment rows'"
        dimension="medium"
        showclosebutton
        @closing="closeSetupDialog"
      >
        <div class="setup-dialog-body">
          <div class="setup-dialog-scroll">
            <p class="setup-dialog-intro">
              Prefill from Migration Intake and Product Ownership. Migration ID and Product are locked;
              you can adjust Location and Owner before generating rows.
            </p>

            <div class="setup-field">
              <label class="setup-label">Migration ID</label>
              <mc-input
                label="Migration ID"
                hiddenlabel
                fit="medium"
                width="full-width"
                :value="setupForm.migrationRequestId"
                disabled
              />
            </div>

            <div class="setup-field">
              <label class="setup-label">Product</label>
              <mc-input
                label="Product"
                hiddenlabel
                fit="medium"
                width="full-width"
                :value="setupForm.productsDisplay"
                disabled
              />
            <p v-if="setupMeta.matchedOwnershipAreas.length" class="setup-hint">
              Matched Product Ownership areas:
              {{ setupMeta.matchedOwnershipAreas.join(' · ') }}
            </p>
            <p v-else class="setup-hint setup-hint--warn">
              No Product Ownership match found for region
              {{ setupMeta.region || '—' }}. You can still set Owner manually.
            </p>
            </div>

            <div class="setup-field">
              <label class="setup-label">Location</label>
              <mc-input
                label="Location"
                hiddenlabel
                fit="medium"
                width="full-width"
                :value="setupForm.location"
                placeholder="Location Strategy"
                @input="onSetupLocationInput"
              />
              <p v-if="setupMeta.locationOptions.length" class="setup-hint">
                From Location Strategy:
                {{ setupMeta.locationOptions.join(', ') }}
              </p>
            </div>

            <div class="setup-field">
              <label class="setup-label">Owner (Migration Manager)</label>
              <mc-select
                v-if="setupMeta.ownerOptions.length"
                label="Owner"
                hiddenlabel
                fit="medium"
                width="full-width"
                placeholder="Select owner"
                :value="setupForm.owner"
                @optionselected="onSetupOwnerSelect"
              >
                <mc-option
                  v-for="owner in setupMeta.ownerOptions"
                  :key="owner"
                  :value="owner"
                >
                  {{ owner }}
                </mc-option>
              </mc-select>
              <mc-input
                label="Owner"
                :hiddenlabel="setupMeta.ownerOptions.length > 0"
                fit="medium"
                width="full-width"
                :value="setupForm.owner"
                :placeholder="
                  setupMeta.ownerOptions.length
                    ? 'Or type a different owner'
                    : 'Migration Manager'
                "
                @input="onSetupOwnerInput"
              />
            </div>

            <div class="setup-field">
              <label class="setup-label">Number of rows</label>
              <mc-input
                label="Number of rows"
                hiddenlabel
                fit="medium"
                width="full-width"
                type="number"
                :value="String(setupForm.rowCount)"
                placeholder="e.g. 10"
                @input="onSetupRowCountInput"
              />
              <p class="setup-hint">Generate 1–{{ MAX_ROWS }} rows with the values above.</p>
            </div>
          </div>

          <div class="setup-dialog-footer">
            <mc-button
              type="button"
              appearance="neutral"
              variant="outlined"
              fit="medium"
              label="Cancel"
              @click="closeSetupDialog"
            />
            <mc-button
              type="button"
              appearance="primary"
              variant="filled"
              fit="medium"
              :label="setupMode === 'append' ? 'Add rows' : 'Generate'"
              :disabled="!canConfirmSetup"
              @click="confirmSetupDialog"
            />
          </div>
        </div>
      </mc-dialog>

      <mc-dialog
        :open="uploadDialogOpen"
        :heading="uploadDialogHeading"
        dimension="medium"
        showclosebutton
        @closing="closeUploadDialog"
      >
        <div class="upload-dialog-body" :class="{ 'upload-dialog-body--error': uploadDialogIsError }">
          <p v-if="uploadDialogIsError" class="upload-dialog-alert">
            Upload blocked — check <strong>migration_request_id</strong>
          </p>
          <p class="upload-dialog-expected">
            Expected ID for this page:
            <code>{{ migrationRequestId || '—' }}</code>
          </p>
          <p class="upload-dialog-message">{{ uploadDialogMessage }}</p>
          <ul v-if="uploadDialogDetails.length" class="upload-dialog-list">
            <li v-for="(item, idx) in uploadDialogDetails" :key="idx">{{ item }}</li>
          </ul>
          <p v-if="uploadDialogIsError" class="upload-dialog-hint">
            Tip: Download the template from this page again, keep column A unchanged, then re-upload.
          </p>
        </div>

        <div slot="footer" class="upload-dialog-footer">
          <mc-button
            type="button"
            appearance="primary"
            variant="filled"
            fit="medium"
            label="OK"
            @click="closeUploadDialog"
          />
        </div>
      </mc-dialog>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import Handsontable from 'handsontable'
import 'handsontable/styles/handsontable.min.css'
import 'handsontable/styles/ht-theme-horizon.min.css'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-tag'
import '@maersk-global/mds-components-core/mc-loading-indicator'
import '@maersk-global/mds-components-core/mc-dialog'
import '@maersk-global/mds-components-core/mc-input'
import '@maersk-global/mds-components-core/mc-select'
import '@maersk-global/mds-components-core/mc-option'
import {
  createAfterColumnResizeHandler,
  loadColumnWidths,
  resolveColumnWidth
} from '../utils/handsontableColumnWidths.js'

const CASCADE_KEYS = ['l1', 'l2', 'l3', 'l4']
const YN_DROPDOWN_KEYS = ['task_found_in_service_catalog', 'migratable_to_gsc']
const YN_OPTIONS = ['Y', 'N']

/** Width / readOnly only — column order & labels come from the API (model order). */
const COLUMN_META = {
  migration_request_id: { width: 180, readOnly: true },
  product: { width: 140, readOnly: true },
  owner: { width: 90 },
  location: { width: 140 },
  l1: { width: 200 },
  l2: { width: 180 },
  l3: { width: 200 },
  l4: { width: 220 },
  task_name: { width: 160 },
  task_description: { width: 220 },
  upstream: { width: 180 },
  downstream: { width: 180 },
  risks_related: { width: 180 },
  complexity: { width: 120 },
  sop_iop_exists: { width: 120 },
  training_time_needed: { width: 140 },
  recommended_handoff_duration: { width: 160 },
  task_frequency: { width: 140 },
  unit_of_measure: { width: 120 },
  volume_monthly: { width: 110 },
  task_time_per_unit_min: { width: 140 },
  area: { width: 140 },
  gsc_site: { width: 160 },
  task_found_in_service_catalog: { width: 200 },
  migratable_to_gsc: { width: 200 },
  fte_calculation: { width: 110 }
}

const tableColumns = shallowRef([])

function applyColumnsFromApi(apiColumns) {
  const list = Array.isArray(apiColumns) ? apiColumns : []
  tableColumns.value = list.map((col) => {
    const meta = COLUMN_META[col.key] || {}
    return {
      key: col.key,
      label: col.label || col.key,
      width: meta.width ?? 140,
      readOnly: !!meta.readOnly
    }
  })
}

function getAllKeys() {
  return tableColumns.value.map((c) => c.key)
}

const CASCADE_SET = new Set(CASCADE_KEYS)
const YN_DROPDOWN_SET = new Set(YN_DROPDOWN_KEYS)
const COLUMN_WIDTH_STORAGE_ID = 'opportunity-assessment'
const MAX_ROWS = 200

const CLEAR_FROM = {
  l1: ['l2', 'l3', 'l4'],
  l2: ['l3', 'l4'],
  l3: ['l4']
}

const route = useRoute()
const hotContainer = ref(null)
const hotInstance = shallowRef(null)
const cascade = shallowRef({ l1_list: [], by_l1: {} })
const migrationRequestId = ref('')
const projectName = ref('')
const loading = ref(false)
const hotReady = ref(false)
const error = ref('')
const rowCount = ref(0)
const allChanges = ref([])
const saving = ref(false)
const deleting = ref(false)
const downloading = ref(false)
const uploading = ref(false)
const fileInput = ref(null)
const uploadDialogOpen = ref(false)
const uploadDialogHeading = ref('')
const uploadDialogMessage = ref('')
const uploadDialogDetails = ref([])
const uploadDialogIsError = ref(false)
const helpDialogOpen = ref(false)
const hasExistingRows = ref(false)
const setupDialogOpen = ref(false)
const setupMode = ref('create') // 'create' | 'append'
const setupMeta = ref({
  region: '',
  locationOptions: [],
  ownerOptions: [],
  matchedOwnershipAreas: []
})
const setupForm = ref({
  migrationRequestId: '',
  productsDisplay: '',
  products: [],
  location: '',
  owner: '',
  rowCount: 10
})

function openUploadDialog({ heading, message, details = [], isError = false }) {
  uploadDialogHeading.value = heading
  uploadDialogMessage.value = message
  uploadDialogDetails.value = details
  uploadDialogIsError.value = isError
  uploadDialogOpen.value = true
}

function closeUploadDialog() {
  uploadDialogOpen.value = false
}

const projectId = computed(() => route.params.id)
const backTo = computed(() => `/migration-dashboard/${projectId.value}`)

const pendingCount = computed(() => {
  const map = new Map()
  allChanges.value.forEach((item) => {
    const key = item.id != null && item.id !== '' ? `id:${item.id}` : `cid:${item._cid}`
    map.set(key, item)
  })
  return map.size
})

const canConfirmSetup = computed(() => {
  const n = Number(setupForm.value.rowCount)
  return Number.isFinite(n) && n >= 1 && n <= MAX_ROWS
})

function eventValue(event) {
  const target = event?.currentTarget ?? event?.target
  return String(target?.value ?? event?.detail?.value ?? event?.detail ?? '')
}

function onSetupLocationInput(event) {
  setupForm.value.location = eventValue(event)
}

function onSetupOwnerInput(event) {
  setupForm.value.owner = eventValue(event)
}

function onSetupOwnerSelect(event) {
  setupForm.value.owner = eventValue(event)
}

function onSetupRowCountInput(event) {
  const raw = eventValue(event)
  const n = Number.parseInt(raw, 10)
  setupForm.value.rowCount = Number.isFinite(n) ? n : raw
}

function applySetupPayload(setup = {}) {
  setupMeta.value = {
    region: setup.region || '',
    locationOptions: Array.isArray(setup.location_options) ? setup.location_options : [],
    ownerOptions: Array.isArray(setup.owner_options) ? setup.owner_options : [],
    matchedOwnershipAreas: Array.isArray(setup.matched_ownership_areas)
      ? setup.matched_ownership_areas
      : []
  }
  setupForm.value = {
    migrationRequestId: setup.migration_request_id || migrationRequestId.value || '',
    productsDisplay: setup.products_display || '',
    products: Array.isArray(setup.products) ? setup.products : [],
    location: setup.location_default || '',
    owner: setup.owner_default || '',
    rowCount: 10
  }
}

function openSetupDialog(mode = 'create') {
  setupMode.value = mode
  setupDialogOpen.value = true
}

function closeSetupDialog() {
  setupDialogOpen.value = false
}

function buildSeedRows(count) {
  const product = setupForm.value.productsDisplay || ''
  const location = String(setupForm.value.location || '').trim()
  const owner = String(setupForm.value.owner || '').trim()
  const rows = []
  for (let i = 0; i < count; i += 1) {
    const row = emptyRow()
    row.product = product
    row.location = location
    row.owner = owner
    row.migration_request_id = migrationRequestId.value || setupForm.value.migrationRequestId || ''
    row.id = null
    row._cid = makeClientId()
    rows.push(row)
  }
  return rows
}

function trackSeedRows(seedRows) {
  seedRows.forEach((row) => {
    const snapshot = { id: null, _cid: row._cid || makeClientId() }
    getAllKeys().forEach((k) => {
      snapshot[k] = row[k] ?? ''
    })
    allChanges.value.push(snapshot)
  })
}

function getFilledSourceRows() {
  const hot = hotInstance.value
  if (!hot || hot.isDestroyed) return []
  return (hot.getSourceData() || []).filter((row) => row?.id || !isBlankRow(row))
}

async function confirmSetupDialog() {
  if (!canConfirmSetup.value) return
  const count = Math.min(Math.max(Number(setupForm.value.rowCount) || 0, 1), MAX_ROWS)
  const seedRows = buildSeedRows(count)
  const append = setupMode.value === 'append' && hotReady.value

  if (append) {
    const existing = getFilledSourceRows()
    const combined = [...existing, ...seedRows]
    if (combined.length > MAX_ROWS) {
      alert(`Cannot exceed ${MAX_ROWS} rows. You can add at most ${MAX_ROWS - existing.length} more.`)
      return
    }
    const pendingBefore = [...allChanges.value]
    initHot(combined)
    allChanges.value = pendingBefore
    trackSeedRows(seedRows)
  } else {
    initHot(seedRows)
    trackSeedRows(seedRows)
  }

  hasExistingRows.value = true
  rowCount.value = hotInstance.value?.countRows?.() || seedRows.length
  closeSetupDialog()
  await nextTick()
  onResize()
}

const emptyRow = () => {
  const row = Object.fromEntries(getAllKeys().map((k) => [k, '']))
  row.migration_request_id = migrationRequestId.value || ''
  row.id = null
  row._cid = ''
  return row
}

function isBlankRow(row) {
  if (!row) return true
  return getAllKeys()
    .filter((k) => k !== 'migration_request_id')
    .every((k) => !String(row[k] ?? '').trim())
}

function makeClientId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return `cid-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function trackChangedRow(hot, visualRow) {
  const physicalRow =
    typeof hot.toPhysicalRow === 'function' ? hot.toPhysicalRow(visualRow) : visualRow
  const src = hot.getSourceDataAtRow(physicalRow)
  if (!src || isBlankRow(src)) return

  src.migration_request_id = migrationRequestId.value || src.migration_request_id || ''

  if (!src.id && !src._cid) {
    src._cid = makeClientId()
  }

  const snapshot = { id: src.id ?? null, _cid: src._cid || '' }
  getAllKeys().forEach((k) => {
    snapshot[k] = src[k] ?? ''
  })
  allChanges.value.push(snapshot)
}

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

function optionsFor(prop, rowData) {
  const { l1, l2, l3 } = rowData || {}
  switch (prop) {
    case 'l1':
      return cascade.value.l1_list || []
    case 'l2':
      return getL1Node(l1)?.l2_list || []
    case 'l3':
      return getL2Node(l1, l2)?.l3_list || []
    case 'l4':
      return getL3Node(l1, l2, l3)?.l4_list || []
    default:
      return []
  }
}

function makeDropdownSource(prop) {
  return function source(_query, callback) {
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
    rowData[prop] = value
    callback(optionsFor(prop, rowData).includes(String(value).trim()))
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

  if (updates.length) {
    hot.setDataAtRowProp(updates, 'cascade')
  }
}

function buildColumns() {
  const storedWidths = loadColumnWidths(COLUMN_WIDTH_STORAGE_ID)
  return tableColumns.value.map((col) => {
    const width = resolveColumnWidth(col.width, col.key, storedWidths)
    if (CASCADE_SET.has(col.key)) {
      return {
        data: col.key,
        type: 'dropdown',
        strict: true,
        allowInvalid: true,
        filter: false,
        visibleRows: 12,
        trimDropdown: false,
        source: makeDropdownSource(col.key),
        validator: makeValidator(col.key),
        width
      }
    }

    if (YN_DROPDOWN_SET.has(col.key)) {
      return {
        data: col.key,
        type: 'dropdown',
        strict: true,
        allowInvalid: false,
        filter: false,
        visibleRows: 4,
        trimDropdown: false,
        source: YN_OPTIONS,
        width
      }
    }

    return {
      data: col.key,
      type: 'text',
      readOnly: !!col.readOnly,
      width
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
  if (!tableColumns.value.length) {
    error.value = 'Column definition missing from API.'
    return
  }
  destroyHot()
  allChanges.value = []

  const data = rows.map((r) => {
    const row = emptyRow()
    getAllKeys().forEach((k) => {
      row[k] = r[k] ?? ''
    })
    row.migration_request_id = migrationRequestId.value || r.migration_request_id || ''
    row.id = r.id ?? null
    row._cid = r._cid || ''
    return row
  })

  // Grid size follows the user's chosen / saved row count — no spare blank padding.
  const rowCap = Math.max(data.length, 1)
  rowCount.value = data.length

  const tableHeight = syncTableHeight()
  const columnDefs = tableColumns.value
  const allKeys = getAllKeys()

  const hot = new Handsontable(hotContainer.value, {
    data,
    columns: buildColumns(),
    colHeaders: columnDefs.map((c) => c.label),
    rowHeaders: false,
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
    dropdownMenu: ['filter_by_condition', 'filter_by_value', 'filter_action_bar'],
    multiColumnSorting: true,
    copyPaste: {
      copyColumnHeaders: true,
      copyColumnHeadersOnly: true
    },
    afterColumnResize: createAfterColumnResizeHandler(COLUMN_WIDTH_STORAGE_ID, allKeys),
    contextMenu: {
      items: {
        row_above: {
          name: 'Insert row above',
          disabled() {
            return this.countRows() >= rowCap
          }
        },
        row_below: {
          name: 'Insert row below',
          disabled() {
            return this.countRows() >= rowCap
          }
        },
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
    licenseKey: 'non-commercial-and-evaluation',
    minSpareRows: 0,
    maxRows: rowCap,
    themeName: 'ht-theme-horizon',
    className: 'htLeft htMiddle',
    headerClassName: 'htLeft',
    beforeKeyDown(event) {
      const sel = this.getSelectedLast()
      if (!sel) return
      const prop = this.colToProp(sel[1])
      if (!CASCADE_SET.has(prop)) return
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
      if (!changes || source === 'cascade' || source === 'loadData' || source === 'api') return
      if (!['edit', 'CopyPaste.paste', 'Autofill.fill'].includes(source)) return

      const handledCascade = new Set()
      const touchedRows = new Set()

      changes.forEach(([visualRow, prop, , newValue]) => {
        touchedRows.add(visualRow)
        const physicalRow =
          typeof this.toPhysicalRow === 'function' ? this.toPhysicalRow(visualRow) : visualRow
        const src = this.getSourceDataAtRow(physicalRow)
        if (src && !src.migration_request_id) {
          src.migration_request_id = migrationRequestId.value || ''
        }

        if (CLEAR_FROM[prop]) {
          const key = `${visualRow}|${prop}`
          if (!handledCascade.has(key)) {
            handledCascade.add(key)
            applyCascadeFill(this, visualRow, physicalRow, prop)
          }
        }

        if (prop === 'migration_request_id' && src) {
          src.migration_request_id = migrationRequestId.value || newValue || ''
        }
      })

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

async function downloadTemplate() {
  if (!migrationRequestId.value) return

  const confirmed = confirm(
    `Download Excel template for migration_request_id:\n\n` +
      `${migrationRequestId.value}\n\n` +
      `IMPORTANT:\n` +
      `• Column A (migration_request_id) is pre-filled — do NOT change it.\n` +
      `• Use L1 → L2 → L3 → L4 dropdowns in order (each level filters the next).\n` +
      `• After filling, upload the same file with Bulk upload.\n` +
      `• Upload will reject rows whose migration_request_id does not match.\n\n` +
      `Continue download?`
  )
  if (!confirmed) return

  downloading.value = true
  error.value = ''
  try {
    const response = await axios.get(
      `/api/migration-dashboard/projects/${projectId.value}/opportunity-assessment/template/`,
      { responseType: 'blob' }
    )
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `Opportunity_Assessment_${migrationRequestId.value}.xlsx`
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (e) {
    console.error(e)
    let msg = e.message || 'Download failed'
    if (e?.response?.data instanceof Blob) {
      try {
        const text = await e.response.data.text()
        const parsed = JSON.parse(text)
        msg = parsed.error || msg
      } catch {
        /* ignore */
      }
    } else {
      msg = e?.response?.data?.error || msg
    }
    error.value = msg
    alert(`Download failed: ${msg}`)
  } finally {
    downloading.value = false
  }
}

function triggerUpload() {
  if (!migrationRequestId.value || !fileInput.value) return

  const confirmed = confirm(
    `Bulk upload Excel for migration_request_id:\n\n` +
      `${migrationRequestId.value}\n\n` +
      `IMPORTANT:\n` +
      `• Every filled row MUST keep migration_request_id = ${migrationRequestId.value}\n` +
      `• Rows with a different or empty ID will be rejected.\n` +
      `• Use the template downloaded from this page.\n\n` +
      `Choose a file to continue?`
  )
  if (!confirmed) return
  fileInput.value.value = ''
  fileInput.value.click()
}

async function onFileSelected(event) {
  const file = event?.target?.files?.[0]
  if (!file) return

  uploading.value = true
  error.value = ''
  try {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await axios.post(
      `/api/migration-dashboard/projects/${projectId.value}/opportunity-assessment/upload/`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    const imported = data.imported_count || 0
    const rejected = data.rejected_count || 0
    const details = (data.errors || [])
      .slice(0, 8)
      .map((item) => `Row ${item.row}: ${item.error}`)

    if (rejected > 0 && imported === 0) {
      openUploadDialog({
        heading: 'Upload failed — migration_request_id mismatch',
        message:
          data.message ||
          data.error ||
          'No rows imported. All filled rows failed migration_request_id validation.',
        details,
        isError: true
      })
    } else if (rejected > 0) {
      openUploadDialog({
        heading: 'Upload partially completed',
        message:
          data.message ||
          `Imported ${imported} row(s). Rejected ${rejected} row(s) due to migration_request_id mismatch.`,
        details,
        isError: true
      })
      await loadData()
    } else {
      openUploadDialog({
        heading: 'Upload successful',
        message: data.message || `Imported ${imported} row(s).`,
        details: [],
        isError: false
      })
      await loadData()
    }
  } catch (e) {
    console.error(e)
    const payload = e?.response?.data
    const details = (payload?.errors || [])
      .slice(0, 8)
      .map((item) => `Row ${item.row}: ${item.error}`)
    const msg =
      payload?.error ||
      payload?.message ||
      e.message ||
      'Upload failed'
    error.value = payload?.error || msg
    openUploadDialog({
      heading: 'Upload failed — migration_request_id mismatch',
      message: msg,
      details,
      isError: true
    })
  } finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
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
    item.migration_request_id = migrationRequestId.value
    deduped.set(key, item)
  })

  const uniqueData = [...deduped.values()]
  saving.value = true
  error.value = ''
  try {
    const { data } = await axios.post(
      `/api/migration-dashboard/projects/${projectId.value}/opportunity-assessment/data/`,
      { uniqueData }
    )
    const created = data.created_count || 0
    const updated = data.updated_count || 0
    const errCount = data.error_count || 0
    if (errCount > 0) {
      alert(`Save done: created ${created}, updated ${updated}, errors ${errCount}.`)
    } else {
      alert(`Save done: created ${created}, updated ${updated}.`)
    }
    allChanges.value = []
    await loadData()
  } catch (e) {
    console.error(e)
    const msg =
      e?.response?.data?.error || e?.response?.data?.detail || e.message || 'Save failed'
    error.value = msg
    alert(`Save failed: ${msg}`)
  } finally {
    saving.value = false
  }
}

async function runDeleteRows(idsToRemove) {
  if (deleting.value) return
  deleting.value = true
  error.value = ''
  try {
    const { data } = await axios.delete(
      `/api/migration-dashboard/projects/${projectId.value}/opportunity-assessment/data/delete/`,
      { data: { removedIds: idsToRemove } }
    )
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
      e?.response?.data?.error || e?.response?.data?.detail || e.message || 'Delete failed'
    error.value = msg
    alert(`Delete failed: ${msg}`)
  } finally {
    deleting.value = false
  }
}

async function loadData() {
  loading.value = true
  error.value = ''
  setupDialogOpen.value = false
  try {
    const { data } = await axios.get(
      `/api/migration-dashboard/projects/${projectId.value}/opportunity-assessment/`
    )
    migrationRequestId.value = data.migration_request_id || ''
    projectName.value = data.project_name || ''
    cascade.value = data.cascade || { l1_list: [], by_l1: {} }
    rowCount.value = data.count || 0
    hasExistingRows.value = !!data.has_existing_rows || (data.count || 0) > 0
    applySetupPayload(data.setup || {})
    applyColumnsFromApi(data.columns || [])
    await nextTick()
    if (hasExistingRows.value) {
      initHot(data.rows || [])
    } else {
      destroyHot()
      openSetupDialog('create')
    }
  } catch (e) {
    console.error(e)
    error.value =
      e?.response?.data?.error || e?.response?.data?.detail || e.message || 'Failed to load'
    destroyHot()
    hasExistingRows.value = false
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

watch(
  () => route.params.id,
  () => {
    loadData()
  }
)

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  document.removeEventListener('keydown', handleGlobalKeydown)
  destroyHot()
})
</script>

<style scoped>
.oa-page {
  background: #f3f4f6;
  box-sizing: border-box;
  display: flex;
  flex: 1;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.oa-page-inner {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
  padding: 10px 12px 12px;
}

.oa-toolbar {
  align-items: center;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  display: flex;
  flex-shrink: 0;
  gap: 12px;
  justify-content: space-between;
  padding: 8px 12px;
}

.toolbar-left,
.toolbar-right {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.back-link {
  text-decoration: none;
}

.page-title {
  color: #161616;
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.meta-pill {
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  color: #4b5563;
  font-size: 12px;
  padding: 2px 10px;
}

.meta-pill--loading {
  color: #0077b8;
}

.meta-pill--error {
  background: #fef2f2;
  border-color: #fecaca;
  color: #b91c1c;
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta-pill--pending {
  background: #fff7ed;
  border-color: #fed7aa;
  color: #c2410c;
}

.meta-pill--help {
  background: #eef6fb;
  border-color: #b8d9eb;
  color: #0077b8;
  cursor: pointer;
  font-family: 'Maersk Text', sans-serif;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.meta-pill--help:hover {
  background: #dceef8;
  border-color: #0077b8;
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

.help-section p {
  margin: 0 0 8px;
}

.help-section p:last-child {
  margin-bottom: 0;
}

.help-section ul {
  margin: 0;
  padding-left: 20px;
}

.help-section li {
  margin-bottom: 6px;
}

.help-section li:last-child {
  margin-bottom: 0;
}

.help-section code {
  background: #f3f4f6;
  border-radius: 4px;
  font-family: Consolas, monospace;
  font-size: 12px;
  padding: 1px 5px;
}

.help-section--warn {
  background: #fff7ed;
  border: 1px solid #fed7aa;
  border-radius: 10px;
  padding: 12px 14px;
}

.help-section--warn h3 {
  color: #9a3412;
}

.help-section--warn code {
  background: #ffedd5;
  color: #9a3412;
}

.help-dialog-footer {
  display: flex;
  justify-content: flex-end;
}

.table-loading {
  align-items: center;
  color: #6b7280;
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 12px;
  justify-content: center;
  min-height: 280px;
  padding: 32px;
}

.table-empty {
  align-items: center;
  background: #f9fafb;
  border: 1px dashed #d1d5db;
  border-radius: 12px;
  color: #4b5563;
  display: flex;
  flex-direction: column;
  gap: 14px;
  justify-content: center;
  min-height: 280px;
  padding: 32px;
  text-align: center;
}

.table-empty p {
  margin: 0;
}

.setup-dialog-body {
  display: flex;
  flex-direction: column;
  gap: 0;
  max-height: min(70vh, 640px);
}

.setup-dialog-scroll {
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow: auto;
  padding-bottom: 4px;
}

.setup-dialog-intro {
  color: #4b5563;
  font-size: 13px;
  line-height: 1.45;
  margin: 0;
}

.setup-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.setup-label {
  color: #374151;
  font-size: 12px;
  font-weight: 600;
}

.setup-hint {
  color: #6b7280;
  font-size: 12px;
  line-height: 1.4;
  margin: 0;
}

.setup-hint--warn {
  color: #9a3412;
}

.setup-dialog-footer {
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 16px;
  padding-top: 14px;
}

.oa-banner {
  background: #fff7ed;
  border: 1px solid #fed7aa;
  border-radius: 10px;
  color: #9a3412;
  flex-shrink: 0;
  font-size: 12px;
  line-height: 1.45;
  padding: 8px 12px;
}

.oa-banner code {
  background: #ffedd5;
  border-radius: 4px;
  font-family: Consolas, monospace;
  padding: 1px 6px;
}

.file-input-hidden {
  display: none;
}

.upload-dialog-body {
  color: #161616;
  font-size: 14px;
  line-height: 1.5;
}

.upload-dialog-body--error .upload-dialog-alert {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #b91c1c;
  font-weight: 600;
  margin: 0 0 12px;
  padding: 10px 12px;
}

.upload-dialog-expected {
  margin: 0 0 10px;
}

.upload-dialog-expected code {
  background: #ffedd5;
  border-radius: 4px;
  color: #9a3412;
  font-family: Consolas, monospace;
  font-weight: 600;
  padding: 2px 6px;
}

.upload-dialog-message {
  margin: 0 0 10px;
  white-space: pre-wrap;
}

.upload-dialog-list {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin: 0 0 12px;
  max-height: 200px;
  overflow: auto;
  padding: 8px 12px 8px 28px;
}

.upload-dialog-list li {
  margin-bottom: 4px;
}

.upload-dialog-hint {
  color: #6b7280;
  font-size: 13px;
  margin: 0;
}

.upload-dialog-footer {
  display: flex;
  justify-content: flex-end;
}

.handsontable-host {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  flex: 1;
  min-height: 280px;
  overflow: hidden;
  width: 100%;
}

.handsontable-host.is-hidden {
  height: 0 !important;
  min-height: 0;
  opacity: 0;
  overflow: hidden;
  pointer-events: none;
  position: absolute;
}

:deep(.handsontable) {
  font-size: 11px;
}
</style>
