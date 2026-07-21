<template>
  <PageShell
    :title="pageTitle"
    :subtitle="pageSubtitle"
    :tag="pageTag"
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
            :class="`project-card--${project.status}`"
            variant="bordered"
            fit="medium"
            clickable
            @click="openProject(project.id)"
          >
            <div class="project-card__shell">
              <div class="project-card__header">
                <div class="project-card-icon">
                  <mc-icon icon="mi-file-arrows-square" size="22" />
                </div>
                <div class="project-card__title-block">
                  <h3 class="project-card__title">{{ project.projectName }}</h3>
                  <p class="project-card__id">{{ project.migrationRequestId }}</p>
                </div>
                <mc-tag
                  class="project-card__status"
                  :appearance="statusAppearance(project.status)"
                  fit="small"
                  :label="formatStatusLabel(project.status)"
                />
              </div>

              <div class="project-card__chips">
                <span class="project-card__chip">
                  <mc-icon icon="mi-globe" size="14" />
                  {{ project.region }}
                </span>
                <span class="project-card__chip">
                  <mc-icon icon="mi-users" size="14" />
                  {{ project.fteNumber || '—' }} FTE
                </span>
                <span v-if="project.areasCount" class="project-card__chip">
                  {{ project.areasCount }} area{{ project.areasCount === 1 ? '' : 's' }}
                </span>
                <span v-if="project.function" class="project-card__chip project-card__chip--muted">
                  {{ project.function }}
                </span>
              </div>

              <p v-if="project.productsPreview" class="project-card__products">
                {{ project.productsPreview }}
              </p>

              <div class="project-card__stage">
                <div class="project-card__stage-head">
                  <span class="project-card__stage-label">Current stage</span>
                  <strong class="project-card__stage-name">{{ activeStageLabel(project.status) }}</strong>
                </div>
                <div
                  class="project-card__dots"
                  :aria-label="`${countCompletedMilestones(project.status)} of ${migrationMilestoneTotal} stages complete`"
                >
                  <span
                    v-for="milestone in buildMigrationMilestones(project.status)"
                    :key="milestone.id"
                    class="project-card__dot"
                    :class="`project-card__dot--${milestone.state}`"
                    :title="milestone.shortLabel"
                  />
                </div>
                <span class="project-card__stage-count">
                  {{ countCompletedMilestones(project.status) }}/{{ migrationMilestoneTotal }} stages
                </span>
              </div>

              <div class="project-card__progress">
                <div class="project-card__progress-head">
                  <span>Overall progress</span>
                  <strong>{{ overallProgress(project.status) }}%</strong>
                </div>
                <div class="progress-track">
                  <div
                    class="progress-fill"
                    :style="{ width: `${overallProgress(project.status)}%` }"
                  />
                </div>
              </div>

              <div class="project-card__footer">
                <div class="project-card__meta">
                  <span>{{ project.migrationType }}</span>
                  <span class="project-card__meta-sep">·</span>
                  <span>{{ project.requestor }}</span>
                  <span class="project-card__meta-sep">·</span>
                  <span>{{ project.requestedDate }}</span>
                </div>
                <mc-button
                  appearance="neutral"
                  variant="plain"
                  fit="small"
                  label="View details"
                  trailingicon="mi-arrow-right"
                  tabindex="-1"
                />
              </div>
            </div>
          </mc-card>
        </div>
      </section>
    </div>
  </PageShell>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'
import MigrationProjectsTable from '../components/MigrationProjectsTable.vue'
import { regions } from '../data/regionAreaMapping.js'
import {
  buildMigrationMilestones,
  countCompletedMilestones,
  formatStatusLabel,
  migrationMilestoneTotal,
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
const route = useRoute()

// Project nav reuses this list; later filter to the signed-in user's projects only.
const isMyProjectsView = computed(() => route.name === 'ProjectDashboard')
const pageTitle = computed(() =>
  isMyProjectsView.value ? 'My Projects' : 'Migration Dashboard'
)
const pageSubtitle = computed(() =>
  isMyProjectsView.value
    ? 'Projects under your account — open a project to track migration progress. (User filter coming soon.)'
    : 'Review submitted migration intake requests — overview of all projects and drill-down into progress.'
)
const pageTag = computed(() =>
  isMyProjectsView.value ? 'My Projects' : 'Migration Dashboard'
)

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

const activeStageLabel = (status) => {
  const milestones = buildMigrationMilestones(status)
  if (status === 'completed') return 'All milestones complete'
  const current = milestones.find((item) => item.state === 'active' || item.state === 'at_risk')
  return current?.label ?? milestones[0]?.label ?? '—'
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
  gap: 18px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.project-card {
  height: 100%;
}

.project-card::part(container) {
  border-radius: 14px;
  height: 100%;
  overflow: hidden;
  position: relative;
  transition: box-shadow 0.18s ease, transform 0.18s ease;
}

.project-card::part(container)::before {
  background: linear-gradient(90deg, #0077b8, #42b0d5);
  content: '';
  height: 3px;
  left: 0;
  position: absolute;
  top: 0;
  width: 100%;
}

.project-card--completed::part(container)::before {
  background: #6daa28;
}

.project-card--completed::part(container) {
  background: linear-gradient(180deg, rgba(109, 170, 40, 0.04) 0%, #fff 72px);
}

.project-card--at_risk::part(container)::before {
  background: #e85454;
}

.project-card--at_risk::part(container) {
  background: linear-gradient(180deg, rgba(232, 84, 84, 0.05) 0%, #fff 72px);
}

.project-card--in_progress::part(container),
.project-card--in_review::part(container) {
  background: linear-gradient(180deg, rgba(0, 119, 184, 0.05) 0%, #fff 72px);
}

.project-card:hover::part(container) {
  box-shadow: 0 10px 28px rgba(22, 22, 22, 0.09);
  transform: translateY(-2px);
}

.project-card__shell {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 100%;
}

.project-card__header {
  align-items: flex-start;
  display: flex;
  gap: 12px;
}

.project-card-icon {
  align-items: center;
  background: rgba(0, 119, 184, 0.1);
  border-radius: 12px;
  color: #0077b8;
  display: flex;
  flex-shrink: 0;
  height: 44px;
  justify-content: center;
  width: 44px;
}

.project-card--completed .project-card-icon {
  background: rgba(109, 170, 40, 0.12);
  color: #6daa28;
}

.project-card--at_risk .project-card-icon {
  background: rgba(232, 84, 84, 0.1);
  color: #e85454;
}

.project-card__title-block {
  flex: 1;
  min-width: 0;
}

.project-card__title {
  color: var(--mds_brand_appearance_neutral_default_text-color, #161616);
  font-size: 16px;
  font-weight: 600;
  line-height: 1.35;
  margin: 0 0 4px;
}

.project-card__id {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 12px;
  line-height: 1.4;
  margin: 0;
  word-break: break-all;
}

.project-card__status {
  flex-shrink: 0;
}

.project-card__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.project-card__chip {
  align-items: center;
  background: #f4f6f8;
  border-radius: 999px;
  color: #4a5560;
  display: inline-flex;
  font-size: 12px;
  font-weight: 500;
  gap: 5px;
  line-height: 1;
  padding: 5px 10px;
}

.project-card__chip--muted {
  background: rgba(0, 119, 184, 0.07);
  color: #0077b8;
}

.project-card__products {
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  display: -webkit-box;
  font-size: 12px;
  line-height: 1.45;
  margin: 0;
  overflow: hidden;
}

.project-card__stage {
  background: rgba(22, 22, 22, 0.025);
  border: 1px solid rgba(22, 22, 22, 0.06);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px;
}

.project-card__stage-head {
  align-items: baseline;
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  justify-content: space-between;
}

.project-card__stage-label {
  color: #6c757d;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.project-card__stage-name {
  color: #161616;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.35;
}

.project-card__dots {
  display: flex;
  gap: 6px;
}

.project-card__dot {
  background: #fff;
  border: 1.5px solid #d0d7de;
  border-radius: 999px;
  flex-shrink: 0;
  height: 8px;
  width: 8px;
}

.project-card__dot--complete {
  background: #6daa28;
  border-color: #6daa28;
}

.project-card__dot--active {
  background: #0077b8;
  border-color: #0077b8;
  box-shadow: 0 0 0 3px rgba(0, 119, 184, 0.18);
  height: 10px;
  width: 10px;
}

.project-card__dot--at_risk {
  background: #e85454;
  border-color: #e85454;
  box-shadow: 0 0 0 3px rgba(232, 84, 84, 0.16);
  height: 10px;
  width: 10px;
}

.project-card__stage-count {
  color: #6c757d;
  font-size: 11px;
}

.project-card__progress {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.project-card__progress-head {
  align-items: center;
  color: #6c757d;
  display: flex;
  font-size: 12px;
  justify-content: space-between;
}

.project-card__progress-head strong {
  color: #0077b8;
  font-size: 13px;
  font-weight: 700;
}

.project-card--completed .project-card__progress-head strong {
  color: #6daa28;
}

.project-card--at_risk .project-card__progress-head strong {
  color: #e85454;
}

.project-card__footer {
  align-items: center;
  border-top: 1px solid rgba(22, 22, 22, 0.06);
  display: flex;
  gap: 12px;
  justify-content: space-between;
  margin-top: auto;
  padding-top: 12px;
}

.project-card__meta {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  display: flex;
  flex-wrap: wrap;
  font-size: 12px;
  gap: 4px;
  line-height: 1.4;
  min-width: 0;
}

.project-card__meta-sep {
  opacity: 0.55;
}

.progress-track {
  background: rgba(22, 22, 22, 0.08);
  border-radius: 999px;
  height: 4px;
  overflow: hidden;
  width: 100%;
}

.progress-fill {
  background: linear-gradient(90deg, #0077b8, #42b0d5);
  border-radius: 999px;
  height: 100%;
}

.project-card--completed .progress-fill {
  background: linear-gradient(90deg, #6daa28, #8cc63f);
}

.project-card--at_risk .progress-fill {
  background: linear-gradient(90deg, #e85454, #f3880e);
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
