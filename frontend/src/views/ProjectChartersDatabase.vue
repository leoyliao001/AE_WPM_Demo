<template>
  <PageShell title="Project Charters" subtitle="Maintain charter-owned draft data. Source artefacts remain read-only and are not duplicated in this table."
    back-to="/project-attributes" back-label="Back to Admin" full-width>
    <div class="charters-toolbar">
      <label>Filter records<input v-model="query" type="search" placeholder="Project, request ID, requestor..." /></label>
      <label>Create / open for project<select v-model="selectedProject"><option value="">Select a project</option>
        <option v-for="project in projects" :key="project.id" :value="project.id">{{ project.migrationRequestId }} · {{ project.projectName }}</option>
      </select></label>
      <button type="button" :disabled="!selectedProject || busy || loading" @click="editProject(selectedProject)">Create / edit record</button>
      <button type="button" :disabled="loading || busy || !!editor" @click="loadData">Reload</button>
    </div>
    <p v-if="error" role="alert" class="error">{{ error }}</p>
    <p v-if="success" role="status">{{ success }}</p>
    <form v-if="editor" class="charter-editor" aria-labelledby="record-editor-title" @submit.prevent="saveRecord">
      <h2 id="record-editor-title">{{ editor.saved ? 'Edit' : 'Create' }} Project Charter record</h2>
      <p><strong>{{ editor.migrationRequestId }} · {{ editor.projectName }}</strong> · Revision {{ editor.revision }}</p>
      <p>Only charter-owned database fields are maintained here. Project, leadership, scope, FTE and other source data must be updated in their source tables.</p>
      <p v-if="editor.sourceUpdated" class="source-warning">Source data has changed since this record was saved. The existing vision is preserved; review it before saving.</p>
      <fieldset :disabled="busy">
        <label>Vision<textarea v-model="vision" rows="4" maxlength="10000" /></label>
        <div class="phase-notes">
          <label v-for="phase in editor.sources.deliverables" :key="phase.id">{{ phase.phase }} note
            <textarea v-model="notes[phase.id]" rows="2" maxlength="2000" />
          </label>
        </div>
        <h3>Additional success criteria</h3>
        <p>Saved criteria are add-only and cannot be changed or removed.</p>
        <ul><li v-for="(criterion, index) in criteria" :key="index">{{ criterion }}</li></ul>
        <label>New success criterion<input v-model="newCriterion" maxlength="1000" @keydown.enter.prevent="addCriterion" /></label>
        <button type="button" @click="addCriterion">Add criterion</button>
        <div class="editor-actions">
          <button type="submit">{{ busy ? 'Saving...' : 'Save record' }}</button>
          <button type="button" @click="closeEditor">Cancel</button>
        </div>
      </fieldset>
    </form>
    <p v-if="loading">Loading Project Charters...</p>
    <p v-else-if="!filteredRows.length">No saved charters match this filter. Select a project and use Create / edit record to add one.</p>
    <div v-else class="charters-scroll">
      <table>
        <thead><tr><th>Migration Request ID</th><th>Project</th><th>Requestor</th><th>Vision</th><th>Deliverable notes</th><th>Additional success criteria</th><th>Revision</th><th>Updated by</th><th>Last updated</th><th>Maintain</th></tr></thead>
        <tbody><tr v-for="row in filteredRows" :key="row.id">
          <td>{{ row.migrationRequestId }}</td><td>{{ row.projectName }}</td><td>{{ row.requestor }}</td><td class="text-cell">{{ row.vision }}</td>
          <td class="text-cell"><div v-for="(note, phase) in row.deliverableNotes" :key="phase"><strong>{{ phase }}:</strong> {{ note }}</div></td>
          <td class="text-cell"><ul><li v-for="criterion in row.extraSuccessCriteria" :key="criterion">{{ criterion }}</li></ul></td>
          <td>v0.{{ row.revision }}</td><td>{{ row.updatedBy }}</td><td>{{ new Date(row.updatedAt).toLocaleString() }}</td>
          <td><button type="button" :disabled="busy || loading" @click="editProject(row.projectId)">Edit record</button><button type="button" :disabled="busy || !!editor" @click="deleteRow(row)">Delete</button></td>
        </tr></tbody>
      </table>
    </div>
  </PageShell>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'

const rows = ref([])
const projects = ref([])
const selectedProject = ref('')
const query = ref('')
const loading = ref(false)
const busy = ref(false)
const error = ref('')
const success = ref('')
const editor = ref(null)
const vision = ref('')
const notes = ref({})
const criteria = ref([])
const newCriterion = ref('')
const savedSnapshot = ref('')
const snapshot = () => JSON.stringify([vision.value, notes.value, criteria.value])
const dirty = computed(() => !!editor.value && (snapshot() !== savedSnapshot.value || !!newCriterion.value.trim()))
const filteredRows = computed(() => {
  const term = query.value.trim().toLowerCase()
  return rows.value.filter(row => !term || [row.migrationRequestId, row.projectName, row.requestor, row.vision].some(value => value.toLowerCase().includes(term)))
})
function canDiscard() {
  return !busy.value && (!dirty.value || window.confirm('Discard unsaved record changes?'))
}

function closeEditor() {
  if (!canDiscard()) return
  editor.value = null
  error.value = ''
}

async function editProject(projectId) {
  if (!canDiscard()) return
  busy.value = true
  error.value = ''
  success.value = ''
  try {
    const { data } = await axios.get(`/api/migration-dashboard/projects/${projectId}/project-charter/`)
    editor.value = data
    vision.value = data.vision
    notes.value = { ...data.deliverableNotes }
    criteria.value = [...data.extraSuccessCriteria]
    newCriterion.value = ''
    savedSnapshot.value = snapshot()
    await nextTick()
    document.getElementById('record-editor-title')?.scrollIntoView({ block: 'start' })
  } catch (failure) {
    error.value = failure.response?.data?.error || failure.message
  } finally {
    busy.value = false
  }
}

function addCriterion() {
  const text = newCriterion.value.trim()
  if (!text || criteria.value.includes(text) || criteria.value.length >= 50) {
    error.value = 'Enter a unique, non-empty criterion. At most 50 additional criteria are allowed.'
    return
  }
  criteria.value.push(text)
  newCriterion.value = ''
  error.value = ''
}

async function saveRecord() {
  if (newCriterion.value.trim()) {
    error.value = 'Add the pending success criterion before saving.'
    return
  }
  busy.value = true
  error.value = ''
  success.value = ''
  try {
    await axios.post(`/api/migration-dashboard/projects/${editor.value.projectId}/project-charter/save/`, {
      revision: editor.value.revision, vision: vision.value,
      deliverableNotes: notes.value, extraSuccessCriteria: criteria.value
    })
    editor.value = null
    await loadData()
    success.value = 'Project Charter record saved to the database.'
  } catch (failure) {
    error.value = failure.response?.data?.error || failure.message
  } finally {
    busy.value = false
  }
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const [charters, options] = await Promise.all([
      axios.get('/api/migration-dashboard/project-charters/'),
      axios.get('/api/migration-dashboard/projects/')
    ])
    rows.value = charters.data.rows
    projects.value = options.data.rows
  } catch (failure) {
    error.value = failure.response?.data?.error || failure.message
  } finally {
    loading.value = false
  }
}

async function deleteRow(row) {
  if (!window.confirm(`Delete the saved charter for ${row.migrationRequestId}? This deletes its vision, notes, additional criteria and draft history, but does not delete the project or any source artefact.`)) return
  busy.value = true
  error.value = ''
  success.value = ''
  try {
    await axios.post(`/api/migration-dashboard/projects/${row.projectId}/project-charter/delete/`, { revision: row.revision })
    rows.value = rows.value.filter(item => item.id !== row.id)
    success.value = 'Saved charter deleted. Project and source artefacts are unchanged.'
  } catch (failure) {
    error.value = failure.response?.data?.error || failure.message
  } finally {
    busy.value = false
  }
}
function beforeUnload(event) {
  if (dirty.value || busy.value) {
    event.preventDefault()
    event.returnValue = ''
  }
}
onBeforeRouteLeave(canDiscard)
onMounted(() => {
  window.addEventListener('beforeunload', beforeUnload)
  loadData()
})
onBeforeUnmount(() => window.removeEventListener('beforeunload', beforeUnload))
</script>

<style scoped>
.charters-toolbar { align-items: end; display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 18px; }
label { display: flex; flex-direction: column; font-size: 12px; gap: 5px; }
input, select, button, textarea { background: #fff; border: 1px solid #cbd8e4; border-radius: 4px; font: inherit; padding: 8px; }
.charter-editor { background: #f5f9fc; border: 1px solid #cbd8e4; border-radius: 6px; margin-bottom: 20px; padding: 18px; }
.charter-editor p { font-size: 13px; line-height: 1.6; }
.charter-editor fieldset { border: 0; margin: 0; min-width: 0; padding: 0; }
.charter-editor label { margin-bottom: 12px; }
.charter-editor textarea { box-sizing: border-box; resize: vertical; width: 100%; }
.phase-notes { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(min(100%, 260px), 1fr)); margin-top: 16px; }
.editor-actions { display: flex; gap: 10px; margin-top: 20px; }
.source-warning { color: #885500; }
button { color: #006fa8; cursor: pointer; }
button:disabled { cursor: not-allowed; opacity: .6; }
.charters-scroll { overflow: auto; }
table { border-collapse: collapse; font-size: 12px; width: 100%; }
th { background: #103451; color: #fff; text-align: left; }
td, th { border: 1px solid #dce5ed; padding: 10px; vertical-align: top; }
.text-cell { min-width: 220px; white-space: pre-wrap; }
td:last-child { min-width: 110px; }
td button { display: block; margin-top: 8px; }
.error { color: #be3030; }
</style>
