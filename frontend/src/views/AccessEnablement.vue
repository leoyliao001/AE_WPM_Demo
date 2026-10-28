<template>
  <PageShell title="Access & Enablement" :show-heading="false" :back-to="backTo" back-label="Back to Toll Gates" full-width>
    <div class="pa-page">
      <div v-if="loading" class="pa-panel" role="status">Loading access and IT readiness...</div>
      <div v-if="error" class="pa-feedback pa-feedback--error" role="alert">{{ error }} <button v-if="!record" class="pa-text-button" @click="load">Retry</button></div>
      <div v-if="success" class="pa-feedback pa-feedback--success" role="status">{{ success }}</div>
      <template v-if="record && !loading">
        <header class="pa-hero">
          <div class="pa-heading">
            <div><p class="pa-eyebrow">Initiate / Operational readiness</p><h1>Access &amp; Enablement</h1><span class="pa-status" :class="`pa-status--${record.status}`">{{ record.status.replaceAll('_', ' ') }}</span></div>
            <div class="pa-actions">
              <mc-button appearance="neutral" variant="outlined" label="Export" :disabled="!!busy" @click="exportData" />
              <mc-button v-if="!record.frozen" appearance="neutral" variant="outlined" label="Save draft" :disabled="!!busy || (!record.permissions.edit && !record.permissions.it)" @click="save()" />
              <mc-button v-if="!record.frozen && record.permissions.edit" appearance="primary" label="Submit for confirmation" :disabled="!!busy || !ready" @click="save('submit')" />
            </div>
          </div>
          <div class="pa-project-meta"><strong>{{ record.projectName }}</strong><span>{{ record.migrationRequestId }}</span><span>{{ dirty ? 'Unsaved changes' : record.updatedAt ? `Last saved ${dateTime(record.updatedAt)}` : 'Not yet saved' }}</span></div>
          <div class="pa-metrics">
            <article class="pa-metric"><span>Migrating population</span><strong>{{ population ?? '—' }} <small>FTE</small></strong><small>Locked final Scope FTE</small></article>
            <article class="pa-metric"><span>Systems required</span><strong>{{ record.systems.length }}</strong><small>Recorded from catalogue</small></article>
            <article class="pa-metric"><span>Access secured</span><strong>{{ secured }} / {{ record.systems.length }}</strong><small>Per-system status; not per-user tracking</small></article>
            <article class="pa-metric" :class="{ 'pa-metric--risk': openBarriers.length }"><span>Open barriers</span><strong>{{ openBarriers.length }}</strong><small>{{ overdueCount }} overdue</small></article>
            <article class="pa-metric"><span>IT readiness</span><strong>{{ itComplete }} / 5</strong><small>{{ itConfirmed ? 'Confirmed by GSC Delivery Ops' : 'IT confirmation pending' }}</small></article>
          </div>
        </header>
        <div v-if="!record.source.ready" class="pa-feedback">A submitted, fully locked Scope Statement is needed to establish population and confirm readiness. You can prepare a draft now. <router-link class="pa-link" :to="`/migration-dashboard/${projectId}/scope-statement`">Open Scope</router-link></div>
        <div v-if="record.sourceChanged" class="pa-feedback">Scope has changed since this record was saved. Review users and IT quantities against the new population. Previous IT confirmation is no longer valid.</div>
        <div v-if="record.frozen" class="pa-feedback">This confirmed record is frozen. <span v-if="record.permissions.edit">Enter a reason below to reopen it.</span></div>
        <section class="pa-panel">
          <div class="pa-section-heading"><div><p class="pa-eyebrow">A / Systems</p><h2>System access status</h2></div><mc-button v-if="canEdit" appearance="neutral" variant="outlined" label="Add system" @click="addSystem" /></div>
          <p>Pick systems from the catalogue for record purposes only. This does not provision access or purchase licences. Every unsecured system requires a complete barrier record.</p>
          <div class="pa-scroll">
            <table class="pa-table"><thead><tr><th>System (catalogue)</th><th>Access / licence type</th><th>Users needed</th><th>Secured?</th><th>Barrier</th><th>Action</th></tr></thead>
              <tbody><tr v-for="line in record.systems" :key="line.id">
                <td><select v-model="line.systemId" :disabled="!canEdit" aria-label="System"><option value="">Select system</option><option v-for="system in record.catalogue" :key="system.id" :value="system.id" :disabled="record.systems.some(other => other.id !== line.id && other.systemId === system.id)">{{ system.label }}</option></select></td>
                <td><input v-model="line.accessType" :disabled="!canEdit" aria-label="Access or licence type" maxlength="500" placeholder="Role, profile or licence" /></td>
                <td><input v-model.number="line.usersNeeded" :disabled="!canEdit" aria-label="Users needed" type="number" min="0" max="100000" step="1" /></td>
                <td><select v-model="line.isSecured" :disabled="!canEdit" aria-label="Access secured" @change="ensureBarrier(line)"><option :value="true">Yes</option><option :value="false">No</option></select></td>
                <td><span v-if="line.isSecured">—</span><button v-else class="pa-text-button" @click="scrollToBarriers">Review barrier</button></td>
                <td><button class="pa-text-button" :disabled="!canEdit" aria-label="Remove system" @click="removeSystem(line)">Remove</button></td>
              </tr><tr v-if="!record.systems.length"><td colspan="6" class="pa-empty">No systems recorded. Add a system to start the readiness assessment.</td></tr></tbody>
            </table>
          </div>
          <div class="pa-feedback"><strong>All accesses secured for the migrating population? {{ allSecured ? 'Yes' : 'No' }}</strong> · {{ secured }} of {{ record.systems.length }} systems secured</div>
        </section>
        <section id="enablement-barriers" class="pa-panel">
          <div class="pa-section-heading"><div><p class="pa-eyebrow">Exceptions / Resolution history</p><h2>Barrier register</h2></div><span class="pa-status">{{ openBarriers.length }} open</span></div>
          <p>Owner must be an email address. Securing or removing an affected system closes its saved barriers on save; resolved records remain in history. Reminder links open an email draft, they do not send automatically.</p>
          <div v-if="!record.barriers.length" class="pa-empty">No barriers recorded.</div>
          <article v-for="barrier in record.barriers" :key="barrier.id" class="pa-barrier" :class="{ 'pa-barrier--overdue': overdue(barrier), 'pa-barrier--resolved': barrier.status === 'resolved' }">
            <div class="pa-section-heading"><h3>{{ barrier.systemName || systemName(barrier.systemLineId) }} <span class="pa-status">{{ barrier.status === 'resolved' ? 'Resolved' : overdue(barrier) ? 'Overdue' : 'Open' }}</span></h3><a v-if="barrier.status !== 'resolved' && barrier.owner" class="pa-link" :href="reminderLink(barrier)">Compose owner reminder</a></div>
            <div class="pa-fields" style="margin-top: 16px">
              <label>Affected system<input :value="barrier.systemName || systemName(barrier.systemLineId)" disabled /></label>
              <label>Barrier type<select v-model="barrier.type" :disabled="!canEdit || barrier.status === 'resolved'"><option value="">Select type</option><option v-for="type in record.barrierTypes" :key="type">{{ type }}</option></select></label>
              <label>Owner email<input v-model="barrier.owner" type="email" :disabled="!canEdit || barrier.status === 'resolved'" maxlength="254" /></label>
              <label>Target date<input v-model="barrier.targetDate" type="date" :disabled="!canEdit || barrier.status === 'resolved'" /></label>
            </div>
            <label class="pa-field">Description (maximum 500 characters)<textarea v-model="barrier.description" maxlength="500" rows="2" :disabled="!canEdit || barrier.status === 'resolved'" /></label>
            <small v-if="barrier.resolvedAt" class="pa-note">Resolved {{ dateTime(barrier.resolvedAt) }}</small>
          </article>
        </section>
        <section class="pa-panel">
          <div class="pa-section-heading"><div><p class="pa-eyebrow">B / GSC Delivery Ops</p><h2>IT requirements</h2></div><span class="pa-status">{{ itComplete }} of 5 items confirmed</span></div>
          <p>Required quantities follow locked Scope population. Only a locked GSC Leader / GSC Head-1 or an Access &amp; Enablement administrator can update and confirm IT readiness.</p>
          <div class="pa-scroll"><table class="pa-table"><thead><tr><th>IT item</th><th>Required</th><th>Confirmed quantity</th><th>Status</th></tr></thead>
            <tbody><tr v-for="item in record.itItems" :key="item.id"><th>{{ itemName(item.id) }}</th><td>{{ population ?? '—' }}</td><td><input v-model.number="item.qtyConfirmed" type="number" min="0" :max="population ?? 100000" step="1" :aria-label="`${itemName(item.id)} confirmed quantity`" :disabled="!editable || !record.permissions.it" @input="record.itConfirmation = {}" /></td><td><span class="pa-status" :class="{ 'pa-status--confirmed': population !== null && item.qtyConfirmed === population }">{{ population !== null && item.qtyConfirmed === population ? 'Confirmed' : item.qtyConfirmed ? 'Pending' : 'Not started' }}</span></td></tr></tbody>
          </table></div>
          <label class="pa-field">IT confirmation comment<textarea v-model="confirmationComment" rows="2" maxlength="2000" :disabled="!editable || !record.permissions.it" /></label>
          <div class="pa-section-heading">
            <p v-if="record.itConfirmation.at">Confirmer: <strong>{{ record.itConfirmation.by }}</strong> · {{ dateTime(record.itConfirmation.at) }}<br />{{ record.itConfirmation.comment }}</p><p v-else>No IT readiness confirmation recorded.</p>
            <div class="pa-actions"><a v-if="record.itContacts.length" class="pa-link" :href="itUpdateLink">Request IT update (email draft)</a><span v-else class="pa-note">Assign and lock GSC leaders in Stakeholder Registration to request an IT update.</span><mc-button v-if="record.permissions.it && !record.frozen" appearance="primary" label="Confirm IT readiness" :disabled="!!busy || population === null || itComplete !== 5" @click="save('confirm_it', { confirmationComment })" /></div>
          </div>
        </section>
        <section v-if="record.frozen && record.permissions.edit" class="pa-panel">
          <h2>Reopen for revision</h2><label class="pa-field">Reason<textarea v-model="reason" maxlength="2000" rows="2" /></label><mc-button appearance="neutral" variant="outlined" label="Reopen" :disabled="!!busy || !reason.trim()" @click="reopen" />
        </section>
        <details class="pa-audit"><summary>Audit history · {{ record.auditLog.length }} events</summary><div class="pa-scroll"><table class="pa-table"><thead><tr><th>Revision</th><th>Action</th><th>User</th><th>Timestamp</th><th>Reason</th></tr></thead><tbody><tr v-for="entry in [...record.auditLog].reverse()" :key="entry.revision"><td>{{ entry.revision }}</td><td>{{ entry.action }}</td><td>{{ entry.by }}</td><td>{{ dateTime(entry.at) }}</td><td>{{ entry.reason }}</td></tr></tbody></table></div></details>
      </template>
    </div>
  </PageShell>
</template>

<script setup>
import { computed, ref } from 'vue'
import PageShell from '../components/PageShell.vue'
import { useProjectArtefact } from '../composables/useProjectArtefact.js'
import { exportArtefact } from '../utils/projectArtefactExport.js'
import '@maersk-global/mds-components-core/mc-button'
import '../styles/projectArtefacts.css'

const { record, projectId, backTo, loading, busy, error, success, dirty, editable, load, save } = useProjectArtefact('access-enablement')
const reason = ref('')
const confirmationComment = ref('')
const population = computed(() => record.value?.source.population ?? null)
const canEdit = computed(() => editable.value && record.value.permissions.edit)
const secured = computed(() => record.value?.systems.filter(line => line.isSecured).length || 0)
const allSecured = computed(() => Boolean(record.value?.systems.length) && secured.value === record.value.systems.length)
const openBarriers = computed(() => record.value?.barriers.filter(barrier => barrier.status !== 'resolved') || [])
const overdueCount = computed(() => openBarriers.value.filter(overdue).length)
const itComplete = computed(() => population.value === null ? 0 : record.value.itItems.filter(item => item.qtyConfirmed === population.value).length)
const itConfirmed = computed(() => Boolean(record.value?.itConfirmation.at) && record.value.itConfirmation.sourceVersion === record.value.source.version && itComplete.value === 5)
const ready = computed(() => record.value?.source.ready && allSecured.value && itConfirmed.value && record.value.systems.every(line => line.accessType.trim() && Number.isInteger(line.usersNeeded) && line.usersNeeded > 0))
const itUpdateLink = computed(() => `mailto:${(record.value?.itContacts || []).map(encodeURIComponent).join(',')}?subject=${encodeURIComponent(`IT readiness update: ${record.value?.migrationRequestId}`)}&body=${encodeURIComponent(`Please review the IT readiness checklist for ${record.value?.projectName}.\n${location.href}`)}`)
const dateTime = value => value ? new Date(value).toLocaleString('en-GB') : ''
const itemName = id => record.value.standardItems.find(item => item.id === id)?.label || id
function systemName(id) {
  const line = record.value.systems.find(system => system.id === id)
  return record.value.catalogue.find(system => system.id === line?.systemId)?.label || 'Removed system'
}
function overdue(barrier) {
  return barrier.status !== 'resolved' && barrier.targetDate && barrier.targetDate < new Date().toLocaleDateString('en-CA')
}
function addSystem() {
  const line = { id: crypto.randomUUID(), systemId: '', accessType: '', usersNeeded: population.value ?? 0, isSecured: false }
  record.value.systems.push(line)
  ensureBarrier(line)
}
function ensureBarrier(line) {
  if (line.isSecured) record.value.barriers = record.value.barriers.filter(barrier => barrier.systemLineId !== line.id || record.value.savedBarrierIds.includes(barrier.id))
  if (!line.isSecured && !record.value.barriers.some(barrier => barrier.systemLineId === line.id && barrier.status !== 'resolved')) {
    record.value.barriers.push({ id: crypto.randomUUID(), systemLineId: line.id, type: '', owner: '', targetDate: '', description: '', status: 'open', resolvedAt: '' })
  }
}
function removeSystem(line) {
  if (!window.confirm('Remove this system? Saved barriers will be closed and retained in history.')) return
  record.value.systems = record.value.systems.filter(system => system.id !== line.id)
  record.value.barriers = record.value.barriers.filter(barrier => barrier.systemLineId !== line.id || record.value.savedBarrierIds.includes(barrier.id))
}
function scrollToBarriers() {
  document.getElementById('enablement-barriers')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
function reminderLink(barrier) {
  return `mailto:${encodeURIComponent(barrier.owner)}?subject=${encodeURIComponent(`Access barrier: ${record.value.migrationRequestId}`)}&body=${encodeURIComponent(`${systemName(barrier.systemLineId)}\nTarget: ${barrier.targetDate}\n${barrier.description}\n${location.href}`)}`
}
async function reopen() {
  if (await save('reopen', { reason: reason.value })) reason.value = ''
}
function exportData() {
  error.value = ''
  try {
    exportArtefact(record.value, 'access-enablement', [
      ['System Access', [['System', 'Access type', 'Users needed', 'Secured'], ...record.value.systems.map(line => [record.value.catalogue.find(system => system.id === line.systemId)?.label || line.systemId, line.accessType, line.usersNeeded, line.isSecured ? 'Yes' : 'No'])]],
      ['Barriers', [['System', 'Type', 'Owner', 'Target date', 'Description', 'Status', 'Resolved at'], ...record.value.barriers.map(barrier => [systemName(barrier.systemLineId), barrier.type, barrier.owner, barrier.targetDate, barrier.description, barrier.status, barrier.resolvedAt])]],
      ['IT Requirements', [['Item', 'Required', 'Confirmed'], ...record.value.itItems.map(item => [itemName(item.id), population.value, item.qtyConfirmed])]],
      ['IT Confirmation', [['By', 'At', 'Comment'], [record.value.itConfirmation.by || '', record.value.itConfirmation.at || '', record.value.itConfirmation.comment || '']]],
    ])
    success.value = 'Excel export generated from the current page.'
  } catch (caught) {
    error.value = `Unable to export: ${caught.message}`
  }
}
</script>
