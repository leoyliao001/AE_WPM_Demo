<template>
  <PageShell
    title="People Consultation & Compliance"
    :show-heading="false"
    :back-to="backTo"
    back-label="Back to Artefact Delivery Dashboard"
    back-link-to-topbar
    full-width
  >
    <main class="consultation-page">
      <div v-if="loading" class="notice" role="status">Loading People Consultation &amp; Compliance…</div>
      <div v-if="error" class="notice notice--error" role="alert">
        {{ error }}
        <button v-if="!record" type="button" class="link-button" @click="load">Retry</button>
      </div>
      <div v-if="success" class="notice notice--success" role="status">{{ success }}</div>

      <template v-if="record && !loading">
        <header class="page-hero">
          <div class="hero-row">
            <div>
              <h1>People Consultation &amp; Compliance</h1>
              <span class="state-chip" :class="`state-chip--${overallStatusKey}`">{{ overallStatus }}</span>
              <p class="project-meta">
                <strong>{{ record.projectName }}</strong>
                <span>{{ record.migrationRequestId }}</span>
                <span>Phase: {{ record.phase }}</span>
                <span>{{ record.updatedAt ? `Last saved ${dateTime(record.updatedAt)}` : 'Not yet saved' }}</span>
                <span v-if="dirty">Unsaved changes</span>
              </p>
            </div>
            <div class="toolbar">
              <button type="button" class="button button--outline" :disabled="busy" @click="exportCsv">Export</button>
              <button type="button" class="button button--outline" :disabled="busy || !dirty" @click="save('save')">
                {{ busy === 'save' ? 'Saving…' : 'Save draft' }}
              </button>
              <button type="button" class="button button--primary" :disabled="busy" @click="save('confirm')">
                {{ busy === 'confirm' ? 'Confirming…' : 'Confirm checklist' }}
              </button>
            </div>
          </div>
        </header>

        <div v-if="openCount" class="warning-banner" role="status">
          <span class="warning-icon" aria-hidden="true">!</span>
          <span><strong>{{ openCount }} {{ openCount === 1 ? 'item is' : 'items are' }} still open ahead of the TG2 review.</strong>
            Open items do not block the tollgate; they show as a warning at tollgate review and on the Tollgate Closure dashboard.</span>
          <strong class="warning-count">{{ openCount }}</strong>
        </div>

        <section class="summary-grid" aria-label="Checklist summary">
          <article class="summary-card summary-card--green">
            <span class="summary-label">Items confirmed</span>
            <strong>{{ confirmedCount }} <small>of {{ record.items.length }}</small></strong>
            <span class="summary-foot">Evidence filed and frozen</span>
          </article>
          <article class="summary-card summary-card--orange">
            <span class="summary-label">Open items</span>
            <strong>{{ openCount }}</strong>
            <span class="summary-foot">Warning only, not blocking</span>
          </article>
          <article class="summary-card summary-card--gray">
            <span class="summary-label">Not applicable</span>
            <strong>{{ notApplicableCount }}</strong>
            <span class="summary-foot">Reason recorded for each</span>
          </article>
          <article class="summary-card summary-card--navy">
            <span class="summary-label">Next tollgate</span>
            <strong>TG2</strong>
            <span class="summary-foot">Plan sign-off</span>
          </article>
        </section>

        <section class="checklist-panel" aria-label="People consultation considerations">
          <div class="table-scroll">
            <table class="consultation-table">
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
                  <td class="row-index">{{ index + 1 }}</td>
                  <td>
                    <input
                      :id="`consultation-label-${item.id}`"
                      v-model="item.label"
                      class="consideration-input"
                      :disabled="isFrozen(item)"
                      aria-label="Consideration"
                      maxlength="255"
                    />
                    <input
                      v-if="!item.applicable"
                      v-model="item.naReason"
                      class="na-reason"
                      :disabled="isFrozen(item)"
                      aria-label="Reason not applicable"
                      maxlength="500"
                      placeholder="Reason not applicable…"
                    />
                  </td>
                  <td>
                    <input
                      v-model="item.ownerRole"
                      class="owner-role-input"
                      :disabled="isFrozen(item)"
                      aria-label="Owner role"
                      maxlength="128"
                      placeholder="Role"
                    />
                    <div class="person-picker">
                      <input
                        :id="`consultation-owner-${item.id}`"
                        v-model="item.ownerName"
                        :disabled="isFrozen(item)"
                        aria-label="Owner name"
                        maxlength="255"
                        placeholder="Search directory…"
                        autocomplete="off"
                        @input="searchPeople(item)"
                      />
                      <div v-if="activeSearchId === item.id && peopleResults.length" class="person-results">
                        <button
                          v-for="person in peopleResults"
                          :key="person.id"
                          type="button"
                          @click="selectPerson(item, person)"
                        >
                          <strong>{{ person.name }}</strong><small>{{ person.email }}</small>
                        </button>
                      </div>
                    </div>
                    <small v-if="item.ownerEmail" class="owner-email">{{ item.ownerEmail }}</small>
                  </td>
                  <td>
                    <select
                      v-model="item.applicable"
                      :disabled="isFrozen(item)"
                      aria-label="Applicable"
                      @change="changeApplicability(item)"
                    >
                      <option :value="true">Yes</option>
                      <option :value="false">No</option>
                    </select>
                  </td>
                  <td>
                    <select
                      v-model="item.status"
                      :disabled="isFrozen(item) || !item.applicable"
                      :class="`status-select status-select--${item.status}`"
                      aria-label="Status"
                    >
                      <option value="not_started">Not started</option>
                      <option value="in_progress">In progress</option>
                      <option value="confirmed">Confirmed</option>
                    </select>
                  </td>
                  <td>
                    <input
                      v-model="item.statusDate"
                      :disabled="isFrozen(item) || !item.applicable"
                      type="date"
                      aria-label="Status date"
                    />
                  </td>
                  <td class="evidence-cell">
                    <input
                      v-model="item.evidenceUrl"
                      :disabled="isFrozen(item)"
                      type="url"
                      aria-label="Evidence link"
                      maxlength="1000"
                      placeholder="Evidence link (optional)"
                    />
                    <label class="file-link">
                      {{ item.evidenceFileName || 'Attach file' }}
                      <input
                        type="file"
                        accept=".msg,.pdf,.xlsx,.pptx"
                        :disabled="isFrozen(item) || busy"
                        @change="uploadFile(item, $event)"
                      />
                    </label>
                    <textarea
                      v-model="item.outcomeNote"
                      :disabled="isFrozen(item)"
                      aria-label="Outcome note"
                      maxlength="500"
                      rows="2"
                      placeholder="Short outcome note…"
                    />
                    <a
                      v-if="item.evidenceFileName"
                      class="evidence-link"
                      :href="item.evidenceUrlForDownload"
                      target="_blank"
                      rel="noopener noreferrer"
                    >View {{ item.evidenceFileName }}</a>
                    <a
                      v-else-if="item.evidenceUrl"
                      class="evidence-link"
                      :href="item.evidenceUrl"
                      target="_blank"
                      rel="noopener noreferrer"
                    >View evidence</a>
                  </td>
                  <td>
                    <button
                      v-if="item.confirmedAt"
                      type="button"
                      class="table-action"
                      :disabled="busy"
                      @click="reopen(item)"
                    >Reopen</button>
                    <button
                      v-else-if="!item.ownerName"
                      type="button"
                      class="table-action"
                      @click="focusField(`consultation-owner-${item.id}`)"
                    >Assign owner</button>
                    <button
                      v-else
                      type="button"
                      class="table-action"
                      @click="focusField(`consultation-label-${item.id}`)"
                    >Update</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="adding" class="add-row-form">
            <input v-model="newLabel" maxlength="255" placeholder="New consideration name" aria-label="New consideration name" />
            <button type="button" class="button button--primary" :disabled="busy || !newLabel.trim()" @click="addConsideration">Add</button>
            <button type="button" class="button button--outline" :disabled="busy" @click="adding = false; newLabel = ''">Cancel</button>
          </div>
          <button v-else type="button" class="add-link" :disabled="busy" @click="adding = true">+ Add consideration</button>
          <p class="footnote">Every change is logged with user, date and reason. Confirmed items are frozen as tollgate evidence; re-opening needs a reason.</p>
        </section>

        <details class="audit-panel">
          <summary>Audit history · {{ record.auditLog.length }} changes</summary>
          <div class="table-scroll">
            <table class="consultation-table audit-table">
              <thead><tr><th>Consideration</th><th>Field</th><th>Old value</th><th>New value</th><th>User</th><th>Date</th><th>Reason</th></tr></thead>
              <tbody>
                <tr v-for="(entry, index) in record.auditLog" :key="`${entry.at}-${index}`">
                  <td>{{ entry.item }}</td><td>{{ fieldLabel(entry.field) }}</td><td>{{ entry.old }}</td>
                  <td>{{ entry.new }}</td><td>{{ entry.user }}</td><td>{{ dateTime(entry.at) }}</td><td>{{ entry.reason }}</td>
                </tr>
                <tr v-if="!record.auditLog.length"><td colspan="7" class="empty-row">Changes appear here after the first save.</td></tr>
              </tbody>
            </table>
          </div>
        </details>
      </template>
    </main>
  </PageShell>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'

const route = useRoute()
const projectId = computed(() => String(route.params.id || ''))
const backTo = computed(() => `/toll-gates?project=${encodeURIComponent(projectId.value)}`)
const record = ref(null)
const loading = ref(false)
const busy = ref('')
const error = ref('')
const success = ref('')
const baseline = ref('')
const adding = ref(false)
const newLabel = ref('')
const activeSearchId = ref('')
const peopleResults = ref([])
let searchTimer

const content = data => JSON.stringify(data?.items || [])
const dirty = computed(() => Boolean(record.value) && content(record.value) !== baseline.value)
const confirmedCount = computed(() => record.value?.items.filter(item => item.status === 'confirmed').length || 0)
const notApplicableCount = computed(() => record.value?.items.filter(item => !item.applicable).length || 0)
const openCount = computed(() => record.value?.items.filter(item => item.applicable && item.status !== 'confirmed').length || 0)
const overallStatus = computed(() => {
  if (record.value?.version && openCount.value === 0) return 'Confirmed'
  if (record.value?.revision) return 'In progress'
  return 'Not started'
})
const overallStatusKey = computed(() => overallStatus.value.toLowerCase().replaceAll(' ', '_'))

async function load() {
  const id = projectId.value
  if (!id) return
  loading.value = true
  error.value = ''
  success.value = ''
  record.value = null
  try {
    const { data } = await axios.get(`/api/migration-dashboard/projects/${id}/people-consultation-compliance/`)
    if (id === projectId.value) {
      record.value = data
      baseline.value = content(data)
    }
  } catch (caught) {
    if (id === projectId.value) error.value = caught.response?.data?.error || 'Unable to load the checklist.'
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
    const { data } = await axios.post(
      `/api/migration-dashboard/projects/${projectId.value}/people-consultation-compliance/`,
      { revision: record.value.revision, action, items: record.value.items }
    )
    record.value = data
    baseline.value = content(data)
    success.value = action === 'confirm'
      ? `Checklist version ${data.version} confirmed. Open items remain a warning and do not block the tollgate.`
      : 'Checklist draft saved.'
  } catch (caught) {
    error.value = caught.response?.data?.error || 'Unable to save. Your inputs are retained.'
  } finally {
    busy.value = ''
  }
}

function changeApplicability(item) {
  if (item.applicable) {
    item.status = 'not_started'
    item.naReason = ''
  } else {
    item.status = 'not_applicable'
    item.statusDate = ''
  }
}

async function addConsideration() {
  const label = newLabel.value.trim()
  if (!label || busy.value) return
  busy.value = 'add'
  error.value = ''
  try {
    const { data } = await axios.post(
      `/api/migration-dashboard/projects/${projectId.value}/people-consultation-compliance/`,
      { revision: record.value.revision, action: 'add_item', id: crypto.randomUUID(), label }
    )
    record.value = data
    baseline.value = content(data)
    adding.value = false
    newLabel.value = ''
    success.value = 'Consideration added.'
  } catch (caught) {
    error.value = caught.response?.data?.error || 'Unable to add this consideration.'
  } finally {
    busy.value = ''
  }
}

async function reopen(item) {
  const reason = window.prompt(`Why are you reopening "${item.label}"?`)
  if (!reason?.trim()) return
  busy.value = 'reopen'
  error.value = ''
  success.value = ''
  try {
    const { data } = await axios.post(
      `/api/migration-dashboard/projects/${projectId.value}/people-consultation-compliance/`,
      { revision: record.value.revision, action: 'reopen', id: item.id, reason: reason.trim() }
    )
    record.value = data
    baseline.value = content(data)
    success.value = `${item.label} reopened. The reason is in the audit history.`
  } catch (caught) {
    error.value = caught.response?.data?.error || 'Unable to reopen this consideration.'
  } finally {
    busy.value = ''
  }
}

async function uploadFile(item, event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  busy.value = `upload-${item.id}`
  error.value = ''
  success.value = ''
  const form = new FormData()
  form.append('file', file)
  form.append('revision', String(record.value.revision))
  try {
    const { data } = await axios.post(
      `/api/migration-dashboard/projects/${projectId.value}/people-consultation-compliance/evidence/${item.pk}/`,
      form
    )
    record.value = data
    baseline.value = content(data)
    success.value = 'Evidence uploaded.'
  } catch (caught) {
    error.value = caught.response?.data?.error || 'Unable to upload evidence.'
  } finally {
    busy.value = ''
  }
}

function searchPeople(item) {
  item.ownerUserId = ''
  item.ownerEmail = ''
  activeSearchId.value = item.id
  window.clearTimeout(searchTimer)
  if (item.ownerName.trim().length < 2) {
    peopleResults.value = []
    return
  }
  searchTimer = window.setTimeout(async () => {
    try {
      const { data } = await axios.get(
        `/api/migration-dashboard/projects/${projectId.value}/people-consultation-compliance/people/`,
        { params: { q: item.ownerName.trim() } }
      )
      if (activeSearchId.value === item.id) peopleResults.value = data.rows
    } catch (caught) {
      error.value = caught.response?.data?.error || 'Unable to search the people directory.'
    }
  }, 250)
}

function selectPerson(item, person) {
  item.ownerUserId = person.id
  item.ownerName = person.name
  item.ownerEmail = person.email
  activeSearchId.value = ''
  peopleResults.value = []
}

function isFrozen(item) {
  return Boolean(item.confirmedAt) || Boolean(busy.value)
}

function focusField(id) {
  document.getElementById(id)?.focus()
}

function exportCsv() {
  const rows = [
    ['Consideration', 'Owner role', 'Owner', 'Owner email', 'Applicable', 'Status', 'Date', 'Evidence link', 'Evidence file', 'Outcome / reason'],
    ...record.value.items.map(item => [
      item.label, item.ownerRole, item.ownerName, item.ownerEmail, item.applicable ? 'Yes' : 'No',
      item.status.replaceAll('_', ' '), item.statusDate, item.evidenceUrl, item.evidenceFileName,
      item.applicable ? item.outcomeNote : item.naReason
    ])
  ]
  const csv = rows.map(row => row.map(value => `"${String(value ?? '').replaceAll('"', '""')}"`).join(',')).join('\r\n')
  const url = URL.createObjectURL(new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8' }))
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `people-consultation-${record.value.migrationRequestId}.csv`
  anchor.click()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}

function fieldLabel(value) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, character => character.toUpperCase())
}

function dateTime(value) {
  return value ? new Date(value).toLocaleString('en-GB') : ''
}

watch(projectId, load, { immediate: true })
onBeforeUnmount(() => window.clearTimeout(searchTimer))
</script>

<style scoped>
.consultation-page {
  --ink: #17283e;
  --muted: #647086;
  --line: #d7dfeb;
  --blue: #1464dc;
  width: 100%;
  padding: 4px 10px 32px;
  color: var(--ink);
  font-size: 13px;
}
.page-hero, .checklist-panel, .audit-panel {
  border: 1px solid var(--line);
  border-radius: 7px;
  background: #fff;
}
.page-hero { padding: 14px 16px 11px; }
.hero-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; }
h1 { margin: 0 0 8px; font-size: 24px; letter-spacing: -.3px; }
.state-chip, .status-select {
  display: inline-block;
  border: 0;
  border-radius: 16px;
  padding: 5px 12px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
}
.state-chip { background: #fff2dd; color: #a46100; }
.state-chip--confirmed { background: #e4f4e9; color: #267343; }
.state-chip--not_started { background: #edf0f4; color: #657185; }
.project-meta { display: flex; flex-wrap: wrap; gap: 5px 12px; margin: 7px 0 0; color: var(--muted); font-size: 11px; }
.project-meta strong { color: #35445a; }
.project-meta span + span { padding-left: 12px; border-left: 1px solid var(--line); }
.toolbar { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; }
.button { border: 1px solid #d5deeb; border-radius: 5px; padding: 9px 14px; background: #fff; color: #28374d; font: inherit; font-size: 11px; cursor: pointer; white-space: nowrap; }
.button--primary { border-color: var(--blue); background: var(--blue); color: #fff; font-weight: 700; }
.button:disabled, .table-action:disabled { opacity: .5; cursor: not-allowed; }
.warning-banner { display: flex; align-items: center; gap: 10px; margin: 8px 0; padding: 9px 12px; border: 1px solid #f1c979; border-left: 4px solid #f39427; border-radius: 5px; background: #fff5e3; color: #905506; font-size: 11px; line-height: 1.5; }
.warning-icon, .warning-count { display: grid; flex: 0 0 20px; width: 20px; height: 20px; place-items: center; border-radius: 50%; background: #f39427; color: #fff; font-weight: 700; }
.warning-count { margin-left: auto; }
.summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin: 8px 0; }
.summary-card { display: grid; grid-template-columns: 1fr auto; min-height: 62px; align-content: center; padding: 9px 12px; border: 1px solid var(--line); border-left: 4px solid #122b49; border-radius: 5px; background: #fff; }
.summary-card--green { border-left-color: #23944f; }
.summary-card--orange { border-left-color: #f39427; }
.summary-card--gray { border-left-color: #9299a5; }
.summary-card--navy { border-left-color: #102b4b; }
.summary-label { grid-column: 1 / -1; color: #697386; font-size: 9px; font-weight: 700; text-transform: uppercase; }
.summary-card strong { align-self: center; margin-top: 3px; font-size: 20px; }
.summary-card--green strong { color: #23944f; }
.summary-card--orange strong { color: #e87511; }
.summary-card strong small { color: #667187; font-size: 10px; font-weight: 400; }
.summary-foot { align-self: end; color: var(--muted); font-size: 9px; text-align: right; }
.checklist-panel { padding: 0 0 10px; }
.table-scroll { overflow-x: auto; }
.consultation-table { width: 100%; min-width: 1050px; border-collapse: collapse; text-align: left; font-size: 10px; }
.consultation-table th { padding: 9px 7px; background: #f0f3f8; color: #606b7f; font-size: 9px; white-space: nowrap; }
.consultation-table td { min-width: 84px; padding: 7px; border-bottom: 1px solid #dce3ed; vertical-align: middle; }
.consultation-table tbody tr:nth-child(even) { background: #f7f8fa; }
.consultation-table input:not([type="file"]), .consultation-table select, .consultation-table textarea, .add-row-form input {
  box-sizing: border-box;
  width: 100%;
  min-width: 76px;
  border: 1px solid #d6deea;
  border-radius: 4px;
  padding: 6px;
  background: #fff;
  color: var(--ink);
  font: inherit;
  font-size: 10px;
}
.consultation-table textarea { resize: vertical; }
.consultation-table input:disabled, .consultation-table select:disabled, .consultation-table textarea:disabled { background: #f0f2f5; color: #747d8c; cursor: not-allowed; }
.consultation-table .row-index { min-width: 22px; color: #68748a; font-weight: 700; }
.consideration-input { min-width: 145px !important; color: #25334a !important; font-weight: 700 !important; }
.owner-role-input { margin-bottom: 4px; }
.owner-email { display: block; margin-top: 3px; color: var(--muted); overflow-wrap: anywhere; }
.person-picker { position: relative; }
.person-results { position: absolute; z-index: 4; top: 100%; left: 0; width: max(210px, 100%); max-height: 180px; overflow-y: auto; border: 1px solid var(--line); border-radius: 5px; background: #fff; box-shadow: 0 4px 14px #17283e20; }
.person-results button { display: flex; width: 100%; flex-direction: column; gap: 3px; padding: 8px; border: 0; border-bottom: 1px solid #eef0f4; background: #fff; color: var(--ink); text-align: left; cursor: pointer; }
.person-results button:hover { background: #f3f7ff; }
.person-results small { color: var(--muted); }
.consultation-table td:nth-child(4), .consultation-table td:nth-child(5) { min-width: 98px; }
.status-select { width: 100%; padding: 6px 5px !important; cursor: pointer; }
.status-select--confirmed { background: #e5f4e9 !important; color: #267343 !important; }
.status-select--in_progress { background: #fff3dc !important; color: #9c610a !important; }
.status-select--not_started { background: #f0f1f3 !important; color: #667084 !important; }
.evidence-cell { min-width: 170px !important; }
.file-link { display: inline-block; margin: 5px 0; color: var(--blue); cursor: pointer; }
.file-link input { position: absolute; width: 1px; height: 1px; opacity: 0; }
.evidence-link { display: block; margin: 3px 0; color: var(--blue); text-decoration: none; }
.table-action, .link-button { padding: 3px 0; border: 0; background: none; color: var(--blue); font: inherit; font-size: 10px; font-weight: 700; cursor: pointer; white-space: nowrap; }
.na-reason { margin-top: 5px; }
.add-link { display: block; margin: 9px 12px 0 auto; padding: 4px; border: 0; background: none; color: var(--blue); font: inherit; font-size: 10px; font-weight: 700; cursor: pointer; }
.add-row-form { display: flex; gap: 8px; margin: 10px 12px 0; }
.add-row-form input { max-width: 320px; }
.footnote { margin: 5px 12px 0; color: var(--muted); font-size: 10px; }
.audit-panel { margin-top: 10px; padding: 10px 12px; }
.audit-panel summary { color: #47546b; font-size: 11px; font-weight: 700; cursor: pointer; }
.audit-table { margin-top: 10px; }
.audit-table td { max-width: 240px; overflow-wrap: anywhere; }
.empty-row { color: var(--muted); text-align: center; }
.notice { margin: 6px 0; padding: 10px 12px; border-radius: 5px; background: #eef4fa; color: #34445b; font-size: 12px; }
.notice--error { background: #fff0ed; color: #a3332c; }
.notice--success { background: #e8f6ee; color: #176345; }
@media (max-width: 760px) {
  .consultation-page { padding: 0 0 24px; }
  .hero-row { flex-direction: column; }
  .toolbar { justify-content: flex-start; }
  .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .project-meta { gap: 5px 8px; }
}
</style>
