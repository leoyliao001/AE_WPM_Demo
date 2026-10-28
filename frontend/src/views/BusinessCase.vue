<template>
  <PageShell title="Business Case" :show-heading="false" :back-to="backTo" back-label="Back to Toll Gates" class="bc-page bc-workspace" full-width>
    <p v-if="loading" role="status">Loading Business Case…</p>
    <mc-notification v-if="error" appearance="error" fit="medium" heading="Unable to complete this action" :body="error" role="alert" />
    <mc-notification v-if="success" appearance="success" fit="medium" :body="success" role="status" />
    <mc-button v-if="!record && !loading" appearance="neutral" variant="outlined" fit="medium" label="Try again" @click="loadProject" />
    <template v-if="record">
      <header class="bc-hero">
        <div class="bc-toolbar">
          <div><mc-tag appearance="info" fit="small" label="Project lifecycle · Initiate" /><h1>Business Case</h1>
            <p class="bc-page-subtitle">Review project details, scope and financial value — then submit your business case for approval.</p>
            <p class="bc-project-identity">{{ record.projectName }} <span>{{ record.migrationRequestId }}</span></p>
          </div>
          <div class="bc-actions bc-no-print">
            <details class="bc-more-actions">
              <summary>More actions</summary>
              <div><mc-button appearance="neutral" variant="plain" fit="small" label="Reload latest" :disabled="blocked" @click="reload" />
                <mc-button appearance="neutral" variant="plain" fit="small" label="Print / Save PDF" :disabled="blocked" @click="printPage" />
                <mc-button appearance="neutral" variant="plain" fit="small" label="Save / refresh sources" :disabled="!editable || blocked" @click="persist('refresh')" /></div>
            </details>
            <mc-button appearance="neutral" variant="outlined" fit="medium" label="Save draft" :loading="pending" :disabled="!editable || blocked" @click="persist('save')" />
            <mc-button appearance="primary" fit="medium" label="Complete / submit" :disabled="!record.canSubmit || !editable || blocked || dirty || record.reviewRequired || record.sourceChanged" @click="persist('submit')" />
          </div>
        </div>
        <div class="bc-hero-meta">
          <mc-tag class="bc-record-status" :appearance="record.status === 'approved' ? 'success' : ['needs_review', 'returned'].includes(record.status) ? 'warning' : 'neutral-weak'" fit="small" :label="record.status.replaceAll('_', ' ')" />
          <span aria-live="polite">Revision {{ record.revision }} · {{ dirty ? 'Unsaved changes' : record.saved ? 'Saved' : 'Not yet saved' }}</span>
          <span v-if="record.updatedAt" class="bc-updated">Updated {{ date(record.updatedAt) }} · {{ record.updatedBy || '—' }}</span>
        </div>
      </header>
      <nav class="bc-section-nav bc-no-print" aria-label="Business Case sections">
        <a href="#bc-overview"><span><mc-icon icon="mi-map" size="20" /></span> Project overview</a>
        <a href="#bc-scope"><span><mc-icon icon="mi-file" size="20" /></span> Scope &amp; plan</a>
        <a href="#bc-financials"><span><mc-icon icon="mi-calculator" size="20" /></span> Financials</a>
        <a href="#bc-decision"><span><mc-icon icon="mi-clipboard-check" size="20" /></span> Justification &amp; approval</a>
      </nav>
      <mc-notification v-if="record.sourceChanged || record.reviewRequired" appearance="warning" fit="medium" heading="Source review required" role="status">
        Source data has changed or needs review.
        <template v-if="!editable">Enter a Revision reason, then select Open revision. Review Intake, Scope and cost rates, save / refresh sources, then Complete / submit again.</template>
        <template v-else>Review Intake, Scope and cost rates, then save / refresh sources before submitting.</template>
        Narrative is retained.
      </mc-notification>
      <p v-if="!editable" class="bc-note">This record is read-only. Submitted records stay locked until an authorised revision is opened.</p>
      <p v-if="dirty" class="bc-note bc-no-print">Save / refresh your changes before Complete / submit. The displayed financial result is the last server calculation.</p>

      <section class="bc-section" :class="{ 'bc-section--editing': editIntake }" aria-labelledby="bc-overview">
        <div class="bc-section-heading">
          <div class="bc-heading-group"><span class="bc-section-index"><mc-icon icon="mi-map" size="24" /></span><div><h2 id="bc-overview">Project overview</h2><p class="bc-section-subtitle">The source details behind your business case</p></div></div>
          <div class="bc-actions"><mc-tag appearance="neutral-weak" fit="small" label="Migration Intake" />
            <mc-button v-if="editable && !editIntake" class="bc-edit-button bc-no-print" appearance="secondary" fit="medium" icon="mi-pencil" label="Edit project details" :disabled="blocked" @click="startIntakeEdit" />
            <mc-tag v-if="editIntake" appearance="info" fit="small" label="Editing project details" />
          </div>
        </div>
        <dl v-if="!editIntake" class="bc-summary">
          <div v-for="field in intakeFields" :key="field.key"><dt>{{ field.label }}</dt><dd>{{ sourceValue(editIntake ? intakeDraft[field.key] : record.intake?.[field.key]) }}</dd></div>
        </dl>
        <mc-notification v-if="editIntake" class="bc-no-print" appearance="info" fit="medium" heading="You're editing the original project record." body="Changes will sync to Migration Intake. Changes to locations, function or dates may require Scope review." />
        <mc-notification v-if="editIntake && intakeIssues.length" appearance="warning" fit="medium" heading="Review project selections" role="status"><ul><li v-for="issue in intakeIssues" :key="issue">{{ issue }}</li></ul></mc-notification>
        <p v-if="editIntake" class="bc-note bc-no-print">Selections follow Migration Intake. Search is available for functions and multi-select fields; unavailable existing values are marked for review.</p>
        <fieldset v-if="editIntake && editable" :disabled="blocked" class="bc-fields bc-fields--columns bc-intake-fields bc-no-print">
          <template v-for="field in visibleIntakeFields" :key="field.key">
            <mc-multi-select v-if="field.list" :label="field.label" :value.prop="intakeDraft[field.key]" :disabled="blocked" listsearch fit="medium" width="full-width" optionsheight="320px" placeholder="Select one or more" @optionselected="changeIntakeChoice(field.key, $event)">
              <mc-option v-for="option in displayOptions(field.key)" :key="option.value" :value="option.value">{{ option.label }}</mc-option>
            </mc-multi-select>
            <mc-select v-else-if="choiceOptions(field.key) || field.key === 'location_strategy_custom'" :label="field.label" :value.prop="intakeDraft[field.key]" :disabled="blocked" :listsearch="field.key === 'function_name'" fit="medium" width="full-width" optionsheight="320px" :placeholder="`Select ${field.label.toLowerCase()}`" @optionselected="changeIntakeChoice(field.key, $event)">
              <mc-option v-for="option in field.key === 'location_strategy_custom' ? [{ value: 'Y', label: 'Yes' }, { value: 'N', label: 'No' }] : displayOptions(field.key)" :key="option.value" :value="option.value">{{ option.label }}</mc-option>
            </mc-select>
            <mc-textarea v-else-if="field.key === 'initial_rationale'" class="bc-intake-wide" :label="field.label" :value.prop="intakeDraft[field.key]" :disabled="blocked" fit="medium" :rows="3" @input="intakeDraft[field.key] = $event.target.value" />
            <mc-input v-else :label="field.label" :value.prop="intakeDraft[field.key]" :disabled="blocked" fit="medium" width="full-width" :type="field.type || 'text'" :min="field.key === 'target_end_date' ? intakeDraft.target_start_date : undefined" @input="intakeDraft[field.key] = $event.target.value" />
          </template>
        </fieldset>
        <div v-if="editIntake" class="bc-edit-footer bc-no-print">
          <span>Saving also includes any other unsaved Business Case changes.</span>
          <div class="bc-actions"><mc-button appearance="neutral" variant="outlined" fit="medium" label="Cancel editing" :disabled="blocked" @click="cancelIntakeEdit" /><mc-button appearance="primary" fit="medium" label="Save project details" :loading="pending" :disabled="blocked" @click="persist('save')" /></div>
        </div>
      </section>

      <section class="bc-section" aria-labelledby="bc-scope">
        <div class="bc-section-heading"><div class="bc-heading-group"><span class="bc-section-index"><mc-icon icon="mi-file" size="24" /></span><div><h2 id="bc-scope">Scope &amp; migration plan</h2><p class="bc-section-subtitle">Approved boundaries and delivery capacity</p></div></div>
          <router-link class="bc-no-print" :to="{ name: 'ScopeStatement', params: { id: record.projectId }, query: { from: 'toll-gates', project: record.projectId } }">Maintain Scope at source ↗</router-link>
        </div>
        <p class="bc-note">Read-only source: Scope Statement · {{ record.scope?.reviewRequired ? 'Review required' : record.scope?.status || 'Not available' }} · Revision {{ record.scope?.revision ?? '—' }}</p>
        <mc-notification v-if="record.scope?.reviewRequired" appearance="warning" fit="medium" heading="Scope review required" body="Intake source data has changed. Reopen Scope for revision, review the updated sources and resubmit it before Business Case financials or submission can proceed." role="alert" />
        <div class="bc-scope-grid">
          <article><h3>In scope</h3><p class="bc-source-text">{{ record.scope?.scopeText || 'Not provided' }}</p></article>
          <article><h3>Out of scope</h3><p class="bc-source-text">{{ record.scope?.outOfScope || 'Not provided' }}</p></article>
          <article><h3>Assumptions</h3><p class="bc-source-text">{{ record.scope?.assumptions || 'Not provided' }}</p></article>
        </div>
        <div class="bc-capacity"><span>Final project headcount</span><strong>{{ record.scope?.finalProjectFte ?? '—' }} <small>FTE</small></strong><span>Owned and locked in Scope</span></div>
        <div class="bc-capacity"><span>Migratable FTE</span><strong>{{ record.scope?.migratableFteConfirmed ? record.scope.migratableFte : '—' }} <small>FTE</small></strong><span>{{ record.scope?.migratableFteConfirmed ? 'Manually confirmed in Scope' : 'Manual confirmation pending in Scope' }}</span></div>
        <p class="bc-note">Migratable FTE is an independently confirmed Scope total. Financial calculations continue to use locked Final FTE by job level.</p>
        <div class="bc-plan-grid">
        <div class="bc-scroll"><table><caption>Locked Scope headcount</caption><thead><tr><th>Job level</th><th>Final FTE</th><th>Locked at</th></tr></thead>
          <tbody><tr v-for="line in record.scope?.lines || []" :key="line.jobLevel"><th>{{ line.jobLevel }}</th><td>{{ line.finalFte ?? '—' }}</td><td>{{ line.lockedAt ? date(line.lockedAt) : 'Not locked' }}</td></tr></tbody>
        </table></div>
        <div class="bc-scroll"><table><caption>Migration waves</caption><thead><tr><th>Wave</th><th>Date</th><th>FTE</th></tr></thead>
          <tbody><tr v-for="(wave, index) in record.scope?.waves || []" :key="index"><td>{{ wave.name }}</td><td>{{ wave.date }}</td><td>{{ wave.fte }}</td></tr>
            <tr v-if="!record.scope?.waves?.length"><td colspan="3">No waves defined in Scope.</td></tr>
          </tbody>
        </table></div>
        </div>
        <details class="bc-no-print"><summary>Scope audit log</summary><pre>{{ JSON.stringify(record.scope?.auditLog || [], null, 2) }}</pre></details>
      </section>

      <section class="bc-section" aria-labelledby="bc-financials">
        <div class="bc-section-heading"><div class="bc-heading-group"><span class="bc-section-index"><mc-icon icon="mi-calculator" size="24" /></span><div><h2 id="bc-financials">Financial assessment</h2><p class="bc-section-subtitle">A transparent view of cost, value and payback</p></div></div><mc-tag appearance="neutral-weak" fit="small" label="System calculated · USD" /></div>
        <h3 class="bc-input-title">Cost inputs &amp; adjustments</h3>
        <BusinessCaseFinancialInputs class="bc-no-print" :inputs="financialInputs" :disabled="!editable || blocked" />
        <dl class="bc-summary bc-print-only"><div><dt>One-time cost (USD)</dt><dd>{{ financialInputs.oneTimeCost || 'Not provided' }}</dd></div><div><dt>Adjustment (USD)</dt><dd>{{ financialInputs.adjustment }}</dd></div><div><dt>Adjustment reason</dt><dd>{{ financialInputs.adjustmentReason || 'Not provided' }}</dd></div></dl>
        <BusinessCaseFinancials :financials="record.financials" :stale="dirty" />
      </section>

      <section class="bc-section" aria-labelledby="bc-decision">
        <div class="bc-section-heading"><div class="bc-heading-group"><span class="bc-section-index"><mc-icon icon="mi-clipboard-check" size="24" /></span><div><h2 id="bc-decision">Business justification &amp; approval</h2><p class="bc-section-subtitle">Build the rationale. Align the decision.</p></div></div><mc-tag appearance="neutral-weak" fit="small" label="Business Case owned" /></div>
        <BusinessCaseDetails class="bc-no-print" :details="details" :disabled="!editable || blocked" />
        <div class="bc-print-only"><div v-for="field in detailFields" :key="field.key"><h3>{{ field.label }}</h3><p class="bc-print-value">{{ details[field.key] || 'Not provided' }}</p></div></div>
        <h3>Submission requirements</h3>
        <p class="bc-note">Only the original requestor can submit. Complete Scope and lock final FTE; provide ready financials, rationale, expected benefits, recommendation, business owner and target dates. Drafts can be saved without financial data.</p>
        <p v-if="!record.canSubmit" class="bc-warning">Submission is not currently available. Save / refresh to recheck source data and permissions; resolve the financial errors shown above.</p>
        <div class="bc-toolbar">
          <p v-if="record.approval">Approval: {{ record.approval.completed ? 'Completed' : `Step ${record.approval.step ?? '—'} of ${record.approval.seqLen ?? '—'}` }}</p>
          <p v-else class="bc-note">Complete / submit starts the existing approval chain. No separate Business Case approval process is created.</p>
          <router-link class="bc-no-print" :to="{ name: 'ApprovalCycle', query: { from: 'toll-gates', project: record.projectId } }">Open existing Approval Cycle ↗</router-link>
        </div>
        <form v-if="!editable && ['submitted', 'approved', 'needs_review'].includes(record.status)" class="bc-no-print" @submit.prevent="revise">
          <p class="bc-note">Opening a revision requires authorisation and a reason. The server controls whether this action is available to you.</p>
          <label>Revision reason<textarea v-model="revisionReason" :disabled="blocked" required rows="2" /></label>
          <mc-button type="submit" appearance="neutral" variant="outlined" fit="medium" label="Open revision" :disabled="blocked || !revisionReason.trim()" />
        </form>
        <div v-if="record.legacyFile">
          <h3>Historical file</h3><a :href="record.legacyFile.url" :download="record.legacyFile.name">{{ record.legacyFile.name }}</a>
          <span class="bc-note"> · {{ fileSize(record.legacyFile.size) }} · Retained historical attachment</span>
        </div>
        <p class="bc-note">This online record replaces the final-file upload. Export the current page with Print / Save PDF.</p>
        <BusinessCaseSavedSnapshot :snapshot="record.savedSnapshot" :history="record.financialHistory" />
        <details class="bc-no-print"><summary>Revision history</summary><pre>{{ JSON.stringify(record.history || [], null, 2) }}</pre></details>
        <details class="bc-no-print"><summary>Financial history</summary><pre>{{ JSON.stringify(record.financialHistory || [], null, 2) }}</pre></details>
        <details class="bc-no-print"><summary>Intake source history</summary><pre>{{ JSON.stringify(record.intakeHistory || [], null, 2) }}</pre></details>
      </section>
    </template>
  </PageShell>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import PageShell from '../components/PageShell.vue'
import BusinessCaseDetails from '../components/BusinessCaseDetails.vue'
import BusinessCaseFinancialInputs from '../components/BusinessCaseFinancialInputs.vue'
import BusinessCaseFinancials from '../components/BusinessCaseFinancials.vue'
import BusinessCaseSavedSnapshot from '../components/BusinessCaseSavedSnapshot.vue'
import { businessCaseDetailFields as detailFields, useBusinessCase } from '../composables/useBusinessCase.js'
import { useUnsavedChanges } from '../composables/useUnsavedChanges.js'
import '../styles/businessCase.css'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-tag'
import '@maersk-global/mds-components-core/mc-notification'
import '@maersk-global/mds-components-core/mc-multi-select'
import '@maersk-global/mds-components-core/mc-option'
import '@maersk-global/mds-components-core/mc-select'
import '@maersk-global/mds-components-core/mc-input'
import '@maersk-global/mds-components-core/mc-textarea'
import { migrationTypes } from '../data/intakeOptions'
import { regions, getAreasForRegion } from '../data/regionAreaMapping'
import { getCountriesForAreas } from '../data/areaCountryMapping'
import { functions, getProductsForFunction } from '../data/functionProductMapping'
import { customLocationStrategyOptions, getDefaultLocationStrategiesForAreas } from '../data/areaLocationStrategyMapping'

const route = useRoute()
const { record, details, financialInputs, loading, pending, error, success, dirty: ownedDirty, load, save } = useBusinessCase()
const editIntake = ref(false)
const intakeDraft = ref({})
const intakeBaseline = ref('')
const revisionReason = ref('')
const blocked = computed(() => loading.value || pending.value)
const editable = computed(() => !!record.value?.canEdit)
const dirty = computed(() => ownedDirty.value || (editIntake.value && JSON.stringify(intakeDraft.value) !== intakeBaseline.value) || !!revisionReason.value.trim())
const { canLeave } = useUnsavedChanges(dirty, blocked)
const backTo = computed(() => `/toll-gates?project=${route.query.project || route.params.id}`)
const intakeFields = [
  { key: 'project_name', label: 'Project name' }, { key: 'migration_type', label: 'Migration type' },
  { key: 'function_name', label: 'Function' }, { key: 'products', label: 'Products', list: true },
  { key: 'region', label: 'Region' }, { key: 'areas', label: 'Areas', list: true },
  { key: 'countries', label: 'Source countries', list: true },
  { key: 'default_location_strategies', label: 'Default destination sites', list: true },
  { key: 'custom_location_strategies', label: 'Custom destination sites', list: true },
  { key: 'location_strategy_custom', label: 'Custom location strategy' },
  { key: 'business_owner', label: 'Business owner' },
  { key: 'target_start_date', label: 'Target start date', type: 'date' },
  { key: 'target_end_date', label: 'Target end date', type: 'date' },
  { key: 'initial_rationale', label: 'Initial rationale' }
]
function resetIntake() {
  intakeDraft.value = Object.fromEntries(intakeFields.map(field => {
    const value = record.value?.intake?.[field.key]
    return [field.key, field.list ? [...(value || [])] : field.key === 'location_strategy_custom' ? (value ? 'Y' : 'N') : value ?? '']
  }))
  intakeBaseline.value = JSON.stringify(intakeDraft.value)
}
const intakeEditOrder = [
  'project_name', 'migration_type', 'function_name', 'products', 'region', 'areas',
  'countries', 'business_owner', 'location_strategy_custom', 'default_location_strategies',
  'custom_location_strategies', 'target_start_date', 'target_end_date', 'initial_rationale'
]
const visibleIntakeFields = computed(() => intakeEditOrder
  .map(key => intakeFields.find(field => field.key === key))
  .filter(field => field.key !== (intakeDraft.value.location_strategy_custom === 'Y' ? 'default_location_strategies' : 'custom_location_strategies')))
function choiceOptions(key) {
  const draft = intakeDraft.value
  const choices = {
    migration_type: migrationTypes.map(option => option.label),
    region: regions,
    areas: getAreasForRegion(draft.region),
    countries: getCountriesForAreas(draft.areas || []),
    function_name: functions,
    products: getProductsForFunction(draft.function_name),
    default_location_strategies: getDefaultLocationStrategiesForAreas(draft.areas || []),
    custom_location_strategies: customLocationStrategyOptions
  }
  return choices[key]
}
function displayOptions(key) {
  const choices = choiceOptions(key)
  const selected = intakeDraft.value[key]
  const values = Array.isArray(selected) ? selected : selected ? [selected] : []
  return [...choices.map(value => ({ value, label: value })),
    ...values.filter(value => !choices.includes(value)).map(value => ({ value, label: `${value} — unavailable, review required` }))]
}
const intakeIssues = computed(() => {
  const issues = []
  const original = record.value?.intake || {}
  for (const field of visibleIntakeFields.value) {
    const options = choiceOptions(field.key)
    if (!options) continue
    const value = intakeDraft.value[field.key]
    const values = field.list ? value || [] : value ? [value] : []
    if (values.some(item => !options.includes(item))) {
      issues.push(`${field.label} contains unavailable selections. Existing values are retained; select valid values when changing this field or its parent.`)
    }
  }
  if (intakeDraft.value.countries?.length > 1 ||
      intakeDraft.value[intakeDraft.value.location_strategy_custom === 'Y' ? 'custom_location_strategies' : 'default_location_strategies']?.length > 1) {
    issues.push('Financial calculation supports exactly one source country and one destination site. Multiple selections can be saved as a draft.')
  }
  if (intakeDraft.value.location_strategy_custom === 'Y' &&
      (!original.location_strategy_custom || JSON.stringify(intakeDraft.value.custom_location_strategies) !== JSON.stringify(original.custom_location_strategies))) {
    issues.push('New custom destination selections require approval at the Intake source before they can be used here.')
  }
  return issues
})
function changeIntakeChoice(key, event) {
  const control = event.currentTarget
  const value = Array.isArray(event.detail) ? event.detail.map(option => option.value) : event.detail?.value ?? control.value
  if (JSON.stringify(value) === JSON.stringify(intakeDraft.value[key])) return
  const dependencies = { region: ['areas', 'countries', 'default_location_strategies'], areas: ['countries', 'default_location_strategies'], function_name: ['products'] }
  const affected = dependencies[key] || []
  if (affected.some(field => intakeDraft.value[field]?.length) &&
      !window.confirm('Changing this selection affects related fields. Their current values will be retained and marked for review until you select valid replacements. Continue?')) {
    control.value = intakeDraft.value[key]
    return
  }
  intakeDraft.value[key] = value
}
async function startIntakeEdit() {
  resetIntake()
  editIntake.value = true
  await nextTick()
  document.querySelector('.bc-section--editing mc-input')?.focus({ preventScroll: true })
}
function cancelIntakeEdit() {
  if (JSON.stringify(intakeDraft.value) !== intakeBaseline.value &&
      !window.confirm('Discard unsaved Intake source changes? Business Case changes will be retained.')) return
  editIntake.value = false
}
watch(editIntake, (enabled) => {
  if (!enabled) resetIntake()
})
async function loadProject() {
  if (await load(route.params.id)) {
    editIntake.value = false
    revisionReason.value = ''
    resetIntake()
  }
}
async function reload() {
  if (canLeave()) await loadProject()
}
async function persist(action) {
  if (!editable.value || blocked.value) return
  const extra = editIntake.value ? { intake: Object.fromEntries(intakeFields.map(field => [
    field.key, field.list ? [...intakeDraft.value[field.key]] : field.key === 'location_strategy_custom' ? intakeDraft.value[field.key] === 'Y' : intakeDraft.value[field.key]
  ])) } : {}
  if (action === 'submit' && (!record.value.canSubmit || dirty.value)) return
  if (await save(action, extra)) {
    editIntake.value = false
    resetIntake()
  }
}
async function revise() {
  if (!revisionReason.value.trim() || blocked.value) return
  if (await save('revise', { reason: revisionReason.value.trim() })) revisionReason.value = ''
}
function sourceValue(value) {
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  return Array.isArray(value) ? value.join(', ') || 'Not provided' : value === null || value === undefined || value === '' ? 'Not provided' : String(value)
}
const date = value => value ? new Date(value).toLocaleString() : '—'
const fileSize = value => value === null || value === undefined ? 'Unknown size' : `${Number(value).toLocaleString()} bytes`
function printPage() {
  document.querySelectorAll('.bc-rate-basis').forEach(element => { element.open = true })
  window.print()
}
watch(() => route.params.id, loadProject, { immediate: true })
</script>

<style scoped>
.bc-print-only { display: none; }
@media print { .bc-print-only { display: block; } }
</style>
