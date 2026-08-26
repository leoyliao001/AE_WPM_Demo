<template>
  <div class="ac-page">
    <main class="ac-main">
      <!-- ===================== VIEW 1 — APPROVAL INBOX ===================== -->
      <section v-if="view === 'inbox'" class="ac-shell" aria-labelledby="ac-inbox-title">
        <nav class="ac-crumbs" aria-label="Breadcrumb">
          <a href="#" @click.prevent>Home</a>
          <span aria-hidden="true">/</span>
          <span class="ac-crumbs-current">Approvals</span>
        </nav>

        <h1 id="ac-inbox-title" class="ac-title">Approvals</h1>
        <p class="ac-subtitle">
          {{ waitingCount }} requests waiting on you · {{ breachingCount }} breaching SLA
          <span v-if="loading" class="ac-state">· loading intake data…</span>
          <span v-else-if="loadError" class="ac-state ac-state-warn">· {{ loadError }}</span>
        </p>

        <div class="ac-tabs" role="tablist" aria-label="Approval queues">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            class="ac-tab"
            :class="{ 'is-active': activeTab === tab.key }"
            type="button"
            role="tab"
            :aria-selected="activeTab === tab.key"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
            <span v-if="tab.count != null" class="ac-tab-count">({{ tab.count }})</span>
          </button>
        </div>

        <div class="ac-toolbar">
          <div class="ac-search">
            <svg class="ac-search-icon" viewBox="0 0 20 20" aria-hidden="true">
              <circle cx="9" cy="9" r="5.5" fill="none" stroke="currentColor" stroke-width="1.6" />
              <path d="M13.2 13.2 17 17" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
            </svg>
            <input
              v-model="search"
              type="search"
              placeholder="Search by ID, opportunity or requester"
              aria-label="Search approval requests"
            />
          </div>

          <label class="ac-select">
            <span class="ac-select-label">Type</span>
            <select v-model="typeFilter" aria-label="Filter by request type">
              <option v-for="opt in typeOptions" :key="opt" :value="opt">{{ opt }}</option>
            </select>
          </label>

          <label class="ac-select">
            <span class="ac-select-label">Area</span>
            <select v-model="areaFilter" aria-label="Filter by area">
              <option value="All areas">All areas</option>
              <optgroup v-for="(areas, region) in regionAreaMapping" :key="region" :label="region">
                <option v-for="area in areas" :key="area" :value="area">{{ area }}</option>
              </optgroup>
            </select>
          </label>

          <label class="ac-select">
            <span class="ac-select-label">Budget</span>
            <select v-model="budgetFilter" aria-label="Filter by budget status">
              <option v-for="opt in budgetOptions" :key="opt" :value="opt">{{ opt }}</option>
            </select>
          </label>

          <div class="ac-toolbar-actions">
            <button class="ac-btn ac-btn-ghost" type="button" @click="exportRows">
              Export
            </button>
            <button
              v-if="selected.size > 0"
              class="ac-btn ac-btn-primary"
              type="button"
              @click="approveSelected"
            >
              Approve selected ({{ selected.size }})
            </button>
          </div>
        </div>

        <div class="ac-card ac-table-card">
          <div class="ac-table-scroll">
            <table class="ac-table">
              <thead>
                <tr>
                  <th class="ac-col-check">
                    <input
                      type="checkbox"
                      aria-label="Select all visible requests"
                      :checked="allVisibleSelected"
                      @change="toggleAll"
                    />
                  </th>
                  <th>Request</th>
                  <th>Type</th>
                  <th>Requester / Area</th>
                  <th>Scope</th>
                  <th>Budget</th>
                  <th>Stage</th>
                  <th>Waiting</th>
                  <th class="ac-col-action">Action</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in visibleRows"
                  :key="row.id"
                  class="ac-row"
                  :class="{ 'is-selected': selected.has(row.id) }"
                  tabindex="0"
                  @click="openDetails(row)"
                  @keydown.enter="openDetails(row)"
                >
                  <td class="ac-col-check" @click.stop>
                    <input
                      type="checkbox"
                      :aria-label="`Select ${row.id}`"
                      :checked="selected.has(row.id)"
                      @change="toggleRow(row.id)"
                    />
                  </td>
                  <td>
                    <span class="ac-row-title">{{ row.title }}</span>
                    <span class="ac-row-sub">{{ row.id }} · submitted {{ row.submitted }}</span>
                  </td>
                  <td><span class="ac-tag ac-tag-info">{{ row.type }}</span></td>
                  <td>
                    <span class="ac-row-title">{{ row.requester }}</span>
                    <span class="ac-row-sub">{{ row.area }} · {{ row.region }}</span>
                  </td>
                  <td>
                    <span class="ac-row-title">{{ row.fte.toFixed(1) }} FTE</span>
                    <span class="ac-row-sub">{{ row.scope }}</span>
                  </td>
                  <td>
                    <span class="ac-tag" :class="budgetTagClass(row)">
                      {{ budgetLabel(row) }}
                    </span>
                  </td>
                  <td>
                    <span class="ac-row-title">{{ stageNameFor(row) }}</span>
                    <span class="ac-row-sub">Step {{ row.step }} of {{ totalStepsFor(row) }}</span>
                  </td>
                  <td>
                    <span class="ac-tag" :class="row.slaBreached ? 'ac-tag-error' : 'ac-tag-neutral'">
                      {{ row.waiting }}
                    </span>
                  </td>
                  <td class="ac-col-action" @click.stop>
                    <button class="ac-btn ac-btn-ghost ac-btn-sm" type="button" @click="openDetails(row)">
                      {{ row.actionable ? 'Review' : 'View' }}
                    </button>
                  </td>
                </tr>
                <tr v-if="visibleRows.length === 0">
                  <td class="ac-empty" colspan="9">No requests match the current filters.</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="ac-table-foot">
            <span>Showing {{ visibleRows.length }} of {{ filteredRows.length }}</span>
            <template v-if="visibleCount < filteredRows.length">
              <span aria-hidden="true">·</span>
              <button class="ac-link-btn" type="button" @click="visibleCount += 4">Load more</button>
            </template>
          </div>
        </div>
      </section>

      <!-- ===================== VIEW 2 — REQUEST DETAILS ===================== -->
      <section v-else class="ac-shell" aria-labelledby="ac-detail-title">
        <nav class="ac-crumbs" aria-label="Breadcrumb">
          <a href="#" @click.prevent="view = 'inbox'">Approvals</a>
          <span aria-hidden="true">/</span>
          <span class="ac-crumbs-current">{{ detail.id }}</span>
        </nav>

        <div class="ac-detail-head">
          <div>
            <h1 id="ac-detail-title" class="ac-title">{{ detail.title }}</h1>
            <p class="ac-subtitle">
              {{ detail.id }} · Submitted by {{ detail.requester }} on {{ detail.submitted }} ·
              {{ detail.fte.toFixed(1) }} FTE
            </p>
          </div>
          <div class="ac-detail-tags">
            <span class="ac-tag ac-tag-info">{{ detail.type }}</span>
            <span class="ac-tag" :class="budgetTagClass(detail)">
              {{ budgetLabel(detail) }}
            </span>
            <span class="ac-tag ac-tag-neutral">{{ detail.actionable ? 'Waiting on you' : 'In progress' }}</span>
          </div>
        </div>

        <div v-if="detail.beyondBudget" class="ac-banner" role="status">
          <span class="ac-banner-mark" aria-hidden="true">!</span>
          <div>
            <strong>Beyond budget — FBP approval is mandatory.</strong>
            <p>
              Annualised cost is {{ money(detail.transitionCost) }} above the approved area budget, so the
              FBP Approve step in the chain below cannot be waived.
            </p>
          </div>
        </div>

        <div class="ac-detail-grid">
          <div class="ac-detail-col">
            <!-- Slot 1 — approval chain -->
            <div class="ac-card">
              <h2 class="ac-card-title">Approval chain — {{ detail.type }}</h2>
              <p class="ac-card-sub">
                Pre-requisite: {{ detail.prerequisite }} —
                <span class="ac-met">met</span>
              </p>

              <ol class="ac-chain">
                <li
                  v-for="(step, i) in chainFor(detail)"
                  :key="step.name"
                  class="ac-chain-step"
                  :class="`is-${step.state}`"
                >
                  <span
                    class="ac-chain-line"
                    :class="{ 'is-done': i > 0 && chainFor(detail)[i - 1].state === 'done' }"
                    aria-hidden="true"
                  ></span>
                  <span class="ac-chain-dot">
                    <template v-if="step.state === 'done'">✓</template>
                    <template v-else>{{ i + 1 }}</template>
                  </span>
                  <span class="ac-chain-name">{{ step.name }}</span>
                  <span class="ac-chain-meta">{{ step.meta }}</span>
                </li>
              </ol>
            </div>

            <!-- Slot 2 — business case -->
            <div class="ac-card">
              <h2 class="ac-card-title">Business case</h2>
              <div class="ac-metrics">
                <div v-for="m in detail.businessCase" :key="m.label" class="ac-metric">
                  <span class="ac-metric-label">{{ m.label }}</span>
                  <span class="ac-metric-value">{{ m.value }}</span>
                  <span class="ac-metric-note">{{ m.note }}</span>
                </div>
              </div>
              <p class="ac-case-text">{{ detail.rationale }}</p>
              <p class="ac-doc">
                <a
                  v-if="detail.businessCaseDoc"
                  class="ac-doc-link"
                  :href="detail.businessCaseDoc.url"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <svg viewBox="0 0 20 20" aria-hidden="true">
                    <path
                      d="M11.5 2.5H5.5a1 1 0 0 0-1 1v13a1 1 0 0 0 1 1h9a1 1 0 0 0 1-1V6.5l-4-4Z"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.4"
                      stroke-linejoin="round"
                    />
                    <path d="M11.5 2.5v4h4" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round" />
                  </svg>
                  {{ detail.businessCaseDoc.name }}
                </a>
                <span v-else class="ac-doc-empty">No business case document attached.</span>
              </p>
            </div>

            <!-- Slot 3 — request details -->
            <div class="ac-card">
              <h2 class="ac-card-title">Opportunity summary</h2>
              <dl class="ac-defs">
                <div><dt>Project Name</dt><dd>{{ detail.title }}</dd></div>
                <div><dt>Migration Type</dt><dd>{{ detail.type }}</dd></div>
                <div><dt>Brief Description</dt><dd>{{ detail.briefDescription }}</dd></div>
                <div><dt>Org Unit</dt><dd>{{ detail.orgUnit }}</dd></div>
                <div><dt>Product</dt><dd>{{ detail.product }}</dd></div>
                <div><dt>Function</dt><dd>{{ detail.functionName }}</dd></div>
                <div><dt>Region</dt><dd>{{ detail.region }}</dd></div>
                <div>
                  <dt>No of PIDs to be added in GSC along with Job level detail</dt>
                  <dd>
                    <span>Total {{ detail.pidsAdded }} PID</span>
                    <span v-for="jl in detail.jobLevels" :key="jl.label" class="ac-jl">
                      {{ jl.label }} – {{ jl.count }} PID
                    </span>
                  </dd>
                </div>
                <div><dt>No of PIDs to be released from Area</dt><dd>{{ detail.pidsReleased }}</dd></div>
              </dl>
            </div>

            <div class="ac-card">
              <h2 class="ac-card-title">Activity</h2>
              <ol class="ac-activity">
                <li v-for="item in activityFor(detail)" :key="item.title" :class="`is-${item.state}`">
                  <span class="ac-activity-dot" aria-hidden="true"></span>
                  <p class="ac-activity-head">
                    <strong>{{ item.title }}</strong>
                    <span v-if="item.by"> — {{ item.by }}</span>
                    <span v-if="item.at" class="ac-activity-at"> · {{ item.at }}</span>
                  </p>
                  <p v-if="item.note" class="ac-activity-note">{{ item.note }}</p>
                </li>
              </ol>
            </div>
          </div>

          <aside class="ac-decision-col">
            <!-- Sequential phase: Area Head / PMO Review / BPM Review / FBP Approve -->
            <div v-if="!isParallelPhase(detail)" class="ac-card ac-decision">
              <h2 class="ac-card-title">Your decision</h2>
              <p class="ac-card-sub">Step {{ detail.step }} of {{ totalStepsFor(detail) }} — {{ stageNameFor(detail) }}</p>

              <template v-if="!detail.actionable">
                <p class="ac-card-sub">
                  {{ myEmail || 'Your account' }} is not listed as the <strong>{{ stageNameFor(detail) }}</strong> approver for this
                  function/product in approval_input, so this stage isn't actionable from your account.
                </p>
              </template>
              <template v-else>
                <textarea
                  v-model="comment"
                  class="ac-textarea"
                  rows="4"
                  placeholder="Add a comment (required when rejecting or returning)"
                  aria-label="Decision comment"
                ></textarea>

                <!-- BPM Review: budget call decides whether FBP Approve is required next -->
                <template v-if="stageNameFor(detail) === 'BPM Review'">
                  <label class="ac-select ac-budget-select">
                    <span class="ac-select-label">Budget status</span>
                    <select v-model="budgetChoice" aria-label="Select budget status">
                      <option value="within">Within budget</option>
                      <option value="beyond">Beyond budget</option>
                    </select>
                  </label>
                  <p class="ac-card-sub">
                    {{ budgetChoice === 'beyond' ? 'Beyond budget \u2192 routes to FBP Approve next.' : 'Within budget \u2192 routes straight to ELT & GSC Head.' }}
                  </p>
                  <button class="ac-btn ac-btn-primary ac-btn-block" type="button" @click="decideBpm()">
                    Approve
                  </button>
                  <button class="ac-btn ac-btn-ghost ac-btn-block" type="button" @click="decide('returned')">
                    Return for more information
                  </button>
                  <button class="ac-btn ac-btn-danger ac-btn-block" type="button" @click="decide('rejected')">
                    Reject
                  </button>
                </template>

                <!-- PMO Review -->
                <template v-else-if="stageNameFor(detail) === 'PMO Review'">
                  <button class="ac-btn ac-btn-primary ac-btn-block" type="button" @click="decide('approved')">
                    Approve
                  </button>
                  <button class="ac-btn ac-btn-ghost ac-btn-block" type="button" @click="decide('returned')">
                    Return for more information
                  </button>
                  <button class="ac-btn ac-btn-danger ac-btn-block" type="button" @click="decide('rejected')">
                    Reject
                  </button>
                </template>

                <!-- Area Head / FBP Approve / WPM Review: full decision panel -->
                <template v-else>
                  <button class="ac-btn ac-btn-primary ac-btn-block" type="button" @click="decide('approved')">
                    Approve
                  </button>
                  <button v-if="stageNameFor(detail) !== 'Area Head'" class="ac-btn ac-btn-ghost ac-btn-block" type="button" @click="decide('returned')">
                    Return for more information
                  </button>
                  <button class="ac-btn ac-btn-danger ac-btn-block" type="button" @click="decide('rejected')">
                    Reject
                  </button>
                </template>
              </template>

              <p class="ac-card-sub">Next after you: {{ nextApproverFor(detail) }}</p>
              <p v-if="decisionMessage" class="ac-decision-msg" role="status">{{ decisionMessage }}</p>
            </div>

            <!-- Parallel phase: ELT and GSC Head decide independently, neither waits on the other -->
            <template v-else>
              <div v-if="detail.completed" class="ac-card ac-decision">
                <h2 class="ac-card-title">Fully approved</h2>
                <p class="ac-card-sub">ELT and GSC Head have both signed off.</p>
              </div>
              <div v-for="role in ['elt', 'gscHead']" v-else :key="role" class="ac-card ac-decision">
                <h2 class="ac-card-title">{{ role === 'elt' ? 'ELT decision' : 'GSC Head decision' }}</h2>
                <p class="ac-card-sub">
                  {{ detail.parallel[role] === 'pending' ? 'Waiting on this approver' : `Status: ${detail.parallel[role]}` }}
                </p>
                <template v-if="detail.parallel[role] === 'pending' && myRoleFor(detail, role)">
                  <textarea
                    v-model="parallelComment[role]"
                    class="ac-textarea"
                    rows="3"
                    placeholder="Add a comment (required when rejecting or returning)"
                    :aria-label="`${role} decision comment`"
                  ></textarea>
                  <button class="ac-btn ac-btn-primary ac-btn-block" type="button" @click="openFinalReview(role)">
                    Approve
                  </button>
                  <button class="ac-btn ac-btn-ghost ac-btn-block" type="button" @click="decideParallel(role, 'returned')">
                    Return for more information
                  </button>
                  <button class="ac-btn ac-btn-danger ac-btn-block" type="button" @click="decideParallel(role, 'rejected')">
                    Reject
                  </button>
                </template>
                <p v-else-if="detail.parallel[role] === 'pending'" class="ac-card-sub">
                  You are not listed as this approver for this function/product.
                </p>
              </div>
              <p v-if="decisionMessage" class="ac-decision-msg" role="status">{{ decisionMessage }}</p>
            </template>
          </aside>
        </div>
      </section>
    </main>

    <nav class="ac-switch" aria-label="View switcher">
      <button
        class="ac-switch-btn"
        :class="{ 'is-active': view === 'inbox' }"
        type="button"
        :aria-pressed="view === 'inbox'"
        @click="view = 'inbox'"
      >
        Approval Inbox
      </button>
      <button
        class="ac-switch-btn"
        :class="{ 'is-active': view === 'details' }"
        type="button"
        :aria-pressed="view === 'details'"
        @click="view = 'details'"
      >
        Request Details
      </button>
    </nav>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { regionAreaMapping } from '../data/regionAreaMapping.js'

const router = useRouter()
const view = ref('inbox')
const loading = ref(false)
const loadError = ref('')
const activeTab = ref('waiting')
const search = ref('')
const typeFilter = ref('All types')
const areaFilter = ref('All areas')
const budgetFilter = ref('Any budget status')
const visibleCount = ref(4)
const selected = ref(new Set())
const comment = ref('')
const budgetChoice = ref('within')
const parallelComment = ref({ elt: '', gscHead: '' })
const decisionMessage = ref('')

const tabs = computed(() => [
  { key: 'waiting', label: 'Waiting on me', count: waitingCount.value },
  { key: 'delegated', label: 'Delegated to me', count: delegatedCount.value },
  { key: 'submitted', label: 'Submitted by me', count: submittedCount.value },
  { key: 'completed', label: 'Completed', count: null }
])

const typeOptions = ['All types', '1:1 Migration', 'Co-location', 'New business']
const budgetOptions = ['Any budget status', 'Pending', 'Within budget', 'Beyond budget']

// Approval flow is the same shape for every migration type: three sequential
// roles, an optional FBP Approve gate for beyond-budget requests, then WPM
// Review, followed by ELT and GSC Head approvals in parallel.
const SEQUENTIAL_STEPS = ['Area Head', 'PMO Review', 'BPM Review']
const PARALLEL_STEPS = ['ELT', 'GSC Head-1']

const PREREQUISITES = {
  '1:1 Migration': 'Opportunity Assessment (≥ 1 FTE)',
  'Co-location': 'Opportunity Assessment',
  'New business': 'Opportunity Assessment'
}

const stepsFor = (beyondBudget) =>
  beyondBudget ? [...SEQUENTIAL_STEPS, 'FBP Approve', 'WPM Review', ...PARALLEL_STEPS] : [...SEQUENTIAL_STEPS, 'WPM Review', ...PARALLEL_STEPS]

const sequentialLength = (beyondBudget) => (beyondBudget ? 5 : 4)

const totalStepsFor = (row) => stepsFor(row.beyondBudget).length

const isParallelPhase = (row) => row.step > sequentialLength(row.beyondBudget)

const stageNameFor = (row) => {
  const seqLen = sequentialLength(row.beyondBudget)
  if (row.step <= seqLen) return stepsFor(row.beyondBudget)[row.step - 1]
  return 'ELT & GSC Head'
}

const chainFor = (row) => {
  const steps = stepsFor(row.beyondBudget)
  const seqLen = sequentialLength(row.beyondBudget)
  return steps.map((name, i) => {
    const n = i + 1
    if (n <= seqLen) {
      if (n < row.step) return { name, state: 'done', meta: 'Approved' }
      if (n === row.step) return { name, state: 'current', meta: 'You · pending' }
      return { name, state: 'todo', meta: 'Not started' }
    }
    const key = name === 'ELT' ? 'elt' : 'gscHead'
    const status = row.parallel?.[key] ?? 'pending'
    if (row.step <= seqLen) return { name, state: 'todo', meta: 'Runs in parallel once BPM/FBP is done' }
    if (status === 'pending') return { name, state: 'current', meta: 'You · pending (parallel)' }
    if (status === 'approved') return { name, state: 'done', meta: 'Approved' }
    return { name, state: 'todo', meta: status.charAt(0).toUpperCase() + status.slice(1) }
  })
}

const nextApproverFor = (row) => {
  const chain = chainFor(row)
  const todo = chain.find((s) => s.state === 'todo')
  if (todo) return todo.name
  const current = chain.filter((s) => s.state === 'current').map((s) => s.name)
  if (current.length) return current.join(' & ')
  return 'Final sign-off complete'
}

const activityFor = (row) => {
  const chain = chainFor(row)
  return chain.map((s, i) => {
    const role = approvalRoleForStep(s.name)
    const decision = row.decisions?.[role] || {}
    const responsible = (row.responsibleApprovers?.[role] || []).join(', ') || 'Not configured in Input for Approval'
    if (s.state === 'done') {
      return {
        title: `${s.name} ${decision.status || 'approved'}`,
        by: decision.approvedBy || responsible,
        at: formatDateTime(decision.date),
        note: decision.comment || `Responsible: ${responsible}`,
        state: 'done'
      }
    }
    if (s.state === 'current') {
      return {
        title: `Waiting for ${s.name}`,
        by: responsible,
        at: '',
        note: `${row.waitingDetail} · Responsible: ${responsible}`,
        state: 'current'
      }
    }
    return { title: s.name, at: '', note: `${s.meta || 'Not started'} · Responsible: ${responsible}`, state: 'todo' }
  })
}

const approvalRoleForStep = (step) => ({
  'Area Head': 'area_head',
  'PMO Review': 'pmo',
  'BPM Review': 'bpm',
  'FBP Approve': 'fbp',
  'WPM Review': 'wpm',
  ELT: 'elt',
  'GSC Head-1': 'gsc_head'
}[step] || '')

function money(value) {
  return `USD ${value.toLocaleString('en-US')}`
}

const TYPE_LABELS = {
  '1:1': '1:1 Migration',
  'co-location': 'Co-location',
  colocation: 'Co-location',
  'new business': 'New business'
}

const normaliseType = (value) => {
  const key = String(value || '').trim().toLowerCase()
  if (TYPE_LABELS[key]) return TYPE_LABELS[key]
  if (key.includes('co-loc') || key.includes('coloc')) return 'Co-location'
  if (key.includes('new')) return 'New business'
  return '1:1 Migration'
}

const formatDate = (value) => {
  const parsed = new Date(value)
  if (!value || Number.isNaN(parsed.getTime())) return String(value || '—')
  return parsed.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

const formatDateTime = (value) => {
  const parsed = new Date(value)
  if (!value || Number.isNaN(parsed.getTime())) return ''
  return parsed.toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const first = (value) => (Array.isArray(value) ? value[0] : value) || ''

const isBusinessDay = (date) => date.getDay() !== 0 && date.getDay() !== 6

const businessDaysElapsed = (from, to = new Date()) => {
  const start = new Date(from)
  if (Number.isNaN(start.getTime()) || to <= start) return 0
  const cursor = new Date(start)
  cursor.setHours(0, 0, 0, 0)
  const end = new Date(to)
  end.setHours(0, 0, 0, 0)
  let days = 0
  while (cursor < end) {
    cursor.setDate(cursor.getDate() + 1)
    if (isBusinessDay(cursor)) days += 1
  }
  return days
}

const addBusinessDays = (from, count) => {
  const date = new Date(from)
  if (Number.isNaN(date.getTime())) return null
  let remaining = count
  while (remaining > 0) {
    date.setDate(date.getDate() + 1)
    if (isBusinessDay(date)) remaining -= 1
  }
  return date
}

const formatDueDate = (value) => value.toLocaleDateString('en-GB', {
  day: '2-digit', month: 'short', year: 'numeric'
})

const activeApprovalRoles = (row) => {
  if (row.currentRole) return [row.currentRole]
  return ['elt', 'gsc_head'].filter((role) => row.parallel?.[role === 'gsc_head' ? 'gscHead' : role] === 'pending')
}

const stageStartFor = (row, role) => {
  if (role === 'area_head') return row.businessCaseSubmittedAt
  if (role === 'pmo') return row.decisions.area_head?.date
  if (role === 'bpm') return row.decisions.pmo?.date
  if (role === 'fbp') return row.decisions.bpm?.date
  if (role === 'wpm') return row.decisions[row.beyondBudget ? 'fbp' : 'bpm']?.date
  return row.decisions.wpm?.date
}

const approvalTimeline = (row) => {
  if (!row.businessCaseSubmittedAt) {
    return { waiting: 'Awaiting Business Case', detail: 'Approval timeline starts once the Business Case is submitted.', breached: false }
  }

  const roles = activeApprovalRoles(row)
  const timelines = roles.map((role) => {
    const start = stageStartFor(row, role)
    const allowedDays = role === 'pmo' ? 1 : 2
    if (!start) return null
    const elapsed = businessDaysElapsed(start)
    const dueDate = addBusinessDays(start, allowedDays)
    return { elapsed, allowedDays, dueDate, breached: elapsed > allowedDays }
  }).filter(Boolean)

  if (!timelines.length) {
    return { waiting: 'Timeline pending', detail: 'Waiting for the prior approval stage to be recorded.', breached: false }
  }

  const elapsed = Math.max(...timelines.map((item) => item.elapsed))
  const allowedDays = Math.max(...timelines.map((item) => item.allowedDays))
  const dueDate = timelines.map((item) => item.dueDate).sort((left, right) => left - right)[0]
  return {
    waiting: `${elapsed} of ${allowedDays} business days`,
    detail: `SLA ${allowedDays} business day${allowedDays === 1 ? '' : 's'} · due ${formatDueDate(dueDate)} · ${elapsed} elapsed`,
    breached: timelines.some((item) => item.breached)
  }
}

const budgetLabel = (row) => ({
  pending: 'Pending',
  within: 'Within budget',
  beyond: 'Beyond budget'
}[row.budgetStatus] || 'Pending')

const budgetTagClass = (row) => ({
  pending: 'ac-tag-neutral',
  within: 'ac-tag-success',
  beyond: 'ac-tag-warning'
}[row.budgetStatus] || 'ac-tag-neutral')

// GSC_ROLE_KEY -> template parallel key, used to check access for the ELT/GSC Head cards.
const myRoleFor = (row, role) => (row?.myRoles || []).includes(role === 'gscHead' ? 'gsc_head' : 'elt')

// Server already computed step/beyondBudget/parallel/myRoles/actionable; this only
// shapes the fields the template's business-case & summary sections read.
const toRow = (r) => {
  const fte = Number.parseFloat(r.fte_number) || 0
  const annualSaving = Math.round(fte * 44000) || 1
  const transitionCost = Math.round(fte * 12000)
  const type = normaliseType(r.migration_type_value || r.migration_type)
  const row = {
    id: r.migration_request_id,
    title: r.project_name || r.migration_request_id,
    type,
    requester: r.requestor || 'Unknown requester',
    area: first(r.areas) || r.region || '—',
    region: r.region || '—',
    fte,
    scope: r.proposed_scope || r.function_name || '—',
    budgetStatus: ['within', 'beyond'].includes(r.budgetStatus) ? r.budgetStatus : 'pending',
    beyondBudget: !!r.beyondBudget,
    currentRole: r.currentRole || '',
    decisions: r.decisions || {},
    responsibleApprovers: r.responsibleApprovers || {},
    businessCaseSubmittedAt: r.businessCaseSubmittedAt || null,
    step: r.step,
    totalSteps: r.totalSteps,
    parallel: { elt: r.parallel?.elt || 'pending', gscHead: r.parallel?.gscHead || 'pending' },
    completed: !!r.completed,
    myRoles: r.myRoles || [],
    actionable: !!r.actionable,
    waiting: '',
    waitingDetail: '',
    slaBreached: false,
    submitted: formatDate(r.requested_date),
    annualSaving,
    transitionCost,
    prerequisite: PREREQUISITES[type] ?? PREREQUISITES['1:1 Migration'],
    briefDescription: r.proposed_scope || '—',
    orgUnit: [r.region, first(r.areas)].filter(Boolean).join(' / ') || '—',
    product: first(r.products) || '—',
    functionName: r.function_name || '—',
    businessCaseDoc: null,
    pidsAdded: Number(r.job_level_total) || Math.round(fte),
    pidsReleased: Math.round(fte),
    jobLevels: [
      { label: 'JL1', count: 0 },
      { label: 'JL2', count: Number(r.jl2) || 0 },
      { label: 'JL3', count: Number(r.jl3) || 0 },
      { label: 'JL4', count: Number(r.jl4) || 0 },
      { label: 'JL5', count: 0 }
    ],
    businessCase: [
      { label: 'Annualised saving', value: money(annualSaving), note: 'Net of GSC delivery cost' },
      { label: 'Transition cost', value: money(transitionCost), note: 'One-off, incl. knowledge transfer' },
      {
        label: 'Payback',
        value: `${Math.max(1, Math.round((transitionCost / annualSaving) * 12))} months`,
        note: 'From go-live'
      },
      { label: 'FTE released', value: `${fte.toFixed(1)} FTE`, note: 'Sending entity' }
    ],
    rationale: `${r.proposed_scope || 'This request'} moves to GSC under a ${type.toLowerCase()} model. Process maps, SOPs and quality gates are signed off by the sending entity; ramp-up is phased to protect customer service levels.`,
    status: r.status || ''
  }
  const timeline = approvalTimeline(row)
  row.waiting = timeline.waiting
  row.waitingDetail = timeline.detail
  row.slaBreached = timeline.breached
  return row
}

const rows = ref([])
const detail = ref(null)
const myEmail = ref('')

async function loadQueue() {
  loading.value = true
  loadError.value = ''
  try {
    const { data } = await axios.get('/api/approval-cycle/queue/')
    myEmail.value = data?.email || ''
    const mapped = (data?.rows || []).filter((r) => r.migration_request_id).map(toRow)
    rows.value = mapped
    detail.value = mapped[0] || null
  } catch (e) {
    loadError.value = e?.response?.data?.error || 'Unable to load approval requests.'
    rows.value = []
    detail.value = null
  } finally {
    loading.value = false
  }
}

const filteredRows = computed(() => {
  const q = search.value.trim().toLowerCase()
  return rows.value.filter((row) => {
    if (q && ![row.id, row.title, row.requester].some((v) => String(v).toLowerCase().includes(q))) return false
    if (typeFilter.value !== 'All types' && row.type !== typeFilter.value) return false
    if (areaFilter.value !== 'All areas' && row.area !== areaFilter.value) return false
    if (budgetFilter.value === 'Pending' && row.budgetStatus !== 'pending') return false
    if (budgetFilter.value === 'Within budget' && row.budgetStatus !== 'within') return false
    if (budgetFilter.value === 'Beyond budget' && row.budgetStatus !== 'beyond') return false
    return true
  })
})

const waitingCount = computed(() => rows.value.length)
const breachingCount = computed(() => rows.value.filter((r) => r.slaBreached).length)
const delegatedCount = computed(() => rows.value.filter((r) => isParallelPhase(r)).length)
const submittedCount = computed(() => rows.value.filter((r) => r.step <= 2).length)

const visibleRows = computed(() => filteredRows.value.slice(0, visibleCount.value))

const allVisibleSelected = computed(
  () => visibleRows.value.length > 0 && visibleRows.value.every((r) => selected.value.has(r.id))
)

onMounted(loadQueue)

watch([search, typeFilter, areaFilter, budgetFilter, activeTab], () => {
  visibleCount.value = 4
})

function toggleRow(id) {
  const next = new Set(selected.value)
  next.has(id) ? next.delete(id) : next.add(id)
  selected.value = next
}

function toggleAll() {
  const next = new Set(selected.value)
  const selectAll = !allVisibleSelected.value
  visibleRows.value.forEach((r) => (selectAll ? next.add(r.id) : next.delete(r.id)))
  selected.value = next
}

function openDetails(row) {
  detail.value = row
  comment.value = ''
  decisionMessage.value = ''
  budgetChoice.value = row.budgetStatus === 'beyond' ? 'beyond' : 'within'
  parallelComment.value = { elt: '', gscHead: '' }
  view.value = 'details'
}

function openFinalReview(role) {
  const backendRole = role === 'gscHead' ? 'gsc_head' : role
  router.push(`/approval-cycle/review/${detail.value.id}/${backendRole}`)
}

function approveSelected() {
  decisionMessage.value = `${selected.value.size} request(s) approved.`
  selected.value = new Set()
}

function exportRows() {
  const header = ['Request ID', 'Opportunity', 'Type', 'Requester', 'Area', 'FTE', 'Budget', 'Stage', 'Waiting']
  const lines = filteredRows.value.map((r) =>
    [r.id, r.title, r.type, r.requester, r.area, r.fte, budgetLabel(r), stageNameFor(r), r.waiting]
      .map((v) => `"${String(v).replace(/"/g, '""')}"`)
      .join(',')
  )
  const blob = new Blob([[header.join(','), ...lines].join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'gsc-approvals.csv'
  a.click()
  URL.revokeObjectURL(url)
}

// Posts a decision to the backend, which re-checks approval_input access server-side,
// then swaps in the fresh row it returns so step/parallel/actionable stay in sync.
async function postDecision(role, action, commentText, extra = {}) {
  try {
    const { data } = await axios.post('/api/approval-cycle/decision/', {
      migration_request_id: detail.value.id,
      role,
      action,
      comment: commentText,
      ...extra
    })
    const updated = toRow(data.row)
    const idx = rows.value.findIndex((r) => r.id === updated.id)
    if (idx !== -1) rows.value[idx] = updated
    detail.value = updated
    return { ok: true }
  } catch (e) {
    decisionMessage.value = e?.response?.data?.error || 'Unable to record decision.'
    return { ok: false }
  }
}

const STAGE_ROLE_KEY = {
  'Area Head': 'area_head',
  'PMO Review': 'pmo',
  'BPM Review': 'bpm',
  'FBP Approve': 'fbp',
  'WPM Review': 'wpm'
}

async function decide(action) {
  if (action !== 'approved' && !comment.value.trim()) {
    decisionMessage.value = 'A comment is required for this action.'
    return
  }
  const role = STAGE_ROLE_KEY[stageNameFor(detail.value)]
  const id = detail.value.id
  const { ok } = await postDecision(role, action, comment.value)
  if (ok) {
    decisionMessage.value = `${id} ${action}.`
    comment.value = ''
  }
}

async function decideBpm() {
  const id = detail.value.id
  const { ok } = await postDecision('bpm', 'approved', comment.value, { budget_status: budgetChoice.value })
  if (ok) {
    decisionMessage.value = `${id} approved — ${
      budgetChoice.value === 'beyond' ? 'beyond budget, routed to FBP Approve.' : 'within budget, routed to ELT & GSC Head.'
    }`
    comment.value = ''
  }
}

async function decideParallel(role, action) {
  if (action !== 'approved' && !parallelComment.value[role].trim()) {
    decisionMessage.value = 'A comment is required for this action.'
    return
  }
  const backendRole = role === 'gscHead' ? 'gsc_head' : 'elt'
  const roleLabel = role === 'elt' ? 'ELT' : 'GSC Head'
  const id = detail.value.id
  const { ok } = await postDecision(backendRole, action, parallelComment.value[role])
  if (ok) {
    const other = role === 'elt' ? detail.value.parallel.gscHead : detail.value.parallel.elt
    decisionMessage.value =
      action === 'approved' && other === 'approved'
        ? `${id} fully approved — ELT and GSC Head have both signed off.`
        : `${id}: ${roleLabel} ${action}.`
    parallelComment.value[role] = ''
  }
}
</script>

<style scoped>
.ac-page {
  --ac-blue: #42b0d5;
  --ac-blue-dark: #0073ab;
  --ac-ink: #141414;
  --ac-ink-soft: #6d6d6d;
  --ac-line: #e0e0e0;
  --ac-bg: #f7f7f7;
  background: var(--ac-bg);
  color: var(--ac-ink);
  display: flex;
  flex-direction: column;
  font-family: 'Maersk Text', sans-serif;
  min-height: 100%;
  width: 100%;
}

/* ---------- layout ---------- */
.ac-main {
  flex: 1;
  padding: 24px 24px 120px;
  width: 100%;
}

.ac-shell {
  margin: 0 auto;
  max-width: 1400px;
  width: 100%;
}

.ac-crumbs {
  align-items: center;
  color: var(--ac-ink-soft);
  display: flex;
  font-size: 13px;
  gap: 8px;
  margin-bottom: 12px;
}

.ac-crumbs a {
  color: var(--ac-blue-dark);
  text-decoration: none;
}

.ac-crumbs a:hover {
  text-decoration: underline;
}

.ac-title {
  font-size: 30px;
  font-weight: 400;
  line-height: 1.2;
  margin: 0;
}

.ac-subtitle {
  color: var(--ac-ink-soft);
  font-size: 14px;
  margin: 6px 0 0;
}

.ac-state {
  font-style: italic;
}

.ac-state-warn {
  color: #8a5300;
}

/* ---------- tabs ---------- */
.ac-tabs {
  border-bottom: 1px solid var(--ac-line);
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin: 24px 0 16px;
}

.ac-tab {
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--ac-ink-soft);
  cursor: pointer;
  font-family: inherit;
  font-size: 14px;
  padding: 10px 14px;
}

.ac-tab:hover {
  color: var(--ac-ink);
}

.ac-tab.is-active {
  border-bottom-color: var(--ac-blue);
  color: var(--ac-ink);
  font-weight: 600;
}

.ac-tab-count {
  color: var(--ac-ink-soft);
  margin-left: 4px;
}

/* ---------- toolbar ---------- */
.ac-toolbar {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}

.ac-search {
  align-items: center;
  background: #fff;
  border: 1px solid var(--ac-line);
  border-radius: 6px;
  display: flex;
  flex: 1 1 320px;
  gap: 8px;
  min-width: 260px;
  padding: 0 12px;
}

.ac-search:focus-within {
  border-color: var(--ac-blue);
  box-shadow: 0 0 0 2px rgba(66, 176, 213, 0.25);
}

.ac-search-icon {
  color: var(--ac-ink-soft);
  flex: none;
  height: 18px;
  width: 18px;
}

.ac-search input {
  background: none;
  border: none;
  color: inherit;
  font-family: inherit;
  font-size: 14px;
  outline: none;
  padding: 10px 0;
  width: 100%;
}

.ac-select {
  align-items: center;
  background: #fff;
  border: 1px solid var(--ac-line);
  border-radius: 6px;
  display: flex;
  gap: 8px;
  padding: 0 12px;
}

.ac-select-label {
  color: var(--ac-ink-soft);
  font-size: 12px;
  text-transform: uppercase;
}

.ac-decision .ac-budget-select {
  margin: 0 0 6px;
  width: 100%;
}

.ac-decision .ac-budget-select select {
  flex: 1;
}

.ac-select select {
  background: none;
  border: none;
  color: inherit;
  font-family: inherit;
  font-size: 14px;
  outline: none;
  padding: 10px 0;
}

.ac-toolbar-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

/* ---------- buttons ---------- */
.ac-btn {
  background: #fff;
  border: 1px solid var(--ac-line);
  border-radius: 6px;
  color: var(--ac-ink);
  cursor: pointer;
  font-family: inherit;
  font-size: 14px;
  padding: 10px 18px;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.ac-btn-ghost:hover {
  background: #f0f0f0;
}

.ac-btn-primary {
  background: var(--ac-ink);
  border-color: var(--ac-ink);
  color: #fff;
}

.ac-btn-primary:hover {
  background: #000;
}

.ac-btn-danger {
  border-color: #d24242;
  color: #b02525;
}

.ac-btn-danger:hover {
  background: #fdeeee;
}

.ac-btn-sm {
  font-size: 13px;
  padding: 6px 14px;
}

.ac-btn-block {
  display: block;
  width: 100%;
}

.ac-link-btn {
  background: none;
  border: none;
  color: var(--ac-blue-dark);
  cursor: pointer;
  font-family: inherit;
  font-size: 14px;
  padding: 0;
}

.ac-link-btn:hover {
  text-decoration: underline;
}

/* ---------- cards ---------- */
.ac-card {
  background: #fff;
  border: 1px solid var(--ac-line);
  border-radius: 8px;
  margin-bottom: 20px;
  padding: 24px;
}

.ac-card-title {
  font-size: 18px;
  font-weight: 500;
  margin: 0;
}

.ac-card-sub {
  color: var(--ac-ink-soft);
  font-size: 13px;
  margin: 6px 0 0;
}

.ac-met {
  color: #1a7d3c;
}

/* ---------- table ---------- */
.ac-table-card {
  padding: 0;
}

.ac-table-scroll {
  overflow-x: auto;
}

.ac-table {
  border-collapse: collapse;
  min-width: 1080px;
  width: 100%;
}

.ac-table th {
  border-bottom: 1px solid var(--ac-line);
  color: var(--ac-ink-soft);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  padding: 14px 16px;
  text-align: left;
  text-transform: uppercase;
  white-space: nowrap;
}

.ac-table td {
  border-bottom: 1px solid #efefef;
  font-size: 14px;
  padding: 14px 16px;
  vertical-align: top;
}

.ac-row {
  cursor: pointer;
  transition: background 0.12s ease;
}

.ac-row:hover,
.ac-row:focus-visible {
  background: #f2fafd;
  outline: none;
}

.ac-row.is-selected {
  background: #eaf6fb;
}

.ac-col-check {
  width: 44px;
}

.ac-col-action {
  text-align: right;
  white-space: nowrap;
}

.ac-row-title {
  display: block;
  font-weight: 600;
}

.ac-row-sub {
  color: var(--ac-ink-soft);
  display: block;
  font-size: 12px;
  margin-top: 2px;
}

.ac-empty {
  color: var(--ac-ink-soft);
  padding: 32px 16px;
  text-align: center;
}

.ac-table-foot {
  align-items: center;
  color: var(--ac-ink-soft);
  display: flex;
  font-size: 13px;
  gap: 10px;
  padding: 14px 16px;
}

/* ---------- status tags ---------- */
.ac-tag {
  border-radius: 999px;
  display: inline-block;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.4;
  padding: 3px 10px;
  white-space: nowrap;
}

.ac-tag-info {
  background: #e5f4fa;
  color: #0d6f96;
}

.ac-tag-success {
  background: #e5f5ea;
  color: #1a7d3c;
}

.ac-tag-warning {
  background: #fdf1dd;
  color: #8a5300;
}

.ac-tag-error {
  background: #fdecec;
  color: #b02525;
}

.ac-tag-neutral {
  background: #f0f0f0;
  color: #4a4a4a;
}

/* ---------- details ---------- */
.ac-detail-head {
  align-items: flex-start;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  justify-content: space-between;
}

.ac-detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding-top: 6px;
}

.ac-banner {
  background: #fdf6e8;
  border: 1px solid #f0d9a8;
  border-radius: 8px;
  display: flex;
  gap: 12px;
  margin: 20px 0;
  padding: 16px 20px;
}

.ac-banner p {
  color: #5c4a20;
  font-size: 14px;
  margin: 4px 0 0;
}

.ac-banner-mark {
  color: #8a5300;
  font-weight: 700;
}

.ac-detail-grid {
  align-items: start;
  display: grid;
  gap: 20px;
  grid-template-columns: minmax(0, 1fr) 360px;
}

.ac-decision-col {
  position: sticky;
  top: 96px;
}

.ac-decision {
  border-color: var(--ac-blue);
}

.ac-decision .ac-btn-block {
  margin-top: 10px;
}

.ac-decision-split {
  display: grid;
  gap: 10px;
  grid-template-columns: 1fr 1fr;
  margin: 16px 0 4px;
  padding-top: 16px;
  border-top: 1px solid var(--ac-line);
}

.ac-decision-msg {
  background: #f2fafd;
  border-radius: 6px;
  font-size: 13px;
  margin: 12px 0 0;
  padding: 10px 12px;
}

.ac-textarea {
  border: 1px solid var(--ac-line);
  border-radius: 6px;
  font-family: inherit;
  font-size: 14px;
  margin: 16px 0 6px;
  padding: 12px;
  resize: vertical;
  width: 100%;
}

.ac-textarea:focus {
  border-color: var(--ac-blue);
  outline: none;
}

/* ---------- definition list ---------- */
.ac-defs {
  display: grid;
  gap: 2px;
  margin: 16px 0 0;
}

.ac-defs > div {
  border-top: 1px solid #f0f0f0;
  display: grid;
  gap: 12px;
  grid-template-columns: 200px minmax(0, 1fr);
  padding: 10px 0;
}

.ac-defs dt {
  color: var(--ac-ink-soft);
  font-size: 14px;
}

.ac-defs dd {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  font-size: 14px;
  gap: 8px;
  margin: 0;
}

.ac-jl {
  background: #eef7fb;
  border-radius: 4px;
  color: var(--ac-blue-dark);
  font-size: 13px;
  padding: 2px 8px;
}

/* ---------- business case ---------- */
.ac-metrics {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  margin-top: 16px;
}

.ac-metric {
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 14px 16px;
}

.ac-metric-label {
  color: var(--ac-ink-soft);
  font-size: 12px;
  text-transform: uppercase;
}

.ac-metric-value {
  font-size: 20px;
}

.ac-metric-note {
  color: var(--ac-ink-soft);
  font-size: 12px;
}

.ac-case-text {
  color: #3d3d3d;
  font-size: 14px;
  line-height: 1.6;
  margin: 16px 0 0;
}

.ac-doc {
  border-top: 1px solid #f0f0f0;
  margin: 16px 0 0;
  padding-top: 12px;
}

.ac-doc-link {
  align-items: center;
  color: var(--ac-blue-dark);
  display: inline-flex;
  font-size: 14px;
  gap: 8px;
  text-decoration: none;
}

.ac-doc-link:hover {
  text-decoration: underline;
}

.ac-doc-link svg {
  height: 18px;
  width: 18px;
}

.ac-doc-empty {
  color: var(--ac-ink-soft);
  font-size: 13px;
}

/* ---------- approval chain ---------- */
.ac-chain {
  display: grid;
  gap: 0;
  grid-auto-flow: column;
  grid-auto-columns: 1fr;
  list-style: none;
  margin: 28px 0 0;
  overflow-x: auto;
  padding: 0;
}

.ac-chain-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 120px;
  position: relative;
  text-align: center;
}

.ac-chain-line {
  background: var(--ac-line);
  height: 2px;
  left: -50%;
  position: absolute;
  top: 15px;
  width: 100%;
}

.ac-chain-step:first-child .ac-chain-line {
  display: none;
}

.ac-chain-line.is-done {
  background: var(--ac-ink);
}

.ac-chain-dot {
  align-items: center;
  background: #fff;
  border: 2px solid var(--ac-line);
  border-radius: 50%;
  color: var(--ac-ink-soft);
  display: flex;
  font-size: 13px;
  height: 32px;
  justify-content: center;
  position: relative;
  width: 32px;
  z-index: 1;
}

.ac-chain-step.is-done .ac-chain-dot {
  background: var(--ac-ink);
  border-color: var(--ac-ink);
  color: #fff;
}

.ac-chain-step.is-current .ac-chain-dot {
  border-color: var(--ac-blue);
  color: var(--ac-blue-dark);
  box-shadow: 0 0 0 4px rgba(66, 176, 213, 0.18);
}

.ac-chain-step.is-conditional .ac-chain-dot {
  border-style: dashed;
}

.ac-chain-name {
  font-size: 13px;
  font-weight: 600;
  margin-top: 10px;
}

.ac-chain-step.is-todo .ac-chain-name,
.ac-chain-step.is-conditional .ac-chain-name {
  color: var(--ac-ink-soft);
  font-weight: 500;
}

.ac-chain-meta {
  color: var(--ac-ink-soft);
  font-size: 12px;
  margin-top: 2px;
}

/* ---------- activity ---------- */
.ac-activity {
  list-style: none;
  margin: 16px 0 0;
  padding: 0;
}

.ac-activity li {
  border-left: 1px solid var(--ac-line);
  margin-left: 6px;
  padding: 0 0 20px 22px;
  position: relative;
}

.ac-activity li:last-child {
  border-left-color: transparent;
  padding-bottom: 0;
}

.ac-activity-dot {
  background: #d6d6d6;
  border-radius: 50%;
  height: 11px;
  left: -6px;
  position: absolute;
  top: 4px;
  width: 11px;
}

.ac-activity li.is-done .ac-activity-dot {
  background: #1a7d3c;
}

.ac-activity li.is-current .ac-activity-dot {
  background: var(--ac-blue);
}

.ac-activity-head {
  font-size: 14px;
  margin: 0;
}

.ac-activity-at {
  color: var(--ac-ink-soft);
}

.ac-activity-note {
  color: var(--ac-ink-soft);
  font-size: 13px;
  margin: 4px 0 0;
}

/* ---------- bottom toggle ---------- */
.ac-switch {
  background: #fff;
  border: 1px solid var(--ac-line);
  border-radius: 999px;
  bottom: 24px;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.14);
  display: flex;
  gap: 4px;
  left: 50%;
  padding: 5px;
  position: fixed;
  transform: translateX(-50%);
  z-index: 30;
}

.ac-switch-btn {
  background: none;
  border: none;
  border-radius: 999px;
  color: var(--ac-ink-soft);
  cursor: pointer;
  font-family: inherit;
  font-size: 14px;
  padding: 10px 26px;
  transition: background 0.15s ease, color 0.15s ease;
}

.ac-switch-btn:hover {
  color: var(--ac-ink);
}

.ac-switch-btn.is-active {
  background: var(--ac-ink);
  color: #fff;
}

@media (max-width: 1000px) {
  .ac-detail-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .ac-decision-col {
    position: static;
  }

  .ac-defs > div {
    grid-template-columns: minmax(0, 1fr);
    gap: 2px;
  }

  .ac-toolbar-actions {
    margin-left: 0;
  }
}
</style>
