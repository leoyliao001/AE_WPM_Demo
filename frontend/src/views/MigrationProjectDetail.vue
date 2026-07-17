<template>
  <PageShell
    :title="project?.projectName ?? 'Project Detail'"
    :subtitle="detailSubtitle"
    tag="Migration Project"
    back-to="/migration-dashboard"
    back-label="Back to Migration Dashboard"
  >
    <mc-notification
      v-if="loadError"
      appearance="error"
      fit="medium"
      heading="Unable to load project"
      :body="loadError"
    />

    <div v-else-if="loading" class="loading-state">Loading project details…</div>

    <template v-else-if="project">
      <mc-card class="summary-card" variant="bordered" fit="medium" contentalignment="left">
        <div class="summary-card__content">
          <div class="summary-header">
            <div class="summary-header__main">
              <p class="summary-region">{{ regionLabel }}</p>
              <div class="summary-title-row">
                <h2 class="summary-title">{{ project.projectName }}</h2>
                <div class="summary-tags">
                  <mc-tag appearance="neutral" fit="small" :label="`#${project.id}`" />
                  <mc-tag
                    :appearance="statusAppearance(project.status)"
                    fit="small"
                    :label="formatStatusLabel(project.status)"
                  />
                </div>
              </div>
              <p class="summary-meta">
                {{ project.migrationRequestId }} · {{ project.requestor }} ·
                {{ project.requestedDate }} · {{ project.migrationType }}
              </p>
            </div>

            <div class="summary-donut" :style="{ '--donut-pct': progressPct }">
              <div class="summary-donut__ring" aria-hidden="true" />
              <div class="summary-donut__label">
                <strong>{{ progressPct }}%</strong>
                <span>Complete</span>
              </div>
            </div>
          </div>

          <div class="milestone-stepper" role="list">
            <div
              v-for="(item, index) in migrationMilestones"
              :key="item.id"
              class="milestone-stepper__item"
              :class="`milestone-stepper__item--${item.state}`"
              role="listitem"
            >
              <div
                v-if="index > 0"
                class="milestone-stepper__connector"
                :class="{
                  'milestone-stepper__connector--complete':
                    item.state === 'complete' || item.state === 'active'
                }"
              />
              <div class="milestone-stepper__node">
                <mc-icon
                  v-if="item.state === 'complete'"
                  icon="mi-check"
                  size="14"
                />
                <mc-icon
                  v-else-if="item.state === 'at_risk'"
                  icon="mi-exclamation-triangle"
                  size="14"
                />
                <mc-icon v-else :icon="item.icon" size="14" />
              </div>
              <span class="milestone-stepper__label">{{ item.shortLabel }}</span>
            </div>
          </div>

          <div class="summary-stats">
            <div class="summary-stat">
              <span class="summary-stat__label">Est. FTE saving</span>
              <strong class="summary-stat__value">{{ estimatedFteSaving }}</strong>
            </div>
            <div class="summary-stat">
              <span class="summary-stat__label">Final FTE</span>
              <strong class="summary-stat__value">{{ project.fteNumber || '—' }}</strong>
            </div>
            <div class="summary-stat summary-stat--progress">
              <span class="summary-stat__label">Stages complete</span>
              <div class="summary-stat__progress-row">
                <strong class="summary-stat__value summary-stat__value--accent">
                  {{ completedStages }}/{{ migrationMilestoneTotal }}
                </strong>
                <div class="summary-stat__track">
                  <div
                    class="summary-stat__fill"
                    :style="{ width: `${stageProgressPct}%` }"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </mc-card>

      <section class="progress-panel">
        <div class="panel-head">
          <h2>Migration Progress</h2>
          <p>Select a milestone to review status and next actions for this project.</p>
        </div>

        <div class="milestone-grid">
          <mc-card
            v-for="item in migrationMilestones"
            :key="item.id"
            class="milestone-card"
            :class="`milestone-card--${item.state}`"
            variant="bordered"
            fit="medium"
            contentalignment="middle"
            clickable
            :heading="item.label"
            :body="milestoneCardBody(item)"
            @click="onMilestoneClick(item)"
          >
            <div slot="image" class="milestone-card__icon">
              <span class="milestone-card__icon-wrap">
                <mc-icon :icon="item.icon" size="24" />
              </span>
            </div>

            <div slot="actions" class="milestone-card__actions">
              <mc-tag
                :appearance="item.tagAppearance"
                fit="small"
                :label="item.statusLabel"
              />
              <mc-button
                appearance="neutral"
                variant="plain"
                fit="small"
                label="View"
                trailingicon="mi-arrow-right"
                tabindex="-1"
              />
            </div>
          </mc-card>
        </div>
      </section>

      <section
        v-for="section in detailSections"
        :key="section.id"
        class="detail-section"
        :style="{ '--section-accent': section.accent }"
      >
        <div class="section-head">
          <span class="section-icon">
            <mc-icon :icon="section.icon" size="24" />
          </span>
          <h2>{{ section.title }}</h2>
        </div>

        <dl class="detail-grid">
          <div
            v-for="item in section.items"
            :key="item.label"
            class="detail-item"
            :class="{ 'detail-item--multiline': item.multiline }"
          >
            <dt>{{ item.label }}</dt>
            <dd>{{ item.value }}</dd>
          </div>
        </dl>
      </section>
    </template>
  </PageShell>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'
import {
  buildDetailSections,
  buildMigrationMilestones,
  countCompletedMilestones,
  formatStatusLabel,
  migrationMilestoneTotal,
  overallProgress,
  statusAppearance
} from '../utils/migrationDashboardProgress.js'
import '@maersk-global/mds-components-core/mc-card'
import '@maersk-global/mds-components-core/mc-tag'
import '@maersk-global/mds-components-core/mc-icon'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-notification'

const REGION_LABELS = {
  APA: 'Asia Pacific region',
  EUR: 'Europe region',
  IMEA: 'IMEA region',
  LAM: 'Latin America region',
  NAM: 'North America region'
}

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const loadError = ref('')
const project = ref(null)

const progressPct = computed(() => overallProgress(project.value?.status))
const migrationMilestones = computed(() =>
  buildMigrationMilestones(project.value?.status ?? 'new')
)
const detailSections = computed(() =>
  project.value ? buildDetailSections(project.value) : []
)

const regionLabel = computed(() => {
  const region = project.value?.region ?? ''
  return (REGION_LABELS[region] ?? `${region} region`).toUpperCase()
})

const completedStages = computed(() =>
  countCompletedMilestones(project.value?.status ?? 'new')
)

const stageProgressPct = computed(() =>
  Math.round((completedStages.value / migrationMilestoneTotal) * 100)
)

const estimatedFteSaving = computed(() => {
  const fte = Number.parseInt(project.value?.fteNumber ?? '', 10)
  if (!Number.isFinite(fte) || fte <= 0) return 'N/A'
  return String(Math.max(1, Math.round(fte * 0.18)))
})

const detailSubtitle = computed(() => {
  if (project.value) {
    return `${project.value.migrationRequestId} — detailed intake data and migration progress.`
  }
  return 'Detailed intake data and migration progress.'
})

const milestoneCardBody = (item) => {
  if (item.state === 'complete') return 'Milestone completed for this project.'
  if (item.state === 'active') return 'Currently up to date — review artifacts and owners.'
  if (item.state === 'at_risk') return 'Needs attention — review blockers and recovery plan.'
  return 'Not started yet — will unlock after prior stages.'
}

const onMilestoneClick = (item) => {
  if (item.id === 'opportunity') {
    router.push(`/migration-dashboard/${route.params.id}/opportunity-assessment`)
    return
  }
  console.log('[Migration Project] Milestone selected', item.id)
}

const loadProject = async () => {
  loading.value = true
  loadError.value = ''
  project.value = null

  try {
    const { data } = await axios.get(`/api/migration-dashboard/projects/${route.params.id}/`)
    project.value = data
  } catch (error) {
    loadError.value =
      error?.response?.data?.error ?? 'Unable to load this project. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(loadProject)
watch(() => route.params.id, loadProject)
</script>

<style scoped>
.loading-state {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 14px;
  padding: 24px 0;
}

.summary-card {
  width: 100%;
}

.summary-card::part(container) {
  border-radius: 16px;
  overflow: hidden;
}

.summary-card__content {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.summary-header {
  align-items: flex-start;
  display: flex;
  gap: 20px;
  justify-content: space-between;
}

.summary-region {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  margin: 0 0 8px;
}

.summary-title-row {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 8px;
}

.summary-title {
  color: var(--mds_brand_appearance_neutral_default_text-color, #161616);
  font-size: 24px;
  font-weight: 700;
  line-height: 1.25;
  margin: 0;
}

.summary-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.summary-meta {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 13px;
  line-height: 1.5;
  margin: 0;
}

.summary-donut {
  --donut-pct: 0;
  flex-shrink: 0;
  height: 88px;
  position: relative;
  width: 88px;
}

.summary-donut__ring {
  background: conic-gradient(
    #0077b8 0deg,
    #42b0d5 calc(var(--donut-pct) * 3.6deg),
    #e8edf2 calc(var(--donut-pct) * 3.6deg)
  );
  border-radius: 50%;
  height: 100%;
  position: relative;
  width: 100%;
}

.summary-donut__ring::after {
  background: #fff;
  border-radius: 50%;
  content: '';
  height: 68px;
  left: 50%;
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 68px;
}

.summary-donut__label {
  align-items: center;
  display: flex;
  flex-direction: column;
  inset: 0;
  justify-content: center;
  position: absolute;
  text-align: center;
}

.summary-donut__label strong {
  color: #161616;
  font-size: 18px;
  line-height: 1.1;
}

.summary-donut__label span {
  color: #6c757d;
  font-size: 11px;
  margin-top: 2px;
}

.milestone-stepper {
  display: grid;
  gap: 0;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  overflow-x: auto;
  padding-bottom: 4px;
}

.milestone-stepper__item {
  align-items: center;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 72px;
  position: relative;
}

.milestone-stepper__connector {
  background: #d7dde3;
  height: 2px;
  left: calc(-50% + 16px);
  position: absolute;
  top: 15px;
  width: calc(100% - 32px);
  z-index: 0;
}

.milestone-stepper__connector--complete {
  background: #6daa28;
}

.milestone-stepper__node {
  align-items: center;
  background: #fff;
  border: 2px solid #d7dde3;
  border-radius: 999px;
  color: #6c757d;
  display: flex;
  height: 32px;
  justify-content: center;
  position: relative;
  width: 32px;
  z-index: 1;
}

.milestone-stepper__item--complete .milestone-stepper__node {
  background: #eef8e8;
  border-color: #6daa28;
  color: #6daa28;
}

.milestone-stepper__item--active .milestone-stepper__node {
  background: #0077b8;
  border-color: #0077b8;
  color: #fff;
  box-shadow: 0 0 0 4px rgba(0, 119, 184, 0.15);
}

.milestone-stepper__item--at_risk .milestone-stepper__node {
  background: #fff5f5;
  border-color: #e85454;
  color: #e85454;
}

.milestone-stepper__label {
  color: #6c757d;
  font-size: 11px;
  font-weight: 500;
  line-height: 1.3;
  text-align: center;
}

.milestone-stepper__item--complete .milestone-stepper__label {
  color: #5a9420;
}

.milestone-stepper__item--active .milestone-stepper__label {
  color: #0077b8;
  font-weight: 600;
}

.milestone-stepper__item--at_risk .milestone-stepper__label {
  color: #e85454;
  font-weight: 600;
}

.summary-stats {
  background: linear-gradient(135deg, rgba(0, 119, 184, 0.05) 0%, rgba(66, 176, 213, 0.04) 100%);
  border: 1px solid rgba(0, 119, 184, 0.1);
  border-radius: 12px;
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  padding: 16px 18px;
}

.summary-stat__label {
  color: #6c757d;
  display: block;
  font-size: 12px;
  margin-bottom: 6px;
}

.summary-stat__value {
  color: #161616;
  font-size: 22px;
  font-weight: 700;
  line-height: 1.1;
}

.summary-stat__value--accent {
  color: #0077b8;
}

.summary-stat__progress-row {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.summary-stat__track {
  background: #e2e8ee;
  border-radius: 999px;
  flex: 1;
  height: 6px;
  min-width: 80px;
  overflow: hidden;
}

.summary-stat__fill {
  background: linear-gradient(90deg, #0077b8, #42b0d5);
  border-radius: 999px;
  height: 100%;
}

.progress-panel,
.detail-section {
  background: #fff;
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(22, 22, 22, 0.04);
  padding: 22px 20px;
}

.detail-section {
  position: relative;
}

.detail-section::before {
  background: var(--section-accent, #0077b8);
  border-radius: 16px 16px 0 0;
  content: '';
  height: 3px;
  left: 0;
  position: absolute;
  right: 0;
  top: 0;
}

.panel-head h2,
.section-head h2 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 6px;
}

.panel-head p {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 13px;
  line-height: 1.5;
  margin: 0 0 18px;
}

.milestone-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.milestone-card {
  min-height: 188px;
}

.milestone-card::part(container) {
  border-radius: 14px;
  height: 100%;
  position: relative;
  transition: box-shadow 0.15s ease, transform 0.15s ease;
}

.milestone-card::part(container)::before {
  background: #e8edf2;
  content: '';
  height: 3px;
  left: 0;
  position: absolute;
  top: 0;
  width: 100%;
}

.milestone-card--complete::part(container)::before {
  background: #6daa28;
}

.milestone-card--complete::part(container) {
  background: linear-gradient(180deg, rgba(109, 170, 40, 0.04) 0%, #fff 48px);
}

.milestone-card--active::part(container)::before {
  background: #0077b8;
}

.milestone-card--active::part(container) {
  background: linear-gradient(180deg, rgba(0, 119, 184, 0.06) 0%, #fff 48px);
  box-shadow: 0 2px 16px rgba(0, 119, 184, 0.1);
}

.milestone-card--at_risk::part(container)::before {
  background: #e85454;
}

.milestone-card--at_risk::part(container) {
  background: linear-gradient(180deg, rgba(232, 84, 84, 0.05) 0%, #fff 48px);
}

.milestone-card:hover::part(container) {
  box-shadow: 0 8px 22px rgba(22, 22, 22, 0.08);
  transform: translateY(-1px);
}

.milestone-card__icon {
  display: flex;
  justify-content: center;
  padding: 6px 0 4px;
}

.milestone-card__icon-wrap {
  align-items: center;
  background: #f0f3f6;
  border-radius: 12px;
  color: #6c757d;
  display: inline-flex;
  height: 48px;
  justify-content: center;
  width: 48px;
}

.milestone-card--complete .milestone-card__icon-wrap {
  background: rgba(109, 170, 40, 0.12);
  color: #6daa28;
}

.milestone-card--active .milestone-card__icon-wrap {
  background: rgba(0, 119, 184, 0.12);
  color: #0077b8;
}

.milestone-card--at_risk .milestone-card__icon-wrap {
  background: rgba(232, 84, 84, 0.1);
  color: #e85454;
}

.milestone-card__actions {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: space-between;
  width: 100%;
}

.section-head {
  align-items: center;
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.section-icon {
  align-items: center;
  background: color-mix(in srgb, var(--section-accent, #0077b8) 12%, white);
  border-radius: 12px;
  color: var(--section-accent, #0077b8);
  display: flex;
  height: 44px;
  justify-content: center;
  width: 44px;
}

.detail-grid {
  display: grid;
  gap: 14px 20px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin: 0;
}

.detail-item {
  margin: 0;
}

.detail-item--multiline {
  grid-column: 1 / -1;
}

.detail-item dt {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 12px;
  margin-bottom: 4px;
}

.detail-item dd {
  color: var(--mds_brand_appearance_neutral_default_text-color, #161616);
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
  white-space: pre-wrap;
}

@media (max-width: 960px) {
  .summary-header {
    flex-direction: column;
  }

  .summary-donut {
    align-self: flex-start;
  }

  .summary-stats,
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .milestone-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .milestone-stepper {
    grid-template-columns: repeat(7, minmax(84px, 1fr));
  }
}

@media (max-width: 560px) {
  .milestone-grid {
    grid-template-columns: 1fr;
  }
}
</style>

<style>
.milestone-card::part(heading) {
  text-align: center;
}

.milestone-card::part(body) {
  color: #6c757d;
  font-size: 12px;
  line-height: 1.45;
  text-align: center;
}
</style>
