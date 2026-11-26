<template>
  <PageShell
    title="BAU Control Agreement"
    :show-heading="false"
    :back-to="backTo"
    back-label="Back to Project Phases"
    back-link-to-topbar
    full-width
    class="bau-controls-shell"
  >
    <main class="bau-page">
      <header class="bau-heading">
        <div>
          <mc-tag appearance="info" fit="small" label="BAU CONTROL AGREEMENT" />
          <h1>Business as usual, agreed.</h1>
          <p>
            A simple record of how the Area and GSC will operate after hypercare exit.
            This documents the agreement. It does not create a new governance process.
          </p>
          <p v-if="project" class="project-context">
            {{ project.migrationRequestId }} · {{ project.projectName }}
          </p>
        </div>
        <mc-tag :appearance="agreementStatus === 'confirmed' ? 'success' : 'info'" fit="small" :label="statusLabel" />
      </header>

      <div v-if="loading" class="page-state" role="status">
        <mc-loading-indicator size="medium" />
        <span>Loading BAU agreement…</span>
      </div>
      <div v-else-if="loadError" class="load-error-state">
        <mc-notification
          appearance="error"
          fit="medium"
          heading="Unable to load BAU Controls"
          :body="loadError"
          role="alert"
        />
        <mc-button appearance="neutral" variant="outlined" label="Retry" @click="loadAgreement" />
      </div>

      <form v-else class="bau-form" @submit.prevent>
        <section class="agreement-meta">
          <mc-input
            label="Migration"
            :value.prop="form.migrationName"
            maxlength="255"
            placeholder="Migration name"
            fit="medium"
            width="full-width"
            @input="setText('migrationName', $event)"
          />
          <mc-input
            label="Product"
            :value.prop="form.product"
            maxlength="255"
            placeholder="Product / function"
            fit="medium"
            width="full-width"
            @input="setText('product', $event)"
          />
          <mc-input
            label="Area"
            :value.prop="form.area"
            maxlength="255"
            placeholder="Area"
            fit="medium"
            width="full-width"
            @input="setText('area', $event)"
          />
          <mc-input
            label="BAU effective from"
            type="date"
            :value.prop="form.effectiveFrom"
            fit="medium"
            width="full-width"
            @input="setText('effectiveFrom', $event)"
          />
        </section>

        <section class="agreement-card">
          <div class="section-heading">
            <span class="section-number">1</span>
            <div>
              <h2>Ownership</h2>
              <p>Who owns the day-to-day relationship once WPM exits?</p>
            </div>
          </div>
          <div class="field-grid field-grid--two">
            <mc-input
              label="Area owner"
              :value.prop="form.areaOwner"
              maxlength="255"
              placeholder="Name / role"
              fit="medium"
              width="full-width"
              @input="setText('areaOwner', $event)"
            />
            <mc-input
              label="GSC owner"
              :value.prop="form.gscOwner"
              maxlength="255"
              placeholder="Name / role"
              fit="medium"
              width="full-width"
              @input="setText('gscOwner', $event)"
            />
          </div>
          <mc-textarea
            label="Scope covered"
            :value.prop="form.scopeCovered"
            maxlength="5000"
            placeholder="Short description of the migrated scope now operating in BAU"
            fit="medium"
            width="full-width"
            :rows="3"
            @input="setText('scopeCovered', $event)"
          />
        </section>

        <section class="agreement-card">
          <div class="section-heading">
            <span class="section-number">2</span>
            <div>
              <h2>Performance control</h2>
              <p>Use the product's existing measures. Pulse only records what has been agreed.</p>
            </div>
          </div>
          <div class="field-grid field-grid--four">
            <mc-input
              label="Performance / KPI reference"
              :value.prop="form.kpiReference"
              maxlength="255"
              placeholder="KPI set or link"
              fit="medium"
              width="full-width"
              @input="setText('kpiReference', $event)"
            />
            <mc-input
              label="Reporting source"
              :value.prop="form.reportingSource"
              maxlength="255"
              placeholder="Dashboard / report"
              fit="medium"
              width="full-width"
              @input="setText('reportingSource', $event)"
            />
            <mc-select
              label="Review cadence"
              :value.prop="form.reviewCadence"
              fit="medium"
              width="full-width"
              @optionselected="setSelectValue('reviewCadence', $event)"
            >
              <mc-option v-for="option in reviewCadenceOptions" :key="option" :value="option">{{ option }}</mc-option>
            </mc-select>
            <mc-input
              label="Performance owner"
              :value.prop="form.performanceOwner"
              maxlength="255"
              placeholder="Role"
              fit="medium"
              width="full-width"
              @input="setText('performanceOwner', $event)"
            />
          </div>
        </section>

        <section class="agreement-card">
          <div class="section-heading">
            <span class="section-number">3</span>
            <div>
              <h2>Ways of working</h2>
              <p>Record the existing BAU rhythm. Do not create another WPM meeting.</p>
            </div>
          </div>
          <div class="field-grid field-grid--two">
            <mc-input
              label="BAU forum / channel"
              :value.prop="form.bauForumChannel"
              maxlength="255"
              placeholder="Existing meeting, Teams channel, etc."
              fit="medium"
              width="full-width"
              @input="setText('bauForumChannel', $event)"
            />
            <mc-select
              label="Working cadence"
              :value.prop="form.workingCadence"
              fit="medium"
              width="full-width"
              @optionselected="setSelectValue('workingCadence', $event)"
            >
              <mc-option v-for="option in workingCadenceOptions" :key="option" :value="option">{{ option }}</mc-option>
            </mc-select>
            <mc-input
              label="Area operational contact"
              :value.prop="form.areaOperationalContact"
              maxlength="255"
              placeholder="Name / role"
              fit="medium"
              width="full-width"
              @input="setText('areaOperationalContact', $event)"
            />
            <mc-input
              label="GSC operational contact"
              :value.prop="form.gscOperationalContact"
              maxlength="255"
              placeholder="Name / role"
              fit="medium"
              width="full-width"
              @input="setText('gscOperationalContact', $event)"
            />
          </div>
        </section>

        <section class="agreement-card">
          <div class="section-heading">
            <span class="section-number">4</span>
            <div>
              <h2>Escalation</h2>
              <p>Keep the route clear and proportionate.</p>
            </div>
          </div>
          <div class="escalation-grid">
            <div class="escalation-box">
              <h3>Normal operational issue</h3>
              <mc-input
                label="Route"
                :value.prop="form.normalIssueRoute"
                maxlength="255"
                placeholder="GSC ↔ Area operational owners"
                fit="medium"
                width="full-width"
                @input="setText('normalIssueRoute', $event)"
              />
            </div>
            <span class="escalation-arrow" aria-hidden="true">›</span>
            <div class="escalation-box">
              <h3>Leadership intervention needed</h3>
              <mc-input
                label="Route"
                :value.prop="form.leadershipRoute"
                maxlength="255"
                placeholder="GSC Lead ↔ Area / Product Lead"
                fit="medium"
                width="full-width"
                @input="setText('leadershipRoute', $event)"
              />
            </div>
          </div>
          <mc-textarea
            label="Specific escalation note, if needed"
            :value.prop="form.escalationNote"
            maxlength="5000"
            placeholder="Optional"
            fit="medium"
            width="full-width"
            :rows="2"
            @input="setText('escalationNote', $event)"
          />
        </section>

        <section class="agreement-card acceptance-card">
          <div class="section-heading">
            <span class="section-number">5</span>
            <div>
              <h2>BAU acceptance</h2>
              <p>Both Area and GSC acceptance are required to confirm the record.</p>
            </div>
          </div>
          <p class="acceptance-statement">
            The Area and GSC confirm that the migrated scope has transitioned to Business as Usual and that the ownership,
            performance controls, ways of working and escalation path above are understood and agreed.
          </p>
          <div class="acceptance-grid">
            <section class="acceptance-party" aria-labelledby="area-acceptance-heading">
              <h3 id="area-acceptance-heading">Area</h3>
              <mc-checkbox-group
                name="areaAcceptance"
                orientation="horizontal"
                :value.prop="areaAcceptanceValue"
                @change="setAcceptance('areaAccepted', $event)"
              >
                <mc-checkbox name="areaAcceptance" value="accepted" label="Accepted" />
              </mc-checkbox-group>
              <div class="field-grid field-grid--two">
                <mc-input
                  label="Name / role"
                  :value.prop="form.areaNameRole"
                  maxlength="255"
                  fit="medium"
                  width="full-width"
                  @input="setText('areaNameRole', $event)"
                />
                <mc-input
                  label="Date"
                  type="date"
                  :value.prop="form.areaAcceptanceDate"
                  fit="medium"
                  width="full-width"
                  @input="setText('areaAcceptanceDate', $event)"
                />
              </div>
            </section>
            <section class="acceptance-party" aria-labelledby="gsc-acceptance-heading">
              <h3 id="gsc-acceptance-heading">GSC</h3>
              <mc-checkbox-group
                name="gscAcceptance"
                orientation="horizontal"
                :value.prop="gscAcceptanceValue"
                @change="setAcceptance('gscAccepted', $event)"
              >
                <mc-checkbox name="gscAcceptance" value="accepted" label="Accepted" />
              </mc-checkbox-group>
              <div class="field-grid field-grid--two">
                <mc-input
                  label="Name / role"
                  :value.prop="form.gscNameRole"
                  maxlength="255"
                  fit="medium"
                  width="full-width"
                  @input="setText('gscNameRole', $event)"
                />
                <mc-input
                  label="Date"
                  type="date"
                  :value.prop="form.gscAcceptanceDate"
                  fit="medium"
                  width="full-width"
                  @input="setText('gscAcceptanceDate', $event)"
                />
              </div>
            </section>
          </div>
          <mc-notification
            v-if="agreementStatus === 'confirmed'"
            class="form-message"
            appearance="success"
            fit="medium"
            heading="BAU agreement confirmed"
            body="BAU agreement confirmed. Migration governance can close."
            role="status"
          />
          <mc-notification
            v-if="saveError"
            class="form-message"
            appearance="error"
            fit="medium"
            heading="Unable to save BAU Controls"
            :body="saveError"
            role="alert"
          />
          <mc-notification
            v-if="successMessage"
            class="form-message"
            appearance="success"
            fit="medium"
            heading="BAU Controls saved"
            :body="successMessage"
            role="status"
          />
          <p v-if="agreementStatus === 'confirmed'" class="confirmation-note">
            Saving changes will return the agreement to draft and require re-confirmation by both parties.
          </p>
          <div class="agreement-actions">
            <mc-button
              appearance="neutral"
              variant="outlined"
              fit="medium"
              :label="saving && saveAction === 'save' ? 'Saving…' : agreementStatus === 'confirmed' ? 'Save changes as draft' : 'Save draft'"
              :loading="saving && saveAction === 'save'"
              :disabled="saving"
              @click="saveAgreement('save')"
            />
            <mc-button
              appearance="primary"
              fit="medium"
              :label="saving && saveAction === 'confirm' ? 'Confirming…' : 'Confirm agreement'"
              :loading="saving && saveAction === 'confirm'"
              :disabled="saving"
              @click="saveAgreement('confirm')"
            />
          </div>
        </section>
      </form>
    </main>
  </PageShell>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'
import {
  BAU_REVIEW_CADENCE_OPTIONS,
  BAU_WORKING_CADENCE_OPTIONS
} from '../utils/bauControlsOptions.js'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-checkbox'
import '@maersk-global/mds-components-core/mc-checkbox-group'
import '@maersk-global/mds-components-core/mc-input'
import '@maersk-global/mds-components-core/mc-loading-indicator'
import '@maersk-global/mds-components-core/mc-notification'
import '@maersk-global/mds-components-core/mc-option'
import '@maersk-global/mds-components-core/mc-select'
import '@maersk-global/mds-components-core/mc-tag'
import '@maersk-global/mds-components-core/mc-textarea'

const route = useRoute()
const projectId = computed(() => String(route.params.id || ''))
const endpoint = computed(() => `/api/migration-dashboard/projects/${projectId.value}/bau-controls/`)
const backTo = computed(() => {
  const returnTo = typeof route.query.returnTo === 'string' ? route.query.returnTo : ''
  if (returnTo.startsWith('/') && !returnTo.startsWith('//')) return returnTo
  const project = route.query.project || projectId.value
  return `/toll-gates?project=${encodeURIComponent(project)}`
})
const reviewCadenceOptions = BAU_REVIEW_CADENCE_OPTIONS
const workingCadenceOptions = BAU_WORKING_CADENCE_OPTIONS
const emptyForm = () => ({
  migrationName: '',
  product: '',
  area: '',
  effectiveFrom: '',
  areaOwner: '',
  gscOwner: '',
  scopeCovered: '',
  kpiReference: '',
  reportingSource: '',
  reviewCadence: 'Monthly',
  performanceOwner: '',
  bauForumChannel: '',
  workingCadence: 'Monthly',
  areaOperationalContact: '',
  gscOperationalContact: '',
  normalIssueRoute: '',
  leadershipRoute: '',
  escalationNote: '',
  areaAccepted: false,
  areaNameRole: '',
  areaAcceptanceDate: '',
  gscAccepted: false,
  gscNameRole: '',
  gscAcceptanceDate: ''
})

const form = reactive(emptyForm())
const project = ref(null)
const agreementStatus = ref('draft')
const loading = ref(true)
const saving = ref(false)
const saveAction = ref('')
const loadError = ref('')
const saveError = ref('')
const successMessage = ref('')
const areaAcceptanceValue = computed(() => form.areaAccepted ? ['accepted'] : [])
const gscAcceptanceValue = computed(() => form.gscAccepted ? ['accepted'] : [])
const statusLabel = computed(() => agreementStatus.value === 'confirmed' ? 'CONFIRMED' : 'POST-HYPERCARE · DRAFT')

async function loadAgreement() {
  if (!projectId.value) {
    loadError.value = 'A migration project must be selected to open BAU Controls.'
    loading.value = false
    return
  }
  loading.value = true
  loadError.value = ''
  saveError.value = ''
  successMessage.value = ''
  try {
    const { data } = await axios.get(endpoint.value)
    project.value = data.project
    const defaults = emptyForm()
    if (!data.agreement) {
      defaults.migrationName = data.project?.projectName || ''
      defaults.product = Array.isArray(data.project?.products) ? data.project.products.join(', ') : ''
      defaults.area = data.project?.region || ''
    }
    Object.keys(defaults).forEach((field) => {
      form[field] = data.agreement?.[field] ?? defaults[field]
    })
    agreementStatus.value = data.agreement?.status || 'draft'
  } catch (failure) {
    loadError.value = failure.response?.data?.error || failure.message || 'Unable to load BAU Controls.'
  } finally {
    loading.value = false
  }
}

function setText(field, event) {
  form[field] = event?.target?.value ?? ''
}

function setSelectValue(field, event) {
  form[field] = event?.detail?.value ?? event?.target?.value ?? ''
}

function setAcceptance(field, event) {
  const value = event?.detail ?? event?.currentTarget?.value ?? event?.target?.value
  form[field] = Array.isArray(value) && value.includes('accepted')
}

async function saveAgreement(action) {
  if (saving.value) return
  if (action === 'confirm' && (!form.areaAccepted || !form.gscAccepted)) {
    saveError.value = 'Area and GSC must both accept before the agreement is confirmed.'
    successMessage.value = ''
    return
  }
  saving.value = true
  saveAction.value = action
  saveError.value = ''
  successMessage.value = ''
  try {
    const { data } = await axios.post(endpoint.value, { ...form, action })
    agreementStatus.value = data.agreement.status
    successMessage.value = action === 'confirm'
      ? 'BAU agreement confirmed. Migration governance can close.'
      : 'Draft saved. You can return to this agreement and continue editing.'
  } catch (failure) {
    saveError.value = failure.response?.data?.error || failure.message || 'Unable to save BAU Controls.'
  } finally {
    saving.value = false
    saveAction.value = ''
  }
}

watch(projectId, loadAgreement, { immediate: true })
</script>

<style scoped>
.bau-page {
  color: #183746;
  margin: 0 auto;
  max-width: none;
  padding: 18px clamp(16px, 2.4vw, 36px) 40px;
  width: 100%;
}

.bau-heading {
  align-items: flex-start;
  display: flex;
  gap: 24px;
  justify-content: space-between;
  margin: 0 0 22px;
}

.bau-heading h1 {
  color: #00243d;
  font-size: clamp(26px, 3vw, 34px);
  margin: 12px 0 8px;
}

.bau-heading p {
  color: #667d88;
  line-height: 1.5;
  margin: 0;
  max-width: 760px;
}

.bau-heading .project-context {
  color: #325665;
  font-size: 13px;
  font-weight: 700;
  margin-top: 10px;
}

.bau-form {
  display: grid;
  gap: 14px;
  width: 100%;
}

.agreement-meta {
  background: #fff;
  border: 1px solid #dbe6ea;
  border-radius: 12px;
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  padding: 18px;
}

.agreement-card {
  background: #fff;
  border: 1px solid #dbe6ea;
  border-radius: 12px;
  padding: 20px;
  width: 100%;
}

.section-heading {
  align-items: center;
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.section-heading h2 {
  color: #00243d;
  font-size: 19px;
  margin: 0;
}

.section-heading p {
  color: #667d88;
  font-size: 13px;
  margin: 4px 0 0;
}

.section-number {
  align-items: center;
  background: #00243d;
  border-radius: 50%;
  color: #fff;
  display: inline-flex;
  flex: 0 0 30px;
  font-size: 13px;
  font-weight: 800;
  height: 30px;
  justify-content: center;
}

.field-grid {
  display: grid;
  gap: 14px;
  margin-bottom: 14px;
}

.field-grid--two {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.field-grid--four {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.escalation-grid {
  align-items: center;
  display: grid;
  gap: 12px;
  grid-template-columns: minmax(0, 1fr) 28px minmax(0, 1fr);
  margin-bottom: 14px;
}

.escalation-box,
.acceptance-party {
  background: #f8fbfc;
  border: 1px solid #dbe6ea;
  border-radius: 9px;
  padding: 16px;
}

.escalation-box h3,
.acceptance-party h3 {
  color: #00243d;
  font-size: 14px;
  margin: 0 0 10px;
}

.escalation-arrow {
  color: #42b0d5;
  font-size: 28px;
  font-weight: 800;
  text-align: center;
}

.acceptance-statement {
  background: #f4fbfd;
  border-left: 4px solid #42b0d5;
  color: #325665;
  line-height: 1.55;
  margin: 0 0 16px;
  padding: 14px 16px;
}

.acceptance-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.acceptance-party .field-grid {
  margin: 12px 0 0;
}

.agreement-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 18px;
}

.form-message {
  margin-top: 14px;
}

.confirmation-note {
  color: #667d88;
  font-size: 12px;
  margin: 12px 0 0;
}

.page-state,
.load-error-state {
  align-items: center;
  display: flex;
  gap: 14px;
  min-height: 220px;
}

.load-error-state {
  align-items: flex-start;
  flex-direction: column;
}

@media (max-width: 1000px) {
  .field-grid--four,
  .agreement-meta {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 680px) {
  .bau-heading {
    flex-direction: column;
    gap: 12px;
  }

  .agreement-meta,
  .field-grid--two,
  .field-grid--four,
  .acceptance-grid {
    grid-template-columns: 1fr;
  }

  .escalation-grid {
    grid-template-columns: 1fr;
  }

  .escalation-arrow {
    transform: rotate(90deg);
  }

  .agreement-card {
    padding: 16px;
  }

  .agreement-actions {
    justify-content: stretch;
  }

  .agreement-actions mc-button {
    flex: 1 1 100%;
  }
}
</style>
