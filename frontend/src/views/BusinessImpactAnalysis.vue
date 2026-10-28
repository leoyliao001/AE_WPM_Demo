<template>
  <PageShell title="Business Impact Analysis" :show-heading="false" :back-to="backTo" back-label="Back to Toll Gates" full-width>
    <div class="pa-page bia-page">
      <div v-if="loading" class="pa-panel" role="status">Loading Business Impact Analysis...</div>
      <div v-if="error" class="pa-feedback pa-feedback--error" role="alert">{{ error }} <button v-if="!record" class="pa-text-button" @click="load">Retry</button></div>
      <div v-if="success" class="pa-feedback pa-feedback--success" role="status">{{ success }}</div>
      <template v-if="record && !loading">
        <header class="pa-hero bia-hero">
          <div class="pa-heading">
            <div><p class="pa-eyebrow">Initiate / Business resilience</p><h1>Business Impact Analysis</h1><p class="pa-subtitle">BCP questionnaire · Understand the impact. Build continuity into the move.</p></div>
            <div class="pa-actions">
              <mc-button appearance="neutral" variant="outlined" label="Export Excel" :disabled="!!busy" @click="exportData" />
              <mc-button v-if="canEdit" appearance="primary" label="Save draft" :disabled="!!busy" @click="act('save')" />
            </div>
          </div>
          <div class="pa-project-meta"><strong>{{ record.projectName }}</strong><span>{{ record.migrationRequestId }}</span><span>{{ dirty ? 'Unsaved changes' : record.updatedAt ? `Last saved ${dateTime(record.updatedAt)}` : 'Not yet saved' }}</span><span class="pa-status" :class="`pa-status--${record.status}`">{{ label(record.status) }}</span></div>
          <div class="bia-overview">
            <div><span>Process coverage</span><strong>{{ record.questionnaires.length }} <small>questionnaire{{ record.questionnaires.length === 1 ? '' : 's' }}</small></strong></div>
            <div><span>Signed off</span><strong>{{ signedCount }} <small>/ {{ record.questionnaires.length }} processes</small></strong></div>
            <div><span>Attention flags</span><strong>{{ flagCount }} <small>across all processes</small></strong></div>
            <div><span>Project population</span><strong>{{ record.source.population ?? '—' }} <small>locked Final FTE</small></strong></div>
          </div>
        </header>
        <div v-if="!record.source.ready" class="pa-feedback">Draft preparation is available. Submission requires a submitted, fully locked Scope Statement. <router-link class="pa-link" :to="`/migration-dashboard/${projectId}/scope-statement`">Open Scope Statement</router-link></div>
        <div v-if="record.sourceChanged" class="pa-feedback">Source information has changed. Pre-filled values below are current; previous reviews no longer count. Review and save / resubmit each affected questionnaire. Source changes are captured in the audit log on the next save.</div>
        <div class="bia-layout">
          <aside class="bia-sidebar">
            <section class="pa-panel bia-processes">
              <p class="pa-eyebrow">One questionnaire per process</p>
              <h2>In-scope processes</h2>
              <input v-if="record.questionnaires.length > 4" v-model="processSearch" type="search" aria-label="Search processes" placeholder="Search process..." />
              <button v-for="item in filteredProcesses" :key="item.id" class="bia-process" :aria-pressed="selectedId === item.id" :disabled="dirty && selectedId !== item.id || !!busy" @click="selectedId = item.id">
                <strong>{{ item.process.name }}</strong><span>{{ label(item.status) }} · {{ progressFor(item).answered }}/10 answered</span>
              </button>
              <p v-if="!filteredProcesses.length" class="pa-note">No matching processes.</p>
              <p class="pa-note">Processes are grouped by L1 / L2 / L3 from Task details. Without structured processes, one project-wide Intake / Scope questionnaire is used.</p>
              <p v-if="record.archivedCount" class="pa-note">{{ record.archivedCount }} removed process record(s) retained in audit history.</p>
              <p v-if="dirty" class="pa-note">Save or reload this draft before switching processes.</p>
              <button v-if="dirty" class="pa-text-button" :disabled="!!busy" @click="load">Discard unsaved changes &amp; reload</button>
            </section>
            <nav v-if="questionnaire" class="bia-jump" aria-label="Questionnaire sections">
              <a href="#bia-context">01—05 · Process &amp; operating model</a>
              <a href="#bia-continuity">06—10 · Continuity &amp; contingency</a>
              <a href="#bia-review">Review &amp; sign-off</a>
            </nav>
          </aside>
          <main v-if="questionnaire" class="bia-main">
            <section class="pa-panel bia-process-heading">
              <div class="pa-section-heading"><div><p class="pa-eyebrow">BCP questionnaire</p><h2>{{ questionnaire.process.name }}</h2></div><span class="pa-status" :class="{ 'pa-status--confirmed': questionnaire.status === 'signed_off' }">{{ label(questionnaire.status) }}</span></div>
              <p>{{ questionnaire.process.path }} <span class="bia-source-tag">{{ questionnaire.process.origin }}</span></p>
              <div class="bia-progress"><span>{{ progress.answered }} of 10 questions answered</span><span>{{ Math.round(progress.answered * 10) }}%</span></div>
              <div class="bia-progress-track" role="progressbar" :aria-valuenow="progress.answered" aria-valuemin="0" aria-valuemax="10" aria-label="Questions answered"><i :style="{ width: `${progress.answered * 10}%` }" /></div>
              <p class="pa-note">Assigned to the locked Area POC / Area SME. <strong>Blue fields</strong> are read-only source data. Changes belong in the owning artefact.</p>
              <p v-if="questionnaire.status === 'submitted' || questionnaire.status === 'signed_off'" class="pa-note">Submitted {{ dateTime(questionnaire.submittedAt) }} by {{ questionnaire.submittedBy }}. Answers are frozen.</p>
            </section>
            <section id="bia-context" class="pa-panel bia-question-group">
              <p class="pa-eyebrow">Process &amp; operating model</p>
              <article class="bia-question">
                <h3><span>01</span>Is the process new to GSC, or already performed in a GSC location?</h3>
                <div class="bia-choices" role="group" aria-label="Process type">
                  <button v-for="choice in [{ value: 'new', text: 'New process' }, { value: 'existing', text: 'Existing in a GSC location' }]" :key="choice.value" :aria-pressed="answers.processType === choice.value" :disabled="!canEdit" @click="answers.processType = choice.value">{{ choice.text }}</button>
                </div>
              </article>
              <article class="bia-question">
                <h3><span>02</span>Details of the process being migrated</h3>
                <div class="bia-grid">
                  <div class="bia-prefill"><span>Vertical <em>From Intake</em></span><strong>{{ record.source.verticals.join(', ') || 'Not specified' }}</strong></div>
                  <div class="bia-prefill"><span>Process <em>From Task details / Intake</em></span><strong>{{ questionnaire.process.name }}</strong></div>
                  <div class="bia-prefill bia-span"><span>Subprocesses / project Scope <em>From Scope Statement</em></span><p>{{ record.source.subprocesses || 'Not yet defined in Scope Statement' }}</p></div>
                  <div v-if="questionnaire.process.activities.length" class="bia-prefill bia-span"><span>In-scope process activities <em>From Task details</em></span><p>{{ questionnaire.process.activities.join(' · ') }}</p></div>
                </div>
              </article>
              <article class="bia-question">
                <h3><span>03</span>SLA, region / area served and volumes</h3>
                <div class="bia-grid">
                  <label>SLA<textarea v-model="answers.sla" :disabled="!canEdit" maxlength="2000" rows="2" placeholder="e.g. 24-hour turnaround for amendments" /></label>
                  <div class="bia-prefill"><span>Region / Area served <em>From Intake</em></span><strong>{{ record.source.region }} / {{ record.source.areas.join(', ') }}</strong></div>
                  <label>Peak volume days in month<input v-model="answers.peakDays" :disabled="!canEdit" maxlength="500" placeholder="e.g. Days 1–3 and month-end" /></label>
                  <label>Peak volume months in year<input v-model="answers.peakMonths" :disabled="!canEdit" maxlength="500" placeholder="e.g. March, December; or No seasonal peak" /></label>
                </div>
              </article>
              <article class="bia-question">
                <h3><span>04</span>Number of FTE expected to migrate</h3>
                <div class="bia-grid">
                  <div class="bia-prefill"><span>Total project FTE <em>From locked Scope</em></span><strong>{{ record.source.population ?? 'Awaiting submitted Scope' }}</strong><small>Project-wide Final FTE, not a per-process allocation.</small></div>
                  <label>Language-dependent FTE (if any)<input v-model="answers.languageFte" :disabled="!canEdit" maxlength="500" placeholder="e.g. 4 FTE – Danish, or None" /><small>Intake dependencies: {{ dependencies }}</small></label>
                </div>
              </article>
              <article class="bia-question">
                <h3><span>05</span>Operating time for this process (UTC)</h3>
                <div class="bia-grid"><label>Start (UTC)<input v-model="answers.startUtc" type="time" :disabled="!canEdit" /></label><label>End (UTC)<input v-model="answers.endUtc" type="time" :disabled="!canEdit" /></label></div>
                <fieldset class="bia-days"><legend>Operating days</legend><label v-for="day in record.days" :key="day"><input v-model="operatingDays" type="checkbox" :value="day" :disabled="!canEdit" />{{ day }}</label></fieldset>
                <small class="pa-note">An end time earlier than the start means an overnight operating window.</small>
              </article>
            </section>
            <section id="bia-continuity" class="pa-panel bia-question-group">
              <p class="pa-eyebrow">Continuity &amp; contingency</p>
              <article class="bia-question">
                <h3><span>06</span>Which applications are currently used?</h3>
                <div class="bia-chips"><span v-for="app in applications" :key="app">{{ app }}<button :disabled="!canEdit" :aria-label="`Remove ${app}`" @click="answers.applications = applications.filter(item => item !== app)">×</button></span><small v-if="!applications.length" class="pa-note">No applications recorded.</small></div>
                <div v-if="canEdit" class="bia-app-picker"><label>Search or add an application<input v-model="applicationSearch" list="bia-applications" maxlength="128" placeholder="Select a suggestion or enter an application" @keydown.enter.prevent="addApplication" /></label><datalist id="bia-applications"><option v-for="app in record.applications.filter(item => !applications.includes(item))" :key="app" :value="app" /></datalist><mc-button appearance="neutral" variant="outlined" label="Add application" @click="addApplication" /></div>
              </article>
              <article class="bia-question">
                <h3><span>07</span>Which GSC currently performs this process, and which GSC will receive the scope?</h3>
                <div class="bia-grid">
                  <div v-if="answers.processType === 'new'" class="bia-prefill"><span>Current GSC <em>From Q1</em></span><strong>None — new process</strong></div>
                  <label v-else>Current GSC<input v-model="answers.currentGsc" :disabled="!canEdit" maxlength="500" placeholder="Current performing GSC location(s)" /></label>
                  <div class="bia-prefill"><span>Expected GSC for migration <em>From Intake</em></span><strong>{{ record.source.sites.join(', ') || 'Not specified in Intake' }}</strong></div>
                </div>
              </article>
              <article class="bia-question">
                <h3><span>08</span>Would you recommend two different GSCs for better resilience?</h3>
                <div class="bia-choices" role="group" aria-label="Recommend two GSCs"><button v-for="value in ['yes', 'no', 'maybe']" :key="value" :aria-pressed="answers.secondSite === value" :disabled="!canEdit" @click="setSecondSite(value)">{{ label(value) }}</button></div>
                <label class="pa-field">Recommendation rationale (optional)<textarea v-model="answers.secondSiteReason" :disabled="!canEdit" maxlength="2000" rows="2" placeholder="Consider backup coverage during peak periods." /></label>
                <small v-if="['yes', 'maybe'].includes(answers.secondSite)" class="pa-note">A second-site attention flag is included below. Add its owner and target date before submission.</small>
              </article>
              <article class="bia-question">
                <h3><span>09</span>Will the Area retain competent FTE as contingency support for the GSC?</h3>
                <div class="bia-choices" role="group" aria-label="Retain contingency support"><button v-for="value in ['yes', 'no']" :key="value" :aria-pressed="answers.retainSupport === value" :disabled="!canEdit" @click="answers.retainSupport = value">{{ label(value) }}</button></div>
                <label v-if="answers.retainSupport === 'yes'" class="pa-field">Retained support details<textarea v-model="answers.retainedDetails" :disabled="!canEdit" maxlength="2000" rows="2" placeholder="FTE, job level, availability and duration after hypercare" /></label>
              </article>
              <article class="bia-question">
                <h3><span>10</span>Any other information for setting up BCP in GSC?</h3>
                <label class="pa-field">Other BCP considerations<textarea v-model="answers.otherInformation" :disabled="!canEdit" maxlength="4000" rows="3" placeholder="Critical deadlines, dependencies, offline capability — or enter None." /></label>
              </article>
            </section>
            <section id="bia-review" class="pa-panel bia-review">
              <div class="pa-section-heading"><div><p class="pa-eyebrow">Assess / Mitigate / Review</p><h2>Review &amp; sign-off</h2></div><span class="pa-status">{{ Object.keys(questionnaire.reviews).length }} / 4 reviews</span></div>
              <p>Pay particular attention to critical, single-site, system-sensitive, backlog-prone, complex or crisis-impacting activities. Each flag and action needs an owner and target date.</p>
              <h3>Resilience attention flags</h3>
              <div class="bia-flag-picker"><label v-for="(name, key) in record.flagLabels" :key="key"><input type="checkbox" :checked="questionnaire.flags.some(flag => flag.id === key)" :disabled="!canEdit || key === 'second_site'" @change="toggleFlag(key)" />{{ name }}</label></div>
              <div v-for="flag in questionnaire.flags" :key="flag.id" class="bia-risk-row">
                <strong>{{ record.flagLabels[flag.id] }}</strong><label>Owner email<input v-model="flag.owner" type="email" :disabled="!canEdit" maxlength="254" /></label><label>Target date<input v-model="flag.dueDate" type="date" :disabled="!canEdit" /></label>
              </div>
              <div class="pa-section-heading bia-mitigation-heading"><h3>Mitigation actions</h3><button v-if="canEdit" class="pa-text-button" @click="addMitigation">+ Add action</button></div>
              <p v-if="!questionnaire.mitigations.length" class="pa-note">No mitigation actions recorded. Add at least one action when attention flags are present.</p>
              <article v-for="(action, index) in questionnaire.mitigations" :key="action.id" class="bia-action">
                <div class="pa-section-heading"><strong>Action {{ index + 1 }}</strong><button v-if="canEdit" class="pa-text-button" aria-label="Remove mitigation action" @click="questionnaire.mitigations = questionnaire.mitigations.filter(item => item.id !== action.id)">Remove</button></div>
                <label class="pa-field">Mitigation description<textarea v-model="action.description" :disabled="!canEdit" maxlength="2000" rows="2" /></label>
                <div class="bia-grid bia-grid--three"><label>Owner email<input v-model="action.owner" type="email" :disabled="!canEdit" maxlength="254" /></label><label>Target date<input v-model="action.dueDate" type="date" :disabled="!canEdit" /></label><label>Status<select v-model="action.status" :disabled="!canEdit"><option value="open">Open</option><option value="completed">Completed</option></select></label></div>
              </article>
              <h3 class="bia-mitigation-heading">Joint review <span class="bia-source-tag">From Stakeholder Registration</span></h3>
              <p class="pa-note">Assign and lock the four review roles in <router-link class="pa-link" :to="`/migration-dashboard/${projectId}/stakeholder-registration`">Stakeholder Registration</router-link>. BIA administrators may record a review on behalf of an assigned role; this is explicitly logged.</p>
              <label v-if="questionnaire.status === 'submitted'" class="pa-field">Review comment (optional)<textarea v-model="reviewComment" rows="2" maxlength="2000" :disabled="!!busy" /></label>
              <div class="bia-review-grid">
                <article v-for="(definition, role) in record.reviewRoles" :key="role" class="bia-review-card" :class="{ 'bia-review-card--done': questionnaire.reviews[role] }">
                  <div class="pa-section-heading"><strong>{{ definition.label }}</strong><span>{{ questionnaire.reviews[role] ? 'Reviewed' : 'Pending' }}</span></div>
                  <p>{{ record.source.reviewers[role].map(person => person.name).join(', ') || 'No locked reviewer assigned' }}</p>
                  <small v-if="questionnaire.reviews[role]">{{ questionnaire.reviews[role].by }}<br />{{ dateTime(questionnaire.reviews[role].at) }}<br />{{ questionnaire.reviews[role].comment }}<br v-if="questionnaire.reviews[role].adminOverride" /><span v-if="questionnaire.reviews[role].adminOverride">Administrator on behalf of assigned role</span></small>
                  <button v-if="questionnaire.status === 'submitted' && !questionnaire.reviews[role] && (record.permissions.admin || record.permissions.reviewRoles.includes(role))" class="pa-text-button" :disabled="!!busy || dirty || !record.source.reviewers[role].length" @click="act('review', { reviewRole: role, comment: reviewComment })">Record {{ definition.label }} review</button>
                </article>
              </div>
              <div v-if="canEdit && progress.blockers.length" class="pa-feedback">Before submission: {{ progress.blockers.join(' · ') }}</div>
              <div class="bia-footer">
                <span class="pa-note">All 10 answers are required for submission. Four joint reviews, including Area and Execution, are required for sign-off.</span>
                <mc-button v-if="canEdit" appearance="primary" label="Submit for review" :disabled="!!busy || !!progress.blockers.length" @click="act('submit')" />
                <mc-button v-if="questionnaire.status === 'submitted' && (record.permissions.admin || record.permissions.reviewRoles.some(role => ['area', 'execution'].includes(role)))" appearance="primary" label="Sign off" :disabled="!!busy || dirty || Object.keys(questionnaire.reviews).length !== 4" @click="act('sign_off')" />
              </div>
              <div v-if="questionnaire.status === 'signed_off'" class="pa-feedback pa-feedback--success">Signed off by {{ questionnaire.signedOffBy }} · {{ dateTime(questionnaire.signedOffAt) }}. This process is secured for the current source version.</div>
              <div v-if="record.permissions.edit && ['submitted', 'signed_off', 'needs_review'].includes(questionnaire.status)" class="bia-reopen">
                <label>Reason to reopen<textarea v-model="reopenReason" maxlength="2000" rows="2" placeholder="Explain why answers or reviews must be revised." :disabled="!!busy" /></label>
                <mc-button appearance="neutral" variant="outlined" label="Reopen questionnaire" :disabled="!!busy || !reopenReason.trim()" @click="act('reopen', { reason: reopenReason })" />
              </div>
            </section>
            <details class="pa-audit"><summary>Change history · {{ record.auditLog.length }} events</summary><p v-if="!record.auditLog.length">No saved changes yet.</p><p v-for="entry in [...record.auditLog].reverse()" :key="entry.revision">Revision {{ entry.revision }} · {{ label(entry.action) }} · {{ entry.by }} · {{ dateTime(entry.at) }}<span v-if="entry.reason"> · {{ entry.reason }}</span></p><p>Excel includes complete source snapshots and answer changes.</p></details>
          </main>
        </div>
      </template>
    </div>
  </PageShell>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import PageShell from '../components/PageShell.vue'
import { useProjectArtefact } from '../composables/useProjectArtefact.js'
import { exportArtefact } from '../utils/projectArtefactExport.js'
import { biaExportSections, questionnaireProgress } from '../utils/businessImpactAnalysis.js'
import '../styles/projectArtefacts.css'

const { record, projectId, backTo, loading, busy, error, success, dirty, load, save } = useProjectArtefact('business-impact-analysis')
const selectedId = ref('')
const processSearch = ref('')
const applicationSearch = ref('')
const reviewComment = ref('')
const reopenReason = ref('')
const questionnaire = computed(() => record.value?.questionnaires.find(item => item.id === selectedId.value))
const answers = computed(() => questionnaire.value?.answers || {})
const applications = computed(() => answers.value.applications || [])
const operatingDays = computed({ get: () => answers.value.operatingDays || [], set: value => { answers.value.operatingDays = value } })
const canEdit = computed(() => record.value?.permissions.edit && ['draft', 'needs_review'].includes(questionnaire.value?.status) && !busy.value)
const filteredProcesses = computed(() => record.value.questionnaires.filter(item => item.process.path.toLowerCase().includes(processSearch.value.toLowerCase())))
const progressFor = item => questionnaireProgress(item, record.value.source)
const progress = computed(() => questionnaire.value ? progressFor(questionnaire.value) : { answered: 0, blockers: [] })
const signedCount = computed(() => record.value.questionnaires.filter(item => item.status === 'signed_off').length)
const flagCount = computed(() => record.value.questionnaires.reduce((total, item) => total + item.flags.length, 0))
const dependencies = computed(() => record.value.source.languageDependencies.map(item => typeof item === 'string' ? item : JSON.stringify(item)).join(', ') || 'None specified')
const label = value => String(value).replaceAll('_', ' ').replace(/^./, c => c.toUpperCase())
const dateTime = value => value ? new Date(value).toLocaleString() : '—'
watch(record, value => {
  if (value && !value.questionnaires.some(item => item.id === selectedId.value)) selectedId.value = value.questionnaires[0]?.id || ''
})
watch(selectedId, () => { applicationSearch.value = ''; reviewComment.value = ''; reopenReason.value = '' })
function addApplication() {
  const name = applicationSearch.value.trim()
  if (!name || name.length > 128 || applications.value.length >= 50) {
    error.value = 'Enter an application name of 1–128 characters (maximum 50 applications).'
    return
  }
  if (applications.value.some(item => item.toLowerCase() === name.toLowerCase())) {
    error.value = 'This application is already recorded.'
    return
  }
  answers.value.applications = [...applications.value, name]
  applicationSearch.value = ''
  error.value = ''
}
function setSecondSite(value) {
  answers.value.secondSite = value
  const flags = questionnaire.value.flags
  if (value === 'no') questionnaire.value.flags = flags.filter(flag => flag.id !== 'second_site')
  else if (!flags.some(flag => flag.id === 'second_site')) flags.push({ id: 'second_site', owner: '', dueDate: '' })
}
function toggleFlag(id) {
  const flags = questionnaire.value.flags
  questionnaire.value.flags = flags.some(flag => flag.id === id) ? flags.filter(flag => flag.id !== id) : [...flags, { id, owner: '', dueDate: '' }]
}
function addMitigation() {
  if (questionnaire.value.mitigations.length >= 100) {
    error.value = 'A questionnaire can have at most 100 mitigation actions.'
    return
  }
  questionnaire.value.mitigations.push({ id: crypto.randomUUID(), description: '', owner: '', dueDate: '', status: 'open' })
}
async function act(action, extra = {}) {
  const ok = await save(action, { processId: questionnaire.value.id, questionnaire: questionnaire.value, ...extra })
  if (ok) { reopenReason.value = ''; reviewComment.value = '' }
}
function exportData() {
  error.value = ''
  try { exportArtefact(record.value, 'business-impact-analysis', biaExportSections(record.value)) }
  catch (caught) { error.value = `Unable to export Excel: ${caught.message}` }
}
</script>

<style scoped>
.bia-page { max-width: 1540px; }
.bia-hero { border-top-color: #1d7f91; background: linear-gradient(115deg, #f1f8f9, #fff 75%); }
.bia-overview { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); margin-top: 26px; border-top: 1px solid #dfe7ec; padding-top: 22px; gap: 20px; }
.bia-overview > div { border-right: 1px solid #dfe7ec; padding-right: 16px; }
.bia-overview > div:last-child { border: 0; }
.bia-overview span { display: block; font-size: 11px; text-transform: uppercase; letter-spacing: .06em; color: #607989; }
.bia-overview strong { display: block; font-size: 28px; margin-top: 8px; }
.bia-overview small { font-size: 12px; font-weight: 400; color: #607989; }
.bia-layout { display: grid; grid-template-columns: 260px minmax(0, 1fr); gap: 22px; align-items: start; }
.bia-sidebar { position: sticky; top: 20px; }
.bia-processes { padding: 20px 14px; }
.bia-processes h2 { margin: 10px 6px 16px; }
.bia-processes > input { width: 100%; margin-bottom: 12px; }
.bia-processes .pa-note { padding: 0 6px; font-size: 11px; }
.bia-process { display: block; width: 100%; background: #fff; border: 1px solid transparent; text-align: left; padding: 13px 12px; border-radius: 7px; cursor: pointer; margin-bottom: 6px; color: #143247; }
.bia-process[aria-pressed="true"] { background: #edf7f9; border-color: #b7dfe7; }
.bia-process strong { display: block; font-size: 13px; overflow-wrap: anywhere; }
.bia-process span { display: block; font-size: 11px; color: #607989; margin-top: 6px; }
.bia-process:disabled { cursor: not-allowed; opacity: .6; }
.bia-jump { display: grid; gap: 14px; padding: 22px 10px; }
.bia-jump a { color: #607989; font-size: 12px; text-decoration: none; }
.bia-jump a:hover { color: #00789e; }
.bia-main { min-width: 0; }
.bia-process-heading h2 { margin-top: 6px; }
.bia-source-tag { display: inline-block; font-size: 10px; color: #16789c; border-radius: 4px; background: #edf7fc; padding: 4px 7px; margin-left: 5px; font-weight: 500; }
.bia-progress { display: flex; justify-content: space-between; font-size: 12px; color: #526d7f; margin-top: 18px; }
.bia-progress-track { background: #e8eff2; height: 5px; border-radius: 10px; margin-top: 10px; overflow: hidden; }
.bia-progress-track i { display: block; background: #248e9f; height: 100%; transition: width .2s; }
.bia-question-group { padding: 24px 28px; }
.bia-question { padding: 25px 0; border-bottom: 1px solid #e8eef2; scroll-margin-top: 24px; }
.bia-question:last-child { border-bottom: 0; padding-bottom: 4px; }
.bia-question h3 { display: flex; gap: 12px; align-items: baseline; font-size: 14px; line-height: 1.6; margin-bottom: 20px; font-weight: 600; }
.bia-question h3 > span { font-size: 12px; color: #248e9f; font-variant-numeric: tabular-nums; min-width: 22px; }
.bia-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; align-items: stretch; }
.bia-grid--three { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.bia-span { grid-column: 1 / -1; }
.bia-page label { display: flex; flex-direction: column; font-size: 12px; gap: 8px; color: #526d7f; min-width: 0; }
.bia-page label input:not([type="checkbox"]), .bia-page label select { width: 100%; min-width: 0; }
.bia-page label small { font-size: 11px; line-height: 1.6; }
.bia-prefill { background: #f0f7fc; border: 1px solid #dbeaf3; border-radius: 7px; padding: 13px 15px; color: #216584; min-width: 0; }
.bia-prefill > span { display: flex; justify-content: space-between; flex-wrap: wrap; font-size: 11px; gap: 8px; margin-bottom: 10px; }
.bia-prefill em { font-size: 9px; font-style: normal; text-transform: uppercase; letter-spacing: .04em; color: #3b87a4; }
.bia-prefill strong, .bia-prefill p { font-size: 13px; line-height: 1.7; color: #216584; overflow-wrap: anywhere; margin: 0; white-space: pre-wrap; font-weight: 500; }
.bia-prefill small { display: block; font-size: 10px; margin-top: 8px; line-height: 1.6; }
.bia-choices { display: flex; flex-wrap: wrap; gap: 8px; }
.bia-choices button { font: inherit; font-size: 12px; padding: 11px 20px; border: 1px solid #d4e0e7; border-radius: 6px; background: #fff; color: #526d7f; cursor: pointer; }
.bia-choices button[aria-pressed="true"] { border-color: #228d9e; background: #edf8fa; color: #176f7e; box-shadow: inset 0 0 0 1px #228d9e; }
.bia-choices button:disabled { cursor: not-allowed; }
.bia-days { display: flex; flex-wrap: wrap; gap: 14px; border: 0; padding: 18px 0 12px; margin: 0; }
.bia-days legend { font-size: 12px; color: #526d7f; padding: 18px 0 0; }
.bia-days label, .bia-flag-picker label { flex-direction: row; align-items: center; gap: 7px; }
.bia-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
.bia-chips > span { display: flex; align-items: center; background: #eef5f8; padding: 5px 8px 5px 12px; border-radius: 5px; font-size: 12px; overflow-wrap: anywhere; }
.bia-chips button { border: 0; background: none; font-size: 18px; color: #607989; margin-left: 8px; cursor: pointer; }
.bia-app-picker { display: flex; align-items: end; gap: 12px; }
.bia-app-picker label { flex: 1; }
.bia-flag-picker { display: flex; flex-wrap: wrap; gap: 12px 20px; margin: 18px 0; }
.bia-flag-picker label { padding: 8px 0; }
.bia-risk-row { display: grid; grid-template-columns: 1fr 1.3fr 1fr; gap: 14px; align-items: center; border-left: 3px solid #dba655; padding: 13px 15px; margin-bottom: 10px; background: #fffcf6; border-radius: 5px; }
.bia-risk-row > strong { font-size: 12px; }
.bia-mitigation-heading { margin-top: 30px !important; }
.bia-action { background: #f8fafb; border: 1px solid #e1e9ee; border-radius: 8px; padding: 18px; margin-top: 14px; font-size: 12px; }
.bia-review-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin-top: 20px; }
.bia-review-card { border: 1px solid #dfe7ec; border-radius: 8px; padding: 18px; min-width: 0; }
.bia-review-card .pa-section-heading { font-size: 12px; gap: 8px; }
.bia-review-card .pa-section-heading > span { font-size: 10px; color: #607989; }
.bia-review-card p, .bia-review-card small { overflow-wrap: anywhere; }
.bia-review-card small { display: block; font-size: 11px; line-height: 1.7; color: #607989; }
.bia-review-card--done { border-color: #b9ddcd; background: #f8fcfa; }
.bia-footer { display: flex; align-items: center; gap: 20px; justify-content: space-between; border-top: 1px solid #dfe7ec; margin-top: 26px; padding-top: 22px; }
.bia-footer .pa-note { max-width: 560px; }
.bia-reopen { display: flex; gap: 16px; align-items: end; border-top: 1px solid #dfe7ec; padding-top: 20px; margin-top: 24px; }
.bia-reopen label { flex: 1; }
.bia-audit, .pa-audit p { overflow-wrap: anywhere; }
@media (max-width: 1050px) {
  .bia-layout { grid-template-columns: 215px minmax(0, 1fr); gap: 16px; }
  .bia-risk-row { grid-template-columns: 1fr 1fr; }
  .bia-risk-row > strong { grid-column: 1 / -1; }
  .bia-grid--three { grid-template-columns: 1fr; }
}
@media (max-width: 760px) {
  .bia-layout { grid-template-columns: minmax(0, 1fr); gap: 0; }
  .bia-sidebar { position: static; }
  .bia-jump { display: none; }
  .bia-overview { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px 12px; }
  .bia-overview > div:nth-child(2) { border: 0; }
  .bia-overview strong { font-size: 25px; }
  .bia-overview small { display: block; line-height: 1.7; }
  .bia-grid, .bia-review-grid, .bia-risk-row { grid-template-columns: minmax(0, 1fr); }
  .bia-question-group { padding: 20px 18px; }
  .bia-app-picker, .bia-footer, .bia-reopen { flex-direction: column; align-items: stretch; }
  .bia-choices button { padding: 10px 14px; }
}
</style>
