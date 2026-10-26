<template>
  <PageShell
    title="Stakeholder Registration"
    subtitle="Project Team roster, manually assigned roles, lock status, and change history."
    tag="Project Attributes"
    back-to="/project-attributes"
    back-label="Back to Admin"
    full-width
  >
    <div class="registry-toolbar">
      <label class="search-field">
        <span>Filter registrations</span>
        <input v-model="query" type="search" placeholder="Project, request ID, requestor…" />
      </label>
      <span class="row-count">{{ filteredRows.length }} visible · {{ rows.length }} saved</span>
      <mc-button appearance="neutral" variant="outlined" fit="small" label="Reload" icon="mi-arrow-clockwise" :disabled="loading" @click="loadData" />
    </div>

    <mc-notification v-if="error" appearance="error" fit="medium" heading="Unable to load Stakeholder Registrations" :body="error" />
    <div v-else-if="loading" class="table-state">Loading Stakeholder Registrations…</div>
    <div v-else-if="!filteredRows.length" class="table-state">
      {{ rows.length ? 'No rows match this filter.' : 'No Stakeholder Registrations have been saved yet.' }}
    </div>
    <div v-else class="table-scroll" role="region" aria-label="Saved Stakeholder Registrations" tabindex="0">
      <table class="registry-table">
        <thead>
          <tr>
            <th v-for="column in columns" :key="column.key" scope="col">{{ column.label }}</th>
            <th scope="col">Open</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in filteredRows" :key="row.registration_id">
            <td v-for="column in columns" :key="column.key" :title="String(row[column.key] ?? '')">
              <span>{{ displayCell(row[column.key]) }}</span>
            </td>
            <td>
              <router-link class="open-link" :to="`/migration-dashboard/${row.project_id}/stakeholder-registration?from=admin&project=${row.project_id}`">Open</router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </PageShell>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-notification'

const columns = ref([])
const rows = ref([])
const query = ref('')
const loading = ref(false)
const error = ref('')

const filteredRows = computed(() => {
  const term = query.value.trim().toLowerCase()
  if (!term) return rows.value
  return rows.value.filter((row) =>
    columns.value.some((column) => String(row[column.key] ?? '').toLowerCase().includes(term))
  )
})

function displayCell(value) {
  if (value === null || value === undefined || value === '') return '—'
  return String(value)
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await axios.get('/api/migration-dashboard/stakeholder-registrations/')
    columns.value = data.columns || []
    rows.value = data.rows || []
  } catch (caught) {
    error.value = caught?.response?.data?.error || caught?.response?.data?.detail || caught.message
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.registry-toolbar {
  align-items: end;
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-bottom: 16px;
}

.search-field {
  color: #536571;
  display: grid;
  font-size: 12px;
  gap: 5px;
}

.search-field input {
  border: 1px solid #bac8d0;
  border-radius: 4px;
  font: inherit;
  font-size: 14px;
  min-height: 38px;
  padding: 7px 10px;
  width: min(360px, 72vw);
}

.row-count {
  color: #647681;
  font-size: 12px;
  margin: 0 auto 9px 0;
}

.table-state {
  border-top: 1px solid #d9e2e7;
  color: #647681;
  padding: 26px 12px;
}

.table-scroll {
  border: 1px solid #d7e0e5;
  max-width: 100%;
  overflow: auto;
}

.registry-table {
  border-collapse: separate;
  border-spacing: 0;
  font-size: 12px;
  min-width: 100%;
  width: max-content;
}

.registry-table th,
.registry-table td {
  border-bottom: 1px solid #e1e8ec;
  border-right: 1px solid #e1e8ec;
  max-width: 260px;
  min-width: 105px;
  overflow: hidden;
  padding: 9px 11px;
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.registry-table th {
  background: #edf3f6;
  color: #263b48;
  font-weight: 700;
  position: sticky;
  top: 0;
  z-index: 1;
}

.registry-table tbody tr:hover td {
  background: #f5f9fa;
}

.open-link {
  color: #006bb8;
  font-weight: 700;
}
</style>