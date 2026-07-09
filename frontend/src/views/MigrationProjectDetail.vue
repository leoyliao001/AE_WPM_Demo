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
      <section class="hero-panel">
        <div class="hero-main">
          <div class="hero-tags">
            <mc-tag appearance="info" fit="small" :label="project.migrationRequestId" />
            <mc-tag
              :appearance="statusAppearance(project.status)"
              fit="small"
              :label="formatStatusLabel(project.status)"
            />
          </div>
          <p class="hero-meta">
            {{ project.requestor }} · {{ project.requestedDate }} · {{ project.region }} ·
            {{ project.migrationType }}
          </p>
        </div>

        <div class="hero-progress">
          <div class="hero-progress-head">
            <span>Overall progress</span>
            <strong>{{ progressPct }}%</strong>
          </div>
          <div class="progress-track progress-track--large">
            <div class="progress-fill" :style="{ width: `${progressPct}%` }" />
          </div>
        </div>
      </section>

      <section class="progress-panel">
        <div class="panel-head">
          <h2>Migration Progress</h2>
          <p>High-level milestone tracking for this project (demo — derived from current status).</p>
        </div>

        <ol class="progress-steps">
          <li
            v-for="(step, index) in progressSteps"
            :key="step.id"
            class="progress-step"
            :class="`progress-step--${step.state}`"
          >
            <div class="step-marker">
              <mc-icon
                v-if="step.state === 'complete'"
                icon="mi-check"
                size="16"
              />
              <span v-else>{{ index + 1 }}</span>
            </div>
            <div class="step-content">
              <strong>{{ step.label }}</strong>
              <p>{{ step.description }}</p>
              <mc-tag
                v-if="step.state === 'active'"
                appearance="info"
                fit="small"
                label="In progress"
              />
              <mc-tag
                v-else-if="step.state === 'complete'"
                appearance="success"
                fit="small"
                label="Complete"
              />
              <mc-tag v-else appearance="neutral" fit="small" label="Pending" />
            </div>
          </li>
        </ol>
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
import { useRoute } from 'vue-router'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'
import {
  buildDetailSections,
  buildProgressSteps,
  formatStatusLabel,
  overallProgress,
  statusAppearance
} from '../utils/migrationDashboardProgress.js'
import '@maersk-global/mds-components-core/mc-tag'
import '@maersk-global/mds-components-core/mc-icon'
import '@maersk-global/mds-components-core/mc-notification'

const route = useRoute()
const loading = ref(true)
const loadError = ref('')
const project = ref(null)

const progressPct = computed(() => overallProgress(project.value?.status))
const progressSteps = computed(() => buildProgressSteps(project.value?.status ?? 'new'))
const detailSections = computed(() =>
  project.value ? buildDetailSections(project.value) : []
)

const detailSubtitle = computed(() => {
  if (project.value) {
    return `${project.value.migrationRequestId} — detailed intake data and migration progress.`
  }
  return 'Detailed intake data and migration progress.'
})

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

.hero-panel {
  background: linear-gradient(135deg, #0077b8 0%, #003f6e 100%);
  border-radius: 16px;
  color: #fff;
  display: grid;
  gap: 20px;
  grid-template-columns: minmax(0, 1.4fr) minmax(220px, 0.8fr);
  padding: 24px;
}

.hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.hero-meta {
  font-size: 14px;
  line-height: 1.6;
  margin: 0;
  opacity: 0.92;
}

.hero-progress-head {
  display: flex;
  font-size: 13px;
  justify-content: space-between;
  margin-bottom: 8px;
}

.hero-progress-head strong {
  font-size: 24px;
}

.progress-track {
  background: rgba(255, 255, 255, 0.18);
  border-radius: 999px;
  height: 8px;
  overflow: hidden;
}

.progress-track--large {
  height: 10px;
}

.progress-fill {
  background: linear-gradient(90deg, #ffffff, #42b0d5);
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
  margin: 0 0 16px;
}

.progress-steps {
  display: flex;
  flex-direction: column;
  gap: 14px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.progress-step {
  align-items: flex-start;
  display: flex;
  gap: 14px;
}

.step-marker {
  align-items: center;
  background: rgba(22, 22, 22, 0.06);
  border-radius: 999px;
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  display: flex;
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 700;
  height: 32px;
  justify-content: center;
  width: 32px;
}

.progress-step--complete .step-marker {
  background: rgba(0, 119, 184, 0.12);
  color: #0077b8;
}

.progress-step--active .step-marker {
  background: #0077b8;
  color: #fff;
}

.step-content strong {
  display: block;
  margin-bottom: 4px;
}

.step-content p {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 13px;
  line-height: 1.5;
  margin: 0 0 8px;
}

.section-head {
  align-items: center;
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.section-icon {
  align-items: center;
  background: color-mix(in srgb, var(--section-accent) 12%, white);
  border-radius: 12px;
  color: var(--section-accent);
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
  .hero-panel,
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
