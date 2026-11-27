<template>
  <PageShell
    title="Baseline & KPIs"
    :show-heading="false"
    :back-to="backTo"
    back-label="Back to Toll Gates"
    :show-back-link="false"
    full-width
  >
    <div class="bk-page">
      <div v-if="loading" class="bk-panel" role="status">Loading Baseline &amp; KPIs...</div>
      <div v-if="error" class="bk-alert bk-alert--error" role="alert">{{ error }}</div>
      <div v-if="success" class="bk-alert bk-alert--success" role="status">{{ success }}</div>

      <template v-if="record && !loading">
        <header class="bk-hero">
          <div class="bk-title-row">
            <div>
              <p class="bk-eyebrow">Monitor &amp; Control</p>
              <h1>Baseline &amp; KPIs</h1>
              <p class="bk-subtitle">Track weekly performance against the approved project baseline.</p>
            </div>
            <div class="bk-project"><strong>{{ record.projectName }}</strong><span>{{ record.migrationRequestId }}</span></div>
          </div>
          <div class="bk-metrics">
            <article><span>TOTAL COHORTS</span><strong>{{ record.cohorts.length }}</strong></article>
            <article><span>SETUP COMPLETE</span><strong>{{ setupCount }}</strong></article>
            <article><span>WEEKLY RESULTS</span><strong>{{ weeklyResultCount }}</strong></article>
            <article><span>PROJECT LOCATION</span><strong>{{ record.region }} · {{ record.areas.join(', ') || 'No area' }}</strong></article>
          </div>
        </header>

        <details class="bk-guide">
          <summary>How to use Baseline &amp; KPIs</summary>
          <ol>
            <li>Select countries and a Hypercare start date for each Cohort. Countries can belong to only one Cohort.</li>
            <li>Add KPI rows, complete the KPI definition fields, then save to lock them. Only the assigned Migration Manager or a Super Admin can unlock them with a recorded reason; saving changes locks them again.</li>
            <li>Country, Hypercare start date, and Additional Comments stay editable after setup is locked. Use <strong>Save Cohort details &amp; comments</strong> to persist those changes.</li>
            <li>Setup locking does not lock weekly results. Assigned weekly editors can enter and save results after setup is saved; results are compared with the chosen target baseline.</li>
            <li>To add monitoring time, select <strong>+ Extend Hypercare weeks</strong>, enter the number of weeks and a reason, then select <strong>Add weeks</strong>. The total cannot exceed 10 weeks.</li>
          </ol>
        </details>

        <div v-if="!record.cohorts.length" class="bk-panel bk-empty">
          <h2>No Resources Cohorts yet</h2>
          <p>Create cohorts in the project's Resources page. This page will show one card for each saved Cohort.</p>
          <mc-button appearance="primary" label="Open Resources" @click="openResources" />
        </div>

        <section
          v-for="cohort in record.cohorts"
          :key="cohort.name"
          class="bk-cohort bk-panel"
        >
          <header class="bk-cohort__head">
            <div>
              <p class="bk-eyebrow">Cohort</p>
              <h2>{{ cohort.name }}</h2>
              <p class="bk-cohort__meta">
                {{ countryLabel(cohort) }} · {{ cohort.weeks }} Hypercare weeks
                <span v-if="cohort.startDate"> · starts {{ formatDate(cohort.startDate) }}</span>
              </p>
            </div>
            <span class="bk-status" :class="{ 'bk-status--ready': cohort.setupSubmitted }">
              {{ cohort.setupSubmitted ? (cohort.setupLocked ? 'Setup locked' : 'Setup unlocked') : 'Setup required' }}
            </span>
          </header>

          <div class="bk-owner-grid">
            <p><strong>Setup owners (Area POC / Area SME / Migration Manager):</strong> {{ peopleText(['areaPoc', 'areaSmes', 'migrationManagers']) }}</p>
            <p><strong>Weekly editors (GSC SME / GSC Leaders / Migration Manager):</strong> {{ peopleText(['gscSmes', 'gscLeaders', 'migrationManagers']) }}</p>
          </div>

          <section class="bk-setup" aria-label="Cohort setup">
            <div class="bk-section-head">
              <div>
                <h3>Cohort setup</h3>
                <p>Choose countries and define each KPI before weekly results can be entered.</p>
                <p v-if="cohort.setupSubmitted" class="bk-lock-note">
                  {{ cohort.setupLocked
                    ? 'KPI definition fields are locked. Country, start date, comments, and assigned weekly results remain editable.'
                    : 'KPI definition fields are unlocked; saving the setup will lock them again. Cohort details, comments, and weekly results remain independently editable.' }}
                </p>
                <p v-if="!processOptions.length" class="bk-hint">Complete and save Opportunity Assessment to provide selected L3 Process options.</p>
              </div>
            </div>

            <div class="bk-setup-fields">
              <div class="bk-country-field">
                <div class="bk-field">
                  <span>COUNTRY SELECTION</span>
                  <mc-multi-select
                    label="COUNTRY SELECTION"
                    hiddenlabel
                    class="bk-country-select"
                    fit="medium"
                    width="full-width"
                    listsearch
                    optionsheight="260px"
                    placeholder="Select countries"
                    :value.prop="cohort.countries"
                    :disabled="!canEditDetails(cohort) || busy"
                    @optionselected="selectCountries(cohort, $event)"
                  >
                    <mc-option
                      v-for="country in availableCountries(cohort)"
                      :key="country"
                      :value="country"
                    >{{ country }}</mc-option>
                  </mc-multi-select>
                </div>
                <p class="bk-hint">Countries already assigned to another Cohort are unavailable.</p>
                <p v-if="!availableCountries(cohort).length" class="bk-hint">No eligible countries for this project's Region and Area.</p>
                <p class="bk-selected"><strong>Selected:</strong> {{ cohort.countries.join(', ') || 'None' }}</p>
              </div>
              <label class="bk-field">
                <span>Hypercare start date</span>
                <mc-input
                  label="Hypercare start date"
                  hiddenlabel
                  fit="medium"
                  width="full-width"
                  type="date"
                  :value.prop="cohort.startDate"
                  :disabled="!canEditDetails(cohort) || busy"
                  @input="cohort.startDate = $event.target.value"
                />
              </label>
              <div class="bk-hypercare-readonly">
                <span>HYPERCARE PERIOD</span>
                <strong>{{ cohort.weeks }} weeks</strong>
                <small>Maximum 10 weeks, including extensions.</small>
              </div>
            </div>

            <div class="bk-table-scroll">
              <table class="bk-table">
                <thead>
                  <tr>
                    <th>Country</th>
                    <th>Process</th>
                    <th>Dimension</th>
                    <th>KPI</th>
                    <th>KPI Definition / Formula</th>
                    <th>Frequency</th>
                    <th>Global Target (%)</th>
                    <th>Area Baseline (%)</th>
                    <th>Measure</th>
                    <th>Target Baseline</th>
                    <th v-for="(week, index) in cohort.weeks" :key="`week-header-${index}`">
                      Week {{ index + 1 }}<small>{{ weekRange(cohort, index) }}</small>
                    </th>
                    <th>Additional Comments</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="kpi in cohort.kpis" :key="kpi.id">
                    <td><strong>{{ countryLabel(cohort) }}</strong></td>
                    <td>
                      <mc-multi-select
                        label="Process"
                        hiddenlabel
                        fit="small"
                        width="full-width"
                        listsearch
                        placeholder="Select one or more L3 Processes"
                        :value.prop="kpi.process"
                        :disabled="!canEditDefinitions(cohort) || busy"
                        @optionselected="selectProcess(kpi, $event)"
                      >
                        <mc-option v-for="option in processOptions" :key="option" :value="option">{{ option }}</mc-option>
                      </mc-multi-select>
                    </td>
                    <td>
                      <mc-select
                        label="Dimension"
                        hiddenlabel
                        fit="small"
                        width="full-width"
                        :value.prop="kpi.dimension"
                        :disabled="!canEditDefinitions(cohort) || busy"
                        @optionselected="setSelect(kpi, 'dimension', $event)"
                      >
                        <mc-option value="">Select</mc-option>
                        <mc-option v-for="option in dimensionOptions" :key="option" :value="option">{{ option }}</mc-option>
                      </mc-select>
                    </td>
                    <td>
                      <mc-input
                        label="KPI"
                        hiddenlabel
                        fit="small"
                        width="full-width"
                        maxlength="50"
                        :value.prop="kpi.kpi"
                        :disabled="!canEditDefinitions(cohort) || busy"
                        @input="kpi.kpi = $event.target.value"
                      />
                      <small class="bk-count">{{ kpi.kpi.length }}/50</small>
                      <mc-button
                        v-if="canEditDefinitions(cohort) && cohort.kpis.length > 1"
                        appearance="neutral"
                        variant="outlined"
                        label="Remove KPI"
                        :disabled="busy"
                        @click="removeKpi(cohort, kpi.id)"
                      />
                    </td>
                    <td>
                      <mc-input
                        label="KPI Definition / Formula"
                        hiddenlabel
                        fit="small"
                        width="full-width"
                        maxlength="100"
                        :value.prop="kpi.definition"
                        :disabled="!canEditDefinitions(cohort) || busy"
                        @input="kpi.definition = $event.target.value"
                      />
                      <small class="bk-count">{{ kpi.definition.length }}/100</small>
                    </td>
                    <td>
                      <mc-select
                        label="Frequency"
                        hiddenlabel
                        fit="small"
                        width="full-width"
                        :value.prop="kpi.frequency"
                        :disabled="!canEditDefinitions(cohort) || busy"
                        @optionselected="setSelect(kpi, 'frequency', $event)"
                      >
                        <mc-option value="Weekly">Weekly</mc-option>
                      </mc-select>
                    </td>
                    <td>
                      <div class="bk-percent">
                        <mc-input
                          label="Global Target (%)"
                          hiddenlabel
                          fit="small"
                          width="full-width"
                          type="number"
                          step="1"
                          :value.prop="kpi.globalTarget"
                          :disabled="!canEditDefinitions(cohort) || busy"
                          @input="setInteger(kpi, 'globalTarget', $event)"
                        />
                        <span>%</span>
                      </div>
                    </td>
                    <td>
                      <div class="bk-percent">
                        <mc-input
                          label="Area Baseline (%)"
                          hiddenlabel
                          fit="small"
                          width="full-width"
                          type="number"
                          step="1"
                          :value.prop="kpi.areaBaseline"
                          :disabled="!canEditDefinitions(cohort) || busy"
                          @input="setInteger(kpi, 'areaBaseline', $event)"
                        />
                        <span>%</span>
                      </div>
                    </td>
                    <td>
                      <mc-select
                        label="Measure"
                        hiddenlabel
                        fit="small"
                        width="full-width"
                        :value.prop="kpi.measure"
                        :disabled="!canEditDefinitions(cohort) || busy"
                        @optionselected="setSelect(kpi, 'measure', $event)"
                      >
                        <mc-option v-for="option in measureOptions" :key="option" :value="option">{{ option }}</mc-option>
                      </mc-select>
                    </td>
                    <td>
                      <mc-select
                        label="Target Baseline"
                        hiddenlabel
                        fit="small"
                        width="full-width"
                        :value.prop="kpi.targetBaseline"
                        :disabled="!canEditDefinitions(cohort) || busy"
                        @optionselected="setSelect(kpi, 'targetBaseline', $event)"
                      >
                        <mc-option value="Global">Global</mc-option>
                        <mc-option value="Area">Area</mc-option>
                      </mc-select>
                    </td>
                    <td
                      v-for="(value, index) in kpi.weeklyValues"
                      :key="`${kpi.id}-week-${index}`"
                      :class="{ 'bk-week-cell--locked': !cohort.setupSubmitted || !record.permissions.weekly }"
                    >
                      <div class="bk-week-field">
                        <mc-input
                          :label="`Week ${index + 1} result`"
                          hiddenlabel
                          fit="small"
                          width="full-width"
                          type="number"
                          step="any"
                          placeholder="Result"
                          :value.prop="value"
                          :disabled="!cohort.setupSubmitted || !record.permissions.weekly || busy"
                          @input="setWeekValue(kpi, index, $event)"
                        />
                        <small
                          v-if="weekStatus(kpi, index)"
                          :class="weekStatus(kpi, index) === 'Met' ? 'bk-met' : 'bk-below'"
                        >{{ weekStatus(kpi, index) }}</small>
                      </div>
                    </td>
                    <td class="bk-comments-cell">
                      <mc-textarea
                        :label="`Additional Comments for ${kpi.kpi || 'KPI'}`"
                        hiddenlabel
                        :rows="2"
                        maxlength="500"
                        :value.prop="kpi.additionalComments"
                        :disabled="!canEditDetails(cohort) || busy"
                        @input="kpi.additionalComments = $event.target.value"
                      />
                      <small class="bk-count">{{ kpi.additionalComments.length }}/500</small>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="bk-actions">
              <div class="bk-actions__left">
                <mc-button
                  v-if="canEditDefinitions(cohort)"
                  appearance="neutral"
                  variant="outlined"
                  label="+ Add KPI row"
                  :disabled="busy || cohort.kpis.length >= 100"
                  @click="addKpi(cohort)"
                />
                <mc-button
                  v-if="cohort.setupSubmitted && cohort.setupLocked && record.permissions.unlock && !cohort.unlockOpen"
                  appearance="neutral"
                  variant="outlined"
                  label="Unlock KPI setup"
                  :disabled="busy"
                  @click="cohort.unlockOpen = true"
                />
                <mc-button
                  v-if="cohort.setupSubmitted && record.permissions.extend && !cohort.extensionOpen && cohort.weeks < maxWeeks"
                  appearance="neutral"
                  variant="outlined"
                  label="+ Extend Hypercare weeks"
                  :disabled="busy"
                  @click="cohort.extensionOpen = true"
                />
              </div>
              <div class="bk-actions__right">
                <mc-button
                  v-if="cohort.setupSubmitted && cohort.setupLocked && record.permissions.setup"
                  appearance="neutral"
                  variant="outlined"
                  label="Save Cohort details & comments"
                  :disabled="busy"
                  @click="saveDetails(cohort)"
                />
                <mc-button
                  v-if="canEditDefinitions(cohort)"
                  appearance="primary"
                  :label="cohort.setupSubmitted ? 'Save KPI setup and lock' : 'Save and lock KPI setup'"
                  :disabled="busy"
                  @click="saveSetup(cohort)"
                />
                <mc-button
                  v-if="canEditWeekly(cohort)"
                  appearance="primary"
                  label="Save weekly results"
                  :disabled="busy"
                  @click="saveWeekly(cohort)"
                />
              </div>
            </div>
            <div v-if="cohort.unlockOpen" class="bk-unlock-form">
              <label class="bk-field bk-unlock-reason">
                <span>Reason for unlocking KPI setup <b>*</b></span>
                <mc-textarea
                  label="Unlock reason"
                  hiddenlabel
                  :rows="3"
                  maxlength="2000"
                  :value.prop="cohort.unlockReason"
                  :disabled="busy"
                  @input="cohort.unlockReason = $event.target.value"
                />
              </label>
              <div class="bk-unlock-actions">
                <small>The reason, your account, and the unlock time will be recorded.</small>
                <div>
                  <mc-button
                    appearance="primary"
                    label="Unlock setup"
                    :disabled="busy || !cohort.unlockReason.trim()"
                    @click="unlockSetup(cohort)"
                  />
                  <mc-button
                    appearance="neutral"
                    variant="outlined"
                    label="Cancel"
                    :disabled="busy"
                    @click="cohort.unlockOpen = false"
                  />
                </div>
              </div>
            </div>
          </section>

          <ul v-if="cohort.setupUnlockHistory.length" class="bk-extension-history">
            <li v-for="(entry, index) in cohort.setupUnlockHistory" :key="`${entry.unlockedAt}-${index}`">
              KPI setup unlocked · {{ formatTimestamp(entry.unlockedAt) }} · {{ entry.by }} — {{ entry.reason }}
            </li>
          </ul>

          <section v-if="cohort.setupSubmitted && record.permissions.extend" class="bk-extension">
            <div class="bk-section-head">
              <div><h3>Hypercare extension</h3><p>Add dated weekly columns. Existing and additional weeks cannot exceed 10.</p></div>
            </div>
            <div v-if="cohort.extensionOpen" class="bk-extension-form">
              <label class="bk-field bk-extension-weeks">
                <span>Additional weeks (maximum {{ maxWeeks - cohort.weeks }})</span>
                <mc-input
                  label="Additional weeks"
                  hiddenlabel
                  type="number"
                  min="1"
                  :max="maxWeeks - cohort.weeks"
                  step="1"
                  :value.prop="cohort.additionalWeeks"
                  @input="cohort.additionalWeeks = $event.target.value"
                />
              </label>
              <label class="bk-field bk-extension-reason">
                <span>Reason for extension <b>*</b></span>
                <mc-textarea
                  label="Extension reason"
                  hiddenlabel
                  :rows="3"
                  maxlength="2000"
                  :value.prop="cohort.extensionReason"
                  @input="cohort.extensionReason = $event.target.value"
                />
              </label>
              <div class="bk-extension-actions">
                <p>New weekly columns will be added to the end of the Cohort table.</p>
                <div>
                  <mc-button
                    appearance="primary"
                    label="Add weeks"
                    :disabled="busy || !cohort.extensionReason.trim() || !Number(cohort.additionalWeeks) || Number(cohort.additionalWeeks) > maxWeeks - cohort.weeks"
                    @click="extendHypercare(cohort)"
                  />
                  <mc-button appearance="neutral" variant="outlined" label="Cancel" :disabled="busy" @click="cohort.extensionOpen = false" />
                </div>
              </div>
            </div>
            <ul v-if="cohort.extensionReasons.length" class="bk-extension-history">
              <li v-for="(entry, index) in cohort.extensionReasons" :key="`${entry.extendedAt}-${index}`">
                <strong>+{{ entry.additionalWeeks }} week{{ entry.additionalWeeks === 1 ? '' : 's' }}</strong>
                · {{ entry.extendedAt }} · {{ entry.by }} — {{ entry.reason }}
              </li>
            </ul>
          </section>
          <p v-else-if="cohort.setupSubmitted" class="bk-hint">
            Hypercare extension access: {{ peopleText(['gscSmes', 'gscLeaders', 'migrationManagers']) }}.
          </p>
        </section>
      </template>
    </div>
  </PageShell>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-input'
import '@maersk-global/mds-components-core/mc-multi-select'
import '@maersk-global/mds-components-core/mc-option'
import '@maersk-global/mds-components-core/mc-select'
import '@maersk-global/mds-components-core/mc-textarea'
import { useTopbarBackLink } from '../composables/useTopbarBackLink.js'
import PageShell from '../components/PageShell.vue'

const route = useRoute()
const router = useRouter()
const projectId = computed(() => String(route.params.id || ''))
const backTo = computed(() => `/toll-gates?project=${encodeURIComponent(projectId.value)}`)
useTopbarBackLink(backTo, 'Back to Toll Gates')
const endpoint = computed(() => `/api/migration-dashboard/projects/${projectId.value}/baseline-kpis/`)
const record = ref(null)
const loading = ref(true)
const busy = ref(false)
const error = ref('')
const success = ref('')
const maxWeeks = 10
const dimensionOptions = ['Service', 'Quality', 'Governance', 'Customer', 'Operating Model', 'Capacity']
const measureOptions = ['>=', '<=', '=', '>', '<']

const processOptions = computed(() => record.value?.processOptions || [])
const setupCount = computed(() => record.value?.cohorts.filter(cohort => cohort.setupSubmitted).length || 0)
const weeklyResultCount = computed(() => record.value?.cohorts.reduce(
  (count, cohort) => count + cohort.kpis.reduce(
    (rowCount, kpi) => rowCount + kpi.weeklyValues.filter(value => value !== null && value !== '').length,
    0,
  ),
  0,
) || 0)

async function load() {
  loading.value = true
  error.value = ''
  success.value = ''
  try {
    const { data } = await axios.get(endpoint.value)
    record.value = {
      ...data,
      cohorts: (data.cohorts || []).map(cohort => ({
        ...cohort,
        countries: [...(cohort.countries || [])],
        kpis: (cohort.kpis || []).map(kpi => ({
          ...kpi,
          process: processValues(kpi.process),
          kpi: kpi.kpi || '',
          definition: kpi.definition || '',
          additionalComments: kpi.additionalComments || '',
          weeklyValues: [...(kpi.weeklyValues || [])],
        })),
        extensionReasons: [...(cohort.extensionReasons || [])],
        setupUnlockHistory: [...(cohort.setupUnlockHistory || [])],
        extensionOpen: false,
        additionalWeeks: '1',
        extensionReason: '',
        unlockOpen: false,
        unlockReason: '',
      })),
    }
  } catch (caught) {
    error.value = caught.response?.data?.error || 'Unable to load Baseline & KPIs.'
  } finally {
    loading.value = false
  }
}

function countryLabel(cohort) {
  if (cohort.countries.length > 1) return 'Multiple'
  return cohort.countries[0] || '—'
}

function availableCountries(cohort) {
  const takenElsewhere = new Set(
    record.value.cohorts
      .filter(other => other.name !== cohort.name)
      .flatMap(other => other.countries),
  )
  return record.value.countries.filter(country => !takenElsewhere.has(country))
}

function selectCountries(cohort, event) {
  const selected = selectedValues(event)
  const eligible = new Set(availableCountries(cohort))
  cohort.countries = [...new Set(selected)].filter(country => eligible.has(country))
}

function selectedValues(event) {
  const selected = Array.isArray(event?.detail)
    ? event.detail
    : Array.isArray(event?.detail?.value)
      ? event.detail.value
      : []
  return selected
    .map(option => typeof option === 'string' ? option : option?.value)
    .filter(value => typeof value === 'string' && value)
}

function selectProcess(kpi, event) {
  kpi.process = [...new Set(selectedValues(event))]
}

function processValues(value) {
  const selected = Array.isArray(value) ? value : typeof value === 'string' ? [value] : []
  return [...new Set(selected
    .filter(item => typeof item === 'string')
    .map(item => item.trim())
    .filter(Boolean))]
}

function setSelect(target, field, event) {
  target[field] = event?.detail?.value ?? event?.target?.value ?? ''
}

function setInteger(target, field, event) {
  const value = event.target.value
  target[field] = value === '' ? '' : value
}

function setWeekValue(kpi, index, event) {
  const value = event.target.value
  kpi.weeklyValues[index] = value === '' ? null : value
}

function targetValue(kpi) {
  return kpi.targetBaseline === 'Global' ? Number(kpi.globalTarget) : Number(kpi.areaBaseline)
}

function isMet(kpi, value) {
  if (value === null || value === '' || !Number.isFinite(Number(value))) return null
  const actual = Number(value)
  const target = targetValue(kpi)
  switch (kpi.measure) {
    case '>=': return actual >= target
    case '<=': return actual <= target
    case '=': return actual === target
    case '>': return actual > target
    case '<': return actual < target
    default: return null
  }
}

function weekStatus(kpi, index) {
  const result = isMet(kpi, kpi.weeklyValues[index])
  return result === null ? '' : result ? 'Met' : 'Below target'
}

function canEditWeekly(cohort) {
  return Boolean(record.value?.permissions?.weekly && cohort?.setupSubmitted)
}

function canEditDefinitions(cohort) {
  return Boolean(
    record.value?.permissions?.setup
    && (!cohort?.setupSubmitted || !cohort?.setupLocked),
  )
}

function canEditDetails() {
  return Boolean(record.value?.permissions?.setup)
}

function peopleText(keys) {
  const people = keys.flatMap(key => record.value?.permissions?.people?.[key] || [])
  return [...new Set(people)].join(', ') || 'Not assigned'
}

function addKpi(cohort) {
  cohort.kpis.push({
    id: crypto.randomUUID(),
    process: [],
    dimension: '',
    kpi: '',
    definition: '',
    additionalComments: '',
    frequency: 'Weekly',
    globalTarget: '',
    areaBaseline: '',
    measure: '>=',
    targetBaseline: 'Area',
    weeklyValues: Array(cohort.weeks).fill(null),
  })
}

function removeKpi(cohort, id) {
  cohort.kpis = cohort.kpis.filter(kpi => kpi.id !== id)
}

async function saveAction(action, payload, message) {
  if (busy.value) return false
  busy.value = true
  error.value = ''
  success.value = ''
  try {
    const { data } = await axios.put(endpoint.value, {
      action,
      revision: record.value.revision,
      ...payload,
    })
    const preservedState = new Map(record.value.cohorts.map(cohort => [cohort.name, {
      extensionOpen: cohort.extensionOpen,
      unlockOpen: cohort.unlockOpen,
    }]))
    record.value = {
      ...data,
      cohorts: data.cohorts.map(cohort => ({
        ...cohort,
        countries: [...cohort.countries],
        kpis: cohort.kpis.map(kpi => ({
          ...kpi,
          process: processValues(kpi.process),
          additionalComments: kpi.additionalComments || '',
          weeklyValues: [...kpi.weeklyValues],
        })),
        extensionReasons: [...cohort.extensionReasons],
        setupUnlockHistory: [...(cohort.setupUnlockHistory || [])],
        extensionOpen: preservedState.get(cohort.name)?.extensionOpen || false,
        unlockOpen: preservedState.get(cohort.name)?.unlockOpen || false,
        additionalWeeks: '1',
        extensionReason: '',
        unlockReason: '',
      })),
    }
    success.value = message
    return true
  } catch (caught) {
    error.value = caught.response?.data?.error || 'Unable to save Baseline & KPI data.'
    return false
  } finally {
    busy.value = false
  }
}

async function saveSetup(cohort) {
  const message = cohort.setupSubmitted
    ? `${cohort.name} KPI setup saved and locked.`
    : `${cohort.name} KPI setup saved and locked. Weekly results are now enabled.`
  await saveAction('setup', { cohort }, message)
}

async function saveDetails(cohort) {
  await saveAction(
    'details',
    {
      cohort: {
        name: cohort.name,
        countries: [...cohort.countries],
        startDate: cohort.startDate,
        kpis: cohort.kpis.map(kpi => ({
          id: kpi.id,
          additionalComments: kpi.additionalComments,
        })),
      },
    },
    `${cohort.name} Cohort details and comments saved.`,
  )
}

async function unlockSetup(cohort) {
  if (!record.value?.permissions?.unlock || !cohort?.setupLocked) return
  const saved = await saveAction(
    'unlock',
    { cohortName: cohort.name, reason: cohort.unlockReason },
    `${cohort.name} KPI definition fields unlocked. Reason recorded.`,
  )
  if (saved) {
    const current = record.value.cohorts.find(item => item.name === cohort.name)
    if (current) current.unlockOpen = false
  }
}

async function saveWeekly(cohort) {
  if (!canEditWeekly(cohort)) return
  const saved = await saveAction(
    'weekly',
    {
      cohortName: cohort.name,
      kpis: cohort.kpis.map(kpi => ({
        id: kpi.id,
        weeklyValues: [...kpi.weeklyValues],
      })),
    },
    `${cohort.name} weekly results saved.`,
  )
  if (!saved) return
}

async function extendHypercare(cohort) {
  const added = Number(cohort.additionalWeeks)
  const saved = await saveAction(
    'extend',
    { cohortName: cohort.name, additionalWeeks: added, reason: cohort.extensionReason },
    `${cohort.name} extended by ${added} week${added === 1 ? '' : 's'}.`,
  )
  if (saved) {
    const current = record.value.cohorts.find(item => item.name === cohort.name)
    if (current) current.extensionOpen = false
  }
}

function weekRange(cohort, index) {
  if (!cohort.startDate) return ''
  const start = new Date(`${cohort.startDate}T00:00:00Z`)
  if (Number.isNaN(start.getTime())) return ''
  start.setUTCDate(start.getUTCDate() + index * 7)
  const end = new Date(start)
  end.setUTCDate(end.getUTCDate() + 6)
  const format = value => new Intl.DateTimeFormat('en-GB', {
    day: 'numeric',
    month: 'short',
    timeZone: 'UTC',
  }).format(value)
  return `${format(start)} – ${format(end)}`
}

function formatDate(value) {
  if (!value) return ''
  const parsed = new Date(`${value}T00:00:00`)
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleDateString('en-GB')
}

function formatTimestamp(value) {
  if (!value) return ''
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString('en-GB')
}

function openResources() {
  router.push(`/migration-dashboard/${projectId.value}/resources`)
}

onMounted(load)
</script>

<style scoped>
.bk-page { background: #f3f6f8; color: #17324d; min-height: 100%; padding: 18px 22px 32px; }
.bk-panel, .bk-hero { background: #fff; border: 1px solid #dbe5ea; border-radius: 8px; box-shadow: 0 3px 12px #163c500d; margin: 0 0 16px; padding: 18px; }
.bk-title-row, .bk-cohort__head, .bk-section-head { align-items: center; display: flex; gap: 16px; justify-content: space-between; }
.bk-title-row h1 { color: #002b45; font-size: 28px; margin: 2px 0 4px; }
.bk-subtitle, .bk-cohort__meta, .bk-section-head p { color: #62798a; margin: 0; }
.bk-eyebrow { color: #0077b8; font-size: 11px; font-weight: 800; letter-spacing: .1em; margin: 0; text-transform: uppercase; }
.bk-project { align-items: flex-end; color: #62798a; display: flex; flex-direction: column; font-size: 13px; gap: 4px; }
.bk-project strong { color: #17324d; font-size: 15px; }
.bk-metrics { display: grid; gap: 10px; grid-template-columns: repeat(4, minmax(0, 1fr)); margin-top: 20px; }
.bk-metrics article { background: #f4f7f9; border: 1px solid #e1e9ed; border-radius: 6px; min-height: 82px; padding: 12px; }
.bk-metrics article span { color: #657b8b; display: block; font-size: 10px; font-weight: 800; letter-spacing: .06em; }
.bk-metrics article strong { color: #002b45; display: block; font-size: 22px; margin-top: 7px; overflow-wrap: anywhere; }
.bk-metrics article:last-child strong { font-size: 15px; }
.bk-hypercare-readonly > span { color: #17324d; display: block; font-size: 12px; font-weight: 700; letter-spacing: .02em; }
.bk-guide { background: #fff; border: 1px solid #dbe5ea; border-radius: 8px; box-shadow: 0 3px 12px #163c500d; margin: 0 0 16px; padding: 13px 18px; }
.bk-guide summary { color: #005b83; cursor: pointer; font-size: 14px; font-weight: 700; }
.bk-guide ol { color: #526b7c; font-size: 13px; line-height: 1.6; margin: 12px 0 0; padding-left: 22px; }
.bk-guide li + li { margin-top: 5px; }
.bk-cohort { margin-top: 18px; }
.bk-cohort__head { border-bottom: 1px solid #e4ebef; padding-bottom: 12px; }
.bk-cohort__head h2 { color: #002b45; font-size: 22px; margin: 3px 0 5px; }
.bk-status { background: #fff0d9; border-radius: 20px; color: #8d5000; font-size: 12px; font-weight: 700; padding: 6px 12px; white-space: nowrap; }
.bk-status--ready { background: #e4f5ea; color: #16783a; }
.bk-owner-grid { display: grid; gap: 8px 18px; grid-template-columns: repeat(2, minmax(0, 1fr)); margin: 12px 0; }
.bk-owner-grid p { background: #eef6fa; border-left: 3px solid #0077b8; color: #526b7c; font-size: 12px; margin: 0; padding: 9px 11px; }
.bk-owner-grid strong { color: #17324d; }
.bk-section-head { align-items: flex-start; }
.bk-section-head h3 { color: #17324d; font-size: 16px; margin: 0 0 4px; }
.bk-section-head p { font-size: 12px; }
.bk-section-head .bk-lock-note { color: #526b7c; font-weight: 600; }
.bk-setup-fields { align-items: start; display: grid; gap: 14px; grid-template-columns: minmax(260px, 1.5fr) minmax(190px, 1fr) minmax(180px, 1fr); margin: 16px 0; }
.bk-country-field { min-width: 0; }
.bk-country-select { display: block; }
.bk-country-select::part(label-container) { color: #17324d; font-size: 12px; font-weight: 700; line-height: 1.3; }
.bk-country-select::part(field), .bk-field mc-input::part(input) { font-size: 16px; }
.bk-hint { color: #62798a; font-size: 12px; }
.bk-selected { color: #526b7c; font-size: 12px; margin: 10px 0 0; overflow-wrap: anywhere; }
.bk-field { color: #17324d; display: grid; font-size: 12px; font-weight: 700; gap: 6px; line-height: 1.3; }
.bk-field b { color: #c5221f; }
.bk-hypercare-readonly { background: #f4f7f9; border: 1px solid #e1e9ed; border-radius: 5px; padding: 11px; }
.bk-hypercare-readonly strong, .bk-hypercare-readonly small { display: block; margin-top: 7px; }
.bk-hypercare-readonly strong { color: #17324d; font-size: 16px; font-weight: 700; }
.bk-hypercare-readonly small { color: #62798a; font-size: 12px; line-height: 1.4; }
.bk-table-scroll { border: 1px solid #dbe5ea; margin-top: 14px; overflow: auto; }
.bk-table { border-collapse: collapse; min-width: 2200px; width: 100%; }
.bk-table th { background: #002b45; color: #fff; font-size: 11px; min-width: 120px; padding: 9px; text-align: left; vertical-align: top; }
.bk-table th small { color: #c7d8e2; display: block; font-size: 10px; font-weight: 400; margin-top: 4px; }
.bk-table td { border-bottom: 1px solid #e5ecef; min-width: 120px; padding: 7px; vertical-align: top; }
.bk-table td:first-child { color: #17324d; min-width: 100px; }
.bk-table td:nth-child(2) { min-width: 220px; }
.bk-table td:nth-child(4), .bk-table td:nth-child(5) { min-width: 190px; }
.bk-table td.bk-comments-cell { min-width: 220px; }
.bk-count { color: #657b8b; display: block; font-size: 10px; margin-top: 3px; text-align: right; }
.bk-percent { align-items: center; display: flex; gap: 5px; }
.bk-percent span { color: #526b7c; font-size: 12px; }
.bk-week-field { display: grid; gap: 5px; min-width: 130px; }
.bk-week-cell--locked { background: #f7f9fa; }
.bk-met { color: #16833c; font-size: 11px; font-weight: 800; }
.bk-below { color: #c5221f; font-size: 11px; font-weight: 800; }
.bk-actions { align-items: center; display: flex; flex-wrap: wrap; gap: 10px; justify-content: space-between; margin-top: 12px; }
.bk-actions__left, .bk-actions__right { align-items: center; display: flex; flex-wrap: wrap; gap: 10px; }
.bk-actions__right { margin-left: auto; }
.bk-unlock-form { background: #f7f9fa; border: 1px solid #dbe5ea; border-radius: 8px; margin-top: 12px; padding: 14px; }
.bk-unlock-reason { max-width: 760px; }
.bk-unlock-actions { align-items: center; border-top: 1px solid #e1e9ed; display: flex; flex-wrap: wrap; gap: 12px; justify-content: space-between; margin-top: 12px; padding-top: 12px; }
.bk-unlock-actions small { color: #62798a; font-size: 12px; }
.bk-unlock-actions > div { display: flex; flex-wrap: wrap; gap: 10px; }
.bk-extension { border-top: 1px solid #e4ebef; margin-top: 18px; padding-top: 15px; }
.bk-extension-form { align-items: start; background: #f7f9fa; border: 1px solid #e1e9ed; border-radius: 8px; display: grid; gap: 16px; grid-template-columns: minmax(180px, .7fr) minmax(300px, 2fr); margin: 14px 0 0; padding: 16px; }
.bk-extension-actions { align-items: center; border-top: 1px solid #e1e9ed; display: flex; flex-wrap: wrap; gap: 14px; grid-column: 1 / -1; justify-content: space-between; padding-top: 12px; }
.bk-extension-actions p { color: #62798a; font-size: 12px; margin: 0; }
.bk-extension-actions > div { display: flex; flex-wrap: wrap; gap: 10px; }
.bk-extension-history { color: #526b7c; font-size: 12px; margin: 12px 0 0; padding-left: 20px; }
.bk-alert { border-radius: 5px; margin: 0 0 12px; padding: 10px 14px; }
.bk-alert--error { background: #fff0ef; border: 1px solid #f1c7c3; color: #9c201b; }
.bk-alert--success { background: #e8f6ec; border: 1px solid #c3e3cb; color: #176f35; }
.bk-empty { text-align: center; }
.bk-empty h2 { color: #17324d; }
.bk-empty p { color: #62798a; }
@media (max-width: 900px) {
  .bk-page { padding: 12px; }
  .bk-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .bk-setup-fields, .bk-owner-grid { grid-template-columns: 1fr; }
  .bk-extension-form { grid-template-columns: minmax(150px, .7fr) minmax(0, 2fr); }
}
@media (max-width: 560px) {
  .bk-title-row, .bk-cohort__head, .bk-section-head { align-items: flex-start; flex-direction: column; }
  .bk-project { align-items: flex-start; }
  .bk-metrics { grid-template-columns: 1fr 1fr; }
  .bk-extension-form { grid-template-columns: 1fr; }
  .bk-extension-actions { align-items: flex-start; flex-direction: column; grid-column: auto; }
  .bk-extension-actions > div { justify-content: flex-end; width: 100%; }
  .bk-unlock-actions { align-items: flex-start; flex-direction: column; }
  .bk-unlock-actions > div { justify-content: flex-end; width: 100%; }
}
</style>
