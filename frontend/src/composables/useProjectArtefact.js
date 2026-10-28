import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { useUnsavedChanges } from './useUnsavedChanges.js'

export function useProjectArtefact(endpoint) {
  const route = useRoute()
  const projectId = computed(() => String(route.params.id))
  const record = ref(null)
  const loading = ref(false)
  const busy = ref('')
  const error = ref('')
  const success = ref('')
  const baseline = ref('')
  const content = data => JSON.stringify(data && {
    rows: data.rows, systems: data.systems, barriers: data.barriers, itItems: data.itItems,
    questionnaires: data.questionnaires,
  })
  const dirty = computed(() => Boolean(record.value) && content(record.value) !== baseline.value)
  useUnsavedChanges(dirty, computed(() => loading.value || Boolean(busy.value)))
  const backTo = computed(() => `/toll-gates?project=${projectId.value}`)
  const editable = computed(() => record.value && !record.value.frozen && !busy.value)
  async function load() {
    const id = projectId.value
    loading.value = true
    error.value = ''
    success.value = ''
    record.value = null
    try {
      const { data } = await axios.get(`/api/migration-dashboard/projects/${id}/${endpoint}/`)
      if (id === projectId.value) {
        record.value = data
        baseline.value = content(data)
      }
    } catch (caught) {
      if (id === projectId.value) error.value = caught.response?.data?.error || 'Unable to load project data.'
    } finally {
      if (id === projectId.value) loading.value = false
    }
  }
  async function save(action = 'save', extra = {}) {
    if (!record.value || busy.value) return false
    const id = projectId.value
    busy.value = action
    error.value = ''
    success.value = ''
    try {
      const data = record.value
      const response = await axios.post(`/api/migration-dashboard/projects/${id}/${endpoint}/`, {
        revision: data.revision, sourceVersion: data.source.version, action,
        rows: data.rows, systems: data.systems, barriers: data.barriers,
        itItems: data.itItems, ...extra,
      })
      if (id === projectId.value) {
        record.value = response.data
        baseline.value = content(response.data)
        success.value = endpoint === 'business-impact-analysis' ? ({
          save: 'Questionnaire draft saved.', submit: 'Submitted for joint review. Answers are now frozen.',
          review: 'Review recorded with your identity and timestamp.', sign_off: 'Signed off as Toll Gates evidence.',
          reopen: 'Questionnaire reopened. Previous reviews are retained in the audit history.',
        }[action] || 'Changes saved.') : action === 'submit' ? 'Confirmed and frozen as tollgate evidence.' :
          action === 'confirm_it' ? 'IT readiness confirmed and time-stamped.' :
            action === 'reopen' ? 'Reopened as a draft.' : 'Changes saved.'
      }
      return true
    } catch (caught) {
      if (id === projectId.value) error.value = caught.response?.data?.error || 'Unable to save. Your inputs are retained.'
      return false
    } finally {
      busy.value = ''
    }
  }
  watch(projectId, load, { immediate: true })
  return { record, projectId, backTo, loading, busy, error, success, dirty, editable, load, save }
}
