<template>
  <PageShell title="Final approval review" :subtitle="`${roleLabel} review for the migration request`" back-to="/approval-cycle" back-label="Back to approvals">
    <mc-notification v-if="error" appearance="error" fit="medium" heading="Unable to open approval review" :body="error" />
    <div v-else-if="loading" class="review-loading">Loading approval inputs...</div>
    <section v-else-if="row" class="review-shell">
      <header class="review-head">
        <div>
          <p class="review-eyebrow">{{ row.id }}</p>
          <h2>{{ row.projectName }}</h2>
          <p>{{ row.functionName }} | {{ row.product }} | {{ row.region }}</p>
        </div>
        <mc-tag appearance="warning" fit="small" :label="`${roleLabel} approval required`" />
      </header>

      <div class="review-grid">
        <section class="review-card">
          <h3>Migration request</h3>
          <dl>
            <div><dt>Requestor</dt><dd>{{ row.requester }}</dd></div>
            <div><dt>Migration type</dt><dd>{{ row.type }}</dd></div>
            <div><dt>FTE in scope</dt><dd>{{ row.fte.toFixed(1) }}</dd></div>
            <div><dt>Budget</dt><dd>{{ row.budgetStatus === 'beyond' ? 'Beyond budget' : 'Within budget' }}</dd></div>
          </dl>
        </section>
        <section class="review-card">
          <h3>Scope and recommendation</h3>
          <p>{{ row.scope }}</p>
          <p class="review-muted">Review the migration request and the prior decisions before recording your final decision.</p>
        </section>
      </div>

      <section class="review-card">
        <h3>Approval history</h3>
        <div v-for="entry in history" :key="entry.label" class="history-row">
          <strong>{{ entry.label }}</strong><span>{{ entry.status }}</span><span>{{ entry.date || 'Pending' }}</span>
        </div>
      </section>

      <section v-if="canDecide" class="review-card review-decision">
        <h3>Your {{ roleLabel }} decision</h3>
        <textarea v-model="comment" rows="5" placeholder="Add a comment (required for return or reject)" aria-label="Approval comment"></textarea>
        <div class="review-actions">
          <mc-button appearance="primary" fit="small" label="Confirm approval" :loading="submitting" @click="submit('approved')" />
          <mc-button appearance="neutral" variant="outlined" fit="small" label="Return" :disabled="submitting" @click="submit('returned')" />
          <mc-button appearance="error" variant="outlined" fit="small" label="Reject" :disabled="submitting" @click="submit('rejected')" />
        </div>
      </section>
      <p v-else class="review-note">This approval is not assigned to your account, or it has already been completed.</p>
    </section>
  </PageShell>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-notification'
import '@maersk-global/mds-components-core/mc-tag'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const error = ref('')
const row = ref(null)
const comment = ref('')
const submitting = ref(false)
const role = computed(() => route.params.role === 'gsc_head' ? 'gsc_head' : 'elt')
const roleLabel = computed(() => role.value === 'gsc_head' ? 'GSC Head' : 'ELT')
const parallelKey = computed(() => role.value === 'gsc_head' ? 'gscHead' : 'elt')
const canDecide = computed(() => row.value?.parallel?.[parallelKey.value] === 'pending' && (row.value?.myRoles || []).includes(role.value))
const history = computed(() => [
  ['Area Head', 'area_head'], ['PMO', 'pmo'], ['BPM', 'bpm'], ['FBP', 'fbp'], ['WPM', 'wpm'], ['ELT', 'elt'], ['GSC Head', 'gsc_head']
].map(([label, key]) => ({ label, status: row.value?.decisions?.[key]?.status || 'Pending', date: row.value?.decisions?.[key]?.date || '' })))

async function submit(action) {
  if (action !== 'approved' && !comment.value.trim()) {
    error.value = 'A comment is required when returning or rejecting a request.'
    return
  }
  submitting.value = true
  error.value = ''
  try {
    await axios.post('/api/approval-cycle/decision/', {
      migration_request_id: row.value.id,
      role: role.value,
      action,
      comment: comment.value
    })
    router.push('/approval-cycle')
  } catch (requestError) {
    error.value = requestError?.response?.data?.error || 'Unable to record the approval decision.'
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    const { data } = await axios.get('/api/approval-cycle/queue/')
    const source = (data.rows || []).find((item) => item.migration_request_id === route.params.migrationRequestId)
    if (!source) throw new Error('Migration request not found.')
    row.value = {
      id: source.migration_request_id,
      projectName: source.project_name,
      type: source.migration_type,
      requester: source.requestor,
      region: source.region,
      functionName: source.function_name,
      product: (source.products || []).join(', ') || '-',
      fte: Number(source.fte_number) || 0,
      scope: source.proposed_scope || '-',
      budgetStatus: source.budgetStatus,
      parallel: source.parallel,
      myRoles: source.myRoles,
      decisions: source.decisions
    }
  } catch (requestError) {
    error.value = requestError?.response?.data?.error || requestError.message || 'Please try again.'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.review-loading { color: #5d5d5d; padding: 28px 0; }
.review-shell { display: flex; flex-direction: column; gap: 16px; max-width: 900px; }
.review-head { align-items: flex-start; border-bottom: 1px solid #d9d9d9; display: flex; justify-content: space-between; padding-bottom: 18px; }
.review-head h2, .review-card h3 { margin: 0; }
.review-head p { color: #5d5d5d; margin: 6px 0 0; }
.review-eyebrow { color: #0073ab !important; font-weight: 700; }
.review-grid { display: grid; gap: 16px; grid-template-columns: repeat(2, minmax(0, 1fr)); }
.review-card { border: 1px solid #d9d9d9; border-radius: 6px; padding: 20px; }
.review-card p { line-height: 1.55; }
.review-card dl { display: grid; gap: 10px; margin: 16px 0 0; }
.review-card dl div { display: flex; gap: 16px; justify-content: space-between; }
.review-card dt, .review-muted, .review-note { color: #5d5d5d; }
.review-card dd { margin: 0; text-align: right; }
.history-row { border-top: 1px solid #e4e4e4; display: grid; gap: 16px; grid-template-columns: 1fr 120px 180px; padding: 10px 0; }
.history-row:first-of-type { margin-top: 14px; }
.review-decision textarea { box-sizing: border-box; font: inherit; margin: 14px 0; min-height: 110px; padding: 10px; resize: vertical; width: 100%; }
.review-actions { display: flex; flex-wrap: wrap; gap: 10px; }
.review-note { padding: 12px 0; }
@media (max-width: 640px) { .review-grid { grid-template-columns: 1fr; }.review-head { flex-direction: column; gap: 12px; }.history-row { gap: 4px; grid-template-columns: 1fr; } }
</style>