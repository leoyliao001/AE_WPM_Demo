<template>
  <PageShell title="Resources" :show-heading="false" back-to="/toll-gates" back-label="Back to Toll Gates" full-width>
    <div class="pa-page">
      <header class="pa-hero">
        <div class="pa-heading"><div><p class="pa-eyebrow">People / Projects / Progress</p><h1>Resources</h1><p class="pa-subtitle">A single view of approved capacity, pipeline demand and project-level hiring execution.</p></div><mc-button appearance="neutral" variant="outlined" label="Export" :disabled="loading || !filtered.length" @click="exportData" /></div>
        <div class="pa-metrics"><article v-for="metric in metrics" :key="metric.label" class="pa-metric"><span>{{ metric.label }}</span><strong>{{ metric.value }}</strong><small>{{ metric.note }}</small></article></div>
      </header>
      <div v-if="error" class="pa-feedback pa-feedback--error" role="alert">{{ error }} <button class="pa-text-button" @click="load">Retry</button></div>
      <section class="pa-panel">
        <div class="pa-section-heading"><h2>Project resource portfolio</h2><span class="pa-note">{{ filtered.length }} projects visible</span></div>
        <div class="pa-toolbar">
          <input v-model="query" type="search" aria-label="Search resource projects" placeholder="Search project or request ID..." />
          <select v-model="product" aria-label="Filter product"><option value="">All products</option><option v-for="item in products" :key="item">{{ item }}</option></select>
          <select v-model="region" aria-label="Filter region"><option value="">All regions</option><option v-for="item in regions" :key="item">{{ item }}</option></select>
          <select v-model="area" aria-label="Filter area"><option value="">All areas</option><option v-for="item in areas" :key="item">{{ item }}</option></select>
          <select v-model="status" aria-label="Filter approval status"><option value="">All project statuses</option><option>Approved</option><option>Pipeline</option></select>
          <button class="pa-text-button" @click="reset">Reset</button>
        </div>
        <div v-if="loading" class="pa-empty" role="status">Loading resource projects...</div>
        <div v-else class="pa-scroll"><table class="pa-table"><thead><tr><th>Project name</th><th>Project ID</th><th>Product</th><th>Region</th><th>Area</th><th>GSC site</th><th>Approved FTE</th><th>Pipeline FTE</th><th>Project status</th><th>Resource status</th><th>Action</th></tr></thead>
          <tbody><tr v-for="row in filtered" :key="row.projectId"><td><strong>{{ row.projectName }}</strong></td><td>{{ row.migrationRequestId }}</td><td>{{ row.products.join(', ') }}</td><td>{{ row.region }}</td><td>{{ row.areas.join(', ') }}</td><td>{{ row.sites.join(', ') }}</td><td>{{ row.approvedFte ?? '—' }}</td><td>{{ row.pipelineFte ?? '—' }}</td><td><span class="pa-status" :class="{ 'pa-status--confirmed': row.approvalStatus === 'Approved' }">{{ row.approvalStatus }}</span></td><td>{{ row.status.replaceAll('_', ' ') }}</td><td><router-link class="pa-link" :to="`/migration-dashboard/${row.projectId}/resources?from=resources&project=${row.projectId}`">Open project →</router-link></td></tr><tr v-if="!filtered.length"><td colspan="11" class="pa-empty">No projects match your access or filters.</td></tr></tbody>
        </table></div>
        <p class="pa-note">Approved means Business Case approval is complete and current. FTE comes from submitted, locked Scope; unavailable capacity is shown as —, not replaced with sample values.</p>
      </section>
    </div>
  </PageShell>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'
import { utils, writeFile } from 'xlsx'
import PageShell from '../components/PageShell.vue'
import '@maersk-global/mds-components-core/mc-button'
import '../styles/projectArtefacts.css'

const rows = ref([])
const loading = ref(false)
const error = ref('')
const query = ref('')
const product = ref('')
const region = ref('')
const area = ref('')
const status = ref('')
const products = computed(() => [...new Set(rows.value.flatMap(row => row.products))].sort())
const regions = computed(() => [...new Set(rows.value.map(row => row.region))].sort())
const areas = computed(() => [...new Set(rows.value.flatMap(row => row.areas))].sort())
const filtered = computed(() => rows.value.filter(row =>
  `${row.projectName} ${row.migrationRequestId}`.toLowerCase().includes(query.value.toLowerCase()) &&
  (!product.value || row.products.includes(product.value)) && (!region.value || row.region === region.value) &&
  (!area.value || row.areas.includes(area.value)) && (!status.value || row.approvalStatus === status.value)))
const metrics = computed(() => [
  { label: 'Approved projects', value: filtered.value.filter(row => row.approvalStatus === 'Approved').length, note: 'Current Business Case approval' },
  { label: 'Approved FTEs', value: filtered.value.reduce((sum, row) => sum + (row.approvedFte ?? 0), 0), note: 'Known locked Scope capacity' },
  { label: 'Pipeline projects', value: filtered.value.filter(row => row.approvalStatus === 'Pipeline').length, note: 'Awaiting approval' },
  { label: 'Pipeline FTEs', value: filtered.value.reduce((sum, row) => sum + (row.pipelineFte ?? 0), 0), note: 'Known locked Scope demand' },
])
function reset() { query.value = ''; product.value = ''; region.value = ''; area.value = ''; status.value = '' }
async function load() {
  loading.value = true; error.value = ''
  try { rows.value = (await axios.get('/api/migration-dashboard/resources/')).data.rows }
  catch (caught) { error.value = caught.response?.data?.error || 'Unable to load resource projects.' }
  finally { loading.value = false }
}
function exportData() {
  try {
    const workbook = utils.book_new()
    const sheet = utils.json_to_sheet(filtered.value.map(row => ({
      Project: row.projectName, 'Request ID': row.migrationRequestId,
      Products: row.products.join(', '), Region: row.region, Areas: row.areas.join(', '), Sites: row.sites.join(', '),
      'Approved FTE': row.approvedFte, 'Pipeline FTE': row.pipelineFte, 'Project status': row.approvalStatus, 'Resource status': row.status,
    })))
    sheet['!cols'] = Array.from({ length: 10 }, () => ({ wch: 28 }))
    utils.book_append_sheet(workbook, sheet, 'Resource Projects')
    writeFile(workbook, 'WPM-resource-projects.xlsx', { compression: true })
  } catch (caught) { error.value = `Unable to export: ${caught.message}` }
}
onMounted(load)
</script>
