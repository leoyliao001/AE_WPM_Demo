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

    <div v-else class="dashboard-layout">
      <aside class="summary-panel">
        <div class="panel-head">
          <h2>Portfolio Summary</h2>
          <p>Aggregated view across all submitted migration requests.</p>
        </div>

        <div class="summary-cards">
          <div class="summary-stat">
            <span class="stat-label">Total projects</span>
            <strong class="stat-value">{{ summary.totalProjects }}</strong>
          </div>
          <div class="summary-stat">
            <span class="stat-label">Total FTE</span>
            <strong class="stat-value stat-value--accent">{{ summary.totalFte }}</strong>
          </div>
        </div>

        <div v-if="statusEntries.length" class="summary-group">
          <h3>By status</h3>
          <div class="chip-list">
            <mc-tag
              v-for="item in statusEntries"
              :key="item.status"
              :appearance="statusAppearance(item.status)"
              fit="small"
              :label="`${formatStatusLabel(item.status)} · ${item.count}`"
            />
          </div>
        </div>

        <div v-if="regionEntries.length" class="summary-group">
          <h3>By region</h3>
          <div class="chip-list">
            <mc-tag
              v-for="item in regionEntries"
              :key="item.region"
              appearance="neutral"
              fit="small"
              :label="`${item.region} · ${item.count}`"
            />
          </div>
        </div>
      </aside>

      <section class="table-panel">
        <div class="panel-head">
          <div class="panel-head-row">
            <div>
              <h2>Submitted Projects</h2>
              <p>Select a project to open its detail and progress view.</p>
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
        </div>

        <div v-if="loading" class="loading-state">Loading projects…</div>

        <div v-else class="table-wrap">
          <mc-table
            :data.prop="tableRows"
            :columns.prop="tableColumns"
            datakey="id"
            caption="Submitted migration projects overview"
            fit="medium"
            height="auto"
            outerborderstyle="solid"
            horizontallinestyle="solid"
          />
        </div>

        <div v-if="!loading" class="project-cards">
          <mc-card
            v-for="project in projects"
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
import {
  formatStatusLabel,
  overallProgress,
  statusAppearance
} from '../utils/migrationDashboardProgress.js'
import '@maersk-global/mds-components-core/mc-card'
import '@maersk-global/mds-components-core/mc-table'
import '@maersk-global/mds-components-core/mc-tag'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-icon'
import '@maersk-global/mds-components-core/mc-notification'

const router = useRouter()
const loading = ref(true)
const loadError = ref('')
const projects = ref([])
const summary = ref({
  totalProjects: 0,
  totalFte: 0,
  byStatus: {},
  byRegion: {}
})

const tableColumns = [
  { id: 'migrationRequestId', label: 'Request ID', noWrap: true },
  { id: 'projectName', label: 'Project name', noWrap: true },
  { id: 'statusLabel', label: 'Status', noWrap: true },
  { id: 'region', label: 'Region', noWrap: true },
  { id: 'migrationType', label: 'Migration type', noWrap: true },
  { id: 'fteNumber', label: 'FTE', noWrap: true },
  { id: 'requestor', label: 'Requestor', noWrap: true },
  { id: 'requestedDate', label: 'Requested', noWrap: true },
  { id: 'progressLabel', label: 'Progress', noWrap: true }
]

const tableRows = computed(() =>
  projects.value.map((project) => ({
    id: project.id,
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
  Object.entries(summary.value.byStatus ?? {}).map(([status, count]) => ({ status, count }))
)

const regionEntries = computed(() =>
  Object.entries(summary.value.byRegion ?? {}).map(([region, count]) => ({ region, count }))
)

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
.dashboard-layout {
  display: grid;
  gap: 24px;
  grid-template-columns: 300px minmax(0, 1fr);
}

.panel-head h2,
.summary-group h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 6px;
}

.summary-group h3 {
  font-size: 14px;
}

.panel-head p {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 13px;
  line-height: 1.5;
  margin: 0 0 16px;
}

.panel-head-row {
  align-items: flex-start;
  display: flex;
  gap: 16px;
  justify-content: space-between;
}

.summary-panel,
.table-panel {
  background: #fff;
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(22, 22, 22, 0.04);
  padding: 22px 20px;
}

.summary-cards {
  display: grid;
  gap: 12px;
  margin-bottom: 20px;
}

.summary-stat {
  background: rgba(0, 119, 184, 0.06);
  border-radius: 12px;
  padding: 14px 16px;
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

.summary-group {
  margin-top: 18px;
}

.chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.table-wrap {
  margin-bottom: 20px;
  overflow-x: auto;
}

.loading-state {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 14px;
  padding: 24px 0;
}

.project-cards {
  display: flex;
  flex-direction: column;
  gap: 14px;
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

@media (max-width: 960px) {
  .dashboard-layout {
    grid-template-columns: 1fr;
  }

  .panel-head-row {
    flex-direction: column;
  }
}
</style>
