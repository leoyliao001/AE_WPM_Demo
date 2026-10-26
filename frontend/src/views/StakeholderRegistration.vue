<template>
  <PageShell title="Stakeholder Registration" :show-header="false" full-width class="stakeholder-shell">
    <div class="stakeholder-page">
      <nav class="breadcrumb" aria-label="Breadcrumb">
        <router-link :to="backTo">Toll Gates</router-link><span>/</span>
        <span>{{ registration?.projectName || 'Project' }}</span><span>/</span>
        <strong>Stakeholder Registration</strong>
      </nav>

      <div v-if="loading" class="state-message" role="status">Loading stakeholder registry…</div>
      <div v-else-if="error && !registration" class="state-message state-message--error" role="alert">
        <h1>Unable to load Stakeholder Registration</h1><p>{{ error }}</p>
        <button class="button button--outline" type="button" @click="loadData">Retry</button>
      </div>

      <template v-else-if="registration">
        <header class="project-header">
          <div class="project-heading">
            <div class="title-line">
              <h1>Stakeholder Registration</h1>
              <span class="status-chip" :class="`status-chip--${statusKey}`">{{ statusLabel }}</span>
            </div>
            <div class="project-meta">
              <strong>{{ registration.projectName }}</strong>
              <span>{{ registration.migrationRequestId }}</span>
              <span>Phase: Initiate</span>
              <span>{{ registration.updatedAt ? `Last saved ${formatDate(registration.updatedAt)}` : 'Not yet saved' }}</span>
            </div>
          </div>
          <div class="header-actions">
            <span v-if="error" class="feedback feedback--error" role="alert">{{ error }}</span>
            <span v-if="success" class="feedback feedback--success" role="status">{{ success }}</span>
            <button class="button button--outline" type="button" @click="exportRegistry">Export</button>
            <button class="button button--outline" type="button" :disabled="Boolean(busy)" @click="teamPanelOpen = true">
              Project Team <span class="count-badge">{{ teamMembers.length }}</span>
            </button>
            <button class="button button--primary" type="button" :disabled="Boolean(busy)" @click="saveDraft">
              {{ busy === 'save' ? 'Saving…' : 'Save draft' }}
            </button>
          </div>
        </header>

        <section class="registry-panel" aria-labelledby="registry-title">
          <div class="registry-topline">
            <div class="registry-heading">
              <span class="number-badge">1</span>
              <div><h2 id="registry-title">Project Stakeholders</h2><p>All roles are assigned manually from this project’s Project Team.</p></div>
              <span class="manual-badge">MANUAL</span>
            </div>
            <div class="registry-actions">
              <strong>{{ filledCount }} of {{ requiredCount }} roles filled</strong>
              <span v-if="unassignedCount" class="summary-badge summary-badge--red">{{ unassignedCount }} to assign</span>
              <span v-if="unlockedCount" class="summary-badge summary-badge--amber">{{ unlockedCount }} to lock</span>
              <button class="button button--outline" type="button" :disabled="Boolean(busy) || !canLockAll" @click="lockAll">
                {{ busy === 'lock_all' ? 'Locking…' : 'Lock all' }}
              </button>
              <button class="button button--primary" type="button" :disabled="Boolean(busy)" @click="teamPanelOpen = true">+ Add person</button>
            </div>
          </div>

          <div class="completion-strip">
            <div class="completion-copy">
              <span class="completion-percent">{{ progressPercent }}%</span>
              <span class="completion-description"><strong>Role assignment progress</strong><small>{{ filledCount }} of {{ requiredCount }} required roles filled · {{ lockedRequiredCount }} locked</small></span>
            </div>
            <div class="completion-track" role="progressbar" aria-label="Required role assignment progress" :aria-valuemin="0" :aria-valuemax="100" :aria-valuenow="progressPercent">
              <span :style="{ width: `${progressPercent}%` }" />
            </div>
          </div>

          <div class="legend-row">
            <span><i class="legend-dot legend-dot--manual" /> Manual assignment</span>
            <span><i class="legend-dot legend-dot--locked" /> Locked and confirmed</span>
            <small>Required roles must be filled and locked before Business Case submission.</small>
          </div>

          <div class="role-groups">
            <section v-for="group in registration.groups" :key="group.id" class="role-group">
              <header class="role-group__header"><h3>{{ group.label }}</h3><span>{{ group.roles.length }}</span></header>
              <div class="role-stack">
                <button v-for="role in group.roles" :key="role.code" type="button" class="role-card" :class="roleCardClass(role)" @click="openRole(role)">
                  <span class="role-accent" />
                  <span class="role-card__body">
                    <span class="role-card__top"><strong>{{ role.label }}</strong>
                      <span v-if="isLocked(role.code)" class="role-state role-state--locked">LOCKED</span>
                      <span v-else-if="isNotApplicable(role.code)" class="role-state role-state--na">N/A</span>
                      <span v-else-if="assignedCount(role)" class="role-state role-state--draft">DRAFT</span>
                      <span v-else class="role-state role-state--empty">{{ role.required ? 'TO ASSIGN' : 'OPTIONAL' }}</span>
                    </span>
                    <span v-if="isNotApplicable(role.code)" class="role-person-empty">Not applicable</span>
                    <span v-else-if="peopleForRole(role).length" class="role-people">
                      <span v-for="person in peopleForRole(role).slice(0, 3)" :key="person.id" class="role-person">
                        <span class="avatar" :style="avatarStyle(person)">{{ initials(person.fullName) }}</span>{{ person.fullName }}
                      </span>
                      <span v-if="peopleForRole(role).length > 3" class="more-count">+{{ peopleForRole(role).length - 3 }}</span>
                    </span>
                    <span v-else class="role-person-empty">+ Assign Project Team person</span>
                    <span class="role-card__foot"><span>{{ role.multiple ? 'Multiple people' : 'One focal' }}</span><span>{{ role.required ? 'Required' : 'If applicable' }}</span></span>
                  </span>
                  <span class="role-chevron" aria-hidden="true">›</span>
                </button>
              </div>
            </section>
          </div>
        </section>

        <section class="support-grid">
          <article class="support-panel">
            <header class="support-header">
              <div class="support-title"><span class="number-badge">5</span><h2>MSP Focals</h2><span class="neutral-badge">{{ mspRows.length }} MSP{{ mspRows.length === 1 ? '' : 's' }}</span></div>
              <button class="text-button" type="button" @click="openRole(roleByCode.msp_focals)">Edit MSP focals</button>
            </header>
            <div v-if="mspRows.length" class="table-scroll">
              <table class="msp-table"><thead><tr><th>MSP</th><th>Focal</th><th>Status</th></tr></thead>
                <tbody><tr v-for="row in mspRows" :key="row.mspName"><td>{{ row.mspName }}</td><td>{{ personById(row.personIds[0])?.fullName || 'To assign' }}</td><td>{{ isLocked('msp_focals') ? 'Locked' : 'Draft' }}</td></tr></tbody>
              </table>
            </div>
            <div v-else class="empty-panel"><strong>No MSP focals added</strong><span>Add one focal from the Project Team for each applicable MSP.</span></div>
          </article>

          <article class="support-panel">
            <header class="support-header">
              <div class="support-title"><span class="number-badge">6</span><h2>Change Log</h2><span class="neutral-badge">AUDIT</span></div>
              <small>Every edit, lock and unlock</small>
            </header>
            <div v-if="registration.auditLog.length" class="audit-list">
              <div v-for="(entry, index) in [...registration.auditLog].reverse().slice(0, 8)" :key="`${entry.at}-${index}`" class="audit-row">
                <time>{{ formatDate(entry.at) }}</time><strong>{{ entry.by }}</strong><span>{{ entry.details || auditLabel(entry) }}</span>
              </div>
            </div>
            <p v-else class="empty-audit">Changes will appear here after the first save.</p>
          </article>
        </section>
      </template>

      <Teleport to="body">
      <div v-if="activeRole" class="drawer-backdrop" @click.self="closeRole">
        <aside class="drawer" aria-labelledby="role-editor-title">
          <header class="drawer-header">
            <div><p class="eyebrow">{{ activeRole.required ? 'Required role' : 'If applicable' }}</p><h2 id="role-editor-title">Edit stakeholder: {{ activeRole.label }}</h2><span class="drawer-source">SOURCE: MANUAL · PROJECT TEAM ONLY</span></div>
            <button class="close-button" type="button" aria-label="Close editor" @click="closeRole">×</button>
          </header>
          <div class="drawer-content">
            <p class="role-description">{{ activeRole.description }}</p>
            <div v-if="isLocked(activeRole.code)" class="locked-notice">Locked by {{ activeAssignment.lockedBy }}. Unlock before changing assigned people.</div>

            <template v-if="activeRole.code === 'msp_focals'">
              <div class="section-row"><div><h3>MSP assignments</h3><p>One manually selected Project Team focal per MSP.</p></div><button class="button button--small button--outline" type="button" :disabled="isLocked(activeRole.code)" @click="addMspRow">+ Add MSP</button></div>
              <div v-for="(row, index) in activeAssignment.mspRows" :key="row.localId || row.mspName || index" class="msp-edit-row">
                <label class="field-label">MSP name<input v-model="row.mspName" type="text" placeholder="e.g. MSP A" :disabled="isLocked(activeRole.code)" /></label>
                <label class="field-label">Project Team focal<select v-model="row.personIds[0]" :disabled="isLocked(activeRole.code)"><option value="">Select a team member</option><option v-for="person in teamMembers" :key="person.id" :value="person.id">{{ person.fullName }} · {{ person.email }}</option></select></label>
                <button class="remove-link" type="button" :disabled="isLocked(activeRole.code)" @click="removeMspRow(index)">Remove</button>
              </div>
              <p v-if="!activeAssignment.mspRows.length" class="empty-picker">No MSP entries yet.</p>
            </template>

            <template v-else>
              <label v-if="!activeRole.required" class="na-option"><input v-model="activeAssignment.notApplicable" type="checkbox" :disabled="isLocked(activeRole.code)" /> Not applicable</label>
              <template v-if="!activeAssignment.notApplicable">
                <div class="section-row"><div><h3>Assigned people</h3><p>{{ activeRole.multiple ? 'Select one or more Project Team members.' : 'Select one Project Team member.' }}</p></div><span class="neutral-badge">{{ activeAssignment.personIds.length }} selected</span></div>
                <label class="search-box"><span class="sr-only">Search Project Team</span><input v-model="memberQuery" type="search" placeholder="Search Project Team by name or email…" /></label>
                <div v-if="filteredTeamMembers.length" class="member-picker">
                  <label v-for="person in filteredTeamMembers" :key="person.id" class="member-option" :class="{ 'member-option--selected': activeAssignment.personIds.includes(person.id) }">
                    <input :type="activeRole.multiple ? 'checkbox' : 'radio'" :name="`stakeholder-${activeRole.code}`" :checked="activeAssignment.personIds.includes(person.id)" :disabled="isLocked(activeRole.code)" @change="togglePerson(person.id, $event.target.checked)" />
                    <span class="avatar" :style="avatarStyle(person)">{{ initials(person.fullName) }}</span>
                    <span class="member-copy"><strong>{{ person.fullName }}</strong><small>{{ person.email }}<template v-if="person.organization"> · {{ person.organization }}</template><template v-if="person.location"> · {{ person.location }}</template></small></span>
                  </label>
                </div>
                <div v-else class="empty-picker"><strong>{{ teamMembers.length ? 'No matching team member' : 'Project Team is empty' }}</strong><span>Add the person to the project roster first; there is no automatic role population.</span></div>
                <button class="text-button add-person-link" type="button" :disabled="isLocked(activeRole.code)" @click="teamPanelOpen = true">+ Add person to Project Team</button>
              </template>
            </template>

            <label class="field-label notes-field">Notes (optional)<textarea v-model="activeAssignment.notes" rows="3" placeholder="Add a note…" :disabled="isLocked(activeRole.code)" /></label>
            <div class="drawer-note">Only people manually added to this project’s Project Team can be assigned. Locked stakeholders are used for approvals and notifications.</div>
          </div>
          <footer class="drawer-footer">
            <button class="button button--outline" type="button" :disabled="Boolean(busy)" @click="closeRole">Cancel</button>
            <button v-if="isLocked(activeRole.code)" class="button button--outline" type="button" :disabled="Boolean(busy)" @click="unlockRole">Unlock</button>
            <button class="button button--outline" type="button" :disabled="Boolean(busy) || isLocked(activeRole.code)" @click="saveDraft">Save draft</button>
            <button v-if="!isLocked(activeRole.code)" class="button button--primary" type="button" :disabled="Boolean(busy) || !isRoleFilled(activeRole)" @click="saveAndLock">Save and lock</button>
          </footer>
        </aside>
      </div>

      <div v-if="teamPanelOpen" class="drawer-backdrop drawer-backdrop--top" @click.self="teamPanelOpen = false">
        <aside class="drawer drawer--team" aria-labelledby="team-editor-title">
          <header class="drawer-header"><div><p class="eyebrow">Manual roster</p><h2 id="team-editor-title">Project Team</h2><span class="drawer-source">{{ teamMembers.length }} people · no automatic population</span></div><button class="close-button" type="button" aria-label="Close Project Team" @click="teamPanelOpen = false">×</button></header>
          <div class="drawer-content">
            <p class="role-description">Add people to this project roster. Stakeholder roles can only be assigned from this list.</p>
            <form class="team-form" @submit.prevent="addTeamMember">
              <label class="field-label">Full name<input v-model="newMember.fullName" required type="text" autocomplete="name" /></label>
              <label class="field-label">Email<input v-model="newMember.email" required type="email" autocomplete="email" /></label>
              <label class="field-label">Title<input v-model="newMember.title" type="text" /></label>
              <div class="form-pair"><label class="field-label">Organization<input v-model="newMember.organization" type="text" /></label><label class="field-label">Location<input v-model="newMember.location" type="text" /></label></div>
              <button class="button button--primary" type="submit">Add to Project Team</button>
            </form>
            <h3 class="roster-heading">Current Project Team</h3>
            <div v-if="teamMembers.length" class="team-roster">
              <div v-for="person in teamMembers" :key="person.id" class="roster-person"><span class="avatar" :style="avatarStyle(person)">{{ initials(person.fullName) }}</span><span class="member-copy"><strong>{{ person.fullName }}</strong><small>{{ person.email }}<template v-if="person.title"> · {{ person.title }}</template></small></span><button class="remove-link" type="button" :disabled="isMemberLocked(person.id)" :title="isMemberLocked(person.id) ? 'Unlock assigned roles before removing this person.' : 'Remove from Project Team'" @click="removeTeamMember(person.id)">Remove</button></div>
            </div>
            <p v-else class="empty-picker">No Project Team members yet.</p>
          </div>
          <footer class="drawer-footer"><button class="button button--outline" type="button" @click="teamPanelOpen = false">Close</button><button class="button button--primary" type="button" :disabled="Boolean(busy)" @click="saveDraft">Save Project Team</button></footer>
        </aside>
      </div>
      </Teleport>
    </div>
  </PageShell>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'
import '@maersk-global/mds-components-core/mc-icon'

const route = useRoute()
const projectId = computed(() => String(route.params.id || ''))
const backTo = computed(() => `/toll-gates?project=${encodeURIComponent(projectId.value)}`)
const registration = ref(null)
const loading = ref(true)
const busy = ref('')
const error = ref('')
const success = ref('')
const activeRole = ref(null)
const roleDraft = ref(null)
const teamPanelOpen = ref(false)
const memberQuery = ref('')
const newMember = ref(emptyMember())

const teamMembers = computed(() => registration.value?.teamMembers || [])
const allRoles = computed(() => (registration.value?.groups || []).flatMap((group) => group.roles || []))
const roleByCode = computed(() => Object.fromEntries(allRoles.value.map((role) => [role.code, role])))
const requiredRoles = computed(() => allRoles.value.filter((role) => role.required))
const requiredCount = computed(() => requiredRoles.value.length)
const filledCount = computed(() => requiredRoles.value.filter(isRoleFilled).length)
const lockedRequiredCount = computed(() => requiredRoles.value.filter((role) => isRoleFilled(role) && isLocked(role.code)).length)
const progressPercent = computed(() => requiredCount.value ? Math.round((filledCount.value / requiredCount.value) * 100) : 0)
const unassignedCount = computed(() => requiredCount.value - filledCount.value)
const unlockedCount = computed(() => allRoles.value.filter((role) => isRoleFilled(role) && !isLocked(role.code)).length)
const canLockAll = computed(() => unassignedCount.value === 0 && unlockedCount.value > 0)
const mspRows = computed(() => registration.value?.assignments?.msp_focals?.mspRows || [])
const filteredTeamMembers = computed(() => {
  const query = memberQuery.value.trim().toLowerCase()
  if (!query) return teamMembers.value
  return teamMembers.value.filter((person) => `${person.fullName} ${person.email} ${person.organization} ${person.location}`.toLowerCase().includes(query))
})
const activeAssignment = computed(() => roleDraft.value || { personIds: [], mspRows: [], notes: '', notApplicable: false })
const statusKey = computed(() => {
  if (requiredRoles.value.length && requiredRoles.value.every((role) => isRoleFilled(role) && isLocked(role.code))) return 'locked'
  return registration.value?.saved ? 'progress' : 'not-started'
})
const statusLabel = computed(() => statusKey.value === 'locked' ? 'LOCKED' : statusKey.value === 'progress' ? 'IN PROGRESS' : 'NOT STARTED')

function emptyMember() {
  return { fullName: '', email: '', title: '', organization: '', location: '' }
}

function clone(value) {
  return JSON.parse(JSON.stringify(value))
}

function assignmentFor(roleCode) {
  return registration.value?.assignments?.[roleCode] || { personIds: [], mspRows: [], notes: '', notApplicable: false, lockedAt: '', lockedBy: '' }
}

function isLocked(roleCode) {
  return Boolean(assignmentFor(roleCode).lockedAt)
}

function isNotApplicable(roleCode) {
  return Boolean(assignmentFor(roleCode).notApplicable)
}

function isRoleFilled(role) {
  const assignment = assignmentFor(role.code)
  if (assignment.notApplicable) return !role.required
  if (role.code === 'msp_focals') return assignment.mspRows.length > 0 && assignment.mspRows.every((row) => row.personIds?.length === 1)
  return assignment.personIds.length > 0
}

function assignedCount(role) {
  const assignment = assignmentFor(role.code)
  if (assignment.notApplicable) return 0
  if (role.code === 'msp_focals') return assignment.mspRows.reduce((total, row) => total + (row.personIds?.length || 0), 0)
  return assignment.personIds.length
}

function personById(id) {
  return teamMembers.value.find((person) => person.id === id)
}

function peopleForRole(role) {
  const assignment = assignmentFor(role.code)
  const ids = role.code === 'msp_focals' ? assignment.mspRows.flatMap((row) => row.personIds || []) : assignment.personIds
  return ids.map(personById).filter(Boolean)
}

function roleCardClass(role) {
  return { 'role-card--locked': isLocked(role.code), 'role-card--empty': !isRoleFilled(role), 'role-card--optional': !role.required }
}

function openRole(role) {
  if (!role) return
  activeRole.value = role
  roleDraft.value = clone(assignmentFor(role.code))
  memberQuery.value = ''
  error.value = ''
}

function closeRole() {
  activeRole.value = null
  roleDraft.value = null
  memberQuery.value = ''
}

function togglePerson(personId, checked) {
  if (!activeRole.value || !roleDraft.value) return
  if (activeRole.value.multiple) {
    const selected = new Set(roleDraft.value.personIds)
    if (checked) selected.add(personId)
    else selected.delete(personId)
    roleDraft.value.personIds = [...selected]
  } else {
    roleDraft.value.personIds = checked ? [personId] : []
  }
  roleDraft.value.notApplicable = false
}

function addMspRow() {
  roleDraft.value.mspRows.push({ localId: crypto.randomUUID(), mspName: '', personIds: [] })
}

function removeMspRow(index) {
  roleDraft.value.mspRows.splice(index, 1)
}

function commitRoleDraft() {
  if (!activeRole.value || !roleDraft.value) return
  registration.value.assignments[activeRole.value.code] = clone(roleDraft.value)
}

function isMemberLocked(personId) {
  return Object.entries(registration.value?.assignments || {}).some(([roleCode, assignment]) => {
    if (!assignment.lockedAt) return false
    if (roleCode === 'msp_focals') return assignment.mspRows.some((row) => row.personIds.includes(personId))
    return assignment.personIds.includes(personId)
  })
}

function removeTeamMember(personId) {
  if (isMemberLocked(personId)) return
  registration.value.teamMembers = teamMembers.value.filter((person) => person.id !== personId)
  for (const assignment of Object.values(registration.value.assignments)) {
    assignment.personIds = (assignment.personIds || []).filter((id) => id !== personId)
    for (const row of assignment.mspRows || []) row.personIds = row.personIds.filter((id) => id !== personId)
  }
  if (roleDraft.value) {
    roleDraft.value.personIds = roleDraft.value.personIds.filter((id) => id !== personId)
    for (const row of roleDraft.value.mspRows || []) row.personIds = row.personIds.filter((id) => id !== personId)
  }
}

function addTeamMember() {
  const fullName = newMember.value.fullName.trim()
  const email = newMember.value.email.trim().toLowerCase()
  if (!fullName || !email) return
  if (teamMembers.value.some((person) => person.email.toLowerCase() === email)) {
    error.value = `${email} is already in the Project Team.`
    return
  }
  registration.value.teamMembers.push({ ...newMember.value, id: crypto.randomUUID(), fullName, email })
  newMember.value = emptyMember()
  error.value = ''
  success.value = 'Person added to the Project Team draft.'
}

function applyRegistration(data) {
  registration.value = { ...data, teamMembers: data.teamMembers || [], assignments: data.assignments || {}, auditLog: data.auditLog || [] }
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await axios.get(`/api/migration-dashboard/projects/${projectId.value}/stakeholder-registration/`)
    applyRegistration(data)
  } catch (caught) {
    registration.value = null
    error.value = caught?.response?.data?.error || caught?.response?.data?.detail || caught.message || 'Unable to load stakeholder registration.'
  } finally {
    loading.value = false
  }
}

async function saveDraft() {
  if (!registration.value || busy.value) return false
  commitRoleDraft()
  busy.value = 'save'
  error.value = ''
  success.value = ''
  try {
    const { data } = await axios.post(`/api/migration-dashboard/projects/${projectId.value}/stakeholder-registration/save/`, {
      action: 'save', teamMembers: teamMembers.value, assignments: registration.value.assignments
    })
    applyRegistration(data)
    if (activeRole.value) roleDraft.value = clone(assignmentFor(activeRole.value.code))
    success.value = 'Draft saved.'
    return true
  } catch (caught) {
    error.value = caught?.response?.data?.error || caught?.response?.data?.detail || caught.message || 'Unable to save draft.'
    return false
  } finally {
    busy.value = ''
  }
}

async function runRoleAction(action, roleCode = '') {
  if (!(await saveDraft())) return
  busy.value = action
  error.value = ''
  try {
    const { data } = await axios.post(`/api/migration-dashboard/projects/${projectId.value}/stakeholder-registration/save/`, { action, roleCode })
    applyRegistration(data)
    if (activeRole.value) roleDraft.value = clone(assignmentFor(activeRole.value.code))
    success.value = action === 'unlock' ? 'Role unlocked and logged.' : action === 'lock_all' ? 'All assigned roles locked.' : 'Role locked and logged.'
  } catch (caught) {
    error.value = caught?.response?.data?.error || caught?.response?.data?.detail || caught.message || 'Unable to update lock status.'
  } finally {
    busy.value = ''
  }
}

function saveAndLock() {
  return runRoleAction('lock', activeRole.value?.code)
}

function unlockRole() {
  return runRoleAction('unlock', activeRole.value?.code)
}

function lockAll() {
  return runRoleAction('lock_all')
}

async function saveTeam() {
  if (await saveDraft()) teamPanelOpen.value = false
}

function exportRegistry() {
  if (!registration.value) return
  const url = URL.createObjectURL(new Blob([JSON.stringify(registration.value, null, 2)], { type: 'application/json' }))
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${registration.value.migrationRequestId}-stakeholders.json`
  anchor.click()
  URL.revokeObjectURL(url)
}

function initials(name) {
  return String(name || '').split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0].toUpperCase()).join('') || '?'
}

function avatarStyle(person) {
  const colors = ['#143754', '#176b87', '#205d4a', '#5c4b85', '#8d4c28']
  const seed = (person.email || person.id || '').split('').reduce((sum, char) => sum + char.charCodeAt(0), 0)
  return { '--avatar-color': colors[seed % colors.length] }
}

function formatDate(value) {
  return value ? new Date(value).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : ''
}

function auditLabel(entry) {
  const label = roleByCode.value[entry.roleCode]?.label
  return `${String(entry.action || '').replaceAll('_', ' ')}${label ? ` · ${label}` : ''}`
}

watch(projectId, loadData, { immediate: true })
</script>

<style scoped>
.stakeholder-page {
  --ink: #182e3b;
  --muted: #687987;
  --line: #d8e1e8;
  --blue: #006cce;
  --orange: #f08b24;
  --green: #1c8e58;
  color: var(--ink);
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin: 0 auto;
  max-width: 1500px;
  padding: 8px 10px 32px;
  width: 100%;
}

.breadcrumb,
.project-meta,
.header-actions,
.registry-heading,
.registry-actions,
.role-card__top,
.role-person,
.role-card__foot,
.support-header,
.support-title,
.drawer-header,
.drawer-footer,
.section-row,
.member-option,
.roster-person {
  align-items: center;
  display: flex;
}

.breadcrumb { color: #788895; flex-wrap: wrap; font-size: 12px; gap: 9px; }
.breadcrumb a,.text-button { color: var(--blue); text-decoration: none; }
.breadcrumb strong { color: var(--ink); }
.project-header,.registry-panel,.support-panel { background: #fff; border: 1px solid var(--line); border-radius: 8px; }
.project-header { align-items: center; display: flex; gap: 18px; justify-content: space-between; padding: 15px 19px; }
.project-heading { min-width: 0; }
.title-line { align-items: center; display: flex; flex-wrap: wrap; gap: 12px; }
.title-line h1 { font-family: 'Maersk Headline','Maersk Text',sans-serif; font-size: 25px; line-height: 1.15; margin: 0; }
.status-chip,.manual-badge,.role-state,.neutral-badge,.summary-badge,.count-badge { align-items: center; border-radius: 999px; display: inline-flex; font-size: 9px; font-weight: 800; justify-content: center; letter-spacing: .04em; padding: 5px 9px; white-space: nowrap; }
.status-chip--progress,.status-chip--not-started { background: #eaf2ff; color: #1265c4; }
.status-chip--locked { background: #e6f5ec; color: #187a4b; }
.project-meta { color: var(--muted); flex-wrap: wrap; font-size: 11px; gap: 8px; margin-top: 8px; }
.project-meta span + span::before { color: #a7b2bb; content: '|'; margin-right: 8px; }
.header-actions,.registry-actions { flex-wrap: wrap; gap: 8px; justify-content: flex-end; }
.button { align-items: center; background: #fff; border: 1px solid #cbd6df; border-radius: 5px; color: #253947; cursor: pointer; display: inline-flex; font: inherit; font-size: 11px; font-weight: 650; gap: 7px; justify-content: center; min-height: 35px; padding: 7px 12px; }
.button:disabled,.remove-link:disabled { cursor: not-allowed; opacity: .5; }
.button--primary { background: #0869c7; border-color: #0869c7; color: #fff; }
.button--primary:hover:not(:disabled) { background: #0758a8; }
.button--outline { background: #fff; }
.button--small { min-height: 29px; padding: 5px 9px; }
.count-badge { background: #e8f1fa; color: #1a5e9f; letter-spacing: 0; padding: 3px 6px; }
.feedback { font-size: 10px; max-width: 230px; }
.feedback--error { color: #ad352d; }
.feedback--success { color: #187a4b; }
.registry-panel { padding: 15px; }
.registry-topline { align-items: center; display: flex; flex-wrap: wrap; gap: 15px; justify-content: space-between; }
.registry-heading { gap: 10px; min-width: 260px; }
.number-badge { align-items: center; background: var(--orange); border-radius: 50%; color: #fff; display: inline-flex; flex: 0 0 24px; font-size: 11px; font-weight: 800; height: 24px; justify-content: center; width: 24px; }
.registry-heading h2,.support-title h2 { font-size: 15px; margin: 0; }
.registry-heading p { color: var(--muted); font-size: 10px; margin: 3px 0 0; }
.manual-badge { background: #eaf2ff; color: #1265c4; }
.registry-actions > strong { font-size: 11px; }
.summary-badge--red { background: #fff0f0; color: #bc3d3d; }
.summary-badge--amber { background: #fff4df; color: #a86908; }
.legend-row { align-items: center; border-bottom: 1px solid #e9eef2; color: var(--muted); display: flex; flex-wrap: wrap; font-size: 10px; gap: 14px; margin-top: 12px; padding: 0 0 11px; }
.legend-row > span { align-items: center; display: inline-flex; gap: 6px; }
.legend-row small { margin-left: auto; }
.legend-dot { background: #df8a26; border-radius: 50%; height: 8px; width: 8px; }
.legend-dot--locked { background: var(--green); }
.role-groups { display: grid; gap: 11px; grid-template-columns: repeat(4,minmax(0,1fr)); padding-top: 13px; }
.role-group { background: #f5f8fb; border: 1px solid #edf1f4; border-radius: 7px; min-width: 0; padding: 10px; }
.role-group__header { align-items: center; color: #294052; display: flex; font-size: 10px; font-weight: 800; justify-content: space-between; letter-spacing: .03em; margin-bottom: 8px; text-transform: uppercase; }
.role-group__header h3 { font-size: inherit; margin: 0; }
.role-group__header span { color: #6e7f8b; }
.role-stack { display: grid; gap: 7px; }
.role-card { align-items: stretch; background: #fff; border: 1px solid #dbe3e9; border-radius: 6px; color: inherit; cursor: pointer; display: flex; min-height: 74px; padding: 0; text-align: left; transition: border-color .15s ease,box-shadow .15s ease; width: 100%; }
.role-card:hover { border-color: #7fb1df; box-shadow: 0 3px 12px #173a5512; }
.role-accent { background: var(--orange); border-radius: 6px 0 0 6px; flex: 0 0 4px; }
.role-card--locked .role-accent { background: var(--green); }
.role-card--optional:not(.role-card--locked) .role-accent { background: #aab6bf; }
.role-card__body { display: flex; flex: 1; flex-direction: column; gap: 7px; min-width: 0; padding: 8px 9px; }
.role-card__top { gap: 6px; justify-content: space-between; }
.role-card__top strong { color: #5b6d7a; font-size: 9px; line-height: 1.3; text-transform: uppercase; }
.role-state { flex-shrink: 0; font-size: 8px; padding: 4px 7px; }
.role-state--locked { background: #e6f5ec; color: #187a4b; }
.role-state--draft { background: #eaf2ff; color: #1265c4; }
.role-state--empty { background: #fff0ed; color: #bd4337; }
.role-state--na { background: #edf1f4; color: #5c6871; }
.role-person { color: #1d3442; font-size: 11px; font-weight: 650; gap: 6px; min-width: 0; }
.avatar { align-items: center; background: var(--avatar-color,#163753); border: 2px solid #fff; border-radius: 50%; color: white; display: inline-flex; flex: 0 0 24px; font-size: 8px; font-weight: 800; height: 24px; justify-content: center; width: 24px; }
.role-person { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.role-person-empty { color: #bd4a3d; font-size: 10px; font-weight: 700; }
.more-count { color: var(--muted); font-size: 10px; margin-left: 30px; }
.role-card__foot { color: #87949d; display: flex; font-size: 8px; justify-content: space-between; margin-top: auto; }
.role-chevron { align-self: center; color: #8a9aa5; font-size: 20px; padding-right: 8px; }
.support-grid { display: grid; gap: 13px; grid-template-columns: minmax(0,.95fr) minmax(0,1.4fr); }
.support-panel { min-width: 0; padding: 13px 15px; }
.support-header { gap: 12px; justify-content: space-between; margin-bottom: 10px; }
.support-title { flex-wrap: wrap; gap: 8px; }
.neutral-badge { background: #edf1f4; color: #687783; font-size: 8px; padding: 4px 8px; }
.support-header small { color: var(--muted); font-size: 9px; }
.table-scroll { overflow-x: auto; }
.msp-table { border-collapse: collapse; font-size: 10px; min-width: 360px; width: 100%; }
.msp-table th { background: #173d5d; color: #fff; padding: 7px; text-align: left; }
.msp-table td { border-bottom: 1px solid #e2e8ed; padding: 8px 7px; }
.empty-panel,.empty-audit { color: var(--muted); font-size: 10px; }
.empty-panel { background: #fff6e7; border-radius: 5px; display: flex; flex-direction: column; gap: 5px; padding: 12px; }
.empty-panel strong { color: #775319; }
.audit-list { display: grid; }
.audit-row { align-items: baseline; border-top: 1px solid #e7edf1; display: grid; gap: 10px; grid-template-columns: 125px minmax(130px,.7fr) minmax(0,1.7fr); padding: 8px 2px; }
.audit-row time,.audit-row span { color: var(--muted); font-size: 9px; }
.audit-row strong { font-size: 9px; }
.state-message { color: var(--muted); font-size: 13px; padding: 36px; }
.state-message--error { background: #fff; border: 1px solid #edc5c1; border-radius: 8px; }
.state-message h1 { color: var(--ink); font-size: 20px; }
.drawer-backdrop { background: #102b3c66; inset: 0; position: fixed; z-index: 3000; }
.drawer-backdrop--top { z-index: 3010; }
.drawer { background: #fff; border-left: 2px solid #0c6dc5; box-shadow: -12px 0 32px #122c3b24; display: flex; flex-direction: column; height: 100%; margin-left: auto; max-width: 610px; width: min(610px,100%); }
.drawer--team { max-width: 550px; }
.drawer-header { align-items: flex-start; border-bottom: 1px solid var(--line); gap: 16px; justify-content: space-between; padding: 20px 22px 15px; }
.eyebrow { color: var(--blue); font-size: 9px; font-weight: 800; letter-spacing: .07em; margin: 0 0 5px; text-transform: uppercase; }
.drawer-header h2 { font-size: 18px; line-height: 1.25; margin: 0 0 5px; }
.drawer-source { color: #6e7e89; font-size: 8px; font-weight: 800; letter-spacing: .05em; }
.close-button { background: transparent; border: 0; color: #647580; cursor: pointer; font-size: 23px; line-height: 1; }
.drawer-content { flex: 1; overflow-y: auto; padding: 16px 22px 22px; }
.role-description { color: var(--muted); font-size: 11px; line-height: 1.5; margin: 0 0 14px; }
.locked-notice,.drawer-note { background: #eaf3ff; border-radius: 5px; color: #34556e; font-size: 10px; line-height: 1.45; margin: 10px 0; padding: 10px 11px; }
.locked-notice { background: #fff4df; color: #845a16; }
.section-row { align-items: flex-start; gap: 10px; justify-content: space-between; margin: 15px 0 9px; }
.section-row h3,.roster-heading { font-size: 12px; margin: 0; }
.section-row p { color: var(--muted); font-size: 9px; margin: 3px 0 0; }
.field-label { color: #435663; display: grid; font-size: 9px; font-weight: 750; gap: 5px; }
.field-label input,.field-label select,.search-box input { border: 1px solid #cbd6de; border-radius: 4px; color: var(--ink); font: inherit; font-size: 11px; min-height: 34px; padding: 7px 9px; width: 100%; }
.field-label input:focus,.field-label select:focus,.search-box input:focus { border-color: #4c95d8; outline: 2px solid #4c95d82a; }
.search-box { display: block; margin-top: 10px; }
.member-picker,.team-roster { border: 1px solid #dce4e9; border-radius: 5px; margin-top: 8px; max-height: 280px; overflow-y: auto; }
.member-option,.roster-person { border-bottom: 1px solid #e8edf1; gap: 9px; padding: 9px; }
.member-option:last-child,.roster-person:last-child { border-bottom: 0; }
.member-option { cursor: pointer; }
.member-option--selected { background: #edf5ff; }
.member-option input,.na-option input { accent-color: #0869c7; flex: 0 0 auto; }
.member-copy { display: flex; flex: 1; flex-direction: column; gap: 3px; min-width: 0; }
.member-copy strong { font-size: 11px; }
.member-copy small { color: var(--muted); font-size: 9px; overflow-wrap: anywhere; }
.empty-picker { background: #f4f7f9; border-radius: 5px; color: var(--muted); display: flex; flex-direction: column; font-size: 10px; gap: 4px; margin: 9px 0; padding: 12px; }
.empty-picker strong { color: var(--ink); }
.add-person-link { margin-top: 6px; }
.na-option { align-items: center; background: #f3f6f8; border-radius: 4px; display: flex; font-size: 11px; gap: 8px; padding: 9px; }
.notes-field { margin-top: 15px; }
.field-label textarea { border: 1px solid #cbd6de; border-radius: 4px; font: inherit; font-size: 11px; padding: 8px; resize: vertical; }
.msp-edit-row { align-items: end; border-bottom: 1px solid #e7edf1; display: grid; gap: 8px; grid-template-columns: .7fr 1.3fr auto; padding: 10px 0; }
.remove-link { background: transparent; border: 0; color: #ad3932; cursor: pointer; font: inherit; font-size: 9px; padding: 7px 3px; }
.drawer-footer { border-top: 1px solid var(--line); flex-wrap: wrap; gap: 7px; justify-content: flex-end; padding: 12px 18px; }
.team-form { background: #f5f8fa; border: 1px solid #e2e9ee; border-radius: 6px; display: grid; gap: 10px; padding: 12px; }
.form-pair { display: grid; gap: 9px; grid-template-columns: 1fr 1fr; }
.roster-heading { margin: 17px 0 7px; }
.sr-only { clip: rect(0,0,0,0); height: 1px; margin: -1px; overflow: hidden; position: absolute; width: 1px; }

@media (max-width: 1120px) { .role-groups { grid-template-columns: repeat(2,minmax(0,1fr)); } }
@media (max-width: 760px) {
  .stakeholder-page { padding: 4px 0 24px; }
  .project-header,.registry-topline,.support-header { align-items: flex-start; flex-direction: column; }
  .header-actions,.registry-actions { justify-content: flex-start; width: 100%; }
  .role-groups,.support-grid { grid-template-columns: 1fr; }
  .legend-row small { margin-left: 0; }
  .audit-row { gap: 4px 8px; grid-template-columns: 1fr 1fr; }
  .audit-row span { grid-column: 1 / -1; }
  .drawer-header,.drawer-content { padding-left: 15px; padding-right: 15px; }
  .msp-edit-row { grid-template-columns: 1fr; }
}

.status-chip--not-started {
  background: #eef2f6;
  color: #5f7184;
}

.project-header {
  background: linear-gradient(110deg, #fff 0%, #fff 74%, #f7faff 100%);
  border-left-width: 3px;
}

.registry-panel {
  padding: 24px;
}

.registry-topline {
  padding-bottom: 20px;
}

.registry-heading h2 {
  font-size: 20px;
}

.registry-heading p {
  font-size: 13px;
}

.manual-badge {
  align-self: center;
  border: 1px solid #dae8f8;
  font-size: 9px;
  letter-spacing: 0.08em;
}

.registry-actions > strong {
  font-size: 13px;
}

.completion-strip {
  align-items: center;
  background: #f7f9fc;
  border: 1px solid #e7edf4;
  border-radius: 8px;
  display: grid;
  gap: 20px;
  grid-template-columns: minmax(190px, 0.42fr) minmax(0, 1fr);
  margin-top: 17px;
  padding: 12px 16px;
}

.completion-copy {
  align-items: center;
  display: flex;
  gap: 12px;
  min-width: 0;
}

.completion-percent {
  color: #176bb7;
  flex: 0 0 auto;
  font-size: 25px;
  font-weight: 750;
  line-height: 1;
  min-width: 54px;
}

.completion-description {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.completion-description strong {
  color: #29435b;
  font-size: 11px;
}

.completion-description small {
  color: #74849a;
  font-size: 10px;
  line-height: 1.35;
}

.completion-track {
  background: #e3eaf1;
  border-radius: 999px;
  height: 7px;
  overflow: hidden;
}

.completion-track span {
  background: linear-gradient(90deg, #2d8cff, #176bb7);
  border-radius: inherit;
  display: block;
  height: 100%;
  min-width: 0;
  transition: width 0.3s ease;
}

.summary-badge--red {
  background: #fff6e8;
  color: #976517;
}

.role-groups {
  align-items: start;
  gap: 16px;
}

.role-group {
  align-self: start;
  background: #f8fafd;
  border-color: #e7edf4;
  border-radius: 9px;
  box-shadow: none;
  padding: 14px;
}

.role-group__header {
  color: #3b5369;
  font-size: 11px;
  margin-bottom: 12px;
  padding: 0 1px 9px;
}

.role-stack {
  gap: 9px;
}

.role-card {
  border-color: #e2e9f1;
  border-radius: 7px;
  box-shadow: 0 1px 3px rgba(24, 50, 78, 0.035);
  min-height: 92px;
}

.role-card:hover {
  box-shadow: 0 5px 13px rgba(24, 60, 100, 0.075);
  transform: translateY(-1px);
}

.role-card__body {
  gap: 9px;
  padding: 11px 12px 10px;
}

.role-card__top strong {
  color: #405b72;
  font-size: 12px;
  font-weight: 750;
  letter-spacing: 0.01em;
  text-transform: none;
}

.role-state {
  font-size: 8px;
  font-weight: 750;
  letter-spacing: 0.045em;
  padding: 5px 8px;
}

.role-state--empty {
  background: #f3f6f8;
  color: #65798c;
}

.role-person {
  color: #233f58;
  font-size: 12px;
}

.role-person-empty {
  color: #496780;
  font-size: 12px;
  font-weight: 650;
}

.role-card__foot {
  color: #72849a;
  font-size: 9px;
}

.role-chevron {
  color: #8294a5;
}

.support-panel {
  padding: 18px 20px;
}

.support-title h2 {
  font-size: 18px;
}

.audit-row time,
.audit-row span,
.audit-row strong {
  font-size: 10px;
}

.drawer {
  border-left: 2px solid #8aaac6;
  box-shadow: -14px 0 38px rgba(16, 37, 66, 0.16);
  max-width: 640px;
  width: min(640px, 100%);
}

.drawer--team {
  max-width: 570px;
}

.drawer-header {
  padding: 25px 27px 19px;
}

.drawer-header h2 {
  font-size: 22px;
  letter-spacing: -0.01em;
}

.drawer-source {
  color: #698099;
  font-size: 9px;
  letter-spacing: 0.07em;
}

.drawer-content {
  padding: 21px 27px 27px;
}

.role-description {
  color: #5e7288;
  font-size: 13px;
  margin-bottom: 20px;
}

.section-row h3,
.roster-heading {
  font-size: 14px;
}

.section-row p {
  font-size: 11px;
}

.field-label {
  color: #3c556a;
  font-size: 11px;
  gap: 7px;
}

.field-label input,
.field-label select,
.search-box input,
.field-label textarea {
  border-color: #d3dee8;
  border-radius: 6px;
  font-size: 13px;
  min-height: 42px;
  padding: 9px 11px;
}

.field-label textarea {
  min-height: 86px;
}

.member-picker,
.team-roster {
  border-color: #e1e8ef;
  border-radius: 7px;
  max-height: 340px;
}

.member-option,
.roster-person {
  gap: 11px;
  padding: 12px;
}

.member-option:hover {
  background: #f7faff;
}

.member-option--selected {
  background: #eef5fc;
}

.member-copy strong {
  color: #1f3c55;
  font-size: 13px;
}

.member-copy small {
  font-size: 10px;
}

.empty-picker {
  align-items: flex-start;
  background: #f8fafc;
  border: 1px dashed #d5e0e9;
  border-radius: 7px;
  color: #697d90;
  font-size: 11px;
  line-height: 1.5;
  margin: 11px 0;
  padding: 15px;
}

.empty-picker strong {
  color: #344e65;
  font-size: 12px;
}

.text-button {
  background: transparent;
  border: 0;
  cursor: pointer;
  font: inherit;
  font-size: 11px;
  font-weight: 700;
  padding: 5px 2px;
}

.add-person-link {
  align-items: center;
  background: #f7faff;
  border: 1px dashed #b9cee2;
  border-radius: 6px;
  display: inline-flex;
  margin-top: 10px;
  padding: 9px 12px;
}

.add-person-link:hover:not(:disabled) {
  background: #eef5fc;
  border-color: #8caecc;
}

.na-option {
  background: #f7f9fb;
  border: 1px solid #e5ebf0;
  border-radius: 6px;
  font-size: 12px;
  padding: 12px;
}

.drawer-note {
  background: #f1f6fb;
  color: #506a82;
  font-size: 11px;
  line-height: 1.55;
  margin-top: 20px;
  padding: 13px 14px;
}

.drawer-footer {
  background: #fbfcfe;
  gap: 9px;
  padding: 15px 23px;
}

.team-form {
  background: #f8fafd;
  border-color: #e3eaf1;
  border-radius: 8px;
  gap: 13px;
  padding: 16px;
}

.msp-edit-row {
  padding: 13px 0;
}

@media (max-width: 760px) {
  .registry-panel {
    padding: 16px;
  }

  .role-group {
    padding: 12px;
  }

  .drawer-header,
  .drawer-content {
    padding-left: 17px;
    padding-right: 17px;
  }

  .completion-strip {
    gap: 10px;
    grid-template-columns: 1fr;
    padding: 12px;
  }

  .completion-percent {
    font-size: 22px;
  }
}

.stakeholder-shell {
  background: #f5f8fc;
}

.stakeholder-page {
  --ink: #102542;
  --muted: #657791;
  --line: #dfe7f0;
  --blue: #1673df;
  --orange: #f28a24;
  --green: #249a69;
  gap: 18px;
  max-width: 1540px;
  padding: 12px 10px 40px;
}

.breadcrumb {
  color: #75859a;
  font-size: 12px;
  gap: 11px;
  padding: 0 2px;
}

.breadcrumb a {
  color: #2478ce;
  font-weight: 600;
}

.project-header {
  background: linear-gradient(110deg, #fff 0%, #fff 68%, #f5f9ff 100%);
  border: 1px solid #e1e8f2;
  border-left: 4px solid #2d8cff;
  border-radius: 11px;
  box-shadow: 0 8px 24px rgba(32, 73, 125, 0.07);
  min-height: 100px;
  padding: 20px 24px;
}

.title-line {
  gap: 14px;
}

.title-line h1 {
  color: #102542;
  font-size: 29px;
  font-weight: 750;
  letter-spacing: -0.025em;
}

.status-chip {
  font-size: 10px;
  letter-spacing: 0.06em;
  padding: 6px 12px;
}

.project-meta {
  color: #687992;
  font-size: 12px;
  gap: 10px;
  margin-top: 9px;
}

.project-meta strong {
  color: #344b64;
  font-weight: 700;
}

.header-actions {
  gap: 9px;
}

.button {
  border-color: #ced9e5;
  border-radius: 6px;
  font-size: 12px;
  min-height: 39px;
  padding: 8px 15px;
  transition: background-color 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease, transform 0.16s ease;
}

.button--outline:hover:not(:disabled) {
  background: #f5f9ff;
  border-color: #8db7e3;
  color: #145da5;
}

.button--primary {
  box-shadow: 0 3px 8px rgba(22, 115, 223, 0.18);
}

.button--primary:hover:not(:disabled) {
  box-shadow: 0 6px 14px rgba(22, 115, 223, 0.22);
  transform: translateY(-1px);
}

.registry-panel {
  background: linear-gradient(145deg, #fff 0%, #fff 70%, #f9fbfe 100%);
  border-color: #e1e8f2;
  border-radius: 12px;
  box-shadow: 0 10px 28px rgba(35, 63, 100, 0.07);
  padding: 21px 22px 20px;
}

.registry-topline {
  gap: 18px;
  padding-bottom: 17px;
}

.registry-heading {
  gap: 12px;
}

.registry-heading .number-badge,
.support-title .number-badge {
  box-shadow: 0 3px 8px rgba(242, 138, 36, 0.22);
  flex-basis: 30px;
  font-size: 13px;
  height: 30px;
  width: 30px;
}

.registry-heading h2,
.support-title h2 {
  color: #102542;
  font-size: 18px;
  font-weight: 750;
  letter-spacing: -0.01em;
}

.registry-heading p {
  color: #687992;
  font-size: 12px;
  margin-top: 5px;
}

.manual-badge {
  background: #eaf3ff;
  color: #1673df;
  font-size: 9px;
  padding: 6px 11px;
}

.registry-actions {
  gap: 9px;
}

.registry-actions > strong {
  color: #344b64;
  font-size: 12px;
  margin-right: 2px;
}

.summary-badge--red,
.summary-badge--amber {
  font-size: 9px;
  padding: 6px 11px;
}

.legend-row {
  color: #657791;
  font-size: 11px;
  gap: 18px;
  margin-top: 12px;
  padding-bottom: 14px;
}

.legend-row small {
  color: #71819a;
  font-size: 11px;
}

.legend-dot {
  box-shadow: 0 0 0 3px rgba(242, 138, 36, 0.12);
  height: 9px;
  width: 9px;
}

.legend-dot--locked {
  box-shadow: 0 0 0 3px rgba(36, 154, 105, 0.12);
}

.role-groups {
  gap: 15px;
  padding-top: 16px;
}

.role-group {
  background: linear-gradient(180deg, #f8faff 0%, #f4f7fb 100%);
  border: 1px solid #e4ebf3;
  border-radius: 10px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
  padding: 13px;
  position: relative;
}

.role-group::before {
  background: #9db5c9;
  border-radius: 10px 10px 0 0;
  content: '';
  height: 1px;
  left: 0;
  position: absolute;
  right: 0;
  top: 0;
}

.role-group:nth-child(1),
.role-group:nth-child(2),
.role-group:nth-child(3),
.role-group:nth-child(4) { --group-accent: #8da9c0; }

.role-group__header {
  color: #344b64;
  font-size: 11px;
  letter-spacing: 0.045em;
  margin: 2px 0 11px;
  padding: 0 1px 9px;
}

.role-group__header span {
  align-items: center;
  background: color-mix(in srgb, var(--group-accent) 11%, white);
  border-radius: 999px;
  color: color-mix(in srgb, var(--group-accent) 75%, #102542);
  display: inline-flex;
  font-size: 10px;
  height: 23px;
  justify-content: center;
  min-width: 23px;
  padding: 0 7px;
}

.role-stack {
  gap: 9px;
}

.role-card {
  border-color: #e1e8f0;
  border-radius: 8px;
  box-shadow: 0 2px 5px rgba(25, 54, 88, 0.035);
  min-height: 86px;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.role-card:hover {
  border-color: color-mix(in srgb, var(--group-accent) 48%, #dbe5ef);
  box-shadow: 0 7px 18px rgba(28, 65, 110, 0.1);
  transform: translateY(-2px);
}

.role-accent {
  background: #91abc1;
  flex-basis: 2px;
}

.role-card--locked .role-accent {
  background: #42a878;
}

.role-card__body {
  gap: 9px;
  padding: 11px 12px 10px;
}

.role-card__top strong {
  color: #526a7e;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.025em;
  line-height: 1.35;
  text-transform: none;
}

.role-state {
  font-size: 8px;
  letter-spacing: 0.045em;
  padding: 5px 8px;
}

.role-state--locked {
  background: #e9f7ed;
  color: #278552;
}

.role-state--draft {
  background: #edf4ff;
  color: #2672cb;
}

.role-state--empty {
  background: #fff1ef;
  color: #c45c4c;
}

.role-person {
  color: #203b53;
  font-size: 12px;
}

.avatar {
  box-shadow: 0 1px 3px rgba(13, 42, 69, 0.16);
  flex-basis: 27px;
  font-size: 9px;
  height: 27px;
  width: 27px;
}

.role-person-empty {
  color: #c3654f;
  font-size: 11px;
}

.role-card__foot {
  color: #8190a4;
  font-size: 9px;
}

.role-chevron {
  color: #8c9baa;
  font-size: 20px;
  padding-right: 10px;
}

.support-grid {
  gap: 16px;
  grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.4fr);
}

.support-panel {
  border-color: #e1e8f2;
  border-radius: 11px;
  box-shadow: 0 7px 20px rgba(35, 63, 100, 0.055);
  padding: 17px 19px;
}

.support-header {
  margin-bottom: 13px;
}

.support-title h2 {
  font-size: 16px;
}

.support-title .number-badge {
  flex-basis: 26px;
  height: 26px;
  width: 26px;
}

.support-header small {
  color: #71819a;
  font-size: 10px;
}

.msp-table {
  font-size: 11px;
}

.msp-table th {
  background: #173d5d;
  font-size: 10px;
  padding: 9px 10px;
}

.msp-table td {
  color: #354967;
  padding: 10px;
}

.empty-panel {
  background: #fff8ec;
  border: 1px solid #f3e5cc;
  color: #78613f;
  line-height: 1.45;
  padding: 15px;
}

.empty-panel strong {
  color: #7e551c;
  font-size: 12px;
}

.audit-row {
  border-top-color: #e8edf3;
  gap: 13px;
  grid-template-columns: 145px minmax(140px, 0.7fr) minmax(0, 1.7fr);
  padding: 11px 3px;
}

.audit-row time,
.audit-row span,
.audit-row strong {
  font-size: 10px;
}

.empty-audit {
  background: #f7f9fc;
  border-radius: 6px;
  line-height: 1.5;
  margin: 0;
  padding: 15px;
}

.drawer-backdrop {
  animation: stakeholder-fade 0.16s ease-out both;
  backdrop-filter: blur(2px);
  background: rgba(13, 35, 57, 0.42);
}

.drawer {
  animation: stakeholder-slide 0.22s cubic-bezier(0.2, 0.8, 0.2, 1) both;
  border-left: 3px solid #2d8cff;
  box-shadow: -18px 0 48px rgba(16, 37, 66, 0.2);
  max-width: 650px;
  width: min(650px, 100%);
}

.drawer-header {
  background: linear-gradient(120deg, #fff 0%, #f6f9ff 100%);
  padding: 23px 26px 18px;
}

.drawer-header h2 {
  color: #102542;
  font-size: 20px;
}

.drawer-content {
  padding: 20px 26px 26px;
}

.role-description {
  color: #526885;
  font-size: 12px;
  line-height: 1.55;
}

.section-row h3,
.roster-heading {
  color: #18334b;
  font-size: 13px;
}

.field-label {
  color: #425b71;
  font-size: 10px;
  gap: 6px;
}

.field-label input,
.field-label select,
.search-box input,
.field-label textarea {
  border-color: #d1dce8;
  border-radius: 6px;
  font-size: 12px;
  min-height: 39px;
  padding: 9px 11px;
}

.member-picker,
.team-roster {
  border-color: #e0e8f0;
  border-radius: 7px;
  max-height: 330px;
}

.member-option,
.roster-person {
  padding: 11px;
  transition: background-color 0.15s ease;
}

.member-option:hover {
  background: #f5f9ff;
}

.member-option--selected {
  background: #edf5ff;
}

.member-copy strong {
  color: #19354e;
  font-size: 12px;
}

.member-copy small {
  font-size: 10px;
}

.drawer-note {
  background: #eef5ff;
  color: #3c5d7c;
  font-size: 11px;
  margin-top: 20px;
  padding: 13px 14px;
}

.drawer-footer {
  background: #fbfcfe;
  gap: 9px;
  padding: 15px 22px;
}

.team-form {
  background: #f7f9fc;
  border-color: #e2e9f2;
  border-radius: 8px;
  gap: 12px;
  padding: 16px;
}

@keyframes stakeholder-fade {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes stakeholder-slide {
  from { opacity: 0; transform: translateX(22px); }
  to { opacity: 1; transform: translateX(0); }
}

@media (prefers-reduced-motion: reduce) {
  .drawer-backdrop,
  .drawer {
    animation: none;
  }
}

@media (max-width: 760px) {
  .project-header {
    background: #fff;
    border-left-width: 3px;
    padding: 17px;
  }

  .title-line h1 {
    font-size: 24px;
  }

  .registry-panel {
    padding: 15px;
  }

  .registry-heading {
    align-items: flex-start;
  }

  .manual-badge {
    margin-left: 4px;
  }

  .drawer-header,
  .drawer-content {
    padding-left: 16px;
    padding-right: 16px;
  }
}
</style>