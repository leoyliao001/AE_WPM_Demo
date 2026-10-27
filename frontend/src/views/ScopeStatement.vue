<template>
  <PageShell title="Scope Statement" :show-header="false" full-width class="scope-page">
    <div class="scope-workspace">
      <nav class="breadcrumb" aria-label="Breadcrumb">
        <router-link :to="backTo"><mc-icon icon="mi-arrow-left" size="16" /> Toll Gates</router-link>
        <span aria-hidden="true">/</span>
        <span>Initiate</span>
        <span aria-hidden="true">/</span>
        <span class="breadcrumb__current">Scope Statement</span>
      </nav>

      <div v-if="loading" class="state-panel" role="status">
        <span class="loading-indicator" />
        <h1>Preparing your scope workspace</h1>
        <p>Loading project details, headcount agreements and evidence.</p>
      </div>
      <div v-else-if="!statement" class="state-panel" role="alert">
        <mc-icon icon="mi-file" size="32" />
        <h1>Unable to load Scope Statement</h1>
        <p>{{ error }}</p>
        <mc-button appearance="neutral" variant="outlined" label="Try again" @click="loadData" />
      </div>

      <template v-else>
        <header class="scope-hero">
          <div class="scope-hero__top">
            <div class="scope-heading">
              <p class="eyebrow">Project lifecycle <span /> Initiate</p>
              <div class="scope-heading__title">
                <h1>Scope Statement</h1>
                <span class="status-badge" :class="`status-badge--${statusKey}`">
                  <span class="status-dot" />{{ statusLabel }}
                </span>
              </div>
              <p class="scope-description">A clear agreement on what moves, what stays, and the capacity behind it.</p>
            </div>
            <div class="hero-actions">
              <span class="save-indicator" aria-live="polite">
                <span v-if="dirty" class="unsaved-dot" />
                {{ busy ? 'Saving changes...' : dirty ? 'Unsaved changes' : statement.saved ? 'All changes saved' : 'Not yet saved' }}
              </span>
              <div class="hero-actions__buttons">
                <mc-button appearance="neutral" variant="outlined" fit="small" label="Save draft" :disabled="!canEdit || isBusy" :loading="busy === 'save'" @click="saveData('save')" />
                <mc-button appearance="primary" fit="small" label="Submit statement" :disabled="!canEdit || isBusy || !ready" :loading="busy === 'submit'" @click="saveData('submit')" />
              </div>
            </div>
          </div>

          <div class="project-strip">
            <div class="project-identity">
              <span class="project-icon"><mc-icon icon="mi-file" size="20" /></span>
              <div>
                <span class="project-strip__label">Migration project</span>
                <strong>{{ statement.projectName }}</strong>
              </div>
              <span class="project-id">{{ statement.migrationRequestId }}</span>
            </div>
            <div class="project-owner">
              <span class="project-strip__label">Requestor</span>
              <span>{{ statement.requestor }}</span>
            </div>
          </div>

          <div class="metrics-grid" aria-label="Scope summary">
            <article class="metric-card">
              <div class="metric-card__top"><span>Intake ambition</span><mc-icon icon="mi-flag" size="18" /></div>
              <div class="metric-card__value">{{ formatNumber(ambition) }}<span>FTE</span></div>
              <p>Original migration baseline</p>
            </article>
            <article class="metric-card">
              <div class="metric-card__top"><span>Agreed to migrate</span><mc-icon icon="mi-check" size="18" /></div>
              <div class="metric-card__value">{{ totalDisplay('agreedFte') }}<span>FTE</span></div>
              <p>Across three job levels</p>
            </article>
            <article class="metric-card metric-card--teal">
              <div class="metric-card__top"><span>Locked final FTE</span><mc-icon icon="mi-shield" size="18" /></div>
              <div class="metric-card__value">{{ formatNumber(lockedTotal) }}<span>FTE</span></div>
              <p>{{ lockedCount }} of 3 job levels locked</p>
            </article>
            <article class="metric-card">
              <div class="metric-card__top"><span>Not agreed</span><mc-icon icon="mi-file" size="18" /></div>
              <div class="metric-card__value">{{ totalDisplay('notAgreedFte') }}<span>FTE</span></div>
              <p>Exceptions retained in scope review</p>
            </article>
            <article class="metric-card">
              <div class="metric-card__top"><span>Final vs. ambition</span><mc-icon icon="mi-chart-pie" size="18" /></div>
              <div class="metric-card__value">{{ coverage === null ? '—' : `${formatNumber(coverage)}%` }}</div>
              <p>{{ allFinalEntered ? `${formatNumber(finalTotal)} of ${formatNumber(ambition)} FTE` : 'Complete final FTE to calculate' }}</p>
            </article>
          </div>
        </header>

        <div v-if="error" class="notice notice--error" role="alert">
          <mc-icon icon="mi-flag" size="18" /><span>{{ error }}</span>
          <button type="button" class="notice-dismiss" aria-label="Dismiss error" @click="error = ''">×</button>
        </div>
        <div v-if="success" class="notice notice--success" role="status">
          <mc-icon icon="mi-check" size="18" /><span>{{ success }}</span>
        </div>
        <div v-if="statement.reviewRequired" class="notice notice--info" role="alert">
          <mc-icon icon="mi-flag" size="18" />
          <span>Scope review required: Intake source data has changed. Reopen for revision, review the updated sources and resubmit Scope before Business Case financials or submission can proceed.</span>
        </div>
        <div v-if="isSubmitted" class="notice notice--info">
          <mc-icon icon="mi-shield" size="18" />
          <span>Submitted {{ formatDate(statement.submittedAt) }} by {{ statement.submittedBy }}. This statement is now read-only.</span>
        </div>
        <div v-else-if="!canEdit" class="notice notice--info">
          <mc-icon icon="mi-shield" size="18" /><span>Read-only view. The original intake requestor can edit this statement.</span>
        </div>
        <form v-if="isSubmitted" class="detail-card scope-boundaries" @submit.prevent="reopenScope">
          <h2>Reopen for revision</h2>
          <p class="section-description">Authorised editors can reopen this submitted Scope as a draft. Existing job-level locks and evidence are preserved; unlock the relevant level normally before changing its agreement.</p>
          <label class="scope-revision-reason">Revision reason (required, maximum 2,000 characters)
            <textarea v-model="revisionReason" :disabled="isBusy" maxlength="2000" rows="2" required />
          </label>
          <button type="submit" class="scope-add-wave" :disabled="isBusy || !revisionReason.trim()">Reopen for revision</button>
        </form>

        <section class="agreement-card" aria-labelledby="agreement-title">
          <header class="section-heading">
            <div class="section-heading__main">
              <span class="section-icon"><mc-icon icon="mi-shield" size="22" /></span>
              <div><p class="eyebrow">Headcount agreement</p><h2 id="agreement-title">Define the final commitment</h2></div>
            </div>
            <span class="source-badge"><span /> Manually maintained</span>
          </header>
          <div class="agreement-intro">
            <p>Confirm final FTE by job level and attach supporting evidence before locking.</p>
            <span>{{ evidenceCount }} evidence file{{ evidenceCount === 1 ? '' : 's' }} attached</span>
          </div>
          <div class="table-scroll" tabindex="0" role="region" aria-label="Headcount agreement by job level">
            <table class="agreement-table">
              <thead>
                <tr>
                  <th scope="col">Job level</th>
                  <th scope="col">Agreed to migrate <span>Manual input · FTE</span></th>
                  <th scope="col">Final agreement <span>Whole numbers · FTE</span></th>
                  <th scope="col">Variance <span>Final − agreed</span></th>
                  <th scope="col" class="evidence-heading">Supporting evidence</th>
                  <th scope="col">Status</th>
                  <th scope="col" class="action-heading">Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="line in lines" :key="line.jobLevel" :class="{ 'agreement-row--locked': line.lockedAt }">
                  <th scope="row"><span class="job-level">Job level {{ line.jobLevel.slice(2) }}</span><span class="cell-caption">{{ line.jobLevel }}</span></th>
                  <td><input v-model="line.agreedFte" :aria-label="`${line.jobLevel} agreed FTE`" :disabled="!canEdit || isBusy || !!line.lockedAt" type="number" min="0" max="99999999.9999" step="0.0001" placeholder="0" class="number-input" /></td>
                  <td><input v-model="line.finalFte" :aria-label="`${line.jobLevel} final FTE`" :disabled="!canEdit || isBusy || !!line.lockedAt" type="number" min="0" max="99999999" step="1" placeholder="0" class="number-input number-input--final" /></td>
                  <td><span class="variance" :class="{ 'variance--negative': variance(line) < 0, 'variance--positive': variance(line) > 0 }">{{ varianceText(line) }}</span></td>
                  <td class="evidence-cell">
                    <ul v-if="line.evidence.length" class="evidence-list">
                      <li v-for="item in line.evidence" :key="item.id">
                        <button type="button" class="file-link" :disabled="isBusy" @click="downloadEvidence(item)">
                          <mc-icon icon="mi-file" size="15" /><span :title="item.name">{{ item.name }}</span><mc-icon icon="mi-arrow-to-bottom" size="14" />
                        </button>
                      </li>
                    </ul>
                    <label v-if="canEdit && !line.lockedAt" class="attach-button" :class="{ 'attach-button--busy': isBusy }">
                      <input type="file" :aria-label="`Attach evidence for ${line.jobLevel}`" accept=".pdf,.docx,.msg,.xlsx" :disabled="isBusy" @change="uploadEvidence(line.jobLevel, $event)" />
                      <mc-icon icon="mi-arrow-to-top" size="14" />{{ busy === `upload-${line.jobLevel}` ? 'Uploading...' : 'Attach evidence' }}
                    </label>
                    <span v-else-if="!line.evidence.length" class="cell-caption">No evidence attached</span>
                  </td>
                  <td>
                    <span class="status-badge status-badge--compact" :class="line.lockedAt ? 'status-badge--submitted' : 'status-badge--open'"><span class="status-dot" />{{ line.lockedAt ? 'Locked' : 'Open' }}</span>
                    <span v-if="line.lockedAt" class="cell-caption locked-caption" :title="`${line.lockedBy} · ${formatDate(line.lockedAt)}`">Agreement secured</span>
                  </td>
                  <td class="row-action">
                    <button v-if="canEdit && line.lockedAt" type="button" class="text-action text-action--muted" :disabled="isBusy" @click="saveData('unlock', { jobLevel: line.jobLevel })">Unlock</button>
                    <button v-else-if="canEdit" type="button" class="lock-button" :disabled="isBusy || !canLock(line)" :title="canLock(line) ? 'Save and lock this agreement' : 'Complete agreed, exception and final FTE, and attach evidence first'" @click="saveData('lock', { jobLevel: line.jobLevel })">
                      <mc-icon icon="mi-shield" size="14" />Lock final
                    </button>
                    <span v-else class="cell-caption">—</span>
                  </td>
                </tr>
              </tbody>
              <tfoot>
                <tr>
                  <th scope="row">Total FTE</th>
                  <td>{{ totalDisplay('agreedFte') }}</td>
                  <td>{{ totalDisplay('finalFte') }}</td>
                  <td><span class="variance" :class="{ 'variance--negative': totalVariance < 0 }">{{ totalVariance === null ? '—' : signedNumber(totalVariance) }}</span></td>
                  <td>{{ evidenceCount }} file{{ evidenceCount === 1 ? '' : 's' }} attached</td>
                  <td colspan="2">{{ lockedCount }} / 3 locked</td>
                </tr>
              </tfoot>
            </table>
          </div>
          <footer class="agreement-note">
            <mc-icon icon="mi-file" size="16" />
            <span>Agreed and exception figures are entered manually, not synced from Opportunity Assessment. Evidence: PDF, DOCX, MSG or XLSX · up to 20 MB per file.</span>
          </footer>
          <p v-if="aboveAgreed" class="agreement-warning">Final FTE exceeds the agreed figure for {{ aboveAgreed }}. Review the variance before submitting.</p>
        </section>

        <div class="details-grid">
          <section class="detail-card exception-card" aria-labelledby="exceptions-title">
            <header class="detail-heading">
              <div><p class="eyebrow">Scope reconciliation</p><h2 id="exceptions-title">Exceptions to migration</h2></div>
              <span class="count-badge">{{ totalDisplay('notAgreedFte') }} <small>FTE</small></span>
            </header>
            <p class="section-description">Record the capacity not agreed for migration.</p>
            <table class="exception-table">
              <thead><tr><th scope="col">Job level</th><th scope="col">Not agreed · FTE</th><th scope="col">% of ambition</th></tr></thead>
              <tbody>
                <tr v-for="line in lines" :key="line.jobLevel">
                  <th scope="row">Job level {{ line.jobLevel.slice(2) }}</th>
                  <td><input v-model="line.notAgreedFte" :aria-label="`${line.jobLevel} exception FTE`" :disabled="!canEdit || isBusy || !!line.lockedAt" type="number" min="0" max="99999999.9999" step="0.0001" placeholder="0" class="number-input" /></td>
                  <td>{{ exceptionPercentage(line.notAgreedFte) }}</td>
                </tr>
              </tbody>
            </table>
            <div class="reconciliation" :class="{ 'reconciliation--balanced': reconciled, 'reconciliation--gap': reconciliationGap !== null && !reconciled }">
              <mc-icon :icon="reconciled ? 'mi-check' : 'mi-chart-pie'" size="18" />
              <div>
                <strong>{{ reconciled ? 'Ambition fully reconciled' : reconciliationGap === null ? 'Complete the headcount picture' : `${formatNumber(Math.abs(reconciliationGap))} FTE ${reconciliationGap > 0 ? 'above' : 'below'} ambition` }}</strong>
                <span>{{ reconciliationGap === null ? 'Enter agreed and exception figures for all job levels.' : `${formatNumber(agreedTotal)} agreed + ${formatNumber(exceptionTotal)} exceptions / ${formatNumber(ambition)} ambition` }}</span>
              </div>
            </div>
            <router-link class="text-action oa-link" :to="{ path: `/migration-dashboard/${projectId}/opportunity-assessment`, query: { from: 'toll-gates', project: projectId } }">View Opportunity Assessment <span aria-hidden="true">↗</span></router-link>
          </section>

          <section class="detail-card narrative-card" aria-labelledby="narrative-title">
            <header class="detail-heading">
              <div><p class="eyebrow">Project boundaries</p><h2 id="narrative-title">High-level scope statement</h2></div>
              <span class="required-label">{{ statement.reviewRequired ? 'Review required' : isSubmitted ? 'Submitted' : 'Required' }}</span>
            </header>
            <p id="scope-help" class="section-description">Define the activities, locations and responsibilities included in this migration, and what remains out of scope.</p>
            <label for="scope-narrative" class="sr-only">High-level scope statement</label>
            <textarea id="scope-narrative" v-model="scopeText" :disabled="!canEdit || isBusy" maxlength="2000" aria-describedby="scope-help scope-character-count" placeholder="Describe the migration scope, including key activities, receiving locations and exclusions..." />
            <div class="narrative-footer">
              <span><mc-icon :icon="scopeText.trim() ? 'mi-check' : 'mi-file'" size="14" />{{ scopeText.trim() ? 'Scope statement provided' : 'Required before submission' }}</span>
              <span id="scope-character-count">{{ scopeText.length.toLocaleString() }} / 2,000</span>
            </div>
          </section>
        </div>

        <section class="detail-card scope-boundaries" aria-labelledby="scope-plan-title">
          <header class="detail-heading"><div><p class="eyebrow">Source record for Business Case and Charter</p><h2 id="scope-plan-title">Boundaries and migration waves</h2></div></header>
          <div class="scope-boundary-fields">
            <label>Out of scope<textarea v-model="outOfScope" :disabled="!canEdit || isBusy" rows="3" /></label>
            <label>Assumptions<textarea v-model="assumptions" :disabled="!canEdit || isBusy" rows="3" /></label>
          </div>
          <p class="section-description">Maintain actual migration waves here. Dates use YYYY-MM-DD and FTE must be a non-negative whole number. If waves are provided, their total must match final project FTE before submission. These source values are read-only in Business Case.</p>
          <div class="table-scroll">
            <table class="exception-table"><thead><tr><th>Wave name</th><th>Date (YYYY-MM-DD)</th><th>FTE</th><th>Action</th></tr></thead>
              <tbody><tr v-for="(wave, index) in waves" :key="index">
                <td><input v-model="wave.name" :aria-label="`Wave ${index + 1} name`" :disabled="!canEdit || isBusy" /></td>
                <td><input v-model="wave.date" type="date" :aria-label="`Wave ${index + 1} date`" :disabled="!canEdit || isBusy" /></td>
                <td><input v-model="wave.fte" type="number" min="0" step="1" :aria-label="`Wave ${index + 1} FTE`" :disabled="!canEdit || isBusy" /></td>
                <td><button type="button" :disabled="!canEdit || isBusy" :aria-label="`Remove wave ${index + 1}`" @click="waves.splice(index, 1)">Remove</button></td>
              </tr><tr v-if="!waves.length"><td colspan="4">No migration waves defined.</td></tr></tbody>
            </table>
          </div>
          <button type="button" class="scope-add-wave" :disabled="!canEdit || isBusy || waves.length >= 100" @click="waves.push({ name: '', date: '', fte: '' })">Add wave</button>
        </section>

        <footer class="readiness-bar">
          <div class="readiness-copy">
            <span class="readiness-icon" :class="{ 'readiness-icon--complete': !statement.reviewRequired && (ready || isSubmitted) }"><mc-icon :icon="!statement.reviewRequired && (ready || isSubmitted) ? 'mi-check' : 'mi-shield'" size="22" /></span>
            <div>
              <strong>{{ statement.reviewRequired ? 'Scope review required' : isSubmitted ? 'Scope commitment secured' : ready ? 'Ready to submit' : 'Build your scope commitment' }}</strong>
              <p>{{ statement.reviewRequired ? 'Review changed Intake sources and resubmit Scope to restore Business Case readiness.' : isSubmitted ? 'Final project FTE is recorded. This statement is frozen.' : 'Lock each job level and complete the scope statement to submit.' }}</p>
            </div>
          </div>
          <div class="readiness-steps" aria-label="Submission requirements">
            <span v-for="line in lines" :key="line.jobLevel" :class="{ 'readiness-step--done': line.lockedAt }"><span>{{ line.lockedAt ? '✓' : '○' }}</span>{{ line.jobLevel }}</span>
            <span :class="{ 'readiness-step--done': scopeText.trim() }"><span>{{ scopeText.trim() ? '✓' : '○' }}</span>Scope text</span>
          </div>
        </footer>
      </template>
    </div>
  </PageShell>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'
import { useUnsavedChanges } from '../composables/useUnsavedChanges.js'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-icon'

const route = useRoute()
const projectId = computed(() => String(route.params.id))
const backTo = computed(() => `/toll-gates?project=${projectId.value}`)
const statement = ref(null)
const lines = ref([])
const scopeText = ref('')
const outOfScope = ref('')
const assumptions = ref('')
const waves = ref([])
const revisionReason = ref('')
const loading = ref(true)
const busy = ref('')
const error = ref('')
const success = ref('')
const savedSnapshot = ref('')
const isBusy = computed(() => Boolean(busy.value))
const isSubmitted = computed(() => statement.value?.status === 'submitted')
const canEdit = computed(() => Boolean(statement.value?.canEdit) && !isSubmitted.value)
const ambition = computed(() => Number(statement.value?.ambitionFte || 0))
const lockedCount = computed(() => lines.value.filter((line) => line.lockedAt).length)
const lockedTotal = computed(() => lines.value.filter((line) => line.lockedAt).reduce((sum, line) => sum + Number(line.finalFte), 0))
const evidenceCount = computed(() => lines.value.reduce((sum, line) => sum + line.evidence.length, 0))
const agreedTotal = computed(() => sumField('agreedFte'))
const exceptionTotal = computed(() => sumField('notAgreedFte'))
const finalTotal = computed(() => sumField('finalFte'))
const allFinalEntered = computed(() => completeField('finalFte'))
const coverage = computed(() => allFinalEntered.value && ambition.value > 0 ? Math.round(finalTotal.value / ambition.value * 100) : null)
const totalVariance = computed(() => completeField('agreedFte') && allFinalEntered.value ? finalTotal.value - agreedTotal.value : null)
const reconciliationGap = computed(() => completeField('agreedFte') && completeField('notAgreedFte') ? agreedTotal.value + exceptionTotal.value - ambition.value : null)
const reconciled = computed(() => reconciliationGap.value !== null && Math.abs(reconciliationGap.value) < 0.00005)
const ready = computed(() => lockedCount.value === 3 && Boolean(scopeText.value.trim()))
const statusKey = computed(() => statement.value?.reviewRequired ? 'draft' : isSubmitted.value ? 'submitted' : ready.value ? 'ready' : 'draft')
const statusLabel = computed(() => statement.value?.reviewRequired ? 'Review required' : isSubmitted.value ? 'Submitted' : ready.value ? 'Ready to submit' : 'Draft')
const aboveAgreed = computed(() => lines.value.filter((line) => variance(line) > 0).map((line) => line.jobLevel).join(', '))
const dirty = computed(() => Boolean(statement.value) && (snapshot() !== savedSnapshot.value || !!revisionReason.value.trim()))
useUnsavedChanges(dirty, computed(() => isBusy.value || loading.value))

function validNumber(value, whole = false) {
  return value !== '' && value !== null && value !== undefined && Number.isFinite(Number(value)) &&
    Number(value) >= 0 && Number(value) <= 99999999.9999 && (!whole || Number.isInteger(Number(value)))
}

function completeField(key) {
  return lines.value.length === 3 && lines.value.every((line) => validNumber(line[key], key === 'finalFte'))
}

function sumField(key) {
  return lines.value.reduce((sum, line) => sum + (validNumber(line[key]) ? Number(line[key]) : 0), 0)
}

function formatNumber(value) {
  return Number(value).toLocaleString('en-GB', { maximumFractionDigits: 4 })
}

function totalDisplay(key) {
  return completeField(key) ? formatNumber(sumField(key)) : '—'
}

function signedNumber(value) {
  return `${value > 0 ? '+' : ''}${formatNumber(value)}`
}

function variance(line) {
  return validNumber(line.finalFte, true) && validNumber(line.agreedFte) ? Number(line.finalFte) - Number(line.agreedFte) : null
}

function varianceText(line) {
  const value = variance(line)
  return value === null ? '—' : signedNumber(value)
}

function exceptionPercentage(value) {
  return validNumber(value) && ambition.value > 0 ? `${(Number(value) / ambition.value * 100).toFixed(1)}%` : '—'
}

function canLock(line) {
  return validNumber(line.agreedFte) && validNumber(line.notAgreedFte) && validNumber(line.finalFte, true) && line.evidence.length > 0
}

function formatDate(value) {
  return value ? new Date(value).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' }) : ''
}

function snapshot() {
  return JSON.stringify({ text: scopeText.value, outOfScope: outOfScope.value, assumptions: assumptions.value, waves: waves.value, lines: lines.value.map((line) => [line.jobLevel, line.agreedFte, line.notAgreedFte, line.finalFte]) })
}

function applyResponse(data) {
  statement.value = data
  scopeText.value = data.scopeText
  outOfScope.value = data.outOfScope ?? ''
  assumptions.value = data.assumptions ?? ''
  waves.value = (data.waves || []).map(wave => ({ name: wave.name, date: wave.date, fte: wave.fte }))
  lines.value = data.lines.map((line) => ({
    ...line,
    agreedFte: line.agreedFte === null ? '' : Number(line.agreedFte),
    notAgreedFte: line.notAgreedFte === null ? '' : Number(line.notAgreedFte),
    finalFte: line.finalFte === null ? '' : line.finalFte
  }))
  savedSnapshot.value = snapshot()
}

function errorMessage(caught, fallback) {
  return caught?.response?.data?.error || caught?.response?.data?.detail || fallback
}

async function reopenScope() {
  if (!isSubmitted.value || isBusy.value || !revisionReason.value.trim()) return
  busy.value = 'revise'
  error.value = ''
  success.value = ''
  try {
    const { data } = await axios.post(`/api/migration-dashboard/projects/${projectId.value}/scope-statement/save/`, {
      action: 'revise', revision: statement.value.revision, reason: revisionReason.value.trim()
    })
    applyResponse(data)
    revisionReason.value = ''
    success.value = 'Scope reopened as a draft. Existing job-level locks and evidence are preserved.'
  } catch (caught) {
    error.value = errorMessage(caught, 'Unable to reopen Scope. Your reason is retained; reload if another editor has changed the record.')
  } finally {
    busy.value = ''
  }
}

async function loadData() {
  loading.value = true
  error.value = ''
  success.value = ''
  statement.value = null
  revisionReason.value = ''
  const id = projectId.value
  try {
    const { data } = await axios.get(`/api/migration-dashboard/projects/${id}/scope-statement/`)
    if (id === projectId.value) applyResponse(data)
  } catch (caught) {
    if (id === projectId.value) error.value = errorMessage(caught, 'Unable to load Scope Statement. Please try again.')
  } finally {
    if (id === projectId.value) loading.value = false
  }
}

async function persist(action, extra = {}) {
  if (waves.value.some(wave => !wave.name.trim() || !/^\d{4}-\d{2}-\d{2}$/.test(wave.date) ||
      Number.isNaN(Date.parse(wave.date)) || new Date(wave.date).toISOString().slice(0, 10) !== wave.date ||
      !validNumber(wave.fte, true))) {
    error.value = 'Each wave needs a name, valid YYYY-MM-DD date and non-negative integer FTE. Complete or remove unfinished rows before saving.'
    return false
  }
  const editableLines = lines.value.filter((line) => !line.lockedAt)
  if (editableLines.some((line) => ['agreedFte', 'notAgreedFte', 'finalFte'].some((key) =>
    line[key] !== '' && !validNumber(line[key], key === 'finalFte')
  ))) {
    error.value = 'Enter non-negative FTE values. Final FTE must be a whole number.'
    return false
  }
  const { data } = await axios.post(`/api/migration-dashboard/projects/${projectId.value}/scope-statement/save/`, {
    action,
    revision: statement.value.revision,
    scopeText: scopeText.value,
    outOfScope: outOfScope.value,
    assumptions: assumptions.value,
    waves: waves.value.map(wave => ({ name: wave.name.trim(), date: wave.date, fte: Number(wave.fte) })),
    lines: editableLines.map((line) => ({
      jobLevel: line.jobLevel,
      agreedFte: line.agreedFte === '' ? null : line.agreedFte,
      notAgreedFte: line.notAgreedFte === '' ? null : line.notAgreedFte,
      finalFte: line.finalFte === '' ? null : line.finalFte
    })),
    ...extra
  })
  applyResponse(data)
  return true
}

async function saveData(action, extra = {}) {
  if (!canEdit.value || isBusy.value) return
  busy.value = action
  error.value = ''
  success.value = ''
  try {
    if (await persist(action, extra)) {
      success.value = action === 'submit' ? 'Scope Statement submitted. The final agreement has been recorded.' :
        action === 'lock' ? `${extra.jobLevel} agreement locked with supporting evidence.` :
          action === 'unlock' ? `${extra.jobLevel} is open for editing.` : 'Draft saved successfully.'
    }
  } catch (caught) {
    error.value = errorMessage(caught, 'Unable to save your changes. Please try again.')
  } finally {
    busy.value = ''
  }
}

async function uploadEvidence(jobLevel, event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file || !canEdit.value || isBusy.value) return
  error.value = ''
  success.value = ''
  if (!/\.(pdf|docx|msg|xlsx)$/i.test(file.name) || file.size === 0 || file.size > 20 * 1024 * 1024) {
    error.value = 'Choose a non-empty PDF, DOCX, MSG or XLSX file no larger than 20 MB.'
    return
  }
  busy.value = `upload-${jobLevel}`
  try {
    // Persist editable values before the upload response replaces the local draft.
    if (!await persist('save')) return
    const form = new FormData()
    form.append('file', file)
    form.append('revision', String(statement.value.revision))
    const { data } = await axios.post(`/api/migration-dashboard/projects/${projectId.value}/scope-statement/evidence/${jobLevel}/`, form)
    applyResponse(data)
    success.value = `Evidence attached to ${jobLevel}.`
  } catch (caught) {
    error.value = errorMessage(caught, 'Unable to upload evidence. Your saved draft is retained.')
  } finally {
    busy.value = ''
  }
}

async function downloadEvidence(item) {
  error.value = ''
  try {
    const { data } = await axios.get(`/api/migration-dashboard/projects/${projectId.value}/scope-statement/evidence/download/${item.id}/`, { responseType: 'blob' })
    const url = URL.createObjectURL(data)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = item.name
    anchor.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch {
    error.value = 'Unable to download this evidence file. Please try again.'
  }
}

watch(projectId, loadData, { immediate: true })
</script>

<style scoped>
.scope-boundaries { margin-top: 24px; }
.scope-boundary-fields { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; }
.scope-boundary-fields label, .scope-revision-reason { display: flex; flex-direction: column; gap: 8px; font-size: 13px; }
.scope-boundary-fields textarea, .scope-revision-reason textarea { width: 100%; padding: 12px; border: 1px solid #bdcbd5; border-radius: 6px; font: inherit; resize: vertical; }
.scope-boundaries td input { width: 100%; min-width: 90px; padding: 8px; border: 1px solid #bdcbd5; border-radius: 5px; font: inherit; }
.scope-boundaries button { padding: 8px 12px; border: 1px solid #bdcbd5; border-radius: 5px; background: white; color: #17364b; cursor: pointer; }
.scope-boundaries button:disabled { opacity: .5; cursor: not-allowed; }
.scope-add-wave { margin-top: 16px; }
.scope-page {
  --scope-navy: #10314f;
  --scope-muted: #6f8292;
  --scope-line: #e4ebf0;
  --scope-teal: #0e8a7d;
  color: var(--scope-navy);
}
.scope-page mc-icon { color: inherit; }
.scope-page :deep(.page-content) { padding: 28px 32px 64px; }
.scope-workspace { width: 100%; max-width: 1520px; margin: 0 auto; }
.breadcrumb { display: flex; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 26px; color: #82919e; font-size: 12px; }
.breadcrumb a { display: inline-flex; align-items: center; gap: 8px; color: #526b80; text-decoration: none; }
.breadcrumb a:hover { color: #0077b8; }
.breadcrumb__current { color: var(--scope-navy); font-weight: 600; }
.scope-hero { border: 1px solid var(--scope-line); background: #f1f5f8; border-radius: 16px; padding: 28px; margin-bottom: 26px; }
.scope-hero__top { display: flex; justify-content: space-between; align-items: flex-start; gap: 24px; }
.eyebrow { color: #658195; font-size: 10px; font-weight: 700; letter-spacing: .13em; text-transform: uppercase; margin: 0 0 8px; }
.scope-heading > .eyebrow { display: flex; align-items: center; gap: 10px; color: #278bac; }
.eyebrow > span { width: 3px; height: 3px; background: #8eacbd; border-radius: 50%; }
.scope-heading__title { display: flex; align-items: center; flex-wrap: wrap; gap: 18px; }
h1 { font-family: 'Maersk Headline', 'Maersk Text', sans-serif; font-size: clamp(30px, 3vw, 44px); font-weight: 700; letter-spacing: -.045em; line-height: 1.1; margin: 0; }
.scope-description { margin: 12px 0 0; font-size: 13px; line-height: 1.7; color: var(--scope-muted); }
.hero-actions { display: flex; flex-direction: column; align-items: flex-end; gap: 13px; padding-top: 8px; flex-shrink: 0; }
.hero-actions__buttons { display: flex; gap: 10px; }
.save-indicator { display: inline-flex; align-items: center; gap: 6px; font-size: 11px; color: var(--scope-muted); }
.unsaved-dot { background: #d39a36; border-radius: 50%; width: 5px; height: 5px; }
.status-badge { display: inline-flex; align-items: center; gap: 7px; padding: 6px 11px; border-radius: 6px; font-size: 11px; font-weight: 600; white-space: nowrap; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.status-badge--draft, .status-badge--open { background: #fff4df; color: #926715; }
.status-badge--submitted, .status-badge--ready { background: #e5f3ed; color: #167462; }
.status-badge--compact { padding: 5px 9px; font-size: 10px; }
.project-strip { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 20px 0; margin-top: 20px; border-top: 1px solid #dfe7ed; }
.project-identity { display: flex; align-items: center; gap: 12px; min-width: 0; flex-wrap: wrap; }
.project-icon { display: flex; align-items: center; justify-content: center; width: 36px; height: 36px; background: #e3ecf3; border-radius: 9px; color: #41647f; }
.project-strip__label { display: block; font-size: 11px; color: var(--scope-muted); margin-bottom: 4px; }
.project-identity strong { font-size: 14px; font-weight: 600; overflow-wrap: anywhere; }
.project-id { font-size: 10px; font-weight: 600; color: #526f83; border: 1px solid #d9e3eb; padding: 5px 8px; border-radius: 5px; background: #fff9; overflow-wrap: anywhere; }
.project-owner { text-align: right; font-size: 11px; color: #526f83; overflow-wrap: anywhere; }
.metrics-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; }
.metric-card { background: white; border: 1px solid var(--scope-line); border-radius: 10px; padding: 16px 18px; box-shadow: 0 2px 3px #10314f03; }
.metric-card__top { display: flex; align-items: center; justify-content: space-between; gap: 8px; color: #8093a3; }
.metric-card__top > span { color: #677d8e; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .07em; }
.metric-card__value { margin-top: 15px; font-size: clamp(25px, 2.3vw, 34px); font-weight: 700; line-height: 1.15; letter-spacing: -.035em; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.metric-card__value > span { font-size: 10px; color: #8595a1; margin-left: 7px; font-weight: 400; letter-spacing: 0; }
.metric-card p { margin: 8px 0 0; color: var(--scope-muted); font-size: 11px; line-height: 1.6; }
.metric-card--teal { border-color: #b7dcd5; background: #f9fdfb; }
.metric-card--teal .metric-card__value, .metric-card--teal mc-icon { color: var(--scope-teal); }
.agreement-card, .detail-card { background: #fff; border: 1px solid var(--scope-line); border-radius: 12px; box-shadow: 0 3px 12px #10314f04; overflow: hidden; }
.section-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 22px 24px; border-bottom: 1px solid #edf1f4; }
.section-heading__main { display: flex; align-items: center; gap: 13px; }
.section-icon { display: flex; align-items: center; justify-content: center; background: #e8eff4; color: var(--scope-navy); width: 42px; height: 42px; border-radius: 10px; flex-shrink: 0; }
.section-heading .eyebrow { margin-bottom: 5px; font-size: 9px; }
h2 { margin: 0; font-size: 17px; line-height: 1.35; letter-spacing: -.02em; font-weight: 600; }
.source-badge { display: inline-flex; align-items: center; gap: 6px; border: 1px solid #dfe7ed; border-radius: 5px; color: #6b7f90; padding: 6px 9px; font-size: 10px; white-space: nowrap; }
.source-badge > span { width: 5px; height: 5px; border-radius: 50%; background: #9badba; }
.agreement-intro { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 16px 24px; color: var(--scope-muted); font-size: 12px; }
.agreement-intro p { margin: 0; line-height: 1.6; }
.agreement-intro > span { white-space: nowrap; font-size: 10px; }
.table-scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; text-align: left; }
.agreement-table { min-width: 1050px; }
.agreement-table thead { background: #f4f7fa; border-top: 1px solid #edf1f4; border-bottom: 1px solid var(--scope-line); }
.agreement-table thead th { padding: 13px 18px; font-size: 11px; color: #526c80; font-weight: 600; white-space: nowrap; }
.agreement-table thead th > span { display: block; font-size: 10px; font-weight: 400; color: #8796a3; margin-top: 4px; }
.agreement-table thead th:first-child, .agreement-table tbody th, .agreement-table tfoot th { padding-left: 24px; }
.agreement-table tbody th, .agreement-table tbody td { border-bottom: 1px solid #edf1f4; padding: 19px 18px; vertical-align: middle; }
.agreement-table tbody th { width: 145px; }
.job-level { display: block; font-weight: 600; font-size: 13px; white-space: nowrap; }
.cell-caption { display: block; font-size: 10px; color: #81929f; margin-top: 5px; font-weight: 400; line-height: 1.5; }
.locked-caption { font-size: 9px; }
.number-input { box-sizing: border-box; width: 104px; max-width: 100%; height: 36px; border: 1px solid #dce5ec; border-radius: 6px; padding: 6px 10px; background: #fff; font-family: inherit; font-size: 12px; color: var(--scope-navy); font-variant-numeric: tabular-nums; transition: border-color .15s, box-shadow .15s; }
.number-input--final { font-weight: 600; background: #fbfdff; }
.number-input::placeholder { color: #afbbc5; }
.number-input:disabled { background: #f4f7f9; border-color: #e9eef2; color: #6c8090; opacity: 1; }
.number-input:focus, textarea:focus { outline: none; border-color: #46a8cf; box-shadow: 0 0 0 3px #42b0d517; }
.variance { font-size: 12px; font-weight: 600; font-variant-numeric: tabular-nums; color: #7a8e9d; }
.variance--negative { color: #bb5757; }
.variance--positive { color: #287cab; }
.evidence-heading { width: 24%; }
.evidence-cell { min-width: 190px; }
.evidence-list { list-style: none; margin: 0 0 6px; padding: 0; display: flex; flex-direction: column; gap: 5px; }
.file-link { display: flex; align-items: center; gap: 7px; border: 0; background: none; padding: 0; color: #227fa4; cursor: pointer; font-family: inherit; font-size: 11px; width: 100%; text-align: left; }
.file-link span { max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-link mc-icon { flex-shrink: 0; }
.file-link:hover span { text-decoration: underline; }
.attach-button { position: relative; display: inline-flex; align-items: center; gap: 6px; color: #287b9e; font-size: 11px; font-weight: 600; border: 1px dashed #c8dce7; padding: 6px 9px; border-radius: 5px; cursor: pointer; background: #fbfdff; }
.attach-button:hover { background: #eef7fb; border-color: #6eb3cf; }
.attach-button input { position: absolute; inset: 0; opacity: 0; width: 100%; height: 100%; cursor: pointer; }
.attach-button:focus-within { outline: 2px solid #42b0d5; outline-offset: 3px; }
.attach-button--busy { opacity: .5; cursor: wait; }
.lock-button { display: inline-flex; align-items: center; justify-content: center; gap: 6px; border: 1px solid #cedfe9; background: #fff; color: #235573; padding: 8px 10px; border-radius: 6px; font-size: 10px; font-family: inherit; font-weight: 600; white-space: nowrap; cursor: pointer; }
.lock-button:hover:not(:disabled) { border-color: #0077b8; background: #f0f8fc; }
.lock-button:disabled { color: #98a8b4; border-color: #e6edf2; cursor: not-allowed; }
.text-action { color: #247da3; background: none; border: 0; padding: 0; font-family: inherit; font-size: 11px; font-weight: 600; text-decoration: none; cursor: pointer; }
.text-action:hover { text-decoration: underline; }
.text-action--muted { color: #738b9c; }
.action-heading, .row-action { text-align: right; padding-right: 24px !important; }
.agreement-table tfoot { background: #f3f7fa; }
.agreement-table tfoot th, .agreement-table tfoot td { padding: 15px 18px; font-size: 11px; font-weight: 600; color: #3a5b74; font-variant-numeric: tabular-nums; }
.agreement-table tfoot td:nth-child(5), .agreement-table tfoot td:nth-child(6) { color: #72899b; font-size: 10px; }
.agreement-note { display: flex; align-items: flex-start; gap: 8px; padding: 14px 24px; font-size: 11px; color: #8092a0; line-height: 1.7; }
.agreement-note mc-icon { flex-shrink: 0; margin-top: 1px; }
.agreement-warning { margin: 0; padding: 10px 24px; border-top: 1px solid #f2e7cf; background: #fffbf2; color: #99752f; font-size: 11px; }
.details-grid { display: grid; grid-template-columns: minmax(0, .85fr) minmax(0, 1.15fr); gap: 20px; margin-top: 22px; }
.detail-card { padding: 24px; }
.detail-heading { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.detail-heading .eyebrow { margin-bottom: 6px; font-size: 9px; }
.section-description { color: var(--scope-muted); font-size: 12px; line-height: 1.7; margin: 12px 0 18px; }
.count-badge { padding: 7px 10px; background: #f1f5f8; border: 1px solid #e8eef3; border-radius: 7px; font-size: 17px; font-weight: 600; white-space: nowrap; }
.count-badge small { color: #8797a2; font-size: 9px; font-weight: 400; margin-left: 2px; }
.exception-table thead th { background: #f5f8fa; font-size: 10px; font-weight: 500; color: #7d909f; padding: 10px; }
.exception-table thead th:last-child, .exception-table tbody td:last-child { text-align: right; }
.exception-table tbody th, .exception-table tbody td { padding: 10px; border-bottom: 1px solid #edf2f5; font-size: 12px; font-weight: 400; }
.exception-table tbody td:last-child { color: #6f8596; font-variant-numeric: tabular-nums; }
.exception-table .number-input { height: 31px; width: 90px; font-size: 11px; }
.reconciliation { display: flex; align-items: center; gap: 10px; background: #f5f8fa; border: 1px solid #e7edf2; border-radius: 7px; padding: 12px; margin-top: 16px; color: #6b8395; }
.reconciliation strong { display: block; font-size: 11px; font-weight: 600; }
.reconciliation span { display: block; font-size: 10px; line-height: 1.6; margin-top: 4px; }
.reconciliation--balanced { background: #f1f9f6; border-color: #dcefe7; color: #278571; }
.reconciliation--gap { background: #fffbf2; border-color: #f3e8d1; color: #9a7836; }
.oa-link { display: inline-flex; align-items: center; gap: 8px; margin-top: 17px; font-size: 10px; }
.required-label { color: #8093a3; border: 1px solid #e0e8ef; padding: 5px 9px; border-radius: 5px; font-size: 9px; }
.narrative-card { display: flex; flex-direction: column; }
textarea { box-sizing: border-box; resize: vertical; width: 100%; flex: 1; min-height: 210px; border: 1px solid #dce5ec; border-radius: 8px; padding: 16px; color: var(--scope-navy); background: #fcfdfe; font-family: inherit; font-size: 13px; line-height: 1.9; transition: border-color .15s, box-shadow .15s; }
textarea::placeholder { color: #9aaab6; }
textarea:disabled { background: #f7f9fa; opacity: 1; color: #587083; }
.narrative-footer { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; padding-top: 11px; color: #8b9ba7; font-size: 10px; }
.narrative-footer > span:first-child { display: inline-flex; align-items: center; gap: 6px; }
.readiness-bar { display: flex; align-items: center; justify-content: space-between; gap: 24px; margin-top: 22px; padding: 19px 22px; background: #f7f9fb; border: 1px solid var(--scope-line); border-radius: 10px; }
.readiness-copy { display: flex; align-items: center; gap: 13px; }
.readiness-icon { display: flex; align-items: center; justify-content: center; width: 38px; height: 38px; border-radius: 9px; background: #e8eff4; color: #6b8aa0; flex-shrink: 0; }
.readiness-icon--complete { background: #e5f3ed; color: var(--scope-teal); }
.readiness-copy strong { display: block; font-size: 12px; font-weight: 600; }
.readiness-copy p { margin: 5px 0 0; font-size: 10px; color: #7f929f; line-height: 1.6; }
.readiness-steps { display: flex; gap: 20px; flex-wrap: wrap; flex-shrink: 0; }
.readiness-steps > span { display: inline-flex; align-items: center; gap: 6px; color: #8a9ba8; font-size: 10px; }
.readiness-steps .readiness-step--done { color: #278571; }
.notice { display: flex; align-items: center; gap: 10px; border: 1px solid; border-radius: 8px; padding: 12px 16px; margin-bottom: 18px; font-size: 12px; line-height: 1.6; }
.notice > mc-icon { flex-shrink: 0; }
.notice--error { color: #ab4545; background: #fff7f6; border-color: #f3dbd7; }
.notice--success { color: #247b68; background: #f1faf6; border-color: #d9eee4; }
.notice--info { color: #4f738a; background: #f2f8fc; border-color: #dceaf3; }
.notice-dismiss { margin-left: auto; border: 0; background: none; color: inherit; cursor: pointer; font-size: 20px; }
.state-panel { text-align: center; padding: 90px 24px; border: 1px solid var(--scope-line); border-radius: 14px; background: #f7f9fb; color: var(--scope-muted); }
.state-panel h1 { font-size: 24px; color: var(--scope-navy); margin: 20px 0 10px; }
.state-panel p { font-size: 13px; line-height: 1.7; margin-bottom: 22px; }
.loading-indicator { display: inline-block; width: 24px; height: 24px; border: 2px solid #dce6ee; border-top-color: #42b0d5; border-radius: 50%; animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
button:focus-visible, a:focus-visible, .table-scroll:focus-visible { outline: 2px solid #42b0d5; outline-offset: 3px; border-radius: 4px; }
@media (min-width: 1700px) {
  .scope-page :deep(.page-content) { padding-top: 36px; }
  .scope-hero { padding: 32px; }
  .metric-card { padding: 19px 20px; }
}
@media (max-width: 1100px) {
  .scope-hero__top { flex-direction: column; }
  .hero-actions { flex-direction: row; align-items: center; justify-content: space-between; width: 100%; padding-top: 0; }
  .metrics-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .details-grid { grid-template-columns: 1fr 1fr; }
  .readiness-bar { align-items: flex-start; flex-direction: column; gap: 16px; }
}
@media (max-width: 760px) {
  .scope-page :deep(.page-content) { padding: 20px 16px 40px; }
  .breadcrumb { font-size: 10px; gap: 8px; margin-bottom: 20px; }
  .scope-hero { padding: 20px; border-radius: 12px; }
  .scope-heading__title { gap: 12px; }
  .hero-actions { align-items: flex-start; flex-direction: column; gap: 12px; }
  .metrics-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
  .metric-card { padding: 14px; }
  .metric-card:last-child { grid-column: 1 / -1; }
  .project-strip { align-items: flex-start; flex-direction: column; gap: 14px; margin-top: 18px; padding-bottom: 18px; }
  .project-owner { text-align: left; }
  .project-id { margin-left: 48px; }
  .section-heading { padding: 18px; align-items: flex-start; flex-direction: column; }
  .agreement-intro { align-items: flex-start; flex-direction: column; gap: 6px; padding: 14px 18px; }
  .agreement-note { padding: 14px 18px; }
  .details-grid { grid-template-columns: 1fr; gap: 16px; margin-top: 16px; }
  .detail-card { padding: 20px; }
  .readiness-bar { padding: 18px; }
  .readiness-steps { gap: 18px; }
  h2 { font-size: 16px; }
}
@media (prefers-reduced-motion: reduce) {
  .loading-indicator { animation: none; }
  .number-input, textarea { transition: none; }
}
</style>
