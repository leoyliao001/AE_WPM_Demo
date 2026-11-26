<template>
  <PageShell
    title="BAU Controls Database"
    subtitle="Review and maintain project BAU Control Agreements."
    back-to="/project-attributes"
    back-label="Back to Admin"
    full-width
  >
    <div class="bau-db-toolbar">
      <label class="filter-field">
        Filter records
        <input v-model="query" type="search" placeholder="Project, request ID, Area, owner..." />
      </label>
      <mc-button appearance="primary" fit="medium" label="Add agreement" :disabled="loading || busy" @click="startCreate" />
      <mc-button appearance="neutral" variant="outlined" fit="medium" label="Reload" :disabled="loading || busy || editorOpen" @click="loadData" />
    </div>

    <mc-notification
      v-if="error"
      class="bau-db-message"
      appearance="error"
      fit="medium"
      heading="Unable to maintain BAU Controls"
      :body="error"
      role="alert"
    />
    <mc-notification
      v-if="success"
      class="bau-db-message"
      appearance="success"
      fit="medium"
      :body="success"
      role="status"
    />

    <form v-if="editorOpen" class="bau-editor" @submit.prevent="saveRecord">
      <div class="editor-heading">
        <div>
          <h2>{{ form.id === null ? 'Add' : 'Edit' }} BAU Control Agreement</h2>
          <p>One agreement is maintained for each migration project.</p>
        </div>
        <mc-tag :appearance="form.status === 'confirmed' ? 'success' : 'info'" fit="small" :label="form.status.toUpperCase()" />
      </div>
      <fieldset :disabled="busy">
        <div class="editor-meta">
          <label>
            Migration project
            <select v-model="form.projectId" required>
              <option value="">Select a project</option>
              <option v-for="project in availableProjects" :key="project.id" :value="String(project.id)">
                {{ project.migrationRequestId }} · {{ project.projectName }}
              </option>
            </select>
          </label>
          <label>
            Agreement status
            <select v-model="form.status">
              <option value="draft">Draft</option>
              <option value="confirmed">Confirmed</option>
            </select>
          </label>
          <label>Migration<input v-model="form.migrationName" maxlength="255" /></label>
          <label>Product<input v-model="form.product" maxlength="255" /></label>
          <label>Area<input v-model="form.area" maxlength="255" /></label>
          <label>BAU effective from<input v-model="form.effectiveFrom" type="date" /></label>
        </div>

        <section class="editor-section">
          <h3>1 · Ownership</h3>
          <div class="editor-grid editor-grid--two">
            <label>Area owner<input v-model="form.areaOwner" maxlength="255" /></label>
            <label>GSC owner<input v-model="form.gscOwner" maxlength="255" /></label>
            <label class="span-all">Scope covered<textarea v-model="form.scopeCovered" maxlength="5000" rows="3" /></label>
          </div>
        </section>

        <section class="editor-section">
          <h3>2 · Performance control</h3>
          <div class="editor-grid editor-grid--four">
            <label>Performance / KPI reference<input v-model="form.kpiReference" maxlength="255" /></label>
            <label>Reporting source<input v-model="form.reportingSource" maxlength="255" /></label>
            <label>
              Review cadence
              <select v-model="form.reviewCadence">
                <option v-for="option in reviewCadenceOptions" :key="option" :value="option">{{ option }}</option>
              </select>
            </label>
            <label>Performance owner<input v-model="form.performanceOwner" maxlength="255" /></label>
          </div>
        </section>

        <section class="editor-section">
          <h3>3 · Ways of working</h3>
          <div class="editor-grid editor-grid--two">
            <label>BAU forum / channel<input v-model="form.bauForumChannel" maxlength="255" /></label>
            <label>
              Working cadence
              <select v-model="form.workingCadence">
                <option v-for="option in workingCadenceOptions" :key="option" :value="option">{{ option }}</option>
              </select>
            </label>
            <label>Area operational contact<input v-model="form.areaOperationalContact" maxlength="255" /></label>
            <label>GSC operational contact<input v-model="form.gscOperationalContact" maxlength="255" /></label>
          </div>
        </section>

        <section class="editor-section">
          <h3>4 · Escalation</h3>
          <div class="editor-grid editor-grid--two">
            <label>Normal operational issue route<input v-model="form.normalIssueRoute" maxlength="255" /></label>
            <label>Leadership intervention route<input v-model="form.leadershipRoute" maxlength="255" /></label>
            <label class="span-all">Specific escalation note<textarea v-model="form.escalationNote" maxlength="5000" rows="2" /></label>
          </div>
        </section>

        <section class="editor-section">
          <h3>5 · BAU acceptance</h3>
          <div class="editor-grid editor-grid--two">
            <div class="acceptance-edit">
              <label class="accept-checkbox"><input v-model="form.areaAccepted" type="checkbox" /> Area accepted</label>
              <div class="editor-grid editor-grid--two">
                <label>Name / role<input v-model="form.areaNameRole" maxlength="255" /></label>
                <label>Date<input v-model="form.areaAcceptanceDate" type="date" /></label>
              </div>
            </div>
            <div class="acceptance-edit">
              <label class="accept-checkbox"><input v-model="form.gscAccepted" type="checkbox" /> GSC accepted</label>
              <div class="editor-grid editor-grid--two">
                <label>Name / role<input v-model="form.gscNameRole" maxlength="255" /></label>
                <label>Date<input v-model="form.gscAcceptanceDate" type="date" /></label>
              </div>
            </div>
          </div>
        </section>

        <div class="editor-actions">
          <mc-button type="submit" appearance="primary" fit="medium" :label="busy ? 'Saving…' : 'Save agreement'" :loading="busy" />
          <mc-button type="button" appearance="neutral" variant="outlined" fit="medium" label="Cancel" :disabled="busy" @click="closeEditor" />
        </div>
      </fieldset>
    </form>

    <div v-if="loading" class="table-state" role="status">
      <mc-loading-indicator size="medium" />
      <span>Loading BAU Control Agreements…</span>
    </div>
    <p v-else-if="!filteredRows.length" class="table-state">
      {{ rows.length ? 'No agreements match this filter.' : 'No BAU Control Agreements have been saved.' }}
    </p>
    <div v-else class="bau-db-scroll">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Migration request</th>
            <th>Project</th>
            <th>Product</th>
            <th>Area</th>
            <th>Effective from</th>
            <th>Area owner</th>
            <th>GSC owner</th>
            <th>Review cadence</th>
            <th>Acceptance</th>
            <th>Status</th>
            <th>Updated by</th>
            <th>Updated</th>
            <th>Maintain</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in filteredRows" :key="row.id">
            <td>{{ row.id }}</td>
            <td>{{ row.migrationRequestId }}</td>
            <td>{{ row.projectName }}</td>
            <td>{{ row.product }}</td>
            <td>{{ row.area }}</td>
            <td>{{ row.effectiveFrom }}</td>
            <td>{{ row.areaOwner }}</td>
            <td>{{ row.gscOwner }}</td>
            <td>{{ row.reviewCadence }}</td>
            <td>{{ row.areaAccepted ? 'Area ✓' : 'Area —' }} · {{ row.gscAccepted ? 'GSC ✓' : 'GSC —' }}</td>
            <td><mc-tag :appearance="row.status === 'confirmed' ? 'success' : 'info'" fit="small" :label="row.status" /></td>
            <td>{{ row.updatedBy }}</td>
            <td>{{ formatDate(row.updatedAt) }}</td>
            <td class="row-actions">
              <mc-button appearance="neutral" variant="outlined" fit="small" label="Edit" :disabled="busy" @click="editRecord(row)" />
              <mc-button appearance="error" variant="outlined" fit="small" label="Delete" :disabled="busy" @click="deleteRecord(row)" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </PageShell>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'
import {
  BAU_REVIEW_CADENCE_OPTIONS,
  BAU_WORKING_CADENCE_OPTIONS
} from '../utils/bauControlsOptions.js'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-loading-indicator'
import '@maersk-global/mds-components-core/mc-notification'
import '@maersk-global/mds-components-core/mc-tag'

const endpoint = '/api/migration-dashboard/bau-controls/'
const rows = ref([])
const projects = ref([])
const query = ref('')
const loading = ref(false)
const busy = ref(false)
const editorOpen = ref(false)
const error = ref('')
const success = ref('')
const savedSnapshot = ref('')
const reviewCadenceOptions = BAU_REVIEW_CADENCE_OPTIONS
const workingCadenceOptions = BAU_WORKING_CADENCE_OPTIONS

const emptyForm = () => ({
  id: null,
  projectId: '',
  status: 'draft',
  migrationName: '',
  product: '',
  area: '',
  effectiveFrom: '',
  areaOwner: '',
  gscOwner: '',
  scopeCovered: '',
  kpiReference: '',
  reportingSource: '',
  reviewCadence: 'Monthly',
  performanceOwner: '',
  bauForumChannel: '',
  workingCadence: 'Monthly',
  areaOperationalContact: '',
  gscOperationalContact: '',
  normalIssueRoute: '',
  leadershipRoute: '',
  escalationNote: '',
  areaAccepted: false,
  areaNameRole: '',
  areaAcceptanceDate: '',
  gscAccepted: false,
  gscNameRole: '',
  gscAcceptanceDate: ''
})

const form = reactive(emptyForm())
const currentSnapshot = () => JSON.stringify(form)
const dirty = computed(() => editorOpen.value && currentSnapshot() !== savedSnapshot.value)
const availableProjects = computed(() => projects.value.filter((project) =>
  !rows.value.some((row) => row.projectId === project.id && row.id !== form.id)
))
const filteredRows = computed(() => {
  const term = query.value.trim().toLowerCase()
  if (!term) return rows.value
  return rows.value.filter((row) =>
    [
      row.migrationRequestId,
      row.projectName,
      row.requestor,
      row.product,
      row.area,
      row.areaOwner,
      row.gscOwner,
      row.reviewCadence,
      row.status
    ].some((value) => String(value || '').toLowerCase().includes(term))
  )
})

function canDiscard() {
  return !dirty.value || window.confirm('Discard unsaved BAU agreement changes?')
}

function resetForm() {
  Object.assign(form, emptyForm())
  savedSnapshot.value = ''
  editorOpen.value = false
}

function startCreate() {
  if (!canDiscard()) return
  error.value = ''
  success.value = ''
  Object.assign(form, emptyForm())
  savedSnapshot.value = currentSnapshot()
  editorOpen.value = true
}

function editRecord(row) {
  if (!canDiscard()) return
  error.value = ''
  success.value = ''
  Object.assign(form, {
    ...emptyForm(),
    ...row,
    projectId: String(row.projectId),
    status: row.status || 'draft'
  })
  savedSnapshot.value = currentSnapshot()
  editorOpen.value = true
}

function closeEditor() {
  if (!canDiscard()) return
  resetForm()
  error.value = ''
}

function formatDate(value) {
  if (!value) return ''
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString()
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await axios.get(endpoint)
    if (!Array.isArray(data?.rows) || !Array.isArray(data?.projects)) {
      throw new Error('The server returned an invalid BAU Controls database response.')
    }
    rows.value = data.rows
    projects.value = data.projects
    return true
  } catch (failure) {
    error.value = failure.response?.data?.error || failure.message || 'Unable to load BAU Control Agreements.'
    return false
  } finally {
    loading.value = false
  }
}

async function saveRecord() {
  if (busy.value) return
  if (!form.projectId) {
    error.value = 'Select a migration project.'
    return
  }
  if (form.status === 'confirmed' && (!form.areaAccepted || !form.gscAccepted)) {
    error.value = 'Area and GSC must both accept before the agreement can be confirmed.'
    return
  }
  busy.value = true
  error.value = ''
  success.value = ''
  const isEditing = form.id !== null
  const payload = {
    ...form,
    projectId: Number(form.projectId),
    action: form.status === 'confirmed' ? 'confirm' : 'save'
  }
  try {
    if (isEditing) await axios.put(`${endpoint}${form.id}/`, payload)
    else await axios.post(endpoint, payload)
    success.value = isEditing ? 'BAU Control Agreement updated.' : 'BAU Control Agreement created.'
    resetForm()
    await loadData()
  } catch (failure) {
    error.value = failure.response?.data?.error || failure.message || 'Unable to save the BAU Control Agreement.'
  } finally {
    busy.value = false
  }
}

async function deleteRecord(row) {
  if (busy.value || !window.confirm(`Delete the BAU Control Agreement for "${row.projectName}"?`)) return
  busy.value = true
  error.value = ''
  success.value = ''
  try {
    await axios.delete(`${endpoint}${row.id}/`)
    rows.value = rows.value.filter((item) => item.id !== row.id)
    success.value = 'BAU Control Agreement deleted.'
  } catch (failure) {
    error.value = failure.response?.data?.error || failure.message || 'Unable to delete the BAU Control Agreement.'
  } finally {
    busy.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.bau-db-toolbar {
  align-items: flex-end;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 14px;
}

.filter-field {
  color: #183746;
  display: grid;
  flex: 1 1 320px;
  font-size: 13px;
  font-weight: 700;
  gap: 5px;
}

.filter-field input,
.bau-editor input,
.bau-editor select,
.bau-editor textarea {
  border: 1px solid #bdcdd3;
  border-radius: 6px;
  color: #183746;
  font: inherit;
  font-size: 13px;
  padding: 9px 10px;
  width: 100%;
}

.bau-editor {
  background: #fff;
  border: 1px solid #dbe6ea;
  border-radius: 12px;
  margin: 18px 0;
  padding: 20px;
}

.editor-heading {
  align-items: flex-start;
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.editor-heading h2 {
  color: #00243d;
  margin: 0 0 5px;
}

.editor-heading p {
  color: #667d88;
  font-size: 13px;
  margin: 0;
}

.editor-meta,
.editor-grid {
  display: grid;
  gap: 12px;
}

.editor-meta {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.editor-grid--two {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.editor-grid--four {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.bau-editor label {
  color: #183746;
  display: grid;
  font-size: 12px;
  font-weight: 700;
  gap: 5px;
}

.editor-section {
  border-top: 1px solid #e5eef1;
  margin-top: 18px;
  padding-top: 16px;
}

.editor-section h3 {
  color: #00243d;
  font-size: 15px;
  margin: 0 0 12px;
}

.span-all {
  grid-column: 1 / -1;
}

.accept-checkbox {
  align-items: center;
  display: flex !important;
  gap: 8px !important;
  margin-bottom: 12px;
}

.accept-checkbox input {
  width: auto;
}

.editor-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 18px;
}

.bau-db-message {
  margin: 12px 0;
}

.bau-db-scroll {
  border: 1px solid #dbe6ea;
  border-radius: 10px;
  overflow: auto;
  width: 100%;
}

table {
  border-collapse: collapse;
  min-width: 1280px;
  width: 100%;
}

th,
td {
  border-bottom: 1px solid #e6edef;
  padding: 10px 12px;
  text-align: left;
  vertical-align: middle;
}

th {
  background: #f4f8fa;
  color: #325665;
  font-size: 11px;
  position: sticky;
  text-transform: uppercase;
  top: 0;
  z-index: 1;
}

td {
  color: #183746;
  font-size: 12px;
}

.row-actions {
  display: flex;
  gap: 6px;
}

.table-state {
  align-items: center;
  color: #667d88;
  display: flex;
  gap: 12px;
  min-height: 180px;
}

@media (max-width: 900px) {
  .editor-meta,
  .editor-grid--four {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 620px) {
  .editor-meta,
  .editor-grid--two,
  .editor-grid--four {
    grid-template-columns: 1fr;
  }

  .editor-heading {
    flex-direction: column;
    gap: 10px;
  }
}
</style>
