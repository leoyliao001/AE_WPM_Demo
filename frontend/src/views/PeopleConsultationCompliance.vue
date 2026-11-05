<template>
  <PageShell
    title="People Consultation & Compliance"
    :show-heading="false"
    :back-to="backTo"
    back-label="Back to Toll Gates"
    full-width
  >
    <div class="pcc-page">
      <div v-if="loading" class="pcc-feedback" role="status">Loading checklist...</div>
      <div v-if="error" class="pcc-feedback pcc-feedback--error" role="alert">
        {{ error }}
        <button v-if="record" type="button" class="pcc-link-button" @click="load">Reload</button>
      </div>
      <div v-if="success" class="pcc-feedback pcc-feedback--success" role="status">{{ success }}</div>

      <template v-if="record && !loading">
        <nav class="pcc-breadcrumb" aria-label="Breadcrumb">
          <router-link to="/project-dashboard">Projects</router-link>
          <span aria-hidden="true">›</span>
          <router-link :to="backTo">{{ record.projectName }}</router-link>
          <span aria-hidden="true">›</span>
          <span>People Consultation &amp; Compliance</span>
        </nav>

        <header class="pcc-hero">
          <div class="pcc-heading">
            <div>
              <p class="pcc-eyebrow">People &amp; compliance</p>
              <h1>People Consultation &amp; Compliance</h1>
              <p class="pcc-subtitle">Record consultation, compliance checks and supporting evidence for this project.</p>
            </div>
            <div class="pcc-actions">
              <button type="button" class="pcc-button pcc-button--outline" :disabled="!!busy" @click="exportChecklist">Export</button>
              <button
                v-if="record.status !== 'confirmed'"
                type="button"
                class="pcc-button pcc-button--outline"
                :disabled="!!busy || !record.permissions.edit || !dirty"
                @click="save('save')"
              >Save draft</button>
              <button
                v-if="record.status !== 'confirmed'"
                type="button"
                class="pcc-button pcc-button--primary"
                :disabled="!!busy || !record.permissions.edit"
                @click="save('confirm')"
              >Confirm checklist</button>
              <button
                v-else
                type="button"
                class="pcc-button pcc-button--outline"
                :disabled="!!busy || !record.permissions.edit"
                @click="reopenDialog = true"
              >Reopen checklist</button>
            </div>
          </div>
          <div class="pcc-project-meta">
            <strong>{{ record.projectName }}</strong>
            <span>{{ record.migrationRequestId }}</span>
            <span v-if="record.status === 'confirmed'" class="pcc-status pcc-status--confirmed">Confirmed · v{{ record.version }}</span>
            <span v-else class="pcc-status pcc-status--progress">In progress</span>
            <span>{{ dirty ? 'Unsaved changes' : record.updatedAt ? `Last saved ${dateTime(record.updatedAt)}` : 'Not yet saved' }}</span>
          </div>
        </header>

        <div v-if="!record.permissions.edit" class="pcc-feedback">
          You have view-only access to this project checklist.
        </div>
        <div v-if="openCount" class="pcc-warning" role="status">
          <span class="pcc-warning-icon" aria-hidden="true">!</span>
          <span><strong>{{ openCount }} {{ openCount === 1 ? 'item is' : 'items are' }} still open ahead of the next tollgate.</strong>
            Open items do not block the tollgate; they are shown as a warning on this page and the Tollgate Closure dashboard.</span>
        </div>

        <section class="pcc-summary" aria-label="Checklist summary">
          <article class="pcc-summary-card pcc-summary-card--green">
            <span>Items confirmed</span>
            <strong>{{ confirmedCount }} <small>of {{ record.items.length }}</small></strong>
            <small>Evidence filed and frozen</small>
          </article>
          <article class="pcc-summary-card pcc-summary-card--orange">
            <span>Open items</span>
            <strong>{{ openCount }}</strong>
            <small>Warning only, not blocking</small>
          </article>
          <article class="pcc-summary-card pcc-summary-card--gray">
            <span>Not applicable</span>
            <strong>{{ notApplicableCount }}</strong>
            <small>Reason recorded for each</small>
          </article>
          <article class="pcc-summary-card pcc-summary-card--navy">
            <span>Next tollgate</span>
            <strong>TG2</strong>
            <small>Plan sign-off</small>
          </article>
        </section>

        <div class="pcc-table-wrap">
          <table class="pcc-table">
            <thead>
              <tr>
                <th scope="col">#</th>
                <th scope="col">Consideration</th>
                <th scope="col">Owner (recorded here)</th>
                <th scope="col">Applicable?</th>
                <th scope="col">Status</th>
                <th scope="col">Date</th>
                <th scope="col">Evidence / outcome</th>
                <th scope="col">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in record.items" :key="item.id">
                <td class="pcc-row-number">{{ index + 1 }}</td>
                <td class="pcc-consideration">
                  <input
                    v-if="item.custom"
                    v-model="item.consideration"
                    type="text"
                    aria-label="Consideration"
                    maxlength="200"
                    :disabled="!canEdit"
                  />
                  <strong v-else>{{ item.consideration }}</strong>
                </td>
                <td>
                  <div class="pcc-owner">
                    <input v-model="item.ownerRole" type="text" aria-label="Owner role" maxlength="120" placeholder="Role" :disabled="!canEdit" />
                    <input v-model="item.ownerName" type="text" aria-label="Owner name" maxlength="200" placeholder="Person name" :disabled="!canEdit" />
                  </div>
                </td>
                <td>
                  <select
                    :value="item.applicable ? 'yes' : 'no'"
                    aria-label="Applicable"
                    :disabled="!canEdit"
                    @change="setApplicable(item, $event.target.value)"
                  >
                    <option value="yes">Yes</option>
                    <option value="no">No</option>
                  </select>
                  <input
                    v-if="!item.applicable"
                    v-model="item.reason"
                    type="text"
                    class="pcc-reason"
                    aria-label="Not applicable reason"
                    maxlength="1000"
                    placeholder="Reason required"
                    :disabled="!canEdit"
                  />
                </td>
                <td>
                  <select v-model="item.status" aria-label="Status" :disabled="!canEdit || !item.applicable" @change="setStatus(item)">
                    <option value="not_started">Not started</option>
                    <option value="in_progress">In progress</option>
                    <option value="confirmed">Confirmed</option>
                    <option value="not_applicable" disabled>Not applicable</option>
                  </select>
                </td>
                <td><input v-model="item.statusDate" type="date" aria-label="Date" :disabled="!canEdit || !item.applicable" /></td>
                <td>
                  <div class="pcc-evidence">
                    <input
                      v-model="item.evidence"
                      type="text"
                      aria-label="Evidence link"
                      maxlength="2000"
                      placeholder="Evidence link (optional)"
                      :disabled="!canEdit || !item.applicable"
                    />
                    <textarea
                      v-model="item.outcomeNote"
                      aria-label="Outcome note"
                      maxlength="500"
                      rows="1"
                      placeholder="Short outcome note"
                      :disabled="!canEdit || !item.applicable"
                    />
                    <a
                      v-for="file in item.evidenceFiles || []"
                      :key="file.id"
                      class="pcc-file-link"
                      :href="file.url"
                      @click.prevent="downloadEvidence(file)"
                    >{{ file.name }}</a>
                    <label v-if="canEdit && item.applicable" class="pcc-file-upload">
                      Attach MSG / PDF / XLSX / PPTX
                      <input type="file" accept=".msg,.pdf,.xlsx,.pptx" @change="uploadEvidence(item, $event)" />
                    </label>
                  </div>
                </td>
                <td class="pcc-row-action">
                  <a v-if="isWebLink(item.evidence)" :href="item.evidence" target="_blank" rel="noopener noreferrer">View</a>
                  <button v-else-if="canEdit && item.applicable" type="button" @click="focusItem(item)">
                    {{ item.status === 'not_started' ? 'Update' : 'Edit' }}
                  </button>
                  <span v-else>—</span>
                  <button
                    v-for="file in item.evidenceFiles || []"
                    v-if="canEdit"
                    :key="`remove-${file.id}`"
                    type="button"
                    class="pcc-row-action-remove"
                    @click="removeEvidence(item, file)"
                  >Remove file</button>
                  <button v-if="item.custom && canEdit" type="button" class="pcc-remove" @click="removeItem(item.id)">Remove</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="pcc-table-footer">
          <p>Every change is logged with user, date and reason. Confirmed items are frozen as tollgate evidence; reopening needs a reason.</p>
          <button v-if="canEdit" type="button" class="pcc-add-button" :disabled="!!busy || record.items.length >= 100" @click="addItem">+ Add consideration</button>
        </div>

        <details v-if="record.auditLog.length" class="pcc-audit">
          <summary>Change history ({{ record.auditLog.length }} entries)</summary>
          <div class="pcc-audit-scroll">
            <table>
              <thead><tr><th>Date</th><th>Consideration</th><th>Field</th><th>Change</th><th>User</th><th>Reason</th></tr></thead>
              <tbody>
                <tr v-for="(entry, index) in record.auditLog.slice().reverse()" :key="`${entry.at}-${index}`">
                  <td>{{ dateTime(entry.at) }}</td>
                  <td>{{ itemLabel(entry.item) }}</td>
                  <td>{{ entry.field }}</td>
                  <td>{{ displayValue(entry.old) }} → {{ displayValue(entry.new) }}</td>
                  <td>{{ entry.user }}</td>
                  <td>{{ entry.reason || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </details>
      </template>

      <div v-if="reopenDialog" class="pcc-modal-backdrop" @click.self="reopenDialog = false">
        <section class="pcc-modal" role="dialog" aria-modal="true" aria-labelledby="pcc-reopen-title">
          <h2 id="pcc-reopen-title">Reopen checklist</h2>
          <p>Reopening creates a new checklist version. Enter a reason; the previous confirmed version remains in the audit history.</p>
          <label for="pcc-reopen-reason">Reason for reopening</label>
          <textarea id="pcc-reopen-reason" v-model="reopenReason" maxlength="2000" rows="3" />
          <p v-if="reopenError" class="pcc-modal-error" role="alert">{{ reopenError }}</p>
          <div class="pcc-actions">
            <button type="button" class="pcc-button pcc-button--outline" :disabled="!!busy" @click="reopenDialog = false">Cancel</button>
            <button type="button" class="pcc-button pcc-button--primary" :disabled="!!busy" @click="reopenChecklist">Reopen</button>
          </div>
        </section>
      </div>
    </div>
  </PageShell>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'
import { useUnsavedChanges } from '../composables/useUnsavedChanges.js'

const route = useRoute()
const projectId = computed(() => String(route.params.id))
const backTo = computed(() => `/toll-gates?project=${encodeURIComponent(projectId.value)}`)
const record = ref(null)
const loading = ref(false)
const busy = ref('')
const error = ref('')
const success = ref('')
const baseline = ref('')
const reopenDialog = ref(false)
const reopenReason = ref('')
const reopenError = ref('')
const canEdit = computed(() => Boolean(record.value?.permissions?.edit && record.value.status !== 'confirmed' && !busy.value))
const dirty = computed(() => Boolean(record.value) && JSON.stringify(record.value.items) !== baseline.value)
const confirmedCount = computed(() => record.value?.items.filter(item => item.applicable && item.status === 'confirmed').length || 0)
const notApplicableCount = computed(() => record.value?.items.filter(item => !item.applicable).length || 0)
const openCount = computed(() => record.value?.items.filter(item => item.applicable && item.status !== 'confirmed').length || 0)

useUnsavedChanges(dirty, computed(() => loading.value || Boolean(busy.value)))

function requestError(caught, fallback) {
  if (caught.response?.data?.error) return caught.response.data.error
  if (caught.response?.status === 404) {
    return 'The People Consultation & Compliance API is not deployed on this server yet. Deploy the backend endpoint and apply migration 0057, then reload.'
  }
  return fallback
}

async function load() {
  const id = projectId.value
  loading.value = true
  error.value = ''
  success.value = ''
  record.value = null
  try {
    const { data } = await axios.get(`/api/migration-dashboard/projects/${id}/people-consultation-compliance/`)
    if (id === projectId.value) {
      record.value = data
      baseline.value = JSON.stringify(data.items)
    }
  } catch (caught) {
    if (id === projectId.value) error.value = requestError(caught, 'Unable to load the checklist.')
  } finally {
    if (id === projectId.value) loading.value = false
  }
}

async function save(action) {
  if (!record.value || busy.value) return
  busy.value = action
  error.value = ''
  success.value = ''
  try {
    const { data } = await axios.post(`/api/migration-dashboard/projects/${projectId.value}/people-consultation-compliance/`, {
      action,
      revision: record.value.revision,
      items: record.value.items,
    })
    record.value = data
    baseline.value = JSON.stringify(data.items)
    success.value = action === 'confirm'
      ? `Checklist confirmed as version ${data.version}. Open items remain a warning and do not block the tollgate.`
      : 'Checklist draft saved.'
  } catch (caught) {
    error.value = requestError(caught, 'Unable to save the checklist. Your inputs are retained.')
  } finally {
    busy.value = ''
  }
}

async function reopenChecklist() {
  reopenError.value = ''
  if (!reopenReason.value.trim()) {
    reopenError.value = 'Enter a reason to reopen this checklist.'
    return
  }
  busy.value = 'reopen'
  error.value = ''
  try {
    const { data } = await axios.post(`/api/migration-dashboard/projects/${projectId.value}/people-consultation-compliance/`, {
      action: 'reopen',
      revision: record.value.revision,
      reason: reopenReason.value.trim(),
    })
    record.value = data
    baseline.value = JSON.stringify(data.items)
    success.value = `Checklist reopened as version ${data.version}.`
    reopenDialog.value = false
    reopenReason.value = ''
  } catch (caught) {
    reopenError.value = requestError(caught, 'Unable to reopen the checklist.')
  } finally {
    busy.value = ''
  }
}

async function uploadEvidence(item, event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file || !record.value || busy.value) return
  busy.value = 'upload'
  error.value = ''
  const form = new FormData()
  form.append('file', file)
  form.append('itemId', item.id)
  form.append('revision', String(record.value.revision))
  try {
    const { data } = await axios.post(
      `/api/migration-dashboard/projects/${projectId.value}/people-consultation-compliance/evidence/`,
      form
    )
    record.value = data
    baseline.value = JSON.stringify(data.items)
    success.value = 'Evidence uploaded and recorded in the change history.'
  } catch (caught) {
    error.value = requestError(caught, 'Unable to upload evidence.')
  } finally {
    busy.value = ''
  }
}

async function removeEvidence(item, file) {
  if (!record.value || busy.value) return
  busy.value = 'delete-evidence'
  error.value = ''
  try {
    const { data } = await axios.delete(
      `/api/migration-dashboard/projects/${projectId.value}/people-consultation-compliance/evidence/`,
      { data: { evidenceId: file.id, revision: record.value.revision } }
    )
    record.value = data
    baseline.value = JSON.stringify(data.items)
    success.value = `Removed ${file.name} from ${item.consideration}.`
  } catch (caught) {
    error.value = requestError(caught, 'Unable to remove evidence.')
  } finally {
    busy.value = ''
  }
}

async function downloadEvidence(file) {
  try {
    const { data } = await axios.get(file.url, { responseType: 'blob' })
    const url = URL.createObjectURL(data)
    const link = document.createElement('a')
    link.href = url
    link.download = file.name
    link.click()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch (caught) {
    error.value = requestError(caught, `Unable to download ${file.name}.`)
  }
}

function setApplicable(item, value) {
  item.applicable = value === 'yes'
  if (item.applicable) {
    if (item.status === 'not_applicable') item.status = 'not_started'
    item.reason = ''
  } else {
    item.status = 'not_applicable'
  }
}

function setStatus(item) {
  if (item.status === 'confirmed' && !item.statusDate) item.statusDate = new Date().toISOString().slice(0, 10)
}

function addItem() {
  const id = `custom-${globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`}`
  record.value.items.push({
    id, consideration: '', ownerRole: '', ownerName: '', applicable: true, reason: '',
    status: 'not_started', statusDate: '', evidence: '', outcomeNote: '', custom: true,
  })
}

function removeItem(id) {
  record.value.items = record.value.items.filter(item => item.id !== id)
}

function focusItem(item) {
  item.status = 'in_progress'
}

function isWebLink(value) {
  return /^https?:\/\/\S+$/i.test(value || '')
}

function itemLabel(id) {
  return record.value.items.find(item => item.id === id)?.consideration || (id ? 'Removed consideration' : 'Checklist')
}

function displayValue(value) {
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (value && typeof value === 'object') return JSON.stringify(value)
  return value == null || value === '' ? '—' : String(value)
}

function dateTime(value) {
  if (!value) return ''
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

function exportChecklist() {
  const columns = ['Consideration', 'Owner role', 'Owner name', 'Applicable', 'Reason', 'Status', 'Date', 'Evidence', 'Outcome']
  const quote = value => `"${String(value ?? '').replaceAll('"', '""')}"`
  const lines = [
    columns.map(quote).join(','),
    ...record.value.items.map(item => [
      item.consideration, item.ownerRole, item.ownerName, item.applicable ? 'Yes' : 'No',
      item.reason, item.status.replaceAll('_', ' '), item.statusDate, item.evidence, item.outcomeNote,
    ].map(quote).join(',')),
  ]
  const blob = new Blob([`\uFEFF${lines.join('\r\n')}`], { type: 'text/csv;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `people-consultation-compliance-${record.value.migrationRequestId || projectId.value}.csv`
  link.click()
  URL.revokeObjectURL(link.href)
}

watch(projectId, load, { immediate: true })
</script>

<style scoped>
.pcc-page { --ink: #17283d; --muted: #657187; --line: #d7e0ec; color: var(--ink); padding: 8px 8px 32px; width: 100%; }
.pcc-breadcrumb { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 0 0 12px; color: var(--muted); font-size: 12px; }
.pcc-breadcrumb a { color: #1769db; text-decoration: none; }
.pcc-hero { padding: 16px; border: 1px solid var(--line); border-radius: 8px; background: #fff; }
.pcc-heading, .pcc-actions, .pcc-project-meta { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; }
.pcc-heading { justify-content: space-between; }
.pcc-heading h1 { margin: 3px 0 6px; font-size: 22px; line-height: 1.25; }
.pcc-eyebrow { margin: 0; color: #697589; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .07em; }
.pcc-subtitle { margin: 0; color: var(--muted); font-size: 12px; }
.pcc-actions { justify-content: flex-end; }
.pcc-button { min-height: 34px; padding: 0 15px; border: 1px solid #d5deeb; border-radius: 6px; background: #fff; color: #192b43; font: inherit; font-size: 12px; cursor: pointer; }
.pcc-button--primary { border-color: #1769db; background: #1769db; color: #fff; font-weight: 700; }
.pcc-button:disabled { opacity: .55; cursor: not-allowed; }
.pcc-project-meta { margin-top: 12px; color: var(--muted); font-size: 11px; }
.pcc-project-meta span + span { padding-left: 10px; border-left: 1px solid #d8e0e9; }
.pcc-status { padding: 5px 12px; border-radius: 15px; background: #fff3df; color: #ab5a00; font-weight: 700; text-transform: uppercase; }
.pcc-status--confirmed { background: #e6f4ea; color: #1b8c43; }
.pcc-warning, .pcc-feedback { display: flex; align-items: center; gap: 10px; margin-top: 10px; padding: 10px 12px; border: 1px solid #ffd08b; border-radius: 6px; background: #fff4e0; color: #8a4c00; font-size: 12px; line-height: 1.5; }
.pcc-warning-icon { display: grid; width: 20px; height: 20px; flex: 0 0 auto; place-items: center; border-radius: 50%; background: #f28a22; color: #fff; font-weight: 800; }
.pcc-feedback { display: block; border-color: #d6e0e9; background: #f5f8fb; color: #52667c; }
.pcc-feedback--error { border-color: #f1c6c2; background: #fff1ef; color: #a3332c; }
.pcc-feedback--success { border-color: #c5e8d0; background: #edf8f0; color: #176345; }
.pcc-link-button { margin-left: 8px; border: 0; background: none; color: #1769db; cursor: pointer; font: inherit; font-weight: 700; }
.pcc-summary { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 10px 0; }
.pcc-summary-card { min-height: 62px; display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 3px 8px; padding: 9px 12px; border: 1px solid var(--line); border-left: 4px solid #6c7484; border-radius: 6px; background: #fff; }
.pcc-summary-card > span { grid-column: 1 / -1; color: #687286; font-size: 10px; font-weight: 700; text-transform: uppercase; }
.pcc-summary-card strong { color: #192b43; font-size: 22px; line-height: 1.1; }
.pcc-summary-card strong small, .pcc-summary-card > small { color: var(--muted); font-size: 10px; font-weight: 400; }
.pcc-summary-card > small { text-align: right; }
.pcc-summary-card--green { border-left-color: #28a354; }
.pcc-summary-card--green strong { color: #23984b; }
.pcc-summary-card--orange { border-left-color: #f28a22; }
.pcc-summary-card--orange strong { color: #ee7b16; }
.pcc-summary-card--gray { border-left-color: #737b89; }
.pcc-summary-card--navy { border-left-color: #153252; }
.pcc-table-wrap { overflow-x: auto; border: 1px solid var(--line); }
.pcc-table { width: 100%; min-width: 1080px; border-collapse: collapse; text-align: left; font-size: 11px; }
.pcc-table th { padding: 8px 7px; background: #f0f3f8; color: #697285; font-size: 10px; font-weight: 700; white-space: nowrap; }
.pcc-table td { min-width: 82px; padding: 7px; border-top: 1px solid var(--line); vertical-align: middle; }
.pcc-table tbody tr:nth-child(even) { background: #f7f8fa; }
.pcc-row-number { width: 30px; color: #697285; font-weight: 700; }
.pcc-consideration { min-width: 170px !important; font-weight: 700; }
.pcc-table input, .pcc-table select, .pcc-table textarea, .pcc-modal textarea { width: 100%; min-width: 80px; padding: 6px; border: 1px solid #d5deea; border-radius: 5px; background: #fff; color: var(--ink); font: inherit; font-size: 11px; }
.pcc-table textarea { resize: vertical; }
.pcc-owner, .pcc-evidence { display: grid; gap: 4px; min-width: 128px; }
.pcc-file-link { overflow-wrap: anywhere; color: #1769db; font-size: 10px; }
.pcc-file-upload { color: #1769db; font-size: 10px; font-weight: 700; cursor: pointer; }
.pcc-file-upload input { margin-top: 3px; padding: 3px; font-size: 10px; }
.pcc-reason { margin-top: 4px; }
.pcc-row-action { min-width: 75px !important; }
.pcc-row-action button, .pcc-row-action a { display: inline-block; padding: 3px 0; border: 0; background: none; color: #1769db; font: inherit; font-weight: 700; text-decoration: none; cursor: pointer; }
.pcc-row-action .pcc-remove { color: #a3332c; }
.pcc-row-action .pcc-row-action-remove { color: #a3332c; }
.pcc-table-footer { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 8px 2px; }
.pcc-table-footer p { margin: 0; color: #697589; font-size: 10px; line-height: 1.5; }
.pcc-add-button { flex: 0 0 auto; border: 0; background: none; color: #1769db; font: inherit; font-size: 11px; font-weight: 700; cursor: pointer; }
.pcc-add-button:disabled { opacity: .5; cursor: not-allowed; }
.pcc-audit { margin-top: 12px; color: var(--muted); font-size: 12px; }
.pcc-audit summary { padding: 8px 0; font-weight: 700; cursor: pointer; }
.pcc-audit-scroll { overflow-x: auto; }
.pcc-audit table { width: 100%; border-collapse: collapse; font-size: 11px; }
.pcc-audit th, .pcc-audit td { padding: 8px; border: 1px solid var(--line); text-align: left; }
.pcc-audit th { background: #f0f3f8; }
.pcc-modal-backdrop { position: fixed; z-index: 20; inset: 0; display: grid; place-items: center; padding: 16px; background: #10243b88; }
.pcc-modal { width: min(460px, 100%); padding: 22px; border-radius: 9px; background: #fff; box-shadow: 0 12px 40px #10243b33; }
.pcc-modal h2 { margin: 0 0 8px; font-size: 19px; }
.pcc-modal p, .pcc-modal label { color: var(--muted); font-size: 12px; line-height: 1.5; }
.pcc-modal label { display: block; margin: 14px 0 5px; font-weight: 700; }
.pcc-modal textarea { font: inherit; }
.pcc-modal .pcc-actions { margin-top: 16px; }
.pcc-modal-error { color: #a3332c !important; }
@media (max-width: 760px) {
  .pcc-page { padding: 0 0 20px; }
  .pcc-heading { align-items: flex-start; }
  .pcc-heading h1 { font-size: 20px; }
  .pcc-actions { justify-content: flex-start; }
  .pcc-summary { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
  .pcc-table-footer { align-items: flex-start; flex-direction: column; }
}
</style>
