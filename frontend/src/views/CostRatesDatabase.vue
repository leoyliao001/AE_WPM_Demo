<template>
  <PageShell title="Cost Rates" subtitle="Maintain annual cost per FTE and USD exchange rates. Cost year must match the Intake target start date."
    back-to="/project-attributes" back-label="Back to Admin" full-width class="bc-page">
    <p class="bc-note">Locations must exactly match a source country or destination strategy site. Rates are unique by location, job level and year. Business Cases support exactly one source country and one destination; unsupported allocations are reported, never estimated.</p>
    <div class="bc-toolbar">
      <label class="bc-record-filter">Filter rates<input v-model="query" type="search" placeholder="Location, year, job level, version…" /></label>
      <div class="bc-actions"><button type="button" :disabled="blocked" @click="createRate">Add cost rate</button>
        <button type="button" :disabled="blocked" @click="reload">Reload</button></div>
    </div>
    <p v-if="error" class="bc-error" role="alert">{{ error }}</p>
    <p v-if="success" class="bc-success" role="status">{{ success }}</p>
    <p v-if="blocked" role="status">{{ loading ? 'Loading cost rates…' : 'Saving changes…' }}</p>
    <form v-if="editor" class="bc-editor" aria-labelledby="cost-rate-editor-title" @submit.prevent="saveRate">
      <h2 id="cost-rate-editor-title">{{ editor.id ? 'Edit' : 'Create' }} cost rate</h2>
      <fieldset :disabled="blocked">
        <div class="bc-fields bc-fields--columns">
          <label>Exact location<input v-model="editor.location" required /></label>
          <label>Job level<select v-model="editor.jobLevel" required><option value="">Select job level</option><option>JL2</option><option>JL3</option><option>JL4</option></select></label>
          <label>Annual cost per FTE (local currency)<input v-model="editor.annualCost" type="text" inputmode="decimal" required /></label>
          <label>Currency (3 uppercase letters)<input v-model="editor.currency" maxlength="3" pattern="[A-Z]{3}" required placeholder="ISO currency code" /></label>
          <label>USD exchange rate (USD per currency unit)<input v-model="editor.usdRate" type="text" inputmode="decimal" required /></label>
          <label>Cost year · required<input v-model="editor.year" type="number" step="1" min="1" max="9999" required placeholder="YYYY" /></label>
          <label>Version<input v-model="editor.version" type="text" required /></label>
        </div>
        <p class="bc-note">USD currency requires a USD exchange rate of exactly 1. Updating or deleting uses the loaded last-updated timestamp to detect concurrent edits.</p>
        <div class="bc-actions"><button type="submit" class="bc-primary">Save rate</button><button type="button" @click="closeEditor">Cancel</button></div>
      </fieldset>
    </form>
    <p v-if="!loading && !filteredRows.length">No cost rates match this filter.</p>
    <div v-else class="bc-scroll">
      <table>
        <thead><tr><th>Exact location</th><th>Job level</th><th>Annual cost / FTE</th><th>Currency</th><th>USD rate</th><th>Cost year</th><th>Version</th><th>Updated at</th><th>Actions</th></tr></thead>
        <tbody><tr v-for="row in filteredRows" :key="row.id">
          <td>{{ row.location }}</td><td>{{ row.jobLevel }}</td><td>{{ row.annualCost }}</td><td>{{ row.currency }}</td><td>{{ row.usdRate }}</td><td>{{ row.year }}</td><td>{{ row.version }}</td><td>{{ row.updatedAt ? new Date(row.updatedAt).toLocaleString() : '—' }}</td>
          <td><div class="bc-actions"><button type="button" :disabled="blocked" @click="editRate(row)">Edit</button><button type="button" :disabled="blocked" @click="deleteRate(row)">Delete</button></div></td>
        </tr></tbody>
      </table>
    </div>
  </PageShell>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'
import { useUnsavedChanges } from '../composables/useUnsavedChanges.js'
import '../styles/businessCase.css'

const rows = ref([])
const query = ref('')
const editor = ref(null)
const baseline = ref('')
const loading = ref(false)
const pending = ref(false)
const error = ref('')
const success = ref('')
const dirty = computed(() => !!editor.value && JSON.stringify(editor.value) !== baseline.value)
const blocked = computed(() => loading.value || pending.value)
const { canLeave } = useUnsavedChanges(dirty, pending)
const filteredRows = computed(() => rows.value.filter(row => [row.location, row.jobLevel, row.year, row.version, row.currency].some(value =>
  String(value || '').toLowerCase().includes(query.value.trim().toLowerCase()))))

function showError(failure) {
  error.value = failure.response?.data?.error || failure.message
  if (failure.response?.status === 409) error.value += ' Your input is retained. Copy it before reloading the latest rates and resolving the conflict.'
}
async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await axios.get('/api/migration-dashboard/cost-rates/')
    rows.value = data.rows || []
  } catch (failure) {
    showError(failure)
  } finally {
    loading.value = false
  }
}
async function setEditor(value) {
  editor.value = value
  baseline.value = JSON.stringify(value)
  error.value = ''
  success.value = ''
  await nextTick()
  document.getElementById('cost-rate-editor-title')?.scrollIntoView({ block: 'start' })
}
function createRate() {
  if (!canLeave()) return
  setEditor({ location: '', jobLevel: '', annualCost: '', currency: '', usdRate: '', year: '', version: '' })
}
function editRate(row) {
  if (!canLeave()) return
  setEditor({ ...row })
}
function closeEditor() {
  if (canLeave()) editor.value = null
}
async function reload() {
  if (!canLeave()) return
  editor.value = null
  await loadData()
}
function validRate(value) {
  const decimal = /^\d+(?:\.\d+)?$/
  if (!value.location.trim() || !['JL2', 'JL3', 'JL4'].includes(value.jobLevel) ||
      !decimal.test(String(value.annualCost)) || !Number.isFinite(Number(value.annualCost)) ||
      !/^[A-Z]{3}$/.test(value.currency) || !decimal.test(String(value.usdRate)) ||
      !Number.isFinite(Number(value.usdRate)) || Number(value.usdRate) <= 0 ||
      !Number.isInteger(Number(value.year)) || Number(value.year) < 1 || Number(value.year) > 9999 ||
      !value.version.trim()) {
    error.value = 'Provide an exact location, JL2/JL3/JL4, non-negative decimal annual cost, three-uppercase-letter currency, positive decimal USD rate, integer cost year and version.'
    return false
  }
  if (value.currency === 'USD' && Number(value.usdRate) !== 1) {
    error.value = 'USD exchange rate must be exactly 1 when currency is USD.'
    return false
  }
  if (rows.value.some(row => row.id !== value.id && row.location === value.location.trim() && row.jobLevel === value.jobLevel && Number(row.year) === Number(value.year))) {
    error.value = 'A rate already exists for this exact location, job level and year. Edit that record instead.'
    return false
  }
  if (value.id && !value.updatedAt) {
    error.value = 'The loaded rate has no last-updated timestamp. Reload before editing.'
    return false
  }
  return true
}
async function saveRate() {
  if (blocked.value || !editor.value || !validRate(editor.value)) return
  pending.value = true
  error.value = ''
  success.value = ''
  const value = editor.value
  try {
    await axios.post('/api/migration-dashboard/cost-rates/', {
      ...(value.id ? { id: value.id, updatedAt: value.updatedAt } : {}),
      location: value.location.trim(), jobLevel: value.jobLevel,
      annualCost: String(value.annualCost), currency: value.currency,
      usdRate: String(value.usdRate), year: Number(value.year), version: value.version.trim()
    })
    editor.value = null
    pending.value = false
    await loadData()
    success.value = 'Cost rate saved. Refresh affected Business Cases to review the financial impact.'
  } catch (failure) {
    showError(failure)
  } finally {
    pending.value = false
  }
}
async function deleteRate(row) {
  if (!canLeave()) return
  if (!row.updatedAt) {
    error.value = 'The rate has no last-updated timestamp. Reload before deleting.'
    return
  }
  if (!window.confirm(`Delete ${row.location} · ${row.jobLevel} · ${row.year}? Affected Business Cases may no longer have a matching rate.`)) return
  pending.value = true
  error.value = ''
  success.value = ''
  try {
    await axios.delete(`/api/migration-dashboard/cost-rates/${row.id}/`, { data: { updatedAt: row.updatedAt } })
    if (editor.value?.id === row.id) editor.value = null
    pending.value = false
    await loadData()
    success.value = 'Cost rate deleted.'
  } catch (failure) {
    showError(failure)
  } finally {
    pending.value = false
  }
}
onMounted(loadData)
</script>
