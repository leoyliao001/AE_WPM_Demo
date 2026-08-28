<template>
  <PageShell
    :title="pageTitle"
    :subtitle="pageSubtitle"
    :tag="pageTag"
    back-label="Back to Welcome"
    full-width
  >
    <mc-notification
      v-if="loadError"
      appearance="error"
      fit="medium"
      :heading="'Unable to load projects'"
      :body="loadError"
    />

    <mc-notification
      v-else-if="exportError"
      appearance="error"
      fit="medium"
      :heading="'Unable to export dashboard data'"
      :body="exportError"
    />

    <mc-notification
      v-else-if="!loading && !projects.length"
      appearance="info"
      fit="medium"
      :heading="emptyHeading"
      :body="emptyBody"
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

    <div v-else class="dashboard-layout">
      <section class="hero-panel">
        <div class="hero-panel__top">
          <div>
            <p class="hero-eyebrow">Portfolio command center</p>
            <h2 class="hero-title">Migration portfolio overview</h2>
            <p class="hero-desc">
              Track volume, risk, and momentum across
              {{ hasActiveFilters ? 'the filtered selection' : 'all submitted requests' }}.
            </p>
          </div>
          <div class="hero-actions">
            <mc-tag
              v-if="hasActiveFilters"
              appearance="info"
              fit="small"
              :label="`${filteredProjects.length} of ${projects.length} projects`"
            />
            <mc-button
              appearance="neutral"
              variant="outlined"
              fit="small"
              :label="exporting ? 'Preparing…' : 'Download Excel'"
              icon="mi-arrow-down"
              :disabled="exporting || loading || !filteredProjects.length"
              @click="downloadDashboardData"
            />
            <mc-button
              appearance="primary"
              variant="outlined"
              fit="small"
              label="New intake"
              icon="mi-plus"
              @click="router.push('/migration-intake')"
            />
          </div>
        </div>

        <div class="kpi-grid">
          <article
            v-for="stat in summaryStats"
            :key="stat.key"
            class="kpi-card"
            :class="{
              'kpi-card--accent': stat.accent === 'accent',
              'kpi-card--success': stat.accent === 'success',
              'kpi-card--danger': stat.accent === 'danger'
            }"
          >
            <span class="kpi-card__label">{{ stat.label }}</span>
            <strong class="kpi-card__value">{{ stat.value }}</strong>
          </article>
        </div>

        <div class="breakdown-row">
          <div class="breakdown-row__select">
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
      </section>

      <div class="analysis-layout">
        <aside class="sidebar-stack">
          <section class="filters-panel">
            <div class="panel-head">
              <h2 class="section-title">Filters</h2>
              <p class="section-desc">Refine the portfolio view with live filtering.</p>
            </div>
            <div class="filters-toolbar">
              <mc-input
                label="Search"
                hiddenlabel
                fit="small"
                placeholder="Search name, ID, requestor"
                :value="searchQuery"
                width="full-width"
                icon="mi-magnifying-glass"
                @input="onSearchInput"
              />
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
                <mc-option v-for="type in migrationTypeOptions" :key="type" :value="type">
                  {{ type }}
                </mc-option>
              </mc-select>
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
          </section>

          <section class="insights-panel">
            <div class="panel-head">
              <h2 class="section-title">Actionable insights</h2>
              <p class="section-desc">Fast talking points for portfolio reviews.</p>
            </div>

            <div class="insight-list">
              <div v-for="insight in portfolioInsights" :key="insight.label" class="insight-item">
                <span class="insight-item__label">{{ insight.label }}</span>
                <strong class="insight-item__value">{{ insight.value }}</strong>
                <p class="insight-item__detail">{{ insight.detail }}</p>
              </div>
            </div>

            <div class="leaderboard">
              <div class="leaderboard__head">
                <h4>Top products in demand</h4>
                <span>{{ topProductItems.length }} shown</span>
              </div>
              <div v-if="topProductItems.length" class="leaderboard__list">
                <div
                  v-for="item in topProductItems"
                  :key="item.product"
                  class="leaderboard__item"
                >
                  <div>
                    <strong>{{ item.product }}</strong>
                    <span>{{ formatWholeNumber(item.count) }} project(s)</span>
                  </div>
                  <span>{{ formatWholeNumber(item.fte) }} FTE</span>
                </div>
              </div>
              <p v-else class="summary-empty">No product mix data for the current selection.</p>
            </div>
          </section>
        </aside>

        <section class="analytics-panel">
          <div class="panel-head">
            <h2 class="section-title">Analytics</h2>
            <p class="section-desc">Click chart items to cross-filter the full dashboard.</p>
          </div>

          <article class="chart-card chart-card--trend">
            <div class="chart-card__head">
              <div>
                <h3>Intake trend</h3>
                <p>Rolling 12 months of submitted demand.</p>
              </div>
              <div class="chart-toggle">
                <button
                  type="button"
                  class="chart-toggle__button"
                  :class="{ 'chart-toggle__button--active': trendMetric === 'count' }"
                  @click="trendMetric = 'count'"
                >
                  Projects
                </button>
                <button
                  type="button"
                  class="chart-toggle__button"
                  :class="{ 'chart-toggle__button--active': trendMetric === 'fte' }"
                  @click="trendMetric = 'fte'"
                >
                  FTE
                </button>
              </div>
            </div>
            <DashboardLineChart
              :labels="trendLabels"
              :series="trendSeries"
              :value-formatter="formatWholeNumber"
            />
            <p class="trend-summary">{{ trendHeadline }}</p>
            <div class="trend-table-wrap">
              <table class="trend-table">
                <thead>
                  <tr>
                    <th scope="col">Metric</th>
                    <th v-for="month in intakeTrend" :key="`trend-head-${month.key}`" scope="col">
                      {{ month.label }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in trendTableRows" :key="row.key">
                    <th scope="row">{{ row.label }}</th>
                    <td v-for="(value, idx) in row.values" :key="`${row.key}-${idx}`">
                      {{ formatWholeNumber(value) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p class="trend-period-note">{{ trendPeriodSummary }}</p>
          </article>

          <div class="analytics-split">
            <article class="chart-card">
              <div class="chart-card__head">
                <div>
                  <h3>Status distribution</h3>
                  <p>Where projects sit in the delivery lifecycle.</p>
                </div>
              </div>
              <DashboardDonutChart
                :items="statusChartItems"
                :active-key="filterStatus"
                center-label="Projects"
                :value-formatter="formatWholeNumber"
                @select="onStatusChartSelect"
              />
            </article>

            <article class="chart-card">
              <div class="chart-card__head">
                <div>
                  <h3>Regional workload</h3>
                  <p>Top regions by project volume or FTE load.</p>
                </div>
                <div class="chart-toggle">
                  <button
                    type="button"
                    class="chart-toggle__button"
                    :class="{ 'chart-toggle__button--active': regionChartMetric === 'count' }"
                    @click="regionChartMetric = 'count'"
                  >
                    Projects
                  </button>
                  <button
                    type="button"
                    class="chart-toggle__button"
                    :class="{ 'chart-toggle__button--active': regionChartMetric === 'fte' }"
                    @click="regionChartMetric = 'fte'"
                  >
                    FTE
                  </button>
                </div>
              </div>
              <DashboardBarChart
                :items="regionChartItems"
                :active-key="filterRegion"
                :value-formatter="regionChartValueFormatter"
                @select="onRegionChartSelect"
              />
            </article>
          </div>
        </section>
      </div>

      <section class="overview-panel">
        <div class="section-head-row">
          <div>
            <h2 class="section-title">Submitted migration projects overview</h2>
            <p class="section-desc">
              Tabular summary — {{ filteredProjects.length }} project(s) match your criteria.
            </p>
          </div>
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

      <section class="preview-panel">
        <div class="section-head-row">
          <div>
            <h2 class="section-title">Project preview</h2>
            <p class="section-desc">
              Showing {{ previewProjects.length }} highlighted cards from your current selection.
            </p>
          </div>
        </div>

        <div v-if="loading" class="loading-state">Loading projects…</div>
        <div v-else-if="!previewProjects.length" class="empty-filter-state empty-filter-state--compact">
          <p>No project cards to display.</p>
        </div>
        <div v-else class="project-cards">
          <mc-card
            v-for="project in previewProjects"
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
                  <div class="progress-fill" :style="{ width: `${overallProgress(project.status)}%` }" />
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
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { utils, writeFile } from 'xlsx'
import PageShell from '../components/PageShell.vue'
import MigrationProjectsTable from '../components/MigrationProjectsTable.vue'
import DashboardBarChart from '../components/dashboard/DashboardBarChart.vue'
import DashboardDonutChart from '../components/dashboard/DashboardDonutChart.vue'
import DashboardLineChart from '../components/dashboard/DashboardLineChart.vue'
import { regions } from '../data/regionAreaMapping.js'
import {
  buildMigrationMilestones,
  countCompletedMilestones,
  formatStatusLabel,
  migrationMilestoneTotal,
  overallProgress,
  statusAppearance
} from '../utils/migrationDashboardProgress.js'
import { getCurrentUserEmail } from '../auth/azureAuth.js'
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

// /project-dashboard = current user's projects; /migration-dashboard = all projects
const isMyProjectsView = computed(() => route.name === 'ProjectDashboard')
const pageTitle = computed(() =>
  isMyProjectsView.value ? 'My Projects' : 'Migration Dashboard'
)
const pageSubtitle = computed(() =>
  isMyProjectsView.value
    ? 'Only projects you submitted — open a project to track migration progress.'
    : 'Review submitted migration intake requests — overview of all projects and drill-down into progress.'
)
const pageTag = computed(() =>
  isMyProjectsView.value ? 'My Projects' : 'Migration Dashboard'
)
const emptyHeading = computed(() =>
  isMyProjectsView.value ? 'No projects under your account yet' : 'No submitted projects yet'
)
const emptyBody = computed(() =>
  isMyProjectsView.value
    ? 'Projects you submit via the migration intake form will appear here.'
    : 'Submit a migration intake form to see projects appear here.'
)

const loading = ref(true)
const loadError = ref('')
const exportError = ref('')
const projects = ref([])
const regionChartMetric = ref('count')
const trendMetric = ref('count')
const exporting = ref(false)
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

const statusChartColors = {
  new: '#42b0d5',
  in_review: '#f3b562',
  planning: '#94a3b8',
  in_progress: '#0077b8',
  at_risk: '#e85454',
  completed: '#6daa28'
}

const numberFormatter = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 0
})

const decimalFormatter = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 1
})

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

const formatWholeNumber = (value) => numberFormatter.format(Number(value) || 0)

const formatDecimalNumber = (value) => decimalFormatter.format(Number(value) || 0)

const formatExportDate = (date) =>
  new Intl.DateTimeFormat('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short'
  }).format(date)

const getBucketCount = (bucket, key) => bucketEntry(bucket?.[key]).count

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

const migrationTypeEntries = computed(() => {
  const byType = {}
  for (const project of filteredProjects.value) {
    const fte = Number.parseInt(project.fteNumber, 10)
    const safeFte = Number.isNaN(fte) ? 0 : fte
    const typeName = String(project.migrationType ?? '').trim()
    if (!typeName) continue
    if (!byType[typeName]) byType[typeName] = { count: 0, fte: 0 }
    byType[typeName].count += 1
    byType[typeName].fte += safeFte
  }

  return sortCountEntries(
    Object.entries(byType).map(([migrationType, value]) => ({
      migrationType,
      count: value.count,
      fte: value.fte
    })),
    'migrationType'
  )
})

const completedCount = computed(() => getBucketCount(displayedSummary.value.byStatus, 'completed'))
const atRiskCount = computed(() => getBucketCount(displayedSummary.value.byStatus, 'at_risk'))
const averageFtePerProject = computed(() =>
  displayedSummary.value.totalProjects
    ? displayedSummary.value.totalFte / displayedSummary.value.totalProjects
    : 0
)

const summaryStats = computed(() => [
  {
    key: 'projects',
    label: 'Total projects',
    value: formatWholeNumber(displayedSummary.value.totalProjects),
    accent: ''
  },
  {
    key: 'fte',
    label: 'Total FTE',
    value: formatWholeNumber(displayedSummary.value.totalFte),
    accent: 'accent'
  },
  {
    key: 'completed',
    label: 'Completed',
    value: formatWholeNumber(completedCount.value),
    accent: 'success'
  },
  {
    key: 'at-risk',
    label: 'At risk',
    value: formatWholeNumber(atRiskCount.value),
    accent: atRiskCount.value ? 'danger' : ''
  },
  {
    key: 'avg-fte',
    label: 'Avg. FTE / project',
    value: formatDecimalNumber(averageFtePerProject.value),
    accent: ''
  },
  {
    key: 'regions',
    label: 'Regions in scope',
    value: formatWholeNumber(regionEntries.value.length),
    accent: ''
  }
])

const statusChartItems = computed(() =>
  statusEntries.value.map((item) => ({
    key: item.status,
    label: formatStatusLabel(item.status),
    value: item.count,
    color: statusChartColors[item.status] || '#94a3b8'
  }))
)

const regionChartItems = computed(() =>
  regionEntries.value.slice(0, 6).map((item) => ({
    key: item.region,
    label: item.region,
    shortLabel: item.region,
    value: regionChartMetric.value === 'fte' ? item.fte : item.count,
    color: item.region === filterRegion.value ? '#003f6e' : '#0077b8'
  }))
)

const regionChartValueFormatter = (value) =>
  regionChartMetric.value === 'fte' ? `${formatWholeNumber(value)} FTE` : formatWholeNumber(value)

const chartMonthFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  year: '2-digit'
})

const parseRequestedDate = (value) => {
  const text = String(value || '').trim()
  if (!text) return null

  const direct = new Date(text)
  if (!Number.isNaN(direct.getTime())) return direct

  const match = text.match(
    /^(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})(?:,\s*(\d{2}):(\d{2}):(\d{2}))?$/
  )
  if (!match) return null

  const monthIndex = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    .findIndex((month) => month.toLowerCase() === match[2].toLowerCase())
  if (monthIndex < 0) return null

  const [, day, , year, hour = '00', minute = '00', second = '00'] = match
  return new Date(
    Number(year),
    monthIndex,
    Number(day),
    Number(hour),
    Number(minute),
    Number(second)
  )
}

const projectTrendDate = (project) => parseRequestedDate(project.requestedDate) || parseRequestedDate(project.createdAt)

const recentMonths = computed(() => {
  const datedProjects = filteredProjects.value
    .map((project) => projectTrendDate(project))
    .filter((date) => date && !Number.isNaN(date.getTime()))
  const anchor = datedProjects.length
    ? new Date(Math.max(...datedProjects.map((date) => date.getTime())))
    : new Date()

  return Array.from({ length: 12 }, (_, index) => {
    const date = new Date(anchor.getFullYear(), anchor.getMonth() - (11 - index), 1)
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
    return {
      key,
      date,
      label: chartMonthFormatter.format(date)
    }
  })
})

const intakeTrend = computed(() => {
  const buckets = Object.fromEntries(
    recentMonths.value.map((month) => [month.key, { count: 0, fte: 0 }])
  )

  for (const project of filteredProjects.value) {
    const date = projectTrendDate(project)
    if (!date || Number.isNaN(date.getTime())) continue
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
    if (!buckets[key]) continue
    const fte = Number.parseInt(project.fteNumber, 10)
    buckets[key].count += 1
    buckets[key].fte += Number.isNaN(fte) ? 0 : fte
  }

  return recentMonths.value.map((month) => ({
    ...month,
    count: buckets[month.key]?.count ?? 0,
    fte: buckets[month.key]?.fte ?? 0
  }))
})

const trendSeries = computed(() => [
  {
    key: trendMetric.value,
    label: trendMetric.value === 'fte' ? 'Submitted FTE' : 'Submitted projects',
    color: '#0077b8',
    values: intakeTrend.value.map((month) => month[trendMetric.value])
  }
])

const trendLabels = computed(() => intakeTrend.value.map((month) => month.label))

const trendHeadline = computed(() => {
  const values = intakeTrend.value.map((month) => month[trendMetric.value])
  const latest = values[values.length - 1] ?? 0
  const previous = values[values.length - 2] ?? 0
  const noun = trendMetric.value === 'fte' ? 'FTE' : 'projects'

  if (latest === previous) {
    return `Latest month is flat at ${formatWholeNumber(latest)} ${noun}.`
  }

  const direction = latest > previous ? 'up' : 'down'
  const delta = Math.abs(latest - previous)
  return `Latest month is ${direction} by ${formatWholeNumber(delta)} ${noun} versus the previous month.`
})

const trendTableRows = computed(() => [
  {
    key: 'projects',
    label: 'Projects',
    values: intakeTrend.value.map((month) => month.count)
  },
  {
    key: 'fte',
    label: 'FTE',
    values: intakeTrend.value.map((month) => month.fte)
  }
])

const trendPeriodSummary = computed(() => {
  const values = intakeTrend.value.map((month) => month[trendMetric.value])
  const first = values[0] ?? 0
  const last = values[values.length - 1] ?? 0
  const pct = first > 0 ? ((last - first) / first) * 100 : null
  const noun = trendMetric.value === 'fte' ? 'FTE' : 'projects'
  const startLabel = intakeTrend.value[0]?.label ?? 'Start'
  const endLabel = intakeTrend.value[intakeTrend.value.length - 1]?.label ?? 'Now'
  const changeLabel = pct === null ? 'n/a from zero baseline' : `${pct >= 0 ? '▲' : '▼'} ${Math.abs(pct).toFixed(1)}%`
  return `${noun}: ${formatWholeNumber(first)} (${startLabel}) → ${formatWholeNumber(last)} (${endLabel}), ${changeLabel} over the period.`
})

const topRegion = computed(() => regionEntries.value[0] ?? null)
const topMigrationType = computed(() => migrationTypeEntries.value[0] ?? null)
const inFlightCount = computed(() =>
  statusEntries.value
    .filter((item) => ['in_review', 'planning', 'in_progress', 'at_risk'].includes(item.status))
    .reduce((sum, item) => sum + item.count, 0)
)
const averageAreaCount = computed(() =>
  filteredProjects.value.length
    ? filteredProjects.value.reduce((sum, project) => sum + (project.areasCount || 0), 0) /
      filteredProjects.value.length
    : 0
)
const averageCountryCount = computed(() =>
  filteredProjects.value.length
    ? filteredProjects.value.reduce((sum, project) => sum + (project.countriesCount || 0), 0) /
      filteredProjects.value.length
    : 0
)

const portfolioInsights = computed(() => [
  {
    label: 'Primary focus region',
    value: topRegion.value?.region || '—',
    detail: topRegion.value
      ? `${formatWholeNumber(topRegion.value.count)} project(s) · ${formatWholeNumber(topRegion.value.fte)} FTE`
      : 'No regional distribution yet.'
  },
  {
    label: 'Leading migration type',
    value: topMigrationType.value?.migrationType || '—',
    detail: topMigrationType.value
      ? `${formatWholeNumber(topMigrationType.value.count)} project(s) in the current selection`
      : 'No migration type mix available.'
  },
  {
    label: 'Delivery posture',
    value: `${formatWholeNumber(inFlightCount.value)} in flight`,
    detail: `${formatWholeNumber(atRiskCount.value)} at risk · ${formatWholeNumber(
      completedCount.value
    )} completed`
  },
  {
    label: 'Average scope footprint',
    value: `${formatDecimalNumber(averageAreaCount.value)} areas`,
    detail: `${formatDecimalNumber(averageCountryCount.value)} countries per project on average`
  }
])

const topProductItems = computed(() => productEntries.value.slice(0, 4))
const previewProjects = computed(() => filteredProjects.value.slice(0, 4))

const timelineSpanByStatus = {
  new: 1,
  in_review: 2,
  planning: 3,
  in_progress: 4,
  at_risk: 4,
  completed: 5
}

const monthKeyFromDate = (date) =>
  `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`

const projectTimelineRows = computed(() => {
  const monthKeys = recentMonths.value.map((month) => month.key)
  const indexByKey = Object.fromEntries(monthKeys.map((key, idx) => [key, idx]))

  return filteredProjects.value
    .map((project) => {
      const date = projectTrendDate(project)
      if (!date || Number.isNaN(date.getTime())) return null
      const anchorIndex = indexByKey[monthKeyFromDate(date)]
      if (anchorIndex === undefined) return null

      const span = timelineSpanByStatus[project.status] ?? 1
      const startIndex = Math.max(0, anchorIndex - span + 1)
      const cells = monthKeys.map((_, idx) => {
        if (idx < startIndex || idx > anchorIndex) return 'none'
        if (startIndex === anchorIndex) return 'dot'
        if (idx === startIndex) return 'start'
        if (idx === anchorIndex) return 'end'
        return 'mid'
      })

      return {
        id: project.id,
        projectName: project.projectName,
        status: project.status,
        anchorIndex,
        cells
      }
    })
    .filter(Boolean)
    .sort((a, b) => b.anchorIndex - a.anchorIndex || a.projectName.localeCompare(b.projectName))
    .slice(0, 10)
})

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

const onStatusChartSelect = (status) => {
  filterStatus.value = filterStatus.value === status ? '' : status
}

const onRegionChartSelect = (region) => {
  filterRegion.value = filterRegion.value === region ? '' : region
}

const openProject = (id) => {
  router.push(`/migration-dashboard/${id}`)
}

const createDetailRows = () =>
  filteredProjects.value.map((project) => ({
    project_id: project.id || '',
    migration_request_id: project.migrationRequestId || '',
    project_name: project.projectName || '',
    region: project.region || '',
    migration_type: project.migrationType || '',
    status: formatStatusLabel(project.status),
    status_code: project.status || '',
    requestor: project.requestor || '',
    function: project.function || '',
    fte: Number.parseInt(project.fteNumber, 10) || 0,
    areas: Number(project.areasCount) || 0,
    countries: Number(project.countriesCount) || 0,
    products: Array.isArray(project.products) ? project.products.join('; ') : '',
    requested_date: project.requestedDate || '',
    current_stage: activeStageLabel(project.status),
    overall_progress: overallProgress(project.status)
  }))

const downloadDashboardData = () => {
  exporting.value = true
  exportError.value = ''

  try {
    const exportedAt = new Date()
    const workbook = utils.book_new()
    const overviewRows = [
      { metric: 'Exported at', value: formatExportDate(exportedAt) },
      { metric: 'Scope', value: hasActiveFilters.value ? 'Filtered dashboard view' : 'All projects' },
      { metric: 'Active filters', value: hasActiveFilters.value ? 'Yes' : 'No' },
      { metric: 'Search', value: searchQuery.value.trim() || 'All' },
      { metric: 'Region', value: filterRegion.value || 'All' },
      { metric: 'Status', value: filterStatus.value ? formatStatusLabel(filterStatus.value) : 'All' },
      { metric: 'Migration type', value: filterMigrationType.value || 'All' },
      { metric: 'Total projects', value: displayedSummary.value.totalProjects },
      { metric: 'Total FTE', value: displayedSummary.value.totalFte },
      { metric: 'Completed', value: completedCount.value },
      { metric: 'At risk', value: atRiskCount.value },
      { metric: 'Avg. FTE / project', value: formatDecimalNumber(averageFtePerProject.value) },
      { metric: 'Regions in scope', value: regionEntries.value.length },
      { metric: 'Primary region', value: topRegion.value?.region || '—' },
      { metric: 'Leading migration type', value: topMigrationType.value?.migrationType || '—' },
      { metric: 'In flight', value: inFlightCount.value }
    ]

    const detailRows = createDetailRows()
    const trendRows = intakeTrend.value.map((month) => ({
      month: month.label,
      projects: month.count,
      fte: month.fte
    }))
    const breakdownRows = [
      ...statusEntries.value.map((item) => ({
        category: 'Status',
        item: formatStatusLabel(item.status),
        projects: item.count,
        fte: item.fte
      })),
      ...regionEntries.value.map((item) => ({
        category: 'Region',
        item: item.region,
        projects: item.count,
        fte: item.fte
      })),
      ...productEntries.value.map((item) => ({
        category: 'Product',
        item: item.product,
        projects: item.count,
        fte: item.fte
      }))
    ]

    const overviewSheet = utils.json_to_sheet(overviewRows)
    const detailSheet = utils.json_to_sheet(detailRows)
    const trendSheet = utils.json_to_sheet(trendRows)
    const breakdownSheet = utils.json_to_sheet(breakdownRows)

    overviewSheet['!cols'] = [{ wch: 22 }, { wch: 36 }]
    detailSheet['!cols'] = [
      { wch: 14 },
      { wch: 22 },
      { wch: 28 },
      { wch: 18 },
      { wch: 20 },
      { wch: 16 },
      { wch: 16 },
      { wch: 20 },
      { wch: 10 },
      { wch: 10 },
      { wch: 12 },
      { wch: 28 },
      { wch: 20 },
      { wch: 18 },
      { wch: 14 },
      { wch: 12 }
    ]
    trendSheet['!cols'] = [{ wch: 14 }, { wch: 12 }, { wch: 10 }]
    breakdownSheet['!cols'] = [{ wch: 14 }, { wch: 28 }, { wch: 12 }, { wch: 10 }]

    utils.book_append_sheet(workbook, detailSheet, 'Detail')
    utils.book_append_sheet(workbook, overviewSheet, 'Overview')
    utils.book_append_sheet(workbook, trendSheet, 'Trend')
    utils.book_append_sheet(workbook, breakdownSheet, 'Breakdown')

    const suffix = hasActiveFilters.value ? 'filtered' : 'all'
    writeFile(
      workbook,
      `migration_dashboard_${suffix}_${exportedAt.toISOString().slice(0, 10)}.xlsx`
    )
  } catch (error) {
    exportError.value = error?.message || 'The dashboard export could not be generated.'
  } finally {
    exporting.value = false
  }
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
  exportError.value = ''
  try {
    if (isMyProjectsView.value && !getCurrentUserEmail()) {
      projects.value = []
      summary.value = {
        totalProjects: 0,
        totalFte: 0,
        byStatus: {},
        byRegion: {},
        byProduct: {}
      }
      loadError.value = 'Sign in required to view your projects.'
      return
    }

    const params = isMyProjectsView.value ? { mine: 1 } : undefined
    const { data } = await axios.get('/api/migration-dashboard/projects/', { params })
    projects.value = data.rows ?? []
    summary.value = data.summary ?? summary.value
  } catch (error) {
    loadError.value =
      error?.response?.data?.error ?? 'Unable to load migration projects. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadProjects()
})

watch(isMyProjectsView, () => {
  clearFilters()
  loadProjects()
})
</script>

<style scoped>
.dashboard-layout {
  display: grid;
  gap: 20px;
}

.hero-panel,
.analytics-panel,
.filters-panel,
.insights-panel,
.overview-panel,
.timeline-panel,
.preview-panel {
  background: #fff;
  border: 1px solid rgba(12, 35, 64, 0.1);
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(12, 35, 64, 0.06);
  padding: 18px;
}

.hero-panel {
  background: linear-gradient(180deg, #fdfefe 0%, #f6fbff 100%);
}

.hero-panel__top {
  align-items: flex-start;
  display: flex;
  gap: 14px;
  justify-content: space-between;
  margin-bottom: 14px;
}

.hero-eyebrow {
  color: #0077b8;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  margin: 0 0 4px;
  text-transform: uppercase;
}

.hero-title {
  color: #0f2940;
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
  margin: 0 0 6px;
}

.hero-desc {
  color: #5d6b76;
  font-size: 13px;
  line-height: 1.45;
  margin: 0;
}

.hero-actions {
  align-items: flex-end;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.kpi-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  margin-bottom: 12px;
}

.kpi-card {
  background: #fff;
  border: 1px solid rgba(0, 119, 184, 0.12);
  border-radius: 12px;
  padding: 10px 12px;
}

.kpi-card--accent {
  background: rgba(0, 119, 184, 0.06);
}

.kpi-card--success {
  background: rgba(109, 170, 40, 0.08);
  border-color: rgba(109, 170, 40, 0.2);
}

.kpi-card--danger {
  background: rgba(232, 84, 84, 0.08);
  border-color: rgba(232, 84, 84, 0.2);
}

.kpi-card__label {
  color: #6a7680;
  display: block;
  font-size: 11px;
  margin-bottom: 4px;
}

.kpi-card__value {
  color: #0f2940;
  font-size: 22px;
  font-weight: 700;
  line-height: 1.1;
}

.breakdown-row {
  align-items: flex-start;
  border-top: 1px solid rgba(12, 35, 64, 0.08);
  display: grid;
  gap: 10px;
  grid-template-columns: 200px 1fr;
  padding-top: 12px;
}

.breakdown-row__select {
  min-width: 0;
}

.chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.summary-empty {
  color: #6c757d;
  font-size: 12px;
  margin: 8px 0 0;
}

.analysis-layout {
  align-items: start;
  display: grid;
  gap: 16px;
  grid-template-columns: minmax(300px, 0.42fr) minmax(0, 1.58fr);
}

.panel-head {
  margin-bottom: 12px;
}

.section-title {
  color: #10263d;
  font-size: 18px;
  font-weight: 650;
  margin: 0 0 4px;
}

.section-desc {
  color: #66737f;
  font-size: 12px;
  line-height: 1.5;
  margin: 0;
}

.analytics-panel {
  display: grid;
  gap: 12px;
}

.chart-card {
  background: #fbfdff;
  border: 1px solid rgba(12, 35, 64, 0.08);
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
}

.chart-card__head {
  align-items: flex-start;
  display: flex;
  gap: 10px;
  justify-content: space-between;
}

.chart-card__head h3 {
  color: #182b3c;
  font-size: 15px;
  font-weight: 650;
  margin: 0 0 4px;
}

.chart-card__head p {
  color: #6b7782;
  font-size: 12px;
  line-height: 1.45;
  margin: 0;
}

.chart-card--trend {
  padding-bottom: 12px;
}

.analytics-split {
  display: grid;
  gap: 12px;
  grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.05fr);
}

.chart-toggle {
  background: #edf2f7;
  border-radius: 999px;
  display: inline-flex;
  padding: 3px;
}

.chart-toggle__button {
  background: transparent;
  border: 0;
  border-radius: 999px;
  color: #4f5d69;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  padding: 6px 11px;
}

.chart-toggle__button--active {
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
  color: #0077b8;
}

.trend-summary {
  color: #576571;
  font-size: 12px;
  line-height: 1.5;
  margin: 0;
}

.trend-table-wrap {
  margin-top: 2px;
  overflow: auto;
}

.trend-table {
  border-collapse: collapse;
  font-size: 11px;
  min-width: 700px;
  width: 100%;
}

.trend-table th,
.trend-table td {
  border-bottom: 1px solid rgba(12, 35, 64, 0.08);
  font-variant-numeric: tabular-nums;
  padding: 8px 10px;
  text-align: right;
  white-space: nowrap;
}

.trend-table thead th {
  background: #f1f7fc;
  color: #2c4156;
  font-weight: 700;
}

.trend-table th:first-child,
.trend-table td:first-child {
  left: 0;
  position: sticky;
  text-align: left;
  z-index: 1;
}

.trend-table tbody th {
  background: #fff;
  color: #31465a;
  font-weight: 600;
}

.trend-period-note {
  color: #5f6e7b;
  font-size: 12px;
  line-height: 1.5;
  margin: 6px 0 0;
}

.sidebar-stack {
  display: grid;
  gap: 14px;
  position: sticky;
  top: 12px;
}

.filters-toolbar {
  display: grid;
  gap: 10px;
  grid-template-columns: 1fr;
}

.insight-list {
  display: grid;
  gap: 9px;
  margin-bottom: 12px;
}

.insight-item {
  background: #fff;
  border: 1px solid rgba(12, 35, 64, 0.08);
  border-radius: 11px;
  padding: 10px 12px;
}

.insight-item__label {
  color: #6d7983;
  display: block;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.04em;
  margin-bottom: 5px;
  text-transform: uppercase;
}

.insight-item__value {
  color: #132a40;
  display: block;
  font-size: 15px;
  font-weight: 700;
}

.insight-item__detail {
  color: #6d7983;
  font-size: 11px;
  line-height: 1.45;
  margin: 4px 0 0;
}

.leaderboard {
  border-top: 1px solid rgba(12, 35, 64, 0.08);
  display: grid;
  gap: 8px;
  padding-top: 10px;
}

.leaderboard__head {
  align-items: baseline;
  display: flex;
  justify-content: space-between;
}

.leaderboard__head h4 {
  color: #152a3d;
  font-size: 13px;
  margin: 0;
}

.leaderboard__head span {
  color: #6d7983;
  font-size: 11px;
}

.leaderboard__list {
  display: grid;
  gap: 7px;
}

.leaderboard__item {
  align-items: center;
  background: #fff;
  border: 1px solid rgba(12, 35, 64, 0.08);
  border-radius: 10px;
  display: flex;
  justify-content: space-between;
  padding: 8px 10px;
}

.leaderboard__item div {
  display: grid;
  gap: 2px;
}

.leaderboard__item strong {
  color: #1a2e40;
  font-size: 12px;
}

.leaderboard__item span {
  color: #687782;
  font-size: 11px;
}

.overview-panel {
  border-color: rgba(0, 119, 184, 0.16);
}

.section-head-row {
  align-items: flex-start;
  display: flex;
  gap: 12px;
  justify-content: space-between;
  margin-bottom: 14px;
}

.table-shell {
  width: 100%;
}

.loading-state {
  color: #6c757d;
  font-size: 13px;
  padding: 20px 0;
}

.empty-filter-state {
  align-items: center;
  color: #6c757d;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 28px 14px;
  text-align: center;
}

.empty-filter-state p {
  font-size: 13px;
  line-height: 1.45;
  margin: 0;
  max-width: 420px;
}

.empty-filter-state--compact {
  padding: 18px 14px;
}

.project-cards {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.project-card {
  height: 100%;
}

.project-card::part(container) {
  border-radius: 14px;
  box-shadow: 0 3px 10px rgba(12, 35, 64, 0.06);
  height: 100%;
  overflow: hidden;
  position: relative;
  transition: box-shadow 0.18s ease, transform 0.18s ease;
}

.project-card::part(container)::before {
  background: #0077b8;
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

.project-card--at_risk::part(container)::before {
  background: #e85454;
}

.project-card:hover::part(container) {
  box-shadow: 0 12px 28px rgba(12, 35, 64, 0.11);
  transform: translateY(-2px);
}

.project-card__shell {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 100%;
}

.project-card__header {
  align-items: flex-start;
  display: flex;
  gap: 11px;
}

.project-card-icon {
  align-items: center;
  background: rgba(0, 119, 184, 0.1);
  border-radius: 12px;
  color: #0077b8;
  display: flex;
  flex-shrink: 0;
  height: 40px;
  justify-content: center;
  width: 40px;
}

.project-card--completed .project-card-icon {
  background: rgba(109, 170, 40, 0.12);
  color: #6daa28;
}

.project-card--at_risk .project-card-icon {
  background: rgba(232, 84, 84, 0.12);
  color: #e85454;
}

.project-card__title-block {
  flex: 1;
  min-width: 0;
}

.project-card__title {
  color: #162a3b;
  font-size: 15px;
  font-weight: 650;
  line-height: 1.35;
  margin: 0 0 3px;
}

.project-card__id {
  color: #6b7883;
  font-size: 11px;
  margin: 0;
  word-break: break-all;
}

.project-card__status {
  flex-shrink: 0;
}

.project-card__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.project-card__chip {
  align-items: center;
  background: #f4f7fa;
  border-radius: 999px;
  color: #4e5e6d;
  display: inline-flex;
  font-size: 11px;
  gap: 5px;
  line-height: 1;
  padding: 5px 9px;
}

.project-card__chip--muted {
  background: rgba(0, 119, 184, 0.08);
  color: #0077b8;
}

.project-card__products {
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
  color: #667680;
  display: -webkit-box;
  font-size: 11px;
  line-height: 1.45;
  margin: 0;
  overflow: hidden;
}

.project-card__stage {
  background: #f8fafc;
  border: 1px solid rgba(12, 35, 64, 0.08);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 7px;
  padding: 9px 11px;
}

.project-card__stage-head {
  align-items: baseline;
  display: flex;
  gap: 8px;
  justify-content: space-between;
}

.project-card__stage-label {
  color: #6d7983;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.project-card__stage-name {
  color: #172e42;
  font-size: 12px;
  font-weight: 600;
}

.project-card__dots {
  display: flex;
  gap: 6px;
}

.project-card__dot {
  background: #fff;
  border: 1.5px solid #d0d7de;
  border-radius: 999px;
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
  box-shadow: 0 0 0 2px rgba(0, 119, 184, 0.18);
}

.project-card__dot--at_risk {
  background: #e85454;
  border-color: #e85454;
  box-shadow: 0 0 0 2px rgba(232, 84, 84, 0.16);
}

.project-card__stage-count {
  color: #6c757d;
  font-size: 10px;
}

.project-card__progress {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.project-card__progress-head {
  align-items: center;
  color: #667580;
  display: flex;
  font-size: 11px;
  justify-content: space-between;
}

.project-card__progress-head strong {
  color: #0077b8;
  font-size: 12px;
}

.project-card--completed .project-card__progress-head strong {
  color: #6daa28;
}

.project-card--at_risk .project-card__progress-head strong {
  color: #e85454;
}

.progress-track {
  background: rgba(12, 35, 64, 0.12);
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

.project-card__footer {
  align-items: center;
  border-top: 1px solid rgba(12, 35, 64, 0.08);
  display: flex;
  gap: 10px;
  justify-content: space-between;
  margin-top: auto;
  padding-top: 10px;
}

.project-card__meta {
  color: #6a7883;
  display: flex;
  flex-wrap: wrap;
  font-size: 11px;
  gap: 4px;
  line-height: 1.35;
  min-width: 0;
}

.project-card__meta-sep {
  opacity: 0.55;
}

@media (max-width: 1280px) {
  .kpi-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .analysis-layout {
    grid-template-columns: 1fr;
  }

  .sidebar-stack {
    position: static;
  }
}

@media (max-width: 960px) {
  .hero-panel__top {
    flex-direction: column;
  }

  .hero-actions {
    align-items: flex-start;
  }

  .breakdown-row {
    grid-template-columns: 1fr;
  }

  .analytics-split,
  .project-cards {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .hero-title {
    font-size: 21px;
  }

  .section-head-row {
    flex-direction: column;
  }
}
</style>
