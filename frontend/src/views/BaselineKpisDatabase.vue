<template>
  <PageShell
    title="Baseline & KPIs Database"
    subtitle="View and maintain each project's complete Baseline & KPI state."
    back-to="/project-attributes"
    back-label="Back to Admin"
    full-width
  >
    <div class="kpi-db-toolbar">
      <p>Editing the JSON updates the Baseline & KPI record for the selected migration project.</p>
      <mc-button appearance="primary" fit="medium" label="Add record" :disabled="loading || busy || editorOpen || !projects.length" @click="startCreate" />
      <mc-button appearance="neutral" variant="outlined" fit="medium" label="Reload" :disabled="loading || busy || editorOpen" @click="loadData" />
    </div>

    <mc-notification
      v-if="error"
      class="kpi-db-message"
      appearance="error"
      fit="medium"
      heading="Unable to maintain Baseline & KPIs"
      :body="error"
      role="alert"
    />
    <mc-notification
      v-if="success"
      class="kpi-db-message"
      appearance="success"
      fit="medium"
      :body="success"
      role="status"
    />

    <form v-if="editorOpen" class="kpi-editor" @submit.prevent="saveRecord">
      <div class="editor-heading">
        <div>
          <h2>{{ form.id === null ? 'Add' : 'Edit' }} Baseline & KPI record</h2>
          <p>Enter a valid JSON object. The stored state is replaced when you save.</p>
        </div>
        <mc-tag v-if="form.id !== null" appearance="info" fit="small" :label="`REVISION ${form.revision}`" />
      </div>
      <fieldset :disabled="busy">
        <label class="project-field">
          Migration project
          <select v-model="form.projectId" :disabled="form.id !== null" required>
            <option value="">Select a project</option>
            <option v-for="project in availableProjects" :key="project.id" :value="String(project.id)">
              {{ project.migrationRequestId }} · {{ project.projectName }}
            </option>
          </select>
        </label>
        <label class="json-field">
          Complete state JSON
          <textarea v-model="form.stateJson" spellcheck="false" rows="20" required />
        </label>
        <div class="editor-actions">
          <mc-button type="submit" appearance="primary" fit="medium" :label="busy ? 'Saving…' : 'Save record'" :loading="busy" />
          <mc-button type="button" appearance="neutral" variant="outlined" fit="medium" label="Cancel" :disabled="busy" @click="closeEditor" />
        </div>
      </fieldset>
    </form>

    <div v-if="loading" class="table-state" role="status">
      <mc-loading-indicator size="medium" />
      <span>Loading Baseline & KPI records…</span>
    </div>
    <p v-else-if="!rows.length" class="table-state">
      No Baseline & KPI records have been saved.
    </p>
    <div v-else class="kpi-db-scroll">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Migration request</th>
            <th>Project</th>
            <th>Revision</th>
            <th>Updated by</th>
            <th>Updated</th>
            <th>Maintain</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.id">
            <td>{{ row.id }}</td>
            <td>{{ row.migrationRequestId }}</td>
            <td>{{ row.projectName }}</td>
            <td>{{ row.revision }}</td>
            <td>{{ row.updatedBy }}</td>
            <td>{{ formatDate(row.updatedAt) }}</td>
            <td class="row-actions">
              <mc-button appearance="neutral" variant="outlined" fit="small" label="Edit JSON" :disabled="busy || editorOpen" @click="editRecord(row)" />
              <mc-button appearance="error" variant="outlined" fit="small" label="Delete" :disabled="busy || editorOpen" @click="deleteRecord(row)" />
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
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-loading-indicator'
import '@maersk-global/mds-components-core/mc-notification'
import '@maersk-global/mds-components-core/mc-tag'

const endpoint = '/api/baseline-kpis-admin/'
const rows = ref([])
const projects = ref([])
const loading = ref(false)
const busy = ref(false)
const editorOpen = ref(false)
const error = ref('')
const success = ref('')
const savedSnapshot = ref('')

const emptyForm = () => ({ id: null, projectId: '', revision: 0, stateJson: '{\n  \n}' })
const form = reactive(emptyForm())
const currentSnapshot = () => JSON.stringify(form)
const dirty = computed(() => editorOpen.value && currentSnapshot() !== savedSnapshot.value)
const availableProjects = computed(() => projects.value.filter((project) =>
  !rows.value.some((row) => row.projectId === project.id && row.id !== form.id)
))

function resetForm() {
  Object.assign(form, emptyForm())
  savedSnapshot.value = ''
  editorOpen.value = false
}

function canDiscard() {
  return !dirty.value || window.confirm('Discard unsaved Baseline & KPI changes?')
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
    id: row.id,
    projectId: String(row.projectId),
    revision: row.revision,
    stateJson: JSON.stringify(row.state, null, 2)
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
      throw new Error('The server returned an invalid Baseline & KPI database response.')
    }
    rows.value = data.rows
    projects.value = data.projects
    return true
  } catch (failure) {
    error.value = failure.response?.data?.error || failure.message || 'Unable to load Baseline & KPI records.'
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
  let state
  try {
    state = JSON.parse(form.stateJson)
  } catch (failure) {
    error.value = `Invalid JSON: ${failure.message}`
    return
  }
  if (!state || Array.isArray(state) || typeof state !== 'object') {
    error.value = 'The state value must be a JSON object.'
    return
  }

  busy.value = true
  error.value = ''
  success.value = ''
  const isEditing = form.id !== null
  const payload = { state, revision: form.revision }
  try {
    if (isEditing) await axios.put(`${endpoint}${form.id}/`, payload)
    else await axios.post(endpoint, { ...payload, projectId: Number(form.projectId) })
    success.value = isEditing ? 'Baseline & KPI record updated.' : 'Baseline & KPI record created.'
    resetForm()
    await loadData()
  } catch (failure) {
    error.value = failure.response?.data?.error || failure.message || 'Unable to save the Baseline & KPI record.'
  } finally {
    busy.value = false
  }
}

async function deleteRecord(row) {
  if (busy.value || !window.confirm(`Permanently delete the Baseline & KPI record for "${row.projectName}"?`)) return
  busy.value = true
  error.value = ''
  success.value = ''
  try {
    await axios.delete(`${endpoint}${row.id}/`)
    success.value = 'Baseline & KPI record deleted.'
    await loadData()
  } catch (failure) {
    error.value = failure.response?.data?.error || failure.message || 'Unable to delete the Baseline & KPI record.'
  } finally {
    busy.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.kpi-db-toolbar {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-end;
  margin-bottom: 14px;
}

.kpi-db-toolbar p {
  color: #526977;
  flex: 1 1 360px;
  font-size: 13px;
  margin: 0;
}

.kpi-db-message {
  margin: 12px 0;
}

.kpi-editor {
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

.kpi-editor fieldset {
  border: 0;
  margin: 0;
  padding: 0;
}

.project-field,
.json-field {
  color: #183746;
  display: grid;
  font-size: 12px;
  font-weight: 700;
  gap: 6px;
}

.project-field {
  max-width: 700px;
}

.project-field select,
.json-field textarea {
  border: 1px solid #bdcdd3;
  border-radius: 6px;
  color: #183746;
  font: inherit;
  font-size: 13px;
  padding: 9px 10px;
  width: 100%;
}

.json-field {
  margin-top: 16px;
}

.json-field textarea {
  box-sizing: border-box;
  font-family: Consolas, 'Courier New', monospace;
  font-weight: 400;
  line-height: 1.5;
  min-height: 360px;
  resize: vertical;
  tab-size: 2;
}

.editor-actions,
.row-actions {
  display: flex;
  gap: 8px;
}

.editor-actions {
  justify-content: flex-end;
  margin-top: 16px;
}

.table-state {
  align-items: center;
  color: #526977;
  display: flex;
  gap: 10px;
  justify-content: center;
  min-height: 120px;
}

.kpi-db-scroll {
  border: 1px solid #dbe6ea;
  border-radius: 10px;
  overflow: auto;
  width: 100%;
}

table {
  border-collapse: collapse;
  min-width: 850px;
  width: 100%;
}

th,
td {
  border-bottom: 1px solid #e5eef1;
  padding: 10px 12px;
  text-align: left;
  vertical-align: middle;
}

th {
  background: #f4f8fa;
  color: #183746;
  font-size: 12px;
  white-space: nowrap;
}

td {
  color: #304b58;
  font-size: 13px;
}

tbody tr:last-child td {
  border-bottom: 0;
}

@media (max-width: 700px) {
  .editor-heading {
    gap: 12px;
  }

  .editor-actions {
    justify-content: flex-start;
  }
}
</style>
