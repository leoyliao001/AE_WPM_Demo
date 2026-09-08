<template>
  <PageShell
    title="Business case"
    subtitle="Generate a draft, review it, then upload the signed-off version."
    :back-to="backTo"
    :back-label="backLabel"
  >
    <mc-notification v-if="loadError" appearance="error" fit="medium" heading="Unable to load project" :body="loadError" />
    <div v-else-if="loading" class="bc-loading">Loading Business Case…</div>

    <section v-else-if="project" class="bc-workflow" aria-label="Business Case workflow">
      <div class="bc-status">
        <mc-tag :appearance="isSubmitted ? 'success' : 'warning'" fit="small" :label="isSubmitted ? 'Submitted' : 'In progress'" />
      </div>

      <article class="bc-step" :class="{ 'bc-step--complete': draftGenerated }">
        <span class="bc-step__icon"><mc-icon :icon="draftGenerated ? 'mi-check' : 'mi-file'" size="20" /></span>
        <div class="bc-step__content">
          <h2>1. Generate business case</h2>
          <p>Auto-drafted from the project intake data for {{ project.projectName }}.</p>
          <mc-button appearance="neutral" variant="outlined" fit="small" :label="draftGenerated ? 'Regenerate' : 'Generate draft'" icon="mi-arrow-clockwise" :loading="generating" @click="generateDraft" />
        </div>
      </article>

      <article class="bc-step" :class="{ 'bc-step--complete': draftGenerated }">
        <span class="bc-step__icon"><mc-icon icon="mi-file" size="20" /></span>
        <div class="bc-step__content">
          <h2>2. Review draft</h2>
          <p v-if="draftGenerated">{{ draftName }} · Generated in this session</p>
          <p v-else>Generate the Business Case draft before review.</p>
          <mc-button appearance="neutral" variant="outlined" fit="small" label="Download draft" icon="mi-arrow-to-bottom" :disabled="!draftGenerated" @click="downloadDraft" />
        </div>
      </article>

      <article class="bc-step" :class="{ 'bc-step--complete': isSubmitted }">
        <span class="bc-step__icon"><mc-icon :icon="isSubmitted ? 'mi-check' : 'mi-upload'" size="20" /></span>
        <div class="bc-step__content">
          <h2>3. Upload final business case</h2>
          <p v-if="isSubmitted">Submitted {{ submittedAt }}. The approval timeline has started.</p>
          <p v-else>Upload the reviewed and signed-off version to start the approval timeline.</p>

          <a
            v-if="isSubmitted && submittedFile"
            class="bc-attachment"
            :href="submittedFile.url"
            :download="submittedFile.name"
          >
            <span class="bc-attachment__icon"><mc-icon icon="mi-file" size="20" /></span>
            <span class="bc-attachment__text">
              <strong>{{ submittedFile.name }}</strong>
              <span>{{ formatFileSize(submittedFile.size) }} · Final attachment</span>
            </span>
            <span class="bc-attachment__action"><mc-icon icon="mi-arrow-to-bottom" size="18" /></span>
          </a>
          <p v-else-if="isSubmitted" class="bc-attachment-missing">
            Submitted before attachments were stored — no file on record.
          </p>
          <div
            v-if="!isSubmitted"
            class="bc-dropzone"
            :class="{ 'bc-dropzone--busy': submitting, 'bc-dropzone--dragging': isDragging }"
            @dragenter.prevent="onDragEnter"
            @dragover.prevent="onDragEnter"
            @dragleave.prevent="onDragLeave"
            @drop.prevent="onDrop"
            @click="openFileDialog"
          >
            <mc-icon icon="mi-upload" size="24" />
            <span>{{ selectedFile ? selectedFile.name : 'Drag file here or choose file' }}</span>
            <input ref="fileInputRef" type="file" accept=".doc,.docx,.pdf" :disabled="submitting" @change="onFileChange" @click.stop />
            <mc-button appearance="neutral" variant="outlined" fit="small" label="Choose file" icon="mi-folder-open" tabindex="-1" />
          </div>
          <p v-if="fileTypeError" class="bc-error">{{ fileTypeError }}</p>
          <mc-button v-if="selectedFile && !isSubmitted" appearance="primary" fit="small" label="Submit final Business Case" :loading="submitting" @click="submitFinal" />
          <p v-if="submitError" class="bc-error">{{ submitError }}</p>
        </div>
      </article>
    </section>
  </PageShell>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'
import { generateBusinessCaseDocx } from '../utils/businessCaseDocx.js'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-icon'
import '@maersk-global/mds-components-core/mc-notification'
import '@maersk-global/mds-components-core/mc-tag'

const route = useRoute()
const project = ref(null)
const loading = ref(true)
const loadError = ref('')
const generating = ref(false)
const draftGenerated = ref(false)
const selectedFile = ref(null)
const submitting = ref(false)
const submitError = ref('')
const submittedAt = ref('')
const submittedFile = ref(null)
const isDragging = ref(false)
const fileTypeError = ref('')
const fileInputRef = ref(null)

const ALLOWED_EXTENSIONS = ['.doc', '.docx', '.pdf']

const cameFromTollGates = computed(() => route.query.from === 'toll-gates')
const backTo = computed(() =>
  cameFromTollGates.value
    ? `/toll-gates?project=${route.query.project || route.params.id}`
    : `/migration-dashboard/${route.params.id}`
)
const backLabel = computed(() => (cameFromTollGates.value ? 'Back to toll gates' : 'Back to project'))

const isSubmitted = computed(() => Boolean(submittedAt.value))
const draftName = computed(() => `Business_Case_${project.value?.migrationRequestId || 'project'}.docx`)

function formatFileSize(bytes) {
  const size = Number(bytes)
  if (!size || Number.isNaN(size)) return 'Unknown size'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

async function generateDraft() {
  generating.value = true
  try {
    await generateBusinessCaseDocx(project.value)
    draftGenerated.value = true
  } finally {
    generating.value = false
  }
}

function downloadDraft() {
  void generateDraft()
}

function acceptFile(file) {
  if (!file) return
  const name = file.name.toLowerCase()
  if (!ALLOWED_EXTENSIONS.some((ext) => name.endsWith(ext))) {
    fileTypeError.value = 'Only .doc, .docx or .pdf files are accepted.'
    return
  }
  fileTypeError.value = ''
  submitError.value = ''
  selectedFile.value = file
}

function onFileChange(event) {
  acceptFile(event.target.files?.[0] || null)
}

function openFileDialog() {
  if (submitting.value) return
  fileInputRef.value?.click()
}

function onDragEnter() {
  if (submitting.value) return
  isDragging.value = true
}

function onDragLeave() {
  isDragging.value = false
}

function onDrop(event) {
  isDragging.value = false
  if (submitting.value) return
  acceptFile(event.dataTransfer?.files?.[0] || null)
}

async function submitFinal() {
  if (!selectedFile.value) return
  submitting.value = true
  submitError.value = ''
  try {
    const form = new FormData()
    form.append('file', selectedFile.value)
    form.append('filename', selectedFile.value.name)
    const { data } = await axios.post(
      `/api/migration-dashboard/projects/${route.params.id}/business-case/submit/`,
      form
    )
    submittedAt.value = new Date(data.submitted_at).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' })
    submittedFile.value = data.file || null
  } catch (error) {
    submitError.value = error?.response?.data?.error || 'Unable to submit the Business Case.'
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    const { data } = await axios.get(`/api/migration-dashboard/projects/${route.params.id}/`)
    project.value = data
    if (data.businessCaseSubmissionDate) {
      submittedAt.value = new Date(data.businessCaseSubmissionDate).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' })
    }
    submittedFile.value = data.businessCaseFile || null
  } catch (error) {
    loadError.value = error?.response?.data?.error || 'Please try again.'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.bc-loading { color: #5d5d5d; padding: 28px 0; }
.bc-attachment {
  align-items: center;
  background: #f4f9fc;
  border: 1px solid #c6dced;
  border-radius: 8px;
  color: #10314f;
  display: flex;
  gap: 12px;
  margin: 12px 0;
  max-width: 460px;
  padding: 12px 14px;
  text-decoration: none;
  transition: background 0.2s ease, border-color 0.2s ease;
}
.bc-attachment:hover { background: #e9f3fa; border-color: #0077b8; }
.bc-attachment__icon {
  align-items: center;
  background: #0077b8;
  border-radius: 8px;
  color: #fff;
  display: inline-flex;
  flex-shrink: 0;
  height: 36px;
  justify-content: center;
  width: 36px;
}
.bc-attachment__text { display: flex; flex: 1 1 auto; flex-direction: column; min-width: 0; }
.bc-attachment__text strong { font-size: 13.5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bc-attachment__text span { color: #6c757d; font-size: 12px; margin-top: 2px; }
.bc-attachment__action { color: #0077b8; flex-shrink: 0; }
.bc-attachment-missing { color: #8a9099; font-size: 12.5px; font-style: italic; }
.bc-workflow { border: 1px solid #d9d9d9; border-radius: 8px; max-width: 820px; padding: 8px 26px; position: relative; }
.bc-status { display: flex; justify-content: flex-end; padding: 8px 0 0; }
.bc-step { display: grid; gap: 18px; grid-template-columns: 36px minmax(0, 1fr); padding: 24px 0; }
.bc-step + .bc-step { border-top: 1px solid #dedede; }
.bc-step__icon { align-items: center; background: #edf4fd; border-radius: 50%; color: #286cb4; display: flex; height: 34px; justify-content: center; width: 34px; }
.bc-step--complete .bc-step__icon { background: #d5f3d7; color: #238132; }
.bc-step__content { display: flex; flex-direction: column; gap: 10px; align-items: flex-start; }
.bc-step h2 { font-family: 'Maersk Text', sans-serif; font-size: 18px; margin: 0; }
.bc-step p { color: #555; margin: 0; }
.bc-dropzone { align-items: center; border: 1px dashed #b7b7b7; display: flex; flex-direction: column; gap: 10px; justify-content: center; min-height: 134px; padding: 12px; text-align: center; width: min(100%, 620px); }
.bc-dropzone--dragging { background: #edf4fd; border-color: #286cb4; }
.bc-dropzone input { height: 1px; opacity: 0; position: absolute; width: 1px; }
.bc-dropzone--busy { opacity: .65; pointer-events: none; }
.bc-error { color: #b00020 !important; }
@media (max-width: 600px) { .bc-workflow { padding: 8px 16px; } }
</style>