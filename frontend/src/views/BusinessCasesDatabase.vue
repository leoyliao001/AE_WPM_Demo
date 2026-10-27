<template>
  <PageShell title="Business Cases" subtitle="Maintain online Business Case records here. Intake and Scope remain in their original source records."
    back-to="/project-attributes" back-label="Back to Admin" full-width class="bc-page">
    <div class="bc-toolbar">
      <label class="bc-record-filter">Filter records<input v-model="query" type="search" placeholder="Project, request ID, status…" /></label>
      <label class="bc-record-filter">Create / edit for project<select v-model="selectedProject" :disabled="blocked"><option value="">Select a project</option>
        <option v-for="project in projects" :key="project.id" :value="project.id">{{ project.migrationRequestId }} · {{ project.projectName }}</option>
      </select></label>
      <button type="button" :disabled="!selectedProject || blocked" @click="openRecord(selectedProject)">Create / edit record</button>
      <button type="button" :disabled="blocked" @click="reload">Reload</button>
    </div>
    <p v-if="error" class="bc-error" role="alert">{{ error }}</p>
    <p v-if="listError" class="bc-error" role="alert">{{ listError }}</p>
    <p v-if="success" class="bc-success" role="status">{{ success }}</p>
    <p v-if="blocked" role="status">Working…</p>
    <form v-if="record" class="bc-editor" aria-labelledby="bc-record-title" @submit.prevent="saveRecord('save')">
      <h2 id="bc-record-title">{{ record.saved ? 'Edit' : 'Create' }} Business Case record</h2>
      <p><strong>{{ record.migrationRequestId }} · {{ record.projectName }}</strong> · Revision {{ record.revision }} · {{ record.status }}</p>
      <p class="bc-note">This is an inline database editor, not the presentation page. Only Business Case-owned narrative and financial inputs are edited here. Maintain Intake, Scope and Cost Rates in their source databases.</p>
      <p v-if="record.sourceChanged || record.reviewRequired" class="bc-warning">
        Source data has changed or needs review.
        <template v-if="!record.canEdit">Enter a revision reason, then select Open revision. Review Intake, Scope and cost rates, save / refresh sources, then have the requestor resubmit from the Business Case page.</template>
        <template v-else>Review sources, then save / refresh.</template>
        Existing narrative is retained.
      </p>
      <p v-if="!record.canEdit" class="bc-warning">Record locked or read-only. The server controls edit and revision permissions.</p>
      <BusinessCaseDetails :details="details" :disabled="blocked || !record.canEdit" />
      <h3>Financial inputs</h3>
      <BusinessCaseFinancialInputs :inputs="financialInputs" :disabled="blocked || !record.canEdit" />
      <BusinessCaseFinancials :financials="record.financials" :stale="dirty" />
      <BusinessCaseSavedSnapshot :snapshot="record.savedSnapshot" :history="record.financialHistory" />
      <p class="bc-note" aria-live="polite">{{ dirty ? 'Unsaved changes' : 'No pending changes' }}</p>
      <div class="bc-actions">
        <button type="submit" class="bc-primary" :disabled="blocked || !record.canEdit">Save record</button>
        <button type="button" :disabled="blocked || !record.canEdit" @click="saveRecord('refresh')">Save / refresh sources</button>
        <button type="button" :disabled="blocked" @click="closeEditor">Close editor</button>
      </div>
      <div v-if="!record.canEdit && ['submitted', 'approved', 'needs_review'].includes(record.status)">
        <label>Reason to open a revision<textarea v-model="revisionReason" :disabled="blocked" rows="2" /></label>
        <button type="button" :disabled="blocked || !revisionReason.trim()" @click="revise">Open revision</button>
      </div>
      <p v-if="record.legacyFile"><a :href="record.legacyFile.url" :download="record.legacyFile.name">Download historical file: {{ record.legacyFile.name }}</a></p>
    </form>
    <p v-if="!listing && !filteredRows.length">No saved Business Cases match this filter. Select a project to create a draft.</p>
    <div v-else class="bc-scroll">
      <table>
        <thead><tr><th>Request ID</th><th>Project</th><th>Status</th><th>Revision</th><th>Rationale</th><th>One-time cost (USD)</th><th>Adjustment (USD)</th><th>Updated by</th><th>Updated at</th><th>Maintain</th></tr></thead>
        <tbody><tr v-for="row in filteredRows" :key="row.id">
          <td>{{ row.migrationRequestId }}</td><td>{{ row.projectName }}</td><td>{{ row.status }}</td><td>{{ row.revision }}</td>
          <td class="bc-source-text">{{ row.details?.rationale || '—' }}</td><td>{{ row.financialInputs?.oneTimeCost || '—' }}</td><td>{{ row.financialInputs?.adjustment ?? '—' }}</td>
          <td>{{ row.updatedBy || '—' }}</td><td>{{ row.updatedAt ? new Date(row.updatedAt).toLocaleString() : '—' }}</td>
          <td><div class="bc-actions"><button type="button" :disabled="blocked" @click="openRecord(row.projectId)">Edit record</button>
            <button type="button" :disabled="blocked || !['draft', 'returned'].includes(row.status)" @click="deleteRecord(row)">Delete</button></div></td>
        </tr></tbody>
      </table>
    </div>
  </PageShell>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'
import BusinessCaseDetails from '../components/BusinessCaseDetails.vue'
import BusinessCaseFinancialInputs from '../components/BusinessCaseFinancialInputs.vue'
import BusinessCaseFinancials from '../components/BusinessCaseFinancials.vue'
import BusinessCaseSavedSnapshot from '../components/BusinessCaseSavedSnapshot.vue'
import { useBusinessCase } from '../composables/useBusinessCase.js'
import { useUnsavedChanges } from '../composables/useUnsavedChanges.js'
import '../styles/businessCase.css'

const { record, details, financialInputs, loading, pending, error, success, dirty: recordDirty, load, save } = useBusinessCase()
const rows = ref([])
const projects = ref([])
const query = ref('')
const selectedProject = ref('')
const listing = ref(false)
const deleting = ref(false)
const listError = ref('')
const revisionReason = ref('')
const dirty = computed(() => recordDirty.value || !!revisionReason.value.trim())
const blocked = computed(() => listing.value || deleting.value || loading.value || pending.value)
const { canLeave } = useUnsavedChanges(dirty, blocked)
const filteredRows = computed(() => rows.value.filter(row => [row.projectName, row.migrationRequestId, row.status].some(value =>
  String(value || '').toLowerCase().includes(query.value.trim().toLowerCase()))))

async function loadData() {
  listing.value = true
  listError.value = ''
  try {
    const [records, options] = await Promise.all([
      axios.get('/api/migration-dashboard/business-cases/'),
      axios.get('/api/migration-dashboard/projects/')
    ])
    rows.value = records.data.rows || []
    projects.value = options.data.rows || []
  } catch (failure) {
    listError.value = failure.response?.data?.error || failure.message
  } finally {
    listing.value = false
  }
}
async function openRecord(projectId) {
  if (!canLeave()) return
  if (await load(projectId)) {
    revisionReason.value = ''
    await nextTick()
    document.getElementById('bc-record-title')?.scrollIntoView({ block: 'start' })
  }
}
function closeEditor() {
  if (!canLeave()) return
  record.value = null
  revisionReason.value = ''
}
async function reload() {
  if (!canLeave()) return
  record.value = null
  revisionReason.value = ''
  await loadData()
}
async function saveRecord(action) {
  if (blocked.value || !record.value?.canEdit) return
  if (await save(action)) await loadData()
}
async function revise() {
  if (blocked.value || !revisionReason.value.trim()) return
  if (await save('revise', { reason: revisionReason.value.trim() })) {
    revisionReason.value = ''
    await loadData()
  }
}
async function deleteRecord(row) {
  if (!['draft', 'returned'].includes(row.status) || !canLeave()) return
  if (!window.confirm(`Delete the Business Case draft for ${row.migrationRequestId}? Original Intake and Scope data are not deleted.`)) return
  deleting.value = true
  listError.value = ''
  try {
    await axios.post(`/api/migration-dashboard/projects/${row.projectId}/business-case/delete/`, { revision: row.revision })
    if (record.value?.projectId === row.projectId) {
      record.value = null
      revisionReason.value = ''
    }
    await loadData()
    success.value = 'Business Case record deleted.'
  } catch (failure) {
    listError.value = failure.response?.data?.error || failure.message
    if (failure.response?.status === 409) listError.value += ' Reload the latest records before trying again.'
  } finally {
    deleting.value = false
  }
}
onMounted(loadData)
</script>
