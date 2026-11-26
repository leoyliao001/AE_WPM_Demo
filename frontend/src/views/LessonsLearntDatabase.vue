<template>
  <PageShell
    title="Lessons Learnt Database"
    subtitle="Browse and maintain Lessons Learnt records linked to migration projects."
    back-to="/project-attributes"
    back-label="Back to Admin"
    full-width
  >
    <div class="lessons-db-toolbar">
      <label>
        Filter records
        <input v-model="query" type="search" placeholder="Project, request ID, lesson text..." />
      </label>
      <button type="button" :disabled="loading || busy" @click="startCreate">Add lesson</button>
      <button type="button" :disabled="loading || busy || editorOpen" @click="loadData">Reload</button>
    </div>

    <p class="maintenance-note">
      Admins can add multiple records for a project. The project Lessons Learnt page shows the most recently saved record.
    </p>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <p v-if="success" class="success" role="status">{{ success }}</p>

    <form v-if="editorOpen" class="lesson-editor" @submit.prevent="saveRecord">
      <h2>{{ form.id === null ? 'Add' : 'Edit' }} lesson record</h2>
      <fieldset :disabled="busy">
        <label>
          Migration project
          <select v-model="form.projectId" required>
            <option value="">Select a project</option>
            <option v-for="project in projects" :key="project.id" :value="project.id">
              {{ project.migrationRequestId }} · {{ project.projectName }}
            </option>
          </select>
        </label>
        <div class="lesson-editor__fields">
          <label>
            What happened?
            <textarea v-model="form.happened" rows="3" maxlength="5000" required />
          </label>
          <label>
            What did we learn?
            <textarea v-model="form.learned" rows="3" maxlength="5000" required />
          </label>
          <label>
            What should we do differently next time?
            <textarea v-model="form.nextTime" rows="3" maxlength="5000" required />
          </label>
          <label>
            Type
            <select v-model="form.type" required>
              <option v-for="option in LESSON_TYPE_OPTIONS" :key="option" :value="option">{{ option }}</option>
            </select>
          </label>
          <label>
            Phase
            <select v-model="form.phase" required>
              <option v-for="option in LESSON_PHASE_OPTIONS" :key="option" :value="option">{{ option }}</option>
            </select>
          </label>
          <label>
            Related artefact
            <select v-model="form.relatedArtefact" required>
              <option v-for="option in LESSON_ARTEFACT_OPTIONS" :key="option" :value="option">{{ option }}</option>
            </select>
          </label>
          <label>
            Relevant for
            <select v-model="form.relevantFor" required>
              <option v-for="option in LESSON_RELEVANCE_OPTIONS" :key="option" :value="option">{{ option }}</option>
            </select>
          </label>
        </div>
        <div class="lesson-editor__actions">
          <button type="submit">{{ busy ? 'Saving…' : 'Save record' }}</button>
          <button type="button" :disabled="busy" @click="closeEditor">Cancel</button>
        </div>
      </fieldset>
    </form>

    <p v-if="loading">Loading Lessons Learnt records…</p>
    <p v-else-if="!filteredRows.length">
      {{ rows.length ? 'No lessons match this filter.' : 'No Lessons Learnt records have been saved.' }}
    </p>
    <div v-else class="lessons-db-scroll">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Migration request</th>
            <th>Project</th>
            <th>Requestor</th>
            <th>Type</th>
            <th>Phase</th>
            <th>Related artefact</th>
            <th>Relevant for</th>
            <th>What happened?</th>
            <th>What did we learn?</th>
            <th>Next time</th>
            <th>Created by</th>
            <th>Created</th>
            <th>Updated</th>
            <th>Maintain</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in filteredRows" :key="row.id">
            <td>{{ row.id }}</td>
            <td>{{ row.migrationRequestId }}</td>
            <td>{{ row.projectName }}</td>
            <td>{{ row.requestor }}</td>
            <td>{{ row.type }}</td>
            <td>{{ row.phase }}</td>
            <td>{{ row.relatedArtefact }}</td>
            <td>{{ row.relevantFor }}</td>
            <td class="text-cell">{{ row.happened }}</td>
            <td class="text-cell">{{ row.learned }}</td>
            <td class="text-cell">{{ row.nextTime }}</td>
            <td>{{ row.createdBy }}</td>
            <td>{{ formatDate(row.createdAt) }}</td>
            <td>{{ formatDate(row.updatedAt) }}</td>
            <td class="actions-cell">
              <button type="button" :disabled="busy" @click="editRecord(row)">Edit</button>
              <button type="button" :disabled="busy" @click="deleteRecord(row)">Delete</button>
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
  LESSON_ARTEFACT_OPTIONS,
  LESSON_PHASE_OPTIONS,
  LESSON_RELEVANCE_OPTIONS,
  LESSON_TYPE_OPTIONS
} from '../utils/lessonsLearntOptions.js'

const endpoint = '/api/migration-dashboard/lessons-learnt/'
const rows = ref([])
const projects = ref([])
const query = ref('')
const loading = ref(false)
const busy = ref(false)
const editorOpen = ref(false)
const error = ref('')
const success = ref('')
const savedSnapshot = ref('')

const emptyForm = () => ({
  id: null,
  projectId: '',
  happened: '',
  learned: '',
  nextTime: '',
  type: LESSON_TYPE_OPTIONS[0],
  phase: LESSON_PHASE_OPTIONS[0],
  relatedArtefact: LESSON_ARTEFACT_OPTIONS[0],
  relevantFor: LESSON_RELEVANCE_OPTIONS[0]
})
const form = reactive(emptyForm())
const currentSnapshot = () => JSON.stringify(form)
const dirty = computed(() => editorOpen.value && currentSnapshot() !== savedSnapshot.value)
const filteredRows = computed(() => {
  const term = query.value.trim().toLowerCase()
  if (!term) return rows.value
  return rows.value.filter((row) =>
    [
      row.migrationRequestId,
      row.projectName,
      row.requestor,
      row.type,
      row.phase,
      row.relatedArtefact,
      row.relevantFor,
      row.happened,
      row.learned,
      row.nextTime,
      row.createdBy
    ].some((value) => String(value || '').toLowerCase().includes(term))
  )
})

function canDiscard() {
  return !dirty.value || window.confirm('Discard unsaved lesson changes?')
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
    id: row.id,
    projectId: row.projectId,
    happened: row.happened,
    learned: row.learned,
    nextTime: row.nextTime,
    type: row.type,
    phase: row.phase,
    relatedArtefact: row.relatedArtefact,
    relevantFor: row.relevantFor
  })
  savedSnapshot.value = currentSnapshot()
  editorOpen.value = true
}

function closeEditor() {
  if (!canDiscard()) return
  resetForm()
  error.value = ''
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const [lessonsResponse, projectsResponse] = await Promise.all([
      axios.get(endpoint),
      axios.get('/api/migration-dashboard/projects/')
    ])
    if (!Array.isArray(lessonsResponse.data?.rows) || !Array.isArray(projectsResponse.data?.rows)) {
      throw new Error('The server returned an invalid Lessons Learnt database response.')
    }
    rows.value = lessonsResponse.data.rows
    projects.value = projectsResponse.data.rows
    return true
  } catch (failure) {
    error.value = failure.response?.data?.error || failure.message || 'Unable to load Lessons Learnt records.'
    return false
  } finally {
    loading.value = false
  }
}

async function saveRecord() {
  if (busy.value) return
  const requiredText = [form.happened, form.learned, form.nextTime]
  if (!form.projectId || requiredText.some((value) => !value.trim())) {
    error.value = 'Select a project and complete all three lesson text fields.'
    return
  }

  busy.value = true
  error.value = ''
  success.value = ''
  const isEditing = form.id !== null
  const payload = {
    projectId: Number(form.projectId),
    happened: form.happened,
    learned: form.learned,
    nextTime: form.nextTime,
    type: form.type,
    phase: form.phase,
    relatedArtefact: form.relatedArtefact,
    relevantFor: form.relevantFor
  }
  try {
    if (isEditing) {
      await axios.put(`${endpoint}${form.id}/`, payload)
    } else {
      await axios.post(endpoint, payload)
    }
    resetForm()
    const refreshed = await loadData()
    if (refreshed) {
      success.value = isEditing ? 'Lesson record updated.' : 'Lesson record added.'
    } else {
      error.value = 'The record was saved, but the table could not be refreshed. Use Reload to check the latest data.'
    }
  } catch (failure) {
    error.value = failure.response?.data?.error || failure.message || 'Unable to save the lesson record.'
  } finally {
    busy.value = false
  }
}

async function deleteRecord(row) {
  const projectLabel = `${row.migrationRequestId} · ${row.projectName}`
  const confirmed = window.confirm(
    `Delete lesson #${row.id} for ${projectLabel}? The project's Lessons Learnt page will show the next most recent record, if one exists. This cannot be undone.`
  )
  if (!confirmed || busy.value) return

  busy.value = true
  error.value = ''
  success.value = ''
  try {
    await axios.delete(`${endpoint}${row.id}/`)
    const refreshed = await loadData()
    if (refreshed) success.value = 'Lesson record deleted.'
    else error.value = 'The record was deleted, but the table could not be refreshed. Use Reload to check the latest data.'
  } catch (failure) {
    error.value = failure.response?.data?.error || failure.message || 'Unable to delete the lesson record.'
  } finally {
    busy.value = false
  }
}

function formatDate(value) {
  if (!value) return ''
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

onMounted(loadData)
</script>

<style scoped>
.lessons-db-toolbar {
  align-items: end;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;
}

label {
  display: flex;
  flex-direction: column;
  font-size: 12px;
  gap: 5px;
}

input,
select,
textarea,
button {
  background: #fff;
  border: 1px solid #cbd8e4;
  border-radius: 4px;
  font: inherit;
  padding: 8px;
}

button {
  color: #006fa8;
  cursor: pointer;
}

button:disabled {
  cursor: not-allowed;
  opacity: .6;
}

.maintenance-note {
  color: #586d7a;
  font-size: 13px;
  margin: 0 0 14px;
}

.lesson-editor {
  background: #f5f9fc;
  border: 1px solid #cbd8e4;
  border-radius: 6px;
  margin-bottom: 20px;
  padding: 18px;
}

.lesson-editor h2 {
  margin: 0 0 14px;
}

.lesson-editor fieldset {
  border: 0;
  margin: 0;
  min-width: 0;
  padding: 0;
}

.lesson-editor > fieldset > label {
  margin-bottom: 14px;
}

.lesson-editor__fields {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.lesson-editor__fields label:first-child,
.lesson-editor__fields label:nth-child(2),
.lesson-editor__fields label:nth-child(3) {
  grid-column: 1 / -1;
}

.lesson-editor textarea {
  box-sizing: border-box;
  resize: vertical;
  width: 100%;
}

.lesson-editor__actions {
  display: flex;
  gap: 10px;
  margin-top: 16px;
}

.lessons-db-scroll {
  overflow: auto;
}

table {
  border-collapse: collapse;
  font-size: 12px;
  width: 100%;
}

th {
  background: #103451;
  color: #fff;
  text-align: left;
  white-space: nowrap;
}

td,
th {
  border: 1px solid #dce5ed;
  padding: 10px;
  vertical-align: top;
}

.text-cell {
  max-width: 300px;
  min-width: 220px;
  white-space: pre-wrap;
}

.actions-cell {
  min-width: 110px;
}

.actions-cell button {
  display: block;
  margin-bottom: 8px;
}

.error {
  color: #be3030;
}

.success {
  color: #26734d;
}

@media (max-width: 720px) {
  .lesson-editor__fields {
    grid-template-columns: 1fr;
  }

  .lesson-editor__fields label {
    grid-column: auto !important;
  }
}
</style>
