<template>
  <PageShell
    title="Migration Dashboard"
    subtitle="Review submitted migration intake requests — overview of all projects and drill-down into progress."
    tag="Migration Dashboard"
    back-label="Back to Welcome"
  >
    <mc-notification
      v-if="loadError"
      appearance="error"
      fit="medium"
      :heading="'Unable to load projects'"
      :body="loadError"
    />

    <mc-notification
      v-else-if="!loading && !projects.length"
      appearance="info"
      fit="medium"
      heading="No submitted projects yet"
      body="Submit a migration intake form to see projects appear here."
    >
      <mc-button
        slot="actions"
        appearance="primary"
        variant="filled"
        fit="small"
        label="Go to Intake Form"
        trailingicon="mi-arrow-right"
        @click="router.push('/migration-intake')"
      />
    </mc-notification>

    <div v-else class="dashboard-stack">
      <!-- Row 1: Portfolio Summary -->
      <section class="summary-panel">
        <div class="panel-head">
          <div class="panel-head-row">
            <div>
              <h2>Portfolio Summary</h2>
              <p>
                Aggregated view across
                {{ hasActiveFilters ? 'filtered' : 'all' }} submitted migration requests.
              </p>
            </div>
            <mc-tag
              v-if="hasActiveFilters"
              appearance="info"
              fit="small"
              :label="`${filteredProjects.length} of ${projects.length} projects`"
            />
          </div>
        </div>

        <div class="summary-body">
          <div class="summary-metrics">
            <div class="summary-stat">
              <span class="stat-label">Total projects</span>
              <strong class="stat-value">{{ displayedSummary.totalProjects }}</strong>
            </div>
            <div class="summary-stat">
              <span class="stat-label">Total FTE</span>
              <strong class="stat-value stat-value--accent">{{ displayedSummary.totalFte }}</strong>
            </div>
          </div>

          <div class="summary-group">
            <div class="summary-group-head">
              <mc-select
                label="Group by"
                hiddenlabel
                fit="small"
                placeholder="Group by"
                :value="summaryBreakdown"
                width="full-width"
                @optionselected="onSummaryBreakdownChange"
              >
                <mc-option value="status">By status</mc-option>
                <mc-option value="region">By region</mc-option>
                <mc-option value="product">By product</mc-option>
              </mc-select>
            </div>

            <div v-if="activeBreakdownChips.length" class="chip-list">
              <mc-tag
                v-for="chip in activeBreakdownChips"
                :key="chip.key"
                :appearance="chip.appearance"
                fit="small"
                :label="chip.label"
              />
            </div>
            <p v-else class="summary-empty">No breakdown data for the current selection.</p>
          </div>
        </div>
      </section>

      <!-- Row 2: Filters -->
      <section class="filters-panel">
        <div class="section-head-row">
          <div>
            <h2 class="section-title">Search &amp; filter</h2>
            <p class="section-desc">
              Narrow the project list by keyword, region, status, or migration type.
            </p>
          </div>
          <mc-button
            v-if="hasActiveFilters"
            appearance="neutral"
            variant="outlined"
            fit="small"
            label="Clear filters"
            icon="mi-times"
            @click="clearFilters"
          />
        </div>

        <div class="filters-toolbar">
          <div class="filters-toolbar__search">
            <mc-input
              label="Search"
              hiddenlabel
              fit="small"
              placeholder="Search name, ID, or requestor"
              :value="searchQuery"
              width="full-width"
              icon="mi-magnifying-glass"
              @input="onSearchInput"
            />
          </div>

          <mc-select
            label="Region"
            hiddenlabel
            fit="small"
            placeholder="All regions"
            :value="filterRegion"
            width="full-width"
            @optionselected="onFilterRegion"
          >
            <mc-option value="">All regions</mc-option>
            <mc-option v-for="region in regionOptions" :key="region" :value="region">
              {{ region }}
            </mc-option>
          </mc-select>

          <mc-select
            label="Status"
            hiddenlabel
            fit="small"
            placeholder="All statuses"
            :value="filterStatus"
            width="full-width"
            @optionselected="onFilterStatus"
          >
            <mc-option value="">All statuses</mc-option>
            <mc-option
              v-for="option in statusFilterOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </mc-option>
          </mc-select>

          <mc-select
            label="Migration type"
            hiddenlabel
            fit="small"
            placeholder="All types"
            :value="filterMigrationType"
            width="full-width"
            @optionselected="onFilterMigrationType"
          >
            <mc-option value="">All types</mc-option>
            <mc-option
              v-for="type in migrationTypeOptions"
              :key="type"
              :value="type"
            >
              {{ type }}
            </mc-option>
          </mc-select>
        </div>
      </section>

      <!-- Row 3: Submitted migration projects overview -->
      <section class="overview-panel">
        <div class="section-head-row">
          <div>
            <h2 class="section-title">Submitted migration projects overview</h2>
            <p class="section-desc">
              Tabular summary — {{ filteredProjects.length }} project(s) match your criteria.
            </p>
          </div>
          <mc-button
            appearance="primary"
            variant="outlined"
            fit="small"
            label="New intake"
            icon="mi-plus"
            @click="router.push('/migration-intake')"
          />
        </div>

        <div v-if="loading" class="loading-state">Loading projects…</div>

        <div v-else-if="!filteredProjects.length" class="empty-filter-state">
          <mc-icon icon="mi-file-search" size="32" />
          <p>No projects match your filters. Try adjusting search or filter criteria.</p>
          <mc-button
            appearance="primary"
            variant="plain"
            fit="small"
            label="Clear filters"
            @click="clearFilters"
          />
        </div>

        <div v-else class="table-shell">
          <MigrationProjectsTable
            :rows="tableRows"
            :initial-page-size="6"
            @row-click="openProject"
          />
        </div>
      </section>

      <!-- Row 4: Project previews -->
      <section class="preview-panel">
        <div class="section-head-row">
          <div>
            <h2 class="section-title">Project preview</h2>
            <p class="section-desc">Select a project to open its detail and progress view.</p>
          </div>
        </div>

        <div v-if="loading" class="loading-state">Loading projects…</div>

        <div v-else-if="!filteredProjects.length" class="empty-filter-state empty-filter-state--compact">
          <p>No project cards to display.</p>
        </div>

        <div v-else class="project-cards">
          <mc-card
            v-for="project in filteredProjects"
            :key="project.id"
            class="project-card"
            variant="bordered"
            fit="medium"
            clickable
            :heading="project.projectName"
            :body="project.migrationRequestId"
            @click="openProject(project.id)"
          >
            <div slot="image" class="project-card-icon">
              <mc-icon icon="mi-file-arrows-square" size="24" />
            </div>

            <div class="project-card-meta">
              <mc-tag
                :appearance="statusAppearance(project.status)"
                fit="small"
                :label="formatStatusLabel(project.status)"
              />
              <span>{{ project.region }} · {{ project.migrationType }}</span>
              <span>FTE {{ project.fteNumber }} · {{ project.requestor }}</span>
              <span>{{ project.requestedDate }}</span>
            </div>

            <div class="progress-inline">
              <div class="progress-track">
                <div
                  class="progress-fill"
                  :style="{ width: `${overallProgress(project.status)}%` }"
                />
              </div>
              <span class="progress-label">{{ overallProgress(project.status) }}% overall</span>
            </div>

            <mc-button
              slot="actions"
              appearance="neutral"
              variant="plain"
              fit="small"
              label="View details"
              trailingicon="mi-arrow-right"
              tabindex="-1"
            />
          </mc-card>
        </div>
      </section>
    </div>
  </PageShell>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'
import MigrationProjectsTable from '../components/MigrationProjectsTable.vue'
import { regions } from '../data/regionAreaMapping.js'
import {
  formatStatusLabel,
  overallProgress,
  statusAppearance
} from '../utils/migrationDashboardProgress.js'
import '@maersk-global/mds-components-core/mc-card'
import '@maersk-global/mds-components-core/mc-tag'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-icon'
import '@maersk-global/mds-components-core/mc-notification'
import '@maersk-global/mds-components-core/mc-input'
import '@maersk-global/mds-components-core/mc-select'
import '@maersk-global/mds-components-core/mc-option'

const router = useRouter()
const loading = ref(true)
const loadError = ref('')
const projects = ref([])
const summary = ref({
  totalProjects: 0,
  totalFte: 0,
  byStatus: {},
  byRegion: {},
  byProduct: {}
})

const searchQuery = ref('')
const filterRegion = ref('')
const filterStatus = ref('')
const filterMigrationType = ref('')
const summaryBreakdown = ref('status')

const statusFilterOptions = [
  { value: 'new', label: 'New' },
  { value: 'in_review', label: 'In review' },
  { value: 'planning', label: 'Planning' },
  { value: 'in_progress', label: 'In progress' },
  { value: 'at_risk', label: 'At risk' },
  { value: 'completed', label: 'Completed' }
]

const regionOptions = regions

const migrationTypeOptions = computed(() => {
  const types = new Set(projects.value.map((project) => project.migrationType).filter(Boolean))
  return [...types].sort()
})

const hasActiveFilters = computed(
  () =>
    Boolean(searchQuery.value.trim()) ||
    Boolean(filterRegion.value) ||
    Boolean(filterStatus.value) ||
    Boolean(filterMigrationType.value)
)

const filteredProjects = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  return projects.value.filter((project) => {
    if (filterRegion.value && project.region !== filterRegion.value) return false
    if (filterStatus.value && project.status !== filterStatus.value) return false
    if (filterMigrationType.value && project.migrationType !== filterMigrationType.value) {
      return false
    }
    if (!query) return true

    const haystack = [
      project.projectName,
      project.migrationRequestId,
      project.requestor,
      project.region,
      project.migrationType,
      project.function
    ]
      .join(' ')
      .toLowerCase()

    return haystack.includes(query)
  })
})

const buildSummaryFromProjects = (rows) => {
  const byStatus = {}
  const byRegion = {}
  const byProduct = {}
  let totalFte = 0

  const addBucket = (bucket, key, fte) => {
    if (!key) return
    if (!bucket[key]) bucket[key] = { count: 0, fte: 0 }
    bucket[key].count += 1
    bucket[key].fte += fte
  }

  for (const project of rows) {
    const fte = Number.parseInt(project.fteNumber, 10)
    const safeFte = Number.isNaN(fte) ? 0 : fte
    totalFte += safeFte
    addBucket(byStatus, project.status, safeFte)
    addBucket(byRegion, project.region, safeFte)
    for (const product of project.products ?? []) {
      const productName = String(product).trim()
      if (productName) addBucket(byProduct, productName, safeFte)
    }
  }

  return {
    totalProjects: rows.length,
    totalFte,
    byStatus,
    byRegion,
    byProduct
  }
}

const bucketEntry = (value) => {
  if (value && typeof value === 'object') {
    return { count: value.count ?? 0, fte: value.fte ?? 0 }
  }
  return { count: Number(value) || 0, fte: 0 }
}

const formatBreakdownLabel = (name, count, fte) => `${name} · ${count} · ${fte} FTE`

const sortCountEntries = (entries, key) =>
  [...entries].sort((a, b) => b.count - a.count || a[key].localeCompare(b[key]))

const displayedSummary = computed(() =>
  hasActiveFilters.value
    ? buildSummaryFromProjects(filteredProjects.value)
    : summary.value
)

const tableRows = computed(() =>
  filteredProjects.value.map((project) => ({
    id: project.id,
    status: project.status,
    migrationRequestId: project.migrationRequestId,
    projectName: project.projectName,
    statusLabel: formatStatusLabel(project.status),
    region: project.region,
    migrationType: project.migrationType,
    fteNumber: project.fteNumber,
    requestor: project.requestor,
    requestedDate: project.requestedDate,
    progressLabel: `${overallProgress(project.status)}%`
  }))
)

const statusEntries = computed(() =>
  sortCountEntries(
    Object.entries(displayedSummary.value.byStatus ?? {}).map(([status, value]) => {
      const entry = bucketEntry(value)
      return { status, count: entry.count, fte: entry.fte }
    }),
    'status'
  )
)

const regionEntries = computed(() =>
  sortCountEntries(
    Object.entries(displayedSummary.value.byRegion ?? {}).map(([region, value]) => {
      const entry = bucketEntry(value)
      return { region, count: entry.count, fte: entry.fte }
    }),
    'region'
  )
)

const productEntries = computed(() =>
  sortCountEntries(
    Object.entries(displayedSummary.value.byProduct ?? {}).map(([product, value]) => {
      const entry = bucketEntry(value)
      return { product, count: entry.count, fte: entry.fte }
    }),
    'product'
  )
)

const activeBreakdownChips = computed(() => {
  if (summaryBreakdown.value === 'region') {
    return regionEntries.value.map((item) => ({
      key: item.region,
      label: formatBreakdownLabel(item.region, item.count, item.fte),
      appearance: 'neutral'
    }))
  }
  if (summaryBreakdown.value === 'product') {
    return productEntries.value.map((item) => ({
      key: item.product,
      label: formatBreakdownLabel(item.product, item.count, item.fte),
      appearance: 'info'
    }))
  }
  return statusEntries.value.map((item) => ({
    key: item.status,
    label: formatBreakdownLabel(formatStatusLabel(item.status), item.count, item.fte),
    appearance: statusAppearance(item.status)
  }))
})

const onSummaryBreakdownChange = (event) => {
  summaryBreakdown.value = event.detail?.value ?? 'status'
}

const onSearchInput = (event) => {
  searchQuery.value = event.target?.value ?? ''
}

const onFilterRegion = (event) => {
  filterRegion.value = event.detail?.value ?? ''
}

const onFilterStatus = (event) => {
  filterStatus.value = event.detail?.value ?? ''
}

const onFilterMigrationType = (event) => {
  filterMigrationType.value = event.detail?.value ?? ''
}

const clearFilters = () => {
  searchQuery.value = ''
  filterRegion.value = ''
  filterStatus.value = ''
  filterMigrationType.value = ''
}

const openProject = (id) => {
  router.push(`/migration-dashboard/${id}`)
}

const loadProjects = async () => {
  loading.value = true
  loadError.value = ''
  try {
    const { data } = await axios.get('/api/migration-dashboard/projects/')
    projects.value = data.rows ?? []
    summary.value = data.summary ?? summary.value
  } catch (error) {
    loadError.value =
      error?.response?.data?.error ?? 'Unable to load migration projects. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(loadProjects)
</script>

<style scoped>
.dashboard-stack {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.panel-head h2,
.section-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 6px;
}

.panel-head p,
.section-desc {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 13px;
  line-height: 1.5;
  margin: 0;
}

.section-head-row,
.panel-head-row {
  align-items: flex-start;
  display: flex;
  gap: 16px;
  justify-content: space-between;
  margin-bottom: 16px;
}

.summary-panel,
.filters-panel,
.overview-panel,
.preview-panel {
  background: #fff;
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(22, 22, 22, 0.04);
  padding: 22px 20px;
}

.overview-panel {
  border-color: rgba(0, 119, 184, 0.18);
  overflow: visible;
  position: relative;
}

.overview-panel::before {
  background: linear-gradient(90deg, #0077b8 0%, #42b0d5 55%, #003f6e 100%);
  content: '';
  height: 4px;
  left: 0;
  position: absolute;
  right: 0;
  top: 0;
}

.filters-panel {
  position: relative;
}

.filters-toolbar {
  align-items: center;
  display: grid;
  gap: 12px;
  grid-template-columns: minmax(300px, 1.85fr) repeat(3, minmax(148px, 1fr));
}

.filters-toolbar__search {
  min-width: 0;
}

.panel-head {
  margin-bottom: 16px;
}

.summary-body {
  align-items: flex-start;
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
}

.summary-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.summary-group {
  flex: 1;
  min-width: 260px;
}

.summary-group-head {
  margin-bottom: 12px;
  max-width: 200px;
}

.summary-empty {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 13px;
  margin: 0;
}

.summary-stat {
  background: rgba(0, 119, 184, 0.06);
  border-radius: 12px;
  min-width: 140px;
  padding: 14px 20px;
}

.stat-label {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  display: block;
  font-size: 12px;
  margin-bottom: 4px;
}

.stat-value {
  color: var(--mds_brand_appearance_neutral_default_text-color, #161616);
  font-size: 28px;
  font-weight: 700;
}

.stat-value--accent {
  color: #0077b8;
}

.chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.table-shell {
  width: 100%;
}

.loading-state {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 14px;
  padding: 24px 0;
}

.empty-filter-state {
  align-items: center;
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 32px 16px;
  text-align: center;
}

.empty-filter-state p {
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
  max-width: 420px;
}

.empty-filter-state--compact {
  padding: 20px 16px;
}

.project-cards {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.project-card::part(container) {
  border-radius: 12px;
}

.project-card-icon {
  align-items: center;
  background: color-mix(in srgb, #0077b8 12%, white);
  border-radius: 12px;
  color: #0077b8;
  display: flex;
  height: 44px;
  justify-content: center;
  width: 44px;
}

.project-card-meta {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  display: flex;
  flex-direction: column;
  font-size: 13px;
  gap: 6px;
  margin-top: 8px;
}

.progress-inline {
  align-items: center;
  display: flex;
  gap: 10px;
  margin-top: 12px;
}

.progress-track {
  background: rgba(22, 22, 22, 0.08);
  border-radius: 999px;
  flex: 1;
  height: 8px;
  overflow: hidden;
}

.progress-fill {
  background: linear-gradient(90deg, #0077b8, #42b0d5);
  border-radius: 999px;
  height: 100%;
}

.progress-label {
  color: #0077b8;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

@media (max-width: 1100px) {
  .filters-toolbar {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 960px) {
  .section-head-row,
  .panel-head-row {
    flex-direction: column;
  }

  .summary-group {
    min-width: 100%;
  }

  .summary-group-head {
    max-width: none;
  }

  .filters-toolbar,
  .project-cards {
    grid-template-columns: 1fr;
  }
}
</style>
