<template>
  <PageShell
    title="Lessons Learnt"
    :show-heading="false"
    :back-to="backTo"
    back-label="Back to Project Phases"
    back-link-to-topbar
    full-width
    class="lessons-shell"
  >
    <div class="lessons-page">
      <header class="lessons-heading">
        <mc-tag appearance="info" fit="small" label="Lessons &amp; Reuse" />
        <h1>Make the next migration smarter.</h1>
        <p>A lightweight record of what worked, what did not, and what future migrations should know.</p>
      </header>

      <div v-if="loading" class="page-state" role="status">
        <mc-loading-indicator size="medium" />
        <span>Loading Lessons Learnt…</span>
      </div>
      <div v-else-if="loadError" class="load-error-state">
        <mc-notification
          appearance="error"
          fit="medium"
          heading="Unable to load Lessons Learnt"
          :body="loadError"
          role="alert"
        />
        <mc-button appearance="neutral" variant="outlined" label="Retry" @click="loadLessons" />
      </div>

      <section v-else-if="savedLesson" class="lesson-card saved-lesson" aria-labelledby="saved-heading">
        <div class="saved-lesson__heading">
          <div>
            <h2 id="saved-heading">Lesson already submitted</h2>
            <p>This project has a saved lesson. It is shown here and cannot be submitted again.</p>
          </div>
          <mc-tag appearance="success" fit="small" label="Saved" />
        </div>
        <div class="saved-lesson__tags">
          <mc-tag appearance="info" fit="small" :label="`Type · ${savedLesson.type}`" />
          <mc-tag appearance="info" fit="small" :label="`Phase · ${savedLesson.phase}`" />
          <mc-tag appearance="info" fit="small" :label="`Related artefact · ${savedLesson.relatedArtefact}`" />
          <mc-tag appearance="info" fit="small" :label="`Relevant for · ${savedLesson.relevantFor}`" />
        </div>
        <div class="saved-lesson__details">
          <section>
            <h3>What happened?</h3>
            <p>{{ savedLesson.happened }}</p>
          </section>
          <section>
            <h3>What did we learn?</h3>
            <p>{{ savedLesson.learned }}</p>
          </section>
          <section>
            <h3>What should we do differently next time?</h3>
            <p>{{ savedLesson.nextTime }}</p>
          </section>
        </div>
        <p v-if="savedLesson.createdAt" class="saved-lesson__meta">
          Submitted {{ formatSavedAt(savedLesson.createdAt) }}<span v-if="savedLesson.createdBy"> by {{ savedLesson.createdBy }}</span>
        </p>
      </section>

      <section v-else class="lesson-card" aria-labelledby="capture-heading">
        <h2 id="capture-heading">Capture a lesson</h2>
        <form @submit.prevent="saveLesson">
          <mc-textarea
            id="lesson-happened"
            label="What happened?"
            :value.prop="form.happened"
            maxlength="5000"
            placeholder="Brief factual context"
            fit="medium"
            width="full-width"
            :rows="3"
            required
            @input="form.happened = $event.target.value"
          />

          <mc-textarea
            id="lesson-learned"
            label="What did we learn?"
            :value.prop="form.learned"
            maxlength="5000"
            placeholder="The insight we should retain"
            fit="medium"
            width="full-width"
            :rows="3"
            required
            @input="form.learned = $event.target.value"
          />

          <mc-textarea
            id="lesson-next-time"
            label="What should we do differently next time?"
            :value.prop="form.nextTime"
            maxlength="5000"
            placeholder="A practical recommendation for the next migration"
            fit="medium"
            width="full-width"
            :rows="3"
            required
            @input="form.nextTime = $event.target.value"
          />

          <div class="lesson-fields">
            <mc-select
              id="lesson-type"
              label="Type"
              :value.prop="form.type"
              fit="medium"
              width="full-width"
              required
              @optionselected="setSelectValue('type', $event)"
            >
              <mc-option v-for="option in typeOptions" :key="option" :value="option">{{ option }}</mc-option>
            </mc-select>
            <mc-select
              id="lesson-phase"
              label="Phase"
              :value.prop="form.phase"
              fit="medium"
              width="full-width"
              required
              @optionselected="setSelectValue('phase', $event)"
            >
              <mc-option v-for="option in phaseOptions" :key="option" :value="option">{{ option }}</mc-option>
            </mc-select>
            <mc-select
              id="lesson-artefact"
              label="Related artefact"
              :value.prop="form.relatedArtefact"
              fit="medium"
              width="full-width"
              required
              @optionselected="setSelectValue('relatedArtefact', $event)"
            >
              <mc-option v-for="option in artefactOptions" :key="option" :value="option">{{ option }}</mc-option>
            </mc-select>
            <mc-select
              id="lesson-relevance"
              label="Relevant for"
              :value.prop="form.relevantFor"
              fit="medium"
              width="full-width"
              required
              @optionselected="setSelectValue('relevantFor', $event)"
            >
              <mc-option v-for="option in relevanceOptions" :key="option" :value="option">{{ option }}</mc-option>
            </mc-select>
          </div>

          <mc-button
            type="submit"
            appearance="primary"
            fit="medium"
            :label="saving ? 'Saving…' : 'Save lesson'"
            :loading="saving"
            :disabled="saving || !hasRequiredDetails"
          />
          <mc-notification
            v-if="saveError"
            class="form-message"
            appearance="error"
            fit="medium"
            heading="Unable to save lesson"
            :body="saveError"
            role="alert"
          />
        </form>
      </section>
    </div>
  </PageShell>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'
import {
  LESSON_ARTEFACT_OPTIONS,
  LESSON_PHASE_OPTIONS,
  LESSON_RELEVANCE_OPTIONS,
  LESSON_TYPE_OPTIONS
} from '../utils/lessonsLearntOptions.js'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-loading-indicator'
import '@maersk-global/mds-components-core/mc-notification'
import '@maersk-global/mds-components-core/mc-option'
import '@maersk-global/mds-components-core/mc-select'
import '@maersk-global/mds-components-core/mc-tag'
import '@maersk-global/mds-components-core/mc-textarea'

const route = useRoute()
const projectId = computed(() => String(route.params.id || ''))
const endpoint = computed(() => `/api/migration-dashboard/projects/${projectId.value}/lessons-learnt/`)
const backTo = computed(() => {
  const returnTo = typeof route.query.returnTo === 'string' ? route.query.returnTo : ''
  if (returnTo.startsWith('/') && !returnTo.startsWith('//')) return returnTo
  const project = route.query.project || projectId.value
  return `/toll-gates?project=${encodeURIComponent(project)}`
})

const typeOptions = LESSON_TYPE_OPTIONS
const phaseOptions = LESSON_PHASE_OPTIONS
const artefactOptions = LESSON_ARTEFACT_OPTIONS
const relevanceOptions = LESSON_RELEVANCE_OPTIONS

const form = reactive({
  happened: '',
  learned: '',
  nextTime: '',
  type: typeOptions[0],
  phase: phaseOptions[0],
  relatedArtefact: artefactOptions[0],
  relevantFor: relevanceOptions[0]
})
const loading = ref(true)
const saving = ref(false)
const loadError = ref('')
const saveError = ref('')
const savedLesson = ref(null)
const hasRequiredDetails = computed(() =>
  Boolean(form.happened.trim() && form.learned.trim() && form.nextTime.trim())
)

async function loadLessons() {
  loading.value = true
  loadError.value = ''
  try {
    const { data } = await axios.get(endpoint.value)
    const lessons = Array.isArray(data.lessons) ? data.lessons : []
    savedLesson.value = data.lesson || lessons[0] || null
  } catch (error) {
    loadError.value = error.response?.data?.error || 'Unable to load Lessons Learnt.'
  } finally {
    loading.value = false
  }
}

async function saveLesson() {
  if (saving.value || !hasRequiredDetails.value) return
  saving.value = true
  saveError.value = ''
  try {
    const { data } = await axios.post(endpoint.value, { ...form })
    savedLesson.value = data.lesson
  } catch (error) {
    if (error.response?.status === 409 && error.response.data?.lesson) {
      savedLesson.value = error.response.data.lesson
    } else {
      saveError.value = error.response?.data?.error || 'Unable to save this lesson.'
    }
  } finally {
    saving.value = false
  }
}

function formatSavedAt(value) {
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

function setSelectValue(field, event) {
  form[field] = event?.detail?.value ?? event?.target?.value ?? ''
}

watch(projectId, loadLessons, { immediate: true })
</script>

<style scoped>
.lessons-shell :deep(.page-content) {
  padding: 20px 10px 32px;
}

.lessons-shell :deep(.page-main) {
  gap: 0;
}

.lessons-page {
  background: #f4f7f8;
  color: #172f3d;
  min-height: calc(100vh - 120px);
}

.lessons-heading {
  margin: 0 0 2px;
}

.lessons-heading h1 {
  color: #00243d;
  font-size: clamp(26px, 3vw, 36px);
  margin: 8px 0 6px;
}

.lessons-heading > p:last-child {
  color: #647985;
  margin: 0;
}

.lesson-card {
  background: #fff;
  border: 1px solid #d9e4e8;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 36, 61, .06);
  padding: 20px;
}

.lesson-card h2 {
  color: #00243d;
  font-size: 18px;
  margin: 0 0 14px;
}

.saved-lesson__heading {
  align-items: flex-start;
  display: flex;
  gap: 16px;
  justify-content: space-between;
}

.saved-lesson__heading p {
  color: #647985;
  margin: 0;
}

.saved-lesson__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 18px 0;
}

.saved-lesson__details {
  display: grid;
  gap: 18px;
}

.saved-lesson__details section {
  border-top: 1px solid #e6edf1;
  padding-top: 14px;
}

.saved-lesson__details h3 {
  color: #00243d;
  font-size: 14px;
  margin: 0 0 7px;
}

.saved-lesson__details p {
  color: #425466;
  line-height: 1.55;
  margin: 0;
  white-space: pre-wrap;
}

.saved-lesson__meta {
  border-top: 1px solid #e6edf1;
  color: #647985;
  font-size: 12px;
  margin: 18px 0 0;
  padding-top: 12px;
}

.lesson-card mc-textarea {
  display: block;
  margin-bottom: 14px;
}

.lesson-fields {
  display: grid;
  column-gap: 16px;
  row-gap: 4px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.form-message {
  margin-top: 14px;
}

.page-state {
  align-items: center;
  background: #fff;
  border: 1px solid #d9e4e8;
  border-radius: 9px;
  display: flex;
  gap: 12px;
  padding: 18px;
}

.load-error-state {
  display: grid;
  gap: 12px;
  justify-items: start;
}

@media (max-width: 700px) {
  .lessons-heading h1 {
    font-size: 26px;
  }

  .lesson-fields {
    grid-template-columns: 1fr;
  }

  .lesson-card {
    padding: 16px;
  }
}
</style>
