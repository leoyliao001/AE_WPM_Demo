<template>
  <div class="ci-review">
    <header v-if="!embedded" class="ci-review__bar">
      <mc-top-bar product="Automation Excellence" productshort="AE" logosize="auto">
        <nav slot="actions" class="ci-review__nav">
          <span class="ci-review__nav-link ci-review__nav-link--active">Final CI Review</span>
        </nav>
      </mc-top-bar>
      <div class="ci-review__divider" />
    </header>

    <div class="ci-review__body">
      <header class="ci-review__intro">
        <router-link v-if="embedded" class="ci-review__back" to="/">
          <mc-button
            appearance="neutral"
            variant="plain"
            fit="small"
            label="Back to Welcome"
            icon="mi-arrow-left"
          />
        </router-link>
        <mc-tag appearance="info" fit="small" label="CI Governance" />
        <h1>Final CI Review</h1>
        <p>Review automation initiatives, track approvals, and capture value realisation.</p>
      </header>

      <div class="ci-review__layout">
        <!-- Initiative picker — plain section, avoid nesting badges inside mc-card -->
        <section class="picker">
          <h2 class="picker__title">Initiatives</h2>

          <div class="picker__tools">
            <mc-input
              label="Search"
              hiddenlabel
              placeholder="Search by name or ID"
              :value="searchTerm"
              width="full-width"
              icon="mi-magnifying-glass"
              @input="searchTerm = readValue($event)"
            />
            <mc-select
              label="Status"
              hiddenlabel
              placeholder="All statuses"
              :value="statusFilter"
              width="full-width"
              @optionselected="statusFilter = $event?.detail?.value ?? ''"
            >
              <mc-option v-for="opt in statusOptions" :key="opt.value || 'all'" :value="opt.value">
                {{ opt.label }}
              </mc-option>
            </mc-select>
          </div>

          <div class="picker__list">
            <button
              v-for="project in filteredProjects"
              :key="project.id"
              type="button"
              class="picker__item"
              :class="{ 'picker__item--active': selectedProject?.id === project.id }"
              @click="selectProject(project)"
            >
              <span class="picker__item-name">{{ project.name }}</span>
              <span class="picker__item-team">{{ project.team }}</span>
              <span class="picker__item-meta">
                <mc-tag fit="small" appearance="neutral" :label="formatId(project.id)" />
                <mc-tag
                  fit="small"
                  :appearance="statusAppearance(project.automationStatus)"
                  :label="shortStatus(project.automationStatus)"
                />
              </span>
            </button>

            <div v-if="!filteredProjects.length" class="picker__empty">
              <mc-icon icon="mi-magnifying-glass" size="24" />
              <p>No initiatives found</p>
            </div>
          </div>
        </section>

        <!-- Main workspace -->
        <div class="workspace">
          <template v-if="selectedProject && approvalDetail">
            <section class="summary-panel">
              <header class="summary-panel__header">
                <div class="summary-panel__identity">
                  <p class="summary-panel__eyebrow">{{ selectedProject.team }}</p>
                  <div class="summary-panel__title-row">
                    <h2 class="summary-panel__title">{{ selectedProject.name }}</h2>
                    <div class="summary-panel__tags">
                      <mc-tag fit="small" appearance="neutral" :label="formatId(selectedProject.id)" />
                      <mc-tag
                        fit="small"
                        :appearance="statusAppearance(selectedProject.automationStatus)"
                        :label="selectedProject.automationStatus"
                      />
                    </div>
                  </div>
                </div>
                <div class="summary-panel__progress" aria-label="Approval progress">
                  <svg viewBox="0 0 48 48" class="summary-panel__ring-svg">
                    <circle class="summary-panel__ring-bg" cx="24" cy="24" r="20" />
                    <circle
                      class="summary-panel__ring-fill"
                      cx="24"
                      cy="24"
                      r="20"
                      :style="{ strokeDashoffset: ringOffset }"
                    />
                  </svg>
                  <div class="summary-panel__progress-text">
                    <strong>{{ progressPct }}%</strong>
                    <span>Complete</span>
                  </div>
                </div>
              </header>

              <div
                class="summary-panel__stepper"
                aria-label="Approval chain"
                :style="{ gridTemplateColumns: `repeat(${approvalSteps.length}, 1fr)` }"
              >
                <div class="stepper__track" aria-hidden="true">
                  <div class="stepper__track-fill" :style="{ width: stepperFillPct }" />
                </div>
                <div
                  v-for="step in approvalSteps"
                  :key="step.abbr"
                  class="stepper__step"
                  :class="`stepper__step--${step.status}`"
                >
                  <span class="stepper__marker">
                    <span v-if="step.status === 'approved'" class="stepper__check" aria-hidden="true" />
                    <span v-else-if="step.status === 'disabled'" class="stepper__lock" aria-hidden="true" />
                    <span v-else class="stepper__abbr">{{ step.abbr }}</span>
                  </span>
                  <span class="stepper__label">{{ step.role }}</span>
                </div>
              </div>

              <div class="summary-panel__stats">
                <div class="summary-stat">
                  <span class="summary-stat__label">Est. FTE saving</span>
                  <strong class="summary-stat__value">{{ approvalDetail.meta.estimatedFteSaving }}</strong>
                </div>
                <div class="summary-stat">
                  <span class="summary-stat__label">Final FTE</span>
                  <strong class="summary-stat__value">{{ approvalDetail.meta.finalFte }}</strong>
                </div>
                <div class="summary-stat summary-stat--progress">
                  <div class="summary-stat__progress-head">
                    <span class="summary-stat__label">Stages complete</span>
                    <strong class="summary-stat__value summary-stat__value--accent">
                      {{ completedSteps }}/{{ approvalSteps.length }}
                    </strong>
                  </div>
                  <div class="summary-stat__bar">
                    <div class="summary-stat__bar-fill" :style="{ width: `${progressPct}%` }" />
                  </div>
                </div>
              </div>
            </section>

            <div class="workspace__tabs">
              <mc-button
                :appearance="activeTab === 'approval' ? 'primary' : 'neutral'"
                :variant="activeTab === 'approval' ? 'filled' : 'outlined'"
                fit="small"
                label="Workflow"
                @click="activeTab = 'approval'"
              />
              <mc-button
                :appearance="activeTab === 'documents' ? 'primary' : 'neutral'"
                :variant="activeTab === 'documents' ? 'filled' : 'outlined'"
                fit="small"
                label="Documents"
                @click="activeTab = 'documents'"
              />
            </div>

            <template v-if="activeTab === 'approval'">
              <StageTable v-if="approvalDetail" :rows="approvalDetail.rows" />

              <div class="stage-actions">
                <mc-button
                  v-for="row in actionableRows"
                  :key="row.key"
                  :appearance="focusedStage === row.key ? 'primary' : 'neutral'"
                  :variant="focusedStage === row.key ? 'filled' : 'outlined'"
                  fit="small"
                  :label="row.stage"
                  @click="focusStage(row.key)"
                />
              </div>

              <CiStageDetail
                v-if="focusedRow"
                :row="focusedRow"
                :detail="approvalDetail"
                :form-state="formState"
                :can-send-el-email="canSendElEmail"
                @approve-signoff="approveCISignOff"
                @email-el="emailExecutionLeader"
                @mark-value="markValueRealized"
                @update:ci-sign-off-comment="formState.ciSignOffComment = $event"
                @update:exec-leader-recipients="formState.execLeaderRecipients = $event"
                @update:el-pid-details="formState.elPidDetails = $event"
                @update:el-comment="formState.elComment = $event"
              />
            </template>

            <template v-else>
              <div v-if="documentsLoading" class="docs-loading">
                <mc-loading-indicator fit="small" label="Loading documents" hiddenlabel />
                <p>Loading documents…</p>
              </div>

              <div v-else-if="!documents.length" class="docs-empty">
                <mc-notification appearance="neutral" fit="small" heading="No documents">
                  Attachments will appear here when added to this initiative.
                </mc-notification>
              </div>

              <div v-else class="docs-grid">
                <mc-card
                  v-for="doc in documents"
                  :key="doc.url + doc.name"
                  variant="bordered"
                  fit="small"
                  :heading="doc.name"
                  :subheading="`Uploaded by ${doc.uploadedBy}`"
                  contentalignment="left"
                >
                  <mc-button
                    slot="actions"
                    appearance="primary"
                    variant="outlined"
                    fit="small"
                    label="Open"
                    icon="mi-tray-arrow-down"
                    @click="openDoc(doc.url)"
                  />
                </mc-card>
              </div>
            </template>
          </template>

          <mc-card
            v-else
            class="workspace__empty"
            variant="bordered"
            fit="medium"
            heading="Select an initiative"
            body="Choose a project from the list to view its approval workflow and documents."
            contentalignment="middle"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useFinalCiReview } from '../composables/useFinalCiReview'
import CiStageDetail from './CiStageDetail.vue'
import StageTable from './StageTable.vue'

defineProps({
  embedded: { type: Boolean, default: false }
})

const {
  selectedProject,
  searchTerm,
  statusFilter,
  activeTab,
  formState,
  documents,
  documentsLoading,
  statusOptions,
  filteredProjects,
  approvalSteps,
  approvalDetail,
  canSendElEmail,
  selectProject,
  approveCISignOff,
  emailExecutionLeader,
  markValueRealized
} = useFinalCiReview()

const focusedStage = ref('')

const progressPct = computed(() => {
  if (!approvalSteps.value.length) return 0
  const done = approvalSteps.value.filter((s) => s.status === 'approved').length
  return Math.round((done / approvalSteps.value.length) * 100)
})

const completedSteps = computed(
  () => approvalSteps.value.filter((s) => s.status === 'approved').length
)

const ringOffset = computed(() => {
  const circumference = 2 * Math.PI * 20
  return circumference - (progressPct.value / 100) * circumference
})

const stepperFillPct = computed(() => {
  const total = approvalSteps.value.length
  if (total <= 1) return `${progressPct.value}%`
  const done = completedSteps.value
  if (done <= 1) return '0%'
  return `${((done - 1) / (total - 1)) * 100}%`
})

const actionableRows = computed(() => {
  if (!approvalDetail.value) return []
  return approvalDetail.value.rows.filter((row) => row.expandable || row.actionType)
})

const focusedRow = computed(() => {
  if (!approvalDetail.value || !focusedStage.value) return null
  return approvalDetail.value.rows.find((row) => row.key === focusedStage.value) || null
})

watch(
  [selectedProject, actionableRows],
  () => {
    if (!actionableRows.value.length) {
      focusedStage.value = ''
      return
    }
    if (!actionableRows.value.some((r) => r.key === focusedStage.value)) {
      focusedStage.value = actionableRows.value[0].key
    }
  },
  { immediate: true }
)

function readValue(event) {
  return event?.target?.value ?? event?.detail?.value ?? ''
}

function formatId(id) {
  const text = String(id || '').trim()
  return text.startsWith('#') ? text : `#${text.replace(/^#+/, '')}`
}

function shortStatus(status) {
  const s = String(status || 'N/A')
  return s.length > 14 ? `${s.slice(0, 12)}…` : s
}

function statusAppearance(status) {
  const s = String(status || '').toLowerCase()
  if (s.includes('value') || s.includes('complete')) return 'info'
  if (s.includes('hypercare') || s.includes('assigned')) return 'info'
  return 'neutral'
}

function focusStage(key) {
  focusedStage.value = key
}

function openDoc(url) {
  if (url && url !== '#') window.open(url, '_blank', 'noopener,noreferrer')
}
</script>

<style scoped>
.ci-review {
  background: #fff;
  min-height: 100vh;
  overflow-x: hidden;
}

.ci-review__bar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: #fff;
}

.ci-review__divider {
  background: var(--mds_brand_appearance_neutral_weak_border-color, #d9dee3);
  height: 1px;
}

.ci-review__nav {
  display: flex;
  gap: 16px;
  padding: 0 8px;
}

.ci-review__nav-link {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 13px;
  font-weight: 500;
}

.ci-review__nav-link--active {
  color: #0077b8;
  font-weight: 600;
}

.ci-review__body {
  margin: 0 auto;
  max-width: 1200px;
  padding: 40px 24px 72px;
}

.ci-review__intro {
  margin-bottom: 32px;
  max-width: 560px;
}

.ci-review__back {
  display: inline-block;
  margin-bottom: 12px;
  text-decoration: none;
}

.ci-review__intro h1 {
  color: var(--mds_brand_appearance_neutral_default_text-color, #161616);
  font-family: 'Maersk Headline', 'Maersk Text', sans-serif;
  font-size: clamp(28px, 4vw, 38px);
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.15;
  margin: 12px 0 8px;
}

.ci-review__intro p {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 15px;
  line-height: 1.6;
  margin: 0;
}

.ci-review__layout {
  display: grid;
  gap: 24px;
  grid-template-columns: 300px minmax(0, 1fr);
  align-items: start;
}

.picker {
  background: #fff;
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(22, 22, 22, 0.04);
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
  padding: 20px;
  position: relative;
}

.picker::before {
  background: #0077b8;
  content: '';
  height: 3px;
  left: 0;
  position: absolute;
  top: 0;
  width: 100%;
}

.picker__title {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.picker__tools {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.picker__list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: calc(100vh - 280px);
  overflow-x: hidden;
  overflow-y: auto;
}

.picker__item {
  background: #fff;
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  font-family: inherit;
  gap: 4px;
  padding: 14px 16px;
  text-align: left;
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease;
  width: 100%;
}

.picker__item:hover {
  border-color: color-mix(in srgb, #0077b8 28%, transparent);
  box-shadow: 0 4px 12px rgba(22, 22, 22, 0.06);
}

.picker__item--active {
  border-color: color-mix(in srgb, #0077b8 40%, transparent);
  box-shadow: 0 4px 16px rgba(0, 119, 184, 0.12);
}

.picker__item-name {
  color: #161616;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.35;
}

.picker__item-team {
  color: #6c757d;
  font-size: 12px;
}

.picker__item-meta {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
}

.picker__item-meta mc-tag {
  flex-shrink: 0;
}

.picker__empty {
  align-items: center;
  color: #6c757d;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 32px 16px;
  text-align: center;
}

.picker__empty p {
  font-size: 13px;
  margin: 0;
}

.workspace {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
  overflow: hidden;
}

.summary-panel {
  background: #fff;
  border: 2px solid rgba(22, 22, 22, 0.09);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 0;
  overflow: hidden;
  padding: 18px 20px 16px;
}

.summary-panel__header {
  align-items: flex-start;
  display: flex;
  gap: 16px;
  justify-content: space-between;
  margin-bottom: 20px;
}

.summary-panel__identity {
  flex: 1;
  min-width: 0;
}

.summary-panel__eyebrow {
  color: #8a9199;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.02em;
  line-height: 1.2;
  margin: 0 0 6px;
  text-transform: uppercase;
}

.summary-panel__title-row {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
}

.summary-panel__title {
  color: #161616;
  font-family: 'Maersk Headline', 'Maersk Text', sans-serif;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.3;
  margin: 0;
}

.summary-panel__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.summary-panel__progress {
  align-items: center;
  display: flex;
  flex-shrink: 0;
  gap: 10px;
}

.summary-panel__ring-svg {
  flex-shrink: 0;
  height: 44px;
  transform: rotate(-90deg);
  width: 44px;
}

.summary-panel__ring-bg {
  fill: none;
  stroke: #eef0f2;
  stroke-width: 3;
}

.summary-panel__ring-fill {
  fill: none;
  stroke: #aed581;
  stroke-dasharray: 125.66;
  stroke-linecap: round;
  stroke-width: 3;
  transition: stroke-dashoffset 0.4s ease;
}

.summary-panel__progress-text {
  display: flex;
  flex-direction: column;
  gap: 1px;
  line-height: 1.15;
}

.summary-panel__progress-text strong {
  color: #161616;
  font-family: 'Maersk Headline', 'Maersk Text', sans-serif;
  font-size: 18px;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
}

.summary-panel__progress-text span {
  color: #8a9199;
  font-size: 11px;
  font-weight: 500;
}

.summary-panel__stepper {
  display: grid;
  gap: 0;
  margin-bottom: 14px;
  position: relative;
}

.stepper__track {
  background: #eef0f2;
  border-radius: 999px;
  height: 2px;
  left: 10%;
  position: absolute;
  right: 10%;
  top: 8px;
  z-index: 0;
}

.stepper__track-fill {
  background: #c5e1a5;
  border-radius: inherit;
  height: 100%;
  transition: width 0.35s ease;
}

.stepper__step {
  align-items: center;
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
  position: relative;
  z-index: 1;
}

.stepper__marker {
  align-items: center;
  background: #fff;
  border: 1.5px solid #d0d5dd;
  border-radius: 50%;
  color: #6c757d;
  display: inline-flex;
  flex-shrink: 0;
  font-size: 8px;
  font-weight: 600;
  height: 18px;
  justify-content: center;
  width: 18px;
}

.stepper__abbr {
  line-height: 1;
}

.stepper__check {
  border-bottom: 1.5px solid #fff;
  border-right: 1.5px solid #fff;
  display: block;
  height: 7px;
  margin-top: -1px;
  transform: rotate(45deg);
  width: 4px;
}

.stepper__lock {
  border: 1px solid currentColor;
  border-radius: 1px;
  display: block;
  height: 6px;
  position: relative;
  width: 5px;
}

.stepper__lock::before {
  background: currentColor;
  border-radius: 999px 999px 0 0;
  content: '';
  height: 3px;
  left: 50%;
  position: absolute;
  top: -4px;
  transform: translateX(-50%);
  width: 7px;
}

.stepper__label {
  color: #8a9199;
  font-size: 10px;
  font-weight: 400;
  line-height: 1.2;
  max-width: 100%;
  text-align: center;
}

.stepper__step--approved .stepper__marker {
  background: #c5e1a5;
  border-color: #c5e1a5;
  color: #fff;
}

.stepper__step--approved .stepper__label {
  color: #8bc34a;
  font-weight: 400;
}

.stepper__step--pending .stepper__marker {
  background: #e8f4fc;
  border-color: #b3d9f0;
  box-shadow: none;
  color: #6aabce;
}

.stepper__step--pending .stepper__label {
  color: #6aabce;
  font-weight: 400;
}

.stepper__step--disabled .stepper__marker {
  background: #f4f5f7;
  border-color: #d0d5dd;
  color: #adb5bd;
}

.stepper__step--rejected .stepper__marker {
  background: #fff5f5;
  border-color: #e57373;
  color: #c62828;
}

.summary-panel__stats {
  background: #f8f9fb;
  border-radius: 10px;
  display: grid;
  gap: 12px 20px;
  grid-template-columns: 1fr 1fr 1.4fr;
  padding: 14px 16px;
}

.summary-stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.summary-stat__label {
  color: #8a9199;
  font-size: 11px;
  font-weight: 500;
  line-height: 1.2;
}

.summary-stat__value {
  color: #161616;
  font-family: 'Maersk Headline', 'Maersk Text', sans-serif;
  font-size: 20px;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  line-height: 1.1;
}

.summary-stat__value--accent {
  color: #8bc34a;
  font-size: 16px;
}

.summary-stat--progress {
  gap: 8px;
  justify-content: center;
}

.summary-stat__progress-head {
  align-items: baseline;
  display: flex;
  justify-content: space-between;
}

.summary-stat__bar {
  background: rgba(22, 22, 22, 0.08);
  border-radius: 999px;
  height: 4px;
  overflow: hidden;
}

.summary-stat__bar-fill {
  background: linear-gradient(90deg, #dcedc8, #c5e1a5);
  border-radius: inherit;
  height: 100%;
  transition: width 0.35s ease;
}

.workspace__tabs {
  display: flex;
  gap: 6px;
}

.stage-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.docs-loading,
.docs-empty {
  padding: 24px 0;
  text-align: center;
}

.docs-loading p {
  color: #6c757d;
  font-size: 13px;
  margin: 12px 0 0;
}

.docs-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
}

.workspace__empty::part(container) {
  min-height: 280px;
}

@media (max-width: 960px) {
  .ci-review__layout {
    grid-template-columns: 1fr;
  }

  .summary-panel__stats {
    grid-template-columns: 1fr;
  }

  .summary-panel__stepper {
    gap: 8px;
    grid-template-columns: repeat(2, 1fr) !important;
  }

  .stepper__track {
    display: none;
  }
}

@media (max-width: 600px) {
  .ci-review__body {
    padding: 24px 16px 48px;
  }

  .summary-panel__header {
    align-items: center;
    flex-direction: column;
  }

  .summary-panel__progress {
    align-self: flex-start;
  }
}
</style>

<style>
/* MDS web components: keep tags in normal document flow */
.picker__item-meta mc-tag,
.summary-panel__tags mc-tag {
  display: inline-flex !important;
  max-width: 100%;
  position: static !important;
  vertical-align: middle;
}

/* Tab / stage buttons: compact + centered label */
.workspace__tabs mc-button,
.stage-actions mc-button {
  --mds-button-min-height: 28px;
  font-size: 12px;
}

.workspace__tabs mc-button::part(button),
.stage-actions mc-button::part(button) {
  justify-content: center;
  min-height: 28px;
  padding: 4px 10px;
}

.workspace__tabs mc-button::part(label),
.stage-actions mc-button::part(label) {
  font-size: 12px;
  line-height: 1.2;
}
</style>
