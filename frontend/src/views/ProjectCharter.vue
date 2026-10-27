<template>
  <PageShell title="Project Charter" subtitle="Assembled from existing project artefacts. Only vision, deliverable notes and additional success criteria are maintained here."
    :back-to="backTo" :back-label="fromAdmin ? 'Back to Admin' : 'Back to Toll Gates'" full-width>
    <p v-if="loading" class="charter-state">Loading Project Charter...</p>
    <p v-if="error" class="charter-error" role="alert">{{ error }}</p>
    <p v-if="success" class="charter-success" role="status">{{ success }}</p>
    <template v-if="charter && !loading">
      <header class="charter-toolbar">
        <div>
          <strong>{{ charter.projectName }}</strong>
          <span class="charter-badge">DRAFT v0.{{ charter.revision }}</span>
          <p>{{ charter.migrationRequestId }} · Phase: Initiate · {{ charter.updatedAt ? `Last saved ${formatDate(charter.updatedAt)}` : 'Not yet saved' }}</p>
        </div>
        <button type="button" class="charter-primary" :disabled="busy" @click="save('save')">{{ busy ? 'Saving...' : 'Save draft' }}</button>
      </header>
      <aside class="charter-warning" aria-label="Draft storage information">
        <strong>{{ charter.saved ? 'Draft saved in the database.' : 'This project has no saved Charter draft yet.' }}</strong>
        <p>Click <strong>Save draft</strong> to store vision wording, phase notes and additional success criteria in the <code>project_charter</code> table. Changes are not saved automatically. Read-only sections are loaded live from their source artefacts, not copied into this table.</p>
        <RouterLink to="/project-attributes" class="charter-storage-link">Find saved drafts in Admin &gt; Project Charters (requires Project Charter access)</RouterLink>
      </aside>
      <p v-if="charter.sourceUpdated" class="charter-warning" role="status">Source updated since the last draft save. Read-only sections show live data; your vision wording has been preserved. Review the changes before saving.</p>

      <section class="charter-panel" aria-labelledby="charter-leadership">
        <div class="charter-section-head">
          <h2 id="charter-leadership"><span class="charter-number">1</span>Leadership</h2>
          <RouterLink :to="sourceLink('stakeholder-registration')" class="charter-source">From Stakeholder Registration · locked people</RouterLink>
        </div>
        <div class="charter-leadership">
          <div v-for="role in charter.sources.leadership" :key="role.role">
            <h3>{{ role.label }}</h3>
            <template v-if="role.people.length"><p v-for="person in role.people" :key="person.email" :title="person.email">{{ person.name }}</p></template>
            <p v-else class="charter-missing">Not assigned / not locked</p>
          </div>
        </div>
      </section>

      <section class="charter-panel" aria-labelledby="charter-vision">
        <div class="charter-section-head">
          <h2 id="charter-vision"><span class="charter-number">2</span>Desired outcome / vision</h2>
          <span class="charter-source charter-source--editable">Charter-owned · auto-drafted</span>
          <div class="charter-actions">
            <button type="button" :disabled="busy" @click="regenerate">Regenerate draft</button>
            <button type="button" @click="editingVision = !editingVision">{{ editingVision ? 'Done editing' : 'Edit' }}</button>
          </div>
        </div>
        <textarea v-if="editingVision" v-model="vision" rows="4" maxlength="10000" aria-label="Desired outcome / vision" :disabled="busy" />
        <p v-else class="charter-vision">{{ vision || 'No vision wording saved.' }}</p>
      </section>

      <section class="charter-panel" aria-labelledby="charter-facts">
        <div class="charter-section-head">
          <h2 id="charter-facts"><span class="charter-number">3</span>Key facts</h2>
          <span class="charter-source">From Intake + Scope + Business Case · read-only</span>
        </div>
        <div class="charter-facts">
          <div v-for="fact in charter.sources.facts" :key="fact.label" class="charter-fact">
            <h3>{{ fact.label }}</h3>
            <strong :class="{ 'charter-missing': fact.value === null || fact.value === '' }">{{ fact.value === null || fact.value === '' ? 'Source not provided' : fact.value }}</strong>
            <small>{{ fact.source }}</small>
          </div>
        </div>
      </section>

      <section class="charter-panel" aria-labelledby="charter-scope">
        <div class="charter-section-head">
          <h2 id="charter-scope"><span class="charter-number">4</span>Scope</h2>
          <RouterLink :to="sourceLink('scope-statement')" class="charter-source">From Scope Statement · read-only</RouterLink>
        </div>
        <div class="charter-columns">
          <div><h3>In scope</h3><p class="charter-preserve">{{ charter.sources.scope.inScope || 'Source not provided. Complete the Scope Statement.' }}</p></div>
          <div><h3>Out of scope</h3><p class="charter-preserve">{{ charter.sources.scope.outOfScope || 'Source not provided. Maintain out-of-scope boundaries in Scope Statement.' }}</p></div>
          <div><h3>Assumptions</h3><p class="charter-preserve">{{ charter.sources.scope.assumptions || 'Source not provided. Maintain assumptions in Scope Statement.' }}</p></div>
        </div>
      </section>

      <section class="charter-panel" aria-labelledby="charter-deliverables">
        <div class="charter-section-head">
          <h2 id="charter-deliverables"><span class="charter-number">5</span>Key deliverables by phase</h2>
          <RouterLink :to="sourceLink('gantt')" class="charter-source">Standard template · dates and task progress from Gantt</RouterLink>
        </div>
        <p class="charter-muted">Task completion is shown below, not a formal tollgate approval outcome. Dates require a saved plan.</p>
        <div class="charter-table-scroll">
          <table>
            <thead><tr><th>Phase &gt; tollgate</th><th>Migration deliverables</th><th>Timeline</th><th>Task progress</th><th>Charter note</th></tr></thead>
            <tbody><tr v-for="item in charter.sources.deliverables" :key="item.id">
              <th scope="row">{{ item.phase }}</th><td>{{ item.description }}</td>
              <td>{{ item.timeline || 'Source not provided' }}</td>
              <td><span :class="`charter-status--${item.status}`">{{ statusLabels[item.status] }}</span></td>
              <td><textarea v-model="notes[item.id]" rows="2" maxlength="2000" :aria-label="`${item.phase} note`" :disabled="busy" placeholder="Add note" /></td>
            </tr></tbody>
          </table>
        </div>
      </section>

      <div class="charter-columns charter-bottom">
        <section class="charter-panel" aria-labelledby="charter-risks">
          <div class="charter-section-head"><h2 id="charter-risks"><span class="charter-number">6</span>Risks &amp; dependencies</h2></div>
          <RouterLink :to="sourceLink('business-case')" class="charter-source">From Business Case · read-only</RouterLink>
          <h3>Risks</h3><p class="charter-preserve">{{ charter.sources.risks || 'Source not provided. Maintain risks in the online Business Case.' }}</p>
          <h3>Dependencies</h3><p class="charter-preserve">{{ charter.sources.dependencies || 'Source not provided. Maintain dependencies in the online Business Case.' }}</p>
        </section>
        <section class="charter-panel" aria-labelledby="charter-fte">
          <div class="charter-section-head"><h2 id="charter-fte"><span class="charter-number">7</span>FTE timeline</h2></div>
          <RouterLink :to="sourceLink('scope-statement')" class="charter-source">From Scope waves · read-only</RouterLink>
          <div v-if="charter.sources.fteTimeline?.length" class="charter-table-scroll">
            <table><caption>Migration waves from Scope Statement</caption><thead><tr><th>Wave</th><th>Date</th><th>FTE</th></tr></thead>
              <tbody><tr v-for="(wave, index) in charter.sources.fteTimeline" :key="index"><td>{{ wave.name }}</td><td>{{ wave.date }}</td><td>{{ wave.fte }}</td></tr></tbody>
            </table>
          </div>
          <p v-else class="charter-muted">No migration waves provided. Maintain the actual wave names, dates and FTE in Scope Statement.</p>
        </section>
        <section class="charter-panel" aria-labelledby="charter-criteria">
          <div class="charter-section-head"><h2 id="charter-criteria"><span class="charter-number">8</span>Success criteria &amp; sign-off</h2></div>
          <span class="charter-source charter-source--editable">Auto + add-only</span>
          <ul><li v-for="criterion in charter.sources.autoCriteria" :key="criterion">{{ criterion }} <small>(automatic)</small></li>
            <li v-for="(criterion, index) in criteria" :key="index">{{ criterion }}</li></ul>
          <p v-if="!charter.sources.autoCriteria.length" class="charter-muted">Automatic criteria will appear when final FTE is locked. Benefit and target-date criteria await structured source data.</p>
          <label class="charter-new-criterion">Additional success criterion
            <input v-model="newCriterion" maxlength="1000" :disabled="busy" @keydown.enter.prevent="addCriterion" />
          </label>
          <button type="button" :disabled="busy || !newCriterion.trim()" @click="addCriterion">+ Add criterion</button>
          <h3>Completeness checks</h3>
          <ul class="charter-checks"><li v-for="check in charter.sources.completeness" :key="check.source" :class="{ 'charter-missing': !check.complete }">
            {{ check.complete ? 'Ready: ' : 'Missing: ' }}<RouterLink :to="sourceLink(check.source)">{{ check.label }}</RouterLink>
          </li></ul>
          <h3>Sign-off roles · from Stakeholder Registration</h3>
          <ul><li v-for="role in charter.sources.signatories" :key="role.role">{{ roleLabels[role.role] }}: {{ role.people.map(person => person.name).join(', ') || 'Not assigned / not locked' }}</li></ul>
          <p class="charter-muted">Draft-only release. Submission and sign-off are not enabled.</p>
        </section>
      </div>
      <details class="charter-panel"><summary>Draft change history ({{ charter.auditLog.length }})</summary>
        <ul><li v-for="entry in charter.auditLog" :key="entry.revision">v0.{{ entry.revision }} · {{ entry.action }} · {{ entry.by }} · {{ formatDate(entry.at) }}</li></ul>
      </details>
    </template>
  </PageShell>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, onBeforeRouteUpdate, useRoute } from 'vue-router'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'

const route = useRoute()
const charter = ref(null)
const loading = ref(true)
const busy = ref(false)
const error = ref('')
const success = ref('')
const vision = ref('')
const notes = ref({})
const criteria = ref([])
const newCriterion = ref('')
const editingVision = ref(false)
const savedSnapshot = ref('')
const fromAdmin = computed(() => route.query.from === 'admin')
const backTo = computed(() => fromAdmin.value ? '/project-charters-database' : `/toll-gates?project=${route.params.id}`)
const endpoint = computed(() => `/api/migration-dashboard/projects/${route.params.id}/project-charter/`)
const statusLabels = { complete: 'Complete', in_progress: 'In progress', not_started: 'Not started' }
const roleLabels = { project_sponsor: 'Project Sponsor', elt: 'ELT Sponsor', area_functional_leader: 'Area Functional Leader', gsc_head_1: 'GSC Head-1' }
const snapshot = () => JSON.stringify([vision.value, notes.value, criteria.value])
const dirty = computed(() => charter.value && (snapshot() !== savedSnapshot.value || newCriterion.value.trim()))
const sourceLink = (page) => `/migration-dashboard/${route.params.id}/${page}?from=toll-gates&project=${route.params.id}`
const formatDate = (value) => new Date(value).toLocaleString()

function applyData(data) {
  charter.value = data
  vision.value = data.vision
  notes.value = { ...data.deliverableNotes }
  criteria.value = [...data.extraSuccessCriteria]
  savedSnapshot.value = snapshot()
}

function addCriterion() {
  const text = newCriterion.value.trim()
  if (!text) {
    error.value = 'Enter a success criterion before adding.'
    return
  }
  if (criteria.value.includes(text)) {
    error.value = 'This success criterion has already been added.'
    return
  }
  if (criteria.value.length >= 50) {
    error.value = 'At most 50 additional success criteria are allowed.'
    return
  }
  criteria.value.push(text)
  newCriterion.value = ''
  error.value = ''
}

async function save(action) {
  if (newCriterion.value.trim()) {
    error.value = 'Add the pending success criterion before saving.'
    return
  }
  busy.value = true
  error.value = ''
  success.value = ''
  try {
    const { data } = await axios.post(`${endpoint.value}save/`, {
      action, revision: charter.value.revision, vision: vision.value,
      deliverableNotes: notes.value, extraSuccessCriteria: criteria.value
    })
    applyData(data)
    success.value = action === 'regenerate' ? 'Vision regenerated from current sources and draft saved.' : 'Draft saved.'
  } catch (failure) {
    error.value = failure.response?.data?.error || failure.message
  } finally {
    busy.value = false
  }
}

function regenerate() {
  if (window.confirm('Replace the vision with a new draft from current sources? Notes and added criteria will be preserved and saved.')) save('regenerate')
}

function beforeUnload(event) {
  if (dirty.value) {
    event.preventDefault()
    event.returnValue = ''
  }
}
onBeforeRouteLeave(() => !busy.value && (!dirty.value || window.confirm('Leave without saving your Project Charter changes?')))
onBeforeRouteUpdate((to) => to.params.id === route.params.id || (!busy.value && (!dirty.value || window.confirm('Leave without saving your Project Charter changes?'))))
async function loadData() {
  const projectId = route.params.id
  loading.value = true
  charter.value = null
  error.value = ''
  success.value = ''
  newCriterion.value = ''
  editingVision.value = false
  try {
    const { data } = await axios.get(endpoint.value)
    if (route.params.id === projectId) applyData(data)
  } catch (failure) {
    if (route.params.id === projectId) error.value = failure.response?.data?.error || failure.message
  } finally {
    if (route.params.id === projectId) loading.value = false
  }
}
watch(() => route.params.id, loadData)
onMounted(() => {
  window.addEventListener('beforeunload', beforeUnload)
  loadData()
})
onBeforeUnmount(() => window.removeEventListener('beforeunload', beforeUnload))
</script>

<style scoped>
.charter-toolbar { align-items: center; display: flex; gap: 16px; justify-content: space-between; margin-bottom: 14px; }
.charter-toolbar p, .charter-muted, small { color: #718096; font-size: 12px; }
.charter-badge { background: #fff3df; border-radius: 20px; color: #9c6100; font-size: 11px; margin-left: 12px; padding: 5px 12px; }
.charter-panel { background: #fff; border: 1px solid #dfe7ef; border-radius: 7px; margin-bottom: 12px; padding: 16px; }
.charter-section-head { align-items: center; display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 12px; }
h2 { align-items: center; color: #18334e; display: flex; font-size: 16px; gap: 8px; margin: 0; }
h3 { color: #68778b; font-size: 11px; margin: 12px 0 7px; text-transform: uppercase; }
p, li { font-size: 13px; line-height: 1.5; overflow-wrap: anywhere; }
.charter-number { align-items: center; background: #f28a20; border-radius: 50%; color: #fff; display: inline-flex; height: 24px; justify-content: center; width: 24px; }
.charter-source { background: #f0f4f8; border-radius: 16px; color: #53677d; display: inline-block; font-size: 10px; padding: 5px 9px; }
.charter-source--editable { background: #e7f5eb; color: #237b3e; }
.charter-leadership, .charter-facts { display: grid; gap: 10px; grid-template-columns: repeat(6, minmax(0, 1fr)); }
.charter-leadership p { margin: 4px 0; }
.charter-fact { background: #f6f9fc; border: 1px solid #dfe7ef; border-radius: 6px; padding: 9px; }
.charter-fact h3 { margin-top: 0; }
.charter-fact strong, .charter-fact small { display: block; overflow-wrap: anywhere; }
.charter-fact strong { color: #143658; font-size: 14px; }
.charter-fact small { margin-top: 4px; }
.charter-columns { display: grid; gap: 12px; grid-template-columns: repeat(3, minmax(0, 1fr)); }
.charter-actions { display: flex; gap: 8px; margin-left: auto; }
button { background: #fff; border: 1px solid #c9d8e6; border-radius: 4px; color: #006fba; cursor: pointer; font-family: inherit; font-size: 12px; font-weight: 600; padding: 8px 14px; }
button:disabled { cursor: not-allowed; opacity: .6; }
.charter-primary { background: #1263d8; color: #fff; }
textarea, input { border: 1px solid #cbd9e7; border-radius: 4px; box-sizing: border-box; color: #243a50; font: inherit; padding: 8px; width: 100%; }
textarea { resize: vertical; }
.charter-vision, .charter-preserve { white-space: pre-wrap; }
.charter-vision { border: 1px solid #e0e7ef; border-radius: 4px; margin: 0; padding: 12px; }
.charter-table-scroll { overflow-x: auto; }
table { border-collapse: collapse; font-size: 12px; width: 100%; }
thead { background: #103451; color: #fff; text-align: left; }
td, th { border: 1px solid #e0e7ef; padding: 9px; vertical-align: top; }
td:nth-child(2) { min-width: 250px; }
td:last-child { min-width: 180px; }
.charter-status--complete, .charter-success { color: #16763b; }
.charter-status--in_progress { color: #1263d8; }
.charter-status--not_started { color: #718096; }
.charter-missing, .charter-error { color: #be3030 !important; }
.charter-warning { background: #fff6dd; border: 1px solid #f3d288; padding: 12px; }
.charter-storage-link { color: #006bb8; font-size: 13px; font-weight: 600; }
.charter-new-criterion { display: block; font-size: 12px; margin-bottom: 6px; }
.charter-empty-chart { align-items: center; background: #f6f9fc; color: #718096; display: flex; font-size: 13px; line-height: 1.6; margin-top: 16px; min-height: 150px; padding: 18px; }
ul { padding-left: 18px; }
.charter-checks a { color: inherit; }
button:focus-visible, a:focus-visible, summary:focus-visible { outline: 2px solid #1263d8; outline-offset: 3px; }
@media (max-width: 1100px) { .charter-leadership, .charter-facts { grid-template-columns: repeat(3, minmax(0, 1fr)); } .charter-bottom { grid-template-columns: 1fr; } }
@media (max-width: 650px) { .charter-leadership, .charter-facts { grid-template-columns: repeat(2, minmax(0, 1fr)); } .charter-columns { grid-template-columns: 1fr; } .charter-toolbar { align-items: flex-start; flex-direction: column; } }
</style>
