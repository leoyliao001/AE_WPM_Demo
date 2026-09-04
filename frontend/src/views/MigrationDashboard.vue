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

    <div v-else class="dashboard-canvas">
      <div class="dashboard-layout">
        <header class="dash-toolbar">
          <div class="dash-toolbar__filters">
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
          </div>
          <div class="dash-toolbar__actions">
            <mc-tag
              v-if="hasActiveFilters"
              appearance="info"
              fit="small"
              :label="`${filteredProjects.length} of ${projects.length} projects`"
            />
            <mc-button
              v-if="hasActiveFilters"
              appearance="neutral"
              variant="plain"
              fit="small"
              label="Clear"
              icon="mi-times"
              @click="clearFilters"
            />
            <mc-button
              appearance="neutral"
              variant="outlined"
              fit="small"
              :label="exporting ? 'Preparing…' : 'Export'"
              icon="mi-arrow-down"
              :disabled="exporting || loading || !filteredProjects.length"
              @click="downloadDashboardData"
            />
          </div>
        </header>

        <section class="overview-panel">
          <div class="overview-panel__metrics">
            <article class="overview-panel__hero">
              <span class="overview-panel__label">Total projects</span>
              <p class="overview-panel__metric-desc">{{ heroMetricDescription }}</p>
              <div class="overview-panel__hero-row">
                <strong class="overview-panel__hero-value">
                  {{ formatWholeNumber(displayedSummary.totalProjects) }}
                </strong>
                <span class="metric-chip metric-chip--unit">projects</span>
                <span
                  v-if="intakeTrendBadge"
                  class="overview-panel__badge"
                  :class="`overview-panel__badge--${intakeTrendBadge.direction}`"
                  :title="intakeTrendBadgeDescription"
                >
                  {{ intakeTrendBadge.label }}
                </span>
              </div>
              <div class="metric-chip-row">
                <span class="metric-chip metric-chip--fte">
                  <em>{{ formatWholeNumber(displayedSummary.totalFte) }}</em>
                  FTE
                </span>
                <span v-if="hasActiveFilters" class="metric-chip metric-chip--muted">Filtered view</span>
                <span v-else class="metric-chip metric-chip--muted">Full portfolio</span>
              </div>
            </article>

            <div class="overview-panel__stats">
              <article
                v-for="stat in metricCards"
                :key="stat.key"
                class="overview-panel__stat"
              >
                <span class="overview-panel__label">{{ stat.label }}</span>
                <p class="overview-panel__metric-desc">{{ stat.description }}</p>
                <div class="overview-panel__stat-row">
                  <strong class="overview-panel__stat-value">{{ stat.value }}</strong>
                  <span v-if="stat.unit" class="metric-chip metric-chip--unit">{{ stat.unit }}</span>
                </div>
                <div v-if="stat.chips?.length" class="metric-chip-row">
                  <span
                    v-for="chip in stat.chips"
                    :key="chip.label"
                    class="metric-chip"
                    :class="chip.tone ? `metric-chip--${chip.tone}` : ''"
                  >
                    <em v-if="chip.value != null">{{ chip.value }}</em>
                    {{ chip.label }}
                  </span>
                </div>
                <span v-else class="overview-panel__stat-hint">{{ stat.shortHint || stat.hint }}</span>
              </article>
            </div>
          </div>

          <div v-if="statusEntries.length" class="overview-panel__composition">
            <div class="overview-panel__composition-head">
              <p class="overview-panel__composition-desc">{{ statusCompositionDescription }}</p>
              <span class="metric-chip metric-chip--muted">
                <em>{{ formatWholeNumber(displayedSummary.totalProjects) }}</em>
                projects
              </span>
            </div>
            <div class="composition-bar__track" role="img" aria-label="Status composition">
              <button
                v-for="item in statusCompositionItems"
                :key="item.status"
                type="button"
                class="composition-bar__segment"
                :class="{ 'composition-bar__segment--active': filterStatus === item.status }"
                :style="{
                  flexGrow: item.count,
                  backgroundColor: statusChartColors[item.status] || '#94a3b8'
                }"
                :title="`${item.label} · ${formatWholeNumber(item.count)} (${item.pct}%)`"
                @click="onStatusChartSelect(item.status)"
              />
            </div>
            <div class="composition-bar__labels composition-bar__labels--inline">
              <button
                v-for="item in statusCompositionItems"
                :key="`label-${item.status}`"
                type="button"
                class="composition-bar__label"
                :class="{ 'composition-bar__label--active': filterStatus === item.status }"
                @click="onStatusChartSelect(item.status)"
              >
                <span
                  class="composition-bar__dot"
                  :style="{ backgroundColor: statusChartColors[item.status] || '#94a3b8' }"
                />
                <span class="composition-bar__name">{{ item.label }}</span>
                <strong>{{ item.pct }}%</strong>
              </button>
            </div>
          </div>
        </section>

        <section class="dashboard-main">
          <aside class="dash-card dash-card--insights">
            <div class="insights-panel__head">
              <div class="insights-panel__title-row">
                <span class="insights-panel__accent" aria-hidden="true" />
                <h3>Actionable insights</h3>
              </div>
              <p>Fast talking points for portfolio reviews.</p>
            </div>

            <div class="insight-list">
              <article
                v-for="insight in portfolioInsights"
                :key="insight.label"
                class="insight-item"
                :class="insight.tone ? `insight-item--${insight.tone}` : ''"
              >
                <div class="insight-item__top">
                  <span class="insight-item__label">{{ insight.label }}</span>
                  <span v-if="insight.badge" class="insight-item__badge">{{ insight.badge }}</span>
                </div>
                <strong class="insight-item__value">{{ insight.value }}</strong>
                <p v-if="insight.description" class="insight-item__desc">{{ insight.description }}</p>
                <div v-if="insight.chips?.length" class="metric-chip-row">
                  <span
                    v-for="chip in insight.chips"
                    :key="`${insight.label}-${chip.label}`"
                    class="metric-chip"
                    :class="chip.tone ? `metric-chip--${chip.tone}` : ''"
                  >
                    <em v-if="chip.value != null">{{ chip.value }}</em>
                    {{ chip.label }}
                  </span>
                </div>
              </article>
            </div>

            <div class="leaderboard">
              <div class="leaderboard__head">
                <h4>Top products in demand</h4>
                <span class="metric-chip metric-chip--muted">
                  <em>{{ topProductItems.length }}</em>
                  shown
                </span>
              </div>
              <div v-if="topProductItems.length" class="leaderboard__list">
                <div
                  v-for="(item, index) in topProductItems"
                  :key="item.product"
                  class="leaderboard__item"
                >
                  <span class="leaderboard__rank" aria-hidden="true">{{ index + 1 }}</span>
                  <div class="leaderboard__copy">
                    <strong>{{ item.product }}</strong>
                    <div class="metric-chip-row">
                      <span class="metric-chip">
                        <em>{{ formatWholeNumber(item.count) }}</em>
                        projects
                      </span>
                      <span class="metric-chip metric-chip--fte">
                        <em>{{ formatWholeNumber(item.fte) }}</em>
                        FTE
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              <p v-else class="summary-empty">No product mix data for the current selection.</p>
            </div>
          </aside>

          <div class="dashboard-main__charts">
        <article class="dash-card dash-card--breakdown">
          <div class="dash-card__head dash-card__head--tabs">
            <h3>Portfolio breakdown</h3>
            <div class="segmented-tabs" role="tablist">
              <button
                v-for="tab in breakdownTabs"
                :key="tab.id"
                type="button"
                role="tab"
                class="segmented-tabs__btn"
                :class="{ 'segmented-tabs__btn--active': breakdownTab === tab.id }"
                :aria-selected="breakdownTab === tab.id"
                @click="breakdownTab = tab.id"
              >
                {{ tab.label }}
              </button>
            </div>
          </div>
          <DashboardBarChart
            v-if="activeBreakdownBarItems.length"
            :items="activeBreakdownBarItems"
            :active-key="activeBreakdownFilterKey"
            :value-formatter="formatWholeNumber"
            @select="onBreakdownSelect"
          />
          <p v-else class="summary-empty">No data for this dimension.</p>
        </article>

        <article class="dash-card dash-card--analytics">
          <DashboardLineChart
            dual-axis
            title="Portfolio trend"
            :labels="trendLabels"
            :series="trendSeries"
            :value-formatter="formatWholeNumber"
          />
          <p class="trend-caption">{{ trendHeadline }}</p>
          <div class="trend-guide">
            <p class="trend-guide__intro">
              Click a legend item above to show or hide that line. At least one line stays visible.
            </p>
            <div class="trend-guide__list">
              <div
                v-for="guide in trendSeriesGuides"
                :key="guide.key"
                class="trend-guide__item"
              >
                <span
                  class="trend-guide__dot"
                  :style="{ backgroundColor: guide.color }"
                  aria-hidden="true"
                />
                <div>
                  <strong>{{ guide.label }}</strong>
                  <span>{{ guide.description }}</span>
                </div>
              </div>
            </div>
          </div>
        </article>
          </div>
        </section>

        <section class="dash-card dash-card--table">
          <div class="dash-card__head dash-card__head--table">
            <h3>Project registry</h3>
            <span class="dash-card__meta">{{ filteredProjects.length }} matching</span>
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
      </div>
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
import DashboardLineChart from '../components/dashboard/DashboardLineChart.vue'
import DashboardBarChart from '../components/dashboard/DashboardBarChart.vue'
import { regions } from '../data/regionAreaMapping.js'
import {
  buildMigrationMilestones,
  countCompletedMilestones,
  formatStatusLabel,
  migrationMilestoneTotal,
  overallProgress
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
const exporting = ref(false)
const breakdownTab = ref('region')
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
const filterFunction = ref('')

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
    Boolean(filterMigrationType.value) ||
    Boolean(filterFunction.value)
)

const filteredProjects = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  return projects.value.filter((project) => {
    if (filterRegion.value && project.region !== filterRegion.value) return false
    if (filterStatus.value && project.status !== filterStatus.value) return false
    if (filterMigrationType.value && project.migrationType !== filterMigrationType.value) {
      return false
    }
    if (filterFunction.value && project.function !== filterFunction.value) {
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
    productsLabel:
      project.productsPreview ||
      (Array.isArray(project.products) && project.products.length
        ? project.products.join(', ')
        : '—'),
    areasLabel:
      project.areasPreview ||
      (project.areasCount ? `${formatWholeNumber(project.areasCount)} areas` : '—'),
    fteNumber: project.fteNumber,
    requestor: project.requestor,
    requestedDate: project.requestedDate,
    progress: overallProgress(project.status),
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

const statusCompositionItems = computed(() => {
  const total = displayedSummary.value.totalProjects || 0
  return statusEntries.value.map((entry) => ({
    ...entry,
    label: formatStatusLabel(entry.status),
    pct: total ? Math.round((entry.count / total) * 100) : 0
  }))
})

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

const functionEntries = computed(() => {
  const byFunction = {}
  for (const project of filteredProjects.value) {
    const fte = Number.parseInt(project.fteNumber, 10)
    const safeFte = Number.isNaN(fte) ? 0 : fte
    const name = String(project.function ?? '').trim()
    if (!name) continue
    if (!byFunction[name]) byFunction[name] = { count: 0, fte: 0 }
    byFunction[name].count += 1
    byFunction[name].fte += safeFte
  }

  return sortCountEntries(
    Object.entries(byFunction).map(([functionName, value]) => ({
      functionName,
      count: value.count,
      fte: value.fte
    })),
    'functionName'
  )
})

const completedCount = computed(() => getBucketCount(displayedSummary.value.byStatus, 'completed'))
const atRiskCount = computed(() => getBucketCount(displayedSummary.value.byStatus, 'at_risk'))
const averageFtePerProject = computed(() =>
  displayedSummary.value.totalProjects
    ? displayedSummary.value.totalFte / displayedSummary.value.totalProjects
    : 0
)

const inFlightStatuses = ['in_review', 'planning', 'in_progress', 'at_risk']
const activeDeliveryStatuses = ['in_review', 'planning', 'in_progress']

const inFlightCount = computed(() =>
  statusEntries.value
    .filter((item) => inFlightStatuses.includes(item.status))
    .reduce((sum, item) => sum + item.count, 0)
)

const inFlightFte = computed(() =>
  statusEntries.value
    .filter((item) => inFlightStatuses.includes(item.status))
    .reduce((sum, item) => sum + item.fte, 0)
)

const heroMetricDescription =
  'Count of migration intake requests in the current filter selection.'

const intakeTrendBadgeDescription =
  'Month-over-month change in new intake volume (project count submitted in the latest month vs. the prior month).'

const statusCompositionDescription =
  'Portfolio split by lifecycle status. Click a segment or label to filter the dashboard.'

const metricCards = computed(() => [
  {
    key: 'fte',
    label: 'Total FTE',
    description: 'Sum of full-time equivalent (FTE) headcount across all selected projects.',
    value: formatWholeNumber(displayedSummary.value.totalFte),
    unit: 'FTE',
    chips: [
      {
        value: formatDecimalNumber(averageFtePerProject.value),
        label: 'avg / project',
        tone: 'muted'
      }
    ],
    shortHint: `${formatDecimalNumber(averageFtePerProject.value)} avg / project`,
    hint: `${formatDecimalNumber(averageFtePerProject.value)} avg / project`,
    accent: '#0077B8'
  },
  {
    key: 'in-flight',
    label: 'In flight',
    description:
      'Projects actively moving through review, planning, in progress, or flagged at risk.',
    value: formatWholeNumber(inFlightCount.value),
    unit: 'projects',
    chips: [
      {
        value: formatWholeNumber(inFlightFte.value),
        label: 'FTE',
        tone: 'fte'
      }
    ],
    shortHint: `${formatWholeNumber(inFlightFte.value)} FTE`,
    hint: `${formatWholeNumber(inFlightFte.value)} FTE · review through delivery`,
    accent: '#42B0D5'
  },
  {
    key: 'completed',
    label: 'Completed',
    description: 'Projects that have reached completed status in the current selection.',
    value: formatWholeNumber(completedCount.value),
    unit: 'projects',
    chips: [
      {
        value: `${displayedSummary.value.totalProjects ? Math.round((completedCount.value / displayedSummary.value.totalProjects) * 100) : 0}%`,
        label: 'of portfolio',
        tone: 'success'
      }
    ],
    shortHint: `${displayedSummary.value.totalProjects ? Math.round((completedCount.value / displayedSummary.value.totalProjects) * 100) : 0}% of portfolio`,
    hint: `${displayedSummary.value.totalProjects ? Math.round((completedCount.value / displayedSummary.value.totalProjects) * 100) : 0}% of portfolio`,
    accent: '#6DAA28'
  },
  {
    key: 'at-risk',
    label: 'At risk',
    description: 'Projects with an at-risk status that may need escalation or recovery actions.',
    value: formatWholeNumber(atRiskCount.value),
    unit: 'projects',
    chips: [
      {
        label: atRiskCount.value ? 'Needs attention' : 'None flagged',
        tone: atRiskCount.value ? 'danger' : 'muted'
      }
    ],
    shortHint: atRiskCount.value ? 'Needs attention' : 'None flagged',
    hint: atRiskCount.value ? 'Needs attention' : 'No active risk flags',
    accent: atRiskCount.value ? '#E85454' : '#94A3B8'
  }
])

const regionPalette = ['#0077b8', '#13b0a5', '#6daa28', '#f3b562', '#7b61ff', '#e85454']
const productPalette = ['#0b8dbf', '#6daa28', '#f3b562', '#7b61ff', '#13b0a5', '#e85454']
const functionPalette = ['#003f6e', '#f3880e', '#42b0d5', '#6daa28', '#7b61ff', '#e85454']

const shortenLabel = (label, max = 10) => {
  const text = String(label || '').trim()
  if (text.length <= max) return text
  return `${text.slice(0, max - 1)}…`
}

const buildBarItems = (entries, labelFor, colorFor, keyFor, limit = 6) => {
  if (!entries.length) return []

  const top = entries.slice(0, limit)
  const rest = entries.slice(limit)
  const items = top.map((entry, index) => ({
    key: keyFor(entry),
    label: labelFor(entry),
    shortLabel: shortenLabel(labelFor(entry)),
    value: entry.count,
    color: colorFor(entry, index),
    muted: false
  }))

  if (rest.length) {
    items.push({
      key: 'others',
      label: `+${rest.length} more`,
      shortLabel: 'Others',
      value: rest.reduce((sum, entry) => sum + entry.count, 0),
      color: '#cbd5e1',
      muted: true
    })
  }

  return items
}

const regionBarItems = computed(() =>
  buildBarItems(
    regionEntries.value,
    (entry) => entry.region,
    (_entry, index) => regionPalette[index % regionPalette.length],
    (entry) => entry.region
  )
)

const migrationTypeBarItems = computed(() =>
  buildBarItems(
    migrationTypeEntries.value,
    (entry) => entry.migrationType,
    (_entry, index) => productPalette[index % productPalette.length],
    (entry) => entry.migrationType
  )
)

const productBarItems = computed(() =>
  buildBarItems(
    productEntries.value,
    (entry) => entry.product,
    (_entry, index) => productPalette[index % productPalette.length],
    (entry) => entry.product
  )
)

const functionBarItems = computed(() =>
  buildBarItems(
    functionEntries.value,
    (entry) => entry.functionName,
    (_entry, index) => functionPalette[index % functionPalette.length],
    (entry) => entry.functionName
  )
)

const activeBreakdownBarItems = computed(() => {
  switch (breakdownTab.value) {
    case 'migrationType':
      return migrationTypeBarItems.value
    case 'product':
      return productBarItems.value
    case 'function':
      return functionBarItems.value
    default:
      return regionBarItems.value
  }
})

const breakdownTabs = [
  { id: 'region', label: 'Region' },
  { id: 'migrationType', label: 'Migration type' },
  { id: 'product', label: 'Product' },
  { id: 'function', label: 'Function' }
]

const activeBreakdownFilterKey = computed(() => {
  switch (breakdownTab.value) {
    case 'migrationType':
      return filterMigrationType.value
    case 'function':
      return filterFunction.value
    default:
      return breakdownTab.value === 'region' ? filterRegion.value : ''
  }
})

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
    recentMonths.value.map((month) => [
      month.key,
      { count: 0, fte: 0, inFlight: 0, completed: 0, atRisk: 0 }
    ])
  )

  for (const project of filteredProjects.value) {
    const date = projectTrendDate(project)
    if (!date || Number.isNaN(date.getTime())) continue
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
    if (!buckets[key]) continue
    const fte = Number.parseInt(project.fteNumber, 10)
    const safeFte = Number.isNaN(fte) ? 0 : fte

    buckets[key].count += 1
    buckets[key].fte += safeFte
    if (activeDeliveryStatuses.includes(project.status)) buckets[key].inFlight += 1
    if (project.status === 'completed') buckets[key].completed += 1
    if (project.status === 'at_risk') buckets[key].atRisk += 1
  }

  return recentMonths.value.map((month) => ({
    ...month,
    count: buckets[month.key]?.count ?? 0,
    fte: buckets[month.key]?.fte ?? 0,
    inFlight: buckets[month.key]?.inFlight ?? 0,
    completed: buckets[month.key]?.completed ?? 0,
    atRisk: buckets[month.key]?.atRisk ?? 0
  }))
})

const intakeTrendBadge = computed(() => {
  const values = intakeTrend.value.map((month) => month.count)
  const latest = values[values.length - 1] ?? 0
  const previous = values[values.length - 2] ?? 0
  if (latest === previous) return { direction: 'flat', label: 'Flat MoM' }
  const direction = latest > previous ? 'up' : 'down'
  const pct = previous > 0 ? Math.abs(((latest - previous) / previous) * 100) : null
  const label =
    pct === null
      ? `${latest > previous ? '+' : '-'}${formatWholeNumber(Math.abs(latest - previous))}`
      : `${latest > previous ? '+' : '-'}${pct.toFixed(1)}%`
  return { direction, label }
})

const trendSeries = computed(() => [
  {
    key: 'count',
    label: 'New intake',
    color: '#161616',
    yAxis: 'left',
    values: intakeTrend.value.map((month) => month.count)
  },
  {
    key: 'inFlight',
    label: 'In flight',
    color: '#0077b8',
    yAxis: 'left',
    values: intakeTrend.value.map((month) => month.inFlight)
  },
  {
    key: 'completed',
    label: 'Completed',
    color: '#6daa28',
    yAxis: 'left',
    values: intakeTrend.value.map((month) => month.completed)
  },
  {
    key: 'atRisk',
    label: 'At risk',
    color: '#e85454',
    yAxis: 'left',
    values: intakeTrend.value.map((month) => month.atRisk)
  },
  {
    key: 'fte',
    label: 'FTE',
    color: '#b8d96e',
    yAxis: 'right',
    values: intakeTrend.value.map((month) => month.fte)
  }
])

const trendSeriesGuides = [
  {
    key: 'count',
    label: 'New intake',
    color: '#161616',
    description: 'Projects submitted in each month (intake volume).'
  },
  {
    key: 'inFlight',
    label: 'In flight',
    color: '#0077b8',
    description: 'That month’s intake still in review, planning, or in progress.'
  },
  {
    key: 'completed',
    label: 'Completed',
    color: '#6daa28',
    description: 'That month’s intake that has already reached completed.'
  },
  {
    key: 'atRisk',
    label: 'At risk',
    color: '#e85454',
    description: 'That month’s intake currently flagged at risk.'
  },
  {
    key: 'fte',
    label: 'FTE',
    color: '#b8d96e',
    description: 'Total FTE attached to that month’s new intake (right axis).'
  }
]

const trendLabels = computed(() => intakeTrend.value.map((month) => month.label))

const trendHeadline = computed(() => {
  const latest = intakeTrend.value[intakeTrend.value.length - 1]
  const previous = intakeTrend.value[intakeTrend.value.length - 2]
  if (!latest) return 'No trend data in the current selection.'

  const latestIntake = latest.count ?? 0
  const prevIntake = previous?.count ?? latestIntake
  const intakeDelta = latestIntake - prevIntake

  const intakePart =
    intakeDelta === 0
      ? 'intake flat'
      : `intake ${intakeDelta > 0 ? 'up' : 'down'} ${formatWholeNumber(Math.abs(intakeDelta))}`

  return `Latest month vs prior: ${intakePart}. ${formatWholeNumber(latest.inFlight)} in flight, ${formatWholeNumber(latest.completed)} completed, ${formatWholeNumber(latest.atRisk)} at risk, ${formatWholeNumber(latest.fte)} FTE.`
})

const topRegion = computed(() => regionEntries.value[0] ?? null)

const topMigrationType = computed(() => migrationTypeEntries.value[0] ?? null)

const averageAreaCount = computed(() =>
  filteredProjects.value.length
    ? filteredProjects.value.reduce(
        (sum, project) => sum + (Number(project.areasCount) || 0),
        0
      ) / filteredProjects.value.length
    : 0
)

const averageCountryCount = computed(() =>
  filteredProjects.value.length
    ? filteredProjects.value.reduce(
        (sum, project) => sum + (Number(project.countriesCount) || 0),
        0
      ) / filteredProjects.value.length
    : 0
)

const portfolioInsights = computed(() => [
  {
    label: 'Primary focus region',
    badge: 'Region',
    tone: 'region',
    value: topRegion.value?.region || '—',
    description: 'Region with the highest project volume in the current selection.',
    chips: topRegion.value
      ? [
          {
            value: formatWholeNumber(topRegion.value.count),
            label: 'projects'
          },
          {
            value: formatWholeNumber(topRegion.value.fte),
            label: 'FTE',
            tone: 'fte'
          }
        ]
      : [{ label: 'No regional distribution yet.', tone: 'muted' }]
  },
  {
    label: 'Leading migration type',
    badge: 'Type',
    tone: 'type',
    value: topMigrationType.value?.migrationType || '—',
    description: 'Most common migration type among filtered projects.',
    chips: topMigrationType.value
      ? [
          {
            value: formatWholeNumber(topMigrationType.value.count),
            label: 'projects'
          }
        ]
      : [{ label: 'No migration type mix available.', tone: 'muted' }]
  },
  {
    label: 'Delivery posture',
    badge: 'Status',
    tone: 'delivery',
    value: `${formatWholeNumber(inFlightCount.value)} in flight`,
    description: 'Active delivery load versus completed and risk outcomes.',
    chips: [
      {
        value: formatWholeNumber(atRiskCount.value),
        label: 'at risk',
        tone: atRiskCount.value ? 'danger' : 'muted'
      },
      {
        value: formatWholeNumber(completedCount.value),
        label: 'completed',
        tone: 'success'
      }
    ]
  },
  {
    label: 'Average scope footprint',
    badge: 'Scope',
    tone: 'scope',
    value: `${formatDecimalNumber(averageAreaCount.value)} areas`,
    description: 'Typical geographic footprint per project.',
    chips: [
      {
        value: formatDecimalNumber(averageCountryCount.value),
        label: 'countries avg',
        tone: 'muted'
      }
    ]
  }
])

const topProductItems = computed(() => productEntries.value.slice(0, 3))

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
  filterFunction.value = ''
}

const onStatusChartSelect = (status) => {
  if (!status || status === '_others') return
  filterStatus.value = filterStatus.value === status ? '' : status
}

const onRegionChartSelect = (region) => {
  filterRegion.value = filterRegion.value === region ? '' : region
}

const onMigrationTypeChartSelect = (type) => {
  filterMigrationType.value = filterMigrationType.value === type ? '' : type
}

const onFunctionChartSelect = (name) => {
  filterFunction.value = filterFunction.value === name ? '' : name
}

const onBreakdownSelect = (key) => {
  if (!key || key === 'others') return
  if (breakdownTab.value === 'product') return
  if (breakdownTab.value === 'migrationType') {
    onMigrationTypeChartSelect(key)
    return
  }
  if (breakdownTab.value === 'function') {
    onFunctionChartSelect(key)
    return
  }
  onRegionChartSelect(key)
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
      { metric: 'Function', value: filterFunction.value || 'All' },
      { metric: 'Total projects', value: displayedSummary.value.totalProjects },
      { metric: 'Total FTE', value: displayedSummary.value.totalFte },
      { metric: 'In flight', value: inFlightCount.value },
      { metric: 'In flight FTE', value: inFlightFte.value },
      { metric: 'Completed', value: completedCount.value },
      { metric: 'At risk', value: atRiskCount.value },
      { metric: 'Avg. FTE / project', value: formatDecimalNumber(averageFtePerProject.value) },
      { metric: 'Regions in scope', value: regionEntries.value.length },
      { metric: 'Primary region', value: topRegion.value?.region || 'N/A' },
      { metric: 'Leading migration type', value: topMigrationType.value?.migrationType || 'N/A' }
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
      })),
      ...functionEntries.value.map((item) => ({
        category: 'Function',
        item: item.functionName,
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
  return current?.label ?? milestones[0]?.label ?? 'Unknown'
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
.dashboard-canvas {
  --dash-accent: #42b0d5;
  --dash-primary: #0077b8;
  --dash-deep: #003f6e;
  --dash-success: #6daa28;
  --dash-border: rgba(22, 22, 22, 0.08);
  --dash-shadow: 0 2px 3px rgba(15, 23, 42, 0.05), 0 10px 22px rgba(0, 63, 110, 0.08);
  --metric-accent: var(--dash-accent);
}

.dashboard-layout {
  display: grid;
  gap: 24px;
}

.dashboard-main {
  align-items: start;
  display: grid;
  gap: 24px;
  grid-template-columns: minmax(260px, 300px) minmax(0, 1fr);
}

.dashboard-main__charts {
  display: grid;
  gap: 24px;
  min-width: 0;
}

.dash-card--insights {
  gap: 16px;
  padding-bottom: 20px;
  position: relative;
}

.dash-card--insights::before {
  background: linear-gradient(90deg, #42b0d5 0%, #0077b8 55%, #003f6e 100%);
  border-radius: 16px 16px 0 0;
  content: '';
  height: 3px;
  left: 0;
  position: absolute;
  right: 0;
  top: 0;
}

.insights-panel__head {
  display: grid;
  gap: 4px;
}

.insights-panel__title-row {
  align-items: center;
  display: flex;
  gap: 8px;
}

.insights-panel__accent {
  background: #0077b8;
  border-radius: 999px;
  flex-shrink: 0;
  height: 14px;
  width: 4px;
}

.insights-panel__head h3 {
  color: #161616;
  font-family: 'Maersk Headline', 'Maersk Text', sans-serif;
  font-size: 16px;
  font-weight: 700;
  margin: 0;
}

.insights-panel__head p {
  color: #6c757d;
  font-size: 13px;
  line-height: 1.45;
  margin: 0;
}

.insight-list {
  display: grid;
  gap: 10px;
}

.insight-item {
  background: linear-gradient(180deg, #fff 0%, #fafbfd 100%);
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-left: 3px solid #94a3b8;
  border-radius: 12px;
  display: grid;
  gap: 6px;
  padding: 12px 12px 12px 14px;
}

.insight-item--region {
  border-left-color: #0077b8;
}

.insight-item--type {
  border-left-color: #42b0d5;
}

.insight-item--delivery {
  border-left-color: #f3880e;
}

.insight-item--scope {
  border-left-color: #6daa28;
}

.insight-item__top {
  align-items: center;
  display: flex;
  gap: 8px;
  justify-content: space-between;
}

.insight-item__label {
  color: #6c757d;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.insight-item__badge {
  background: rgba(0, 119, 184, 0.08);
  border-radius: 999px;
  color: #0077b8;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
}

.insight-item--type .insight-item__badge {
  background: rgba(66, 176, 213, 0.12);
  color: #0b7ea4;
}

.insight-item--delivery .insight-item__badge {
  background: rgba(243, 136, 14, 0.12);
  color: #c56d0a;
}

.insight-item--scope .insight-item__badge {
  background: rgba(109, 170, 40, 0.12);
  color: #4d7a1c;
}

.insight-item__value {
  color: #161616;
  font-size: 16px;
  font-weight: 700;
  line-height: 1.25;
}

.insight-item__desc {
  color: #94a3b8;
  font-size: 11px;
  line-height: 1.4;
  margin: 0;
}

.leaderboard {
  border-top: 1px solid rgba(22, 22, 22, 0.08);
  display: grid;
  gap: 10px;
  padding-top: 14px;
}

.leaderboard__head {
  align-items: center;
  display: flex;
  justify-content: space-between;
}

.leaderboard__head h4 {
  color: #161616;
  font-size: 13px;
  font-weight: 700;
  margin: 0;
}

.leaderboard__list {
  display: grid;
  gap: 8px;
}

.leaderboard__item {
  align-items: flex-start;
  background: #fff;
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 12px;
  display: grid;
  gap: 10px;
  grid-template-columns: auto minmax(0, 1fr);
  padding: 10px 12px;
}

.leaderboard__rank {
  align-items: center;
  background: linear-gradient(180deg, #e8f4fa 0%, #d7ecf6 100%);
  border-radius: 8px;
  color: #0077b8;
  display: inline-flex;
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 700;
  height: 24px;
  justify-content: center;
  width: 24px;
}

.leaderboard__item:nth-child(1) .leaderboard__rank {
  background: linear-gradient(180deg, #fff4e5 0%, #ffe7c7 100%);
  color: #c56d0a;
}

.leaderboard__item:nth-child(2) .leaderboard__rank {
  background: linear-gradient(180deg, #f1f5f9 0%, #e2e8f0 100%);
  color: #475569;
}

.leaderboard__item:nth-child(3) .leaderboard__rank {
  background: linear-gradient(180deg, #f3ebe3 0%, #e8d9cb 100%);
  color: #8a5a2b;
}

.leaderboard__copy {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.leaderboard__copy strong {
  color: #161616;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.metric-chip-row {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.metric-chip {
  align-items: center;
  background: rgba(22, 22, 22, 0.04);
  border-radius: 999px;
  color: #64748b;
  display: inline-flex;
  font-size: 11px;
  font-weight: 500;
  gap: 4px;
  line-height: 1;
  padding: 4px 8px;
}

.metric-chip em {
  color: #161616;
  font-style: normal;
  font-weight: 700;
}

.metric-chip--unit {
  background: transparent;
  color: #94a3b8;
  font-weight: 600;
  padding-left: 0;
}

.metric-chip--fte {
  background: rgba(184, 217, 110, 0.22);
  color: #5f7a28;
}

.metric-chip--fte em {
  color: #3f5a12;
}

.metric-chip--success {
  background: rgba(109, 170, 40, 0.14);
  color: #4d7a1c;
}

.metric-chip--success em {
  color: #3d6a12;
}

.metric-chip--danger {
  background: rgba(232, 84, 84, 0.12);
  color: #b42318;
}

.metric-chip--danger em {
  color: #9f1d14;
}

.metric-chip--muted {
  background: rgba(148, 163, 184, 0.14);
  color: #64748b;
}

.metric-chip--muted em {
  color: #475569;
}

.dash-toolbar {
  align-items: center;
  background: #fff;
  border: 1px solid var(--dash-border);
  border-radius: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: space-between;
  padding: 14px 16px;
}

.dash-toolbar__filters {
  align-items: center;
  display: grid;
  gap: 10px;
  grid-template-columns: minmax(180px, 1.4fr) repeat(3, minmax(120px, 0.8fr));
  min-width: min(100%, 760px);
}

.dash-toolbar__actions {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.overview-panel {
  background: #fff;
  border: 1px solid var(--dash-border);
  border-radius: 16px;
  box-shadow: var(--dash-shadow);
  display: grid;
  gap: 20px;
  padding: 22px 24px;
}

.overview-panel__metrics {
  align-items: stretch;
  display: grid;
  gap: 20px;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 1.4fr);
}

.overview-panel__hero {
  border-right: 1px solid rgba(22, 22, 22, 0.06);
  display: grid;
  gap: 8px;
  padding-right: 20px;
}

.overview-panel__label {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.overview-panel__metric-desc {
  color: #94a3b8;
  font-size: 11px;
  line-height: 1.4;
  margin: 0;
}

.overview-panel__hero-row {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.overview-panel__hero-value {
  color: var(--dash-deep);
  font-size: clamp(36px, 4vw, 48px);
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1;
}

.overview-panel__badge {
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  padding: 5px 11px;
}

.overview-panel__badge--up {
  background: color-mix(in srgb, var(--dash-success) 16%, white);
  color: #3d6a12;
}

.overview-panel__badge--down {
  background: color-mix(in srgb, #e85454 12%, white);
  color: #b42318;
}

.overview-panel__badge--flat {
  background: rgba(22, 22, 22, 0.06);
  color: #6c757d;
}

.overview-panel__hero-hint {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 13px;
  line-height: 1.5;
  margin: 0;
}

.overview-panel__stats {
  display: grid;
  gap: 12px 20px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.overview-panel__stat {
  display: grid;
  gap: 4px;
}

.overview-panel__stat-row {
  align-items: baseline;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.overview-panel__stat-value {
  color: #161616;
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1;
}

.overview-panel__stat-hint {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 12px;
  line-height: 1.4;
}

.overview-panel__composition {
  border-top: 1px solid rgba(22, 22, 22, 0.06);
  display: grid;
  gap: 10px;
  padding-top: 18px;
}

.overview-panel__composition-head {
  align-items: flex-start;
  display: flex;
  gap: 12px;
  justify-content: space-between;
}

.overview-panel__composition-desc {
  color: #94a3b8;
  flex: 1;
  font-size: 11px;
  line-height: 1.4;
  margin: 0;
}

.composition-bar__track {
  background: #eef2f6;
  border-radius: 999px;
  display: flex;
  height: 8px;
  overflow: hidden;
}

.composition-bar__segment {
  border: 0;
  cursor: pointer;
  min-width: 3px;
  padding: 0;
  transition: filter 0.18s ease;
}

.composition-bar__segment:hover {
  filter: brightness(1.06);
}

.composition-bar__segment--active {
  box-shadow: inset 0 0 0 2px rgba(0, 63, 110, 0.3);
}

.composition-bar__labels--inline {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
}

.composition-bar__label {
  align-items: center;
  background: transparent;
  border: 0;
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  cursor: pointer;
  display: inline-flex;
  font-size: 11px;
  gap: 5px;
  padding: 0;
}

.composition-bar__label:hover,
.composition-bar__label--active {
  color: #161616;
}

.composition-bar__label strong {
  color: #161616;
  font-size: 11px;
  font-weight: 700;
}

.composition-bar__dot {
  border-radius: 999px;
  flex-shrink: 0;
  height: 7px;
  width: 7px;
}

.composition-bar__name {
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dash-card {
  background: #fff;
  border: 1px solid var(--dash-border);
  border-radius: 16px;
  box-shadow: var(--dash-shadow);
  display: grid;
  gap: 16px;
  padding: 20px 24px;
}

.dash-card--breakdown {
  padding-bottom: 22px;
}

.dash-card--analytics {
  gap: 8px;
  padding: 20px 24px 18px;
}

.dash-card--trend {
  gap: 10px;
  min-height: 0;
  padding-bottom: 18px;
}

.dash-card--table {
  padding-bottom: 16px;
}

.dash-card__head {
  align-items: center;
  display: flex;
  gap: 12px;
  justify-content: space-between;
}

.dash-card__head--tabs {
  flex-wrap: wrap;
}

.dash-card__head--table {
  margin-bottom: 2px;
}

.dash-card__head h3 {
  color: #161616;
  font-family: 'Maersk Headline', 'Maersk Text', sans-serif;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.01em;
  margin: 0;
}

.dash-card__meta {
  background: #f4f6f8;
  border-radius: 999px;
  color: #6c757d;
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 600;
  padding: 5px 10px;
  white-space: nowrap;
}

.segmented-tabs {
  background: #f1f5f9;
  border-radius: 999px;
  display: inline-flex;
  flex-wrap: wrap;
  gap: 2px;
  padding: 3px;
}

.segmented-tabs__btn {
  background: transparent;
  border: 0;
  border-radius: 999px;
  color: #6c757d;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  padding: 7px 14px;
  transition: background 0.18s ease, color 0.18s ease, box-shadow 0.18s ease;
  white-space: nowrap;
}

.segmented-tabs__btn--active {
  background: #fff;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
  color: #0077b8;
}

.trend-caption {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 12px;
  line-height: 1.45;
  margin: 0;
}

.trend-guide {
  background: #f8fafc;
  border: 1px solid rgba(22, 22, 22, 0.06);
  border-radius: 12px;
  display: grid;
  gap: 10px;
  padding: 12px 14px;
}

.trend-guide__intro {
  color: #64748b;
  font-size: 11px;
  line-height: 1.45;
  margin: 0;
}

.trend-guide__list {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.trend-guide__item {
  align-items: flex-start;
  display: flex;
  gap: 8px;
}

.trend-guide__dot {
  border-radius: 999px;
  flex-shrink: 0;
  height: 8px;
  margin-top: 4px;
  width: 8px;
}

.trend-guide__item strong {
  color: #161616;
  display: block;
  font-size: 11px;
  font-weight: 700;
  margin-bottom: 2px;
}

.trend-guide__item span {
  color: #6c757d;
  font-size: 11px;
  line-height: 1.4;
}

.summary-empty {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 13px;
  margin: 0;
  padding: 16px 0;
  text-align: center;
}

.table-shell {
  background: #fafbfd;
  border: 1px solid var(--dash-border);
  border-radius: 12px;
  overflow: hidden;
}

.loading-state {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 13px;
  padding: 20px 0;
  text-align: center;
}

.empty-filter-state {
  align-items: center;
  background: #fafbfd;
  border: 1.5px dashed rgba(22, 22, 22, 0.14);
  border-radius: 12px;
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 32px 14px;
  text-align: center;
}

.empty-filter-state p {
  font-size: 13px;
  line-height: 1.45;
  margin: 0;
  max-width: 420px;
}

@media (max-width: 1280px) {
  .dashboard-main {
    grid-template-columns: 1fr;
  }

  .overview-panel__metrics {
    grid-template-columns: 1fr;
  }

  .overview-panel__hero {
    border-bottom: 1px solid rgba(22, 22, 22, 0.06);
    border-right: 0;
    padding-bottom: 16px;
    padding-right: 0;
  }
}

@media (max-width: 960px) {
  .dash-toolbar__filters {
    grid-template-columns: 1fr;
    min-width: 0;
    width: 100%;
  }

  .dash-toolbar__actions {
    justify-content: flex-start;
    width: 100%;
  }

  .overview-panel__stats {
    grid-template-columns: 1fr;
  }

  .dash-card__head--tabs {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
