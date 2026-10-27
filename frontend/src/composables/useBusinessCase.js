import { computed, ref } from 'vue'
import axios from 'axios'

export const businessCaseDetailFields = [
  { key: 'rationale', label: 'Business rationale', required: true },
  { key: 'expectedBenefits', label: 'Expected benefits', required: true },
  { key: 'risks', label: 'Risks' },
  { key: 'dependencies', label: 'Dependencies' },
  { key: 'recommendation', label: 'Recommendation', required: true }
]

export function useBusinessCase() {
  const record = ref(null)
  const details = ref({})
  const financialInputs = ref({})
  const loading = ref(false)
  const pending = ref(false)
  const error = ref('')
  const success = ref('')
  const baseline = ref('')
  const snapshot = () => JSON.stringify([details.value, financialInputs.value])
  const dirty = computed(() => !!record.value && snapshot() !== baseline.value)
  const apply = (data) => {
    record.value = data
    details.value = Object.fromEntries(businessCaseDetailFields.map(({ key }) => [key, data.details?.[key] ?? '']))
    financialInputs.value = {
      oneTimeCost: data.financialInputs?.oneTimeCost ?? '',
      adjustment: data.financialInputs?.adjustment ?? '0',
      adjustmentReason: data.financialInputs?.adjustmentReason ?? ''
    }
    baseline.value = snapshot()
  }
  function showError(failure) {
    const message = failure.response?.data?.error || failure.message || 'The request could not be completed.'
    error.value = failure.response?.status === 409
      ? `${message} Your changes are retained. Copy them before reloading the latest record and reviewing the conflict.`
      : message
  }
  async function load(projectId) {
    if (pending.value || loading.value) return false
    loading.value = true
    error.value = ''
    success.value = ''
    record.value = null
    try {
      const { data } = await axios.get(`/api/migration-dashboard/projects/${projectId}/business-case/`)
      apply(data)
      return true
    } catch (failure) {
      showError(failure)
      return false
    } finally {
      loading.value = false
    }
  }
  async function save(action = 'save', extra = {}) {
    if (pending.value || loading.value || !record.value) return false
    const inputs = financialInputs.value
    if ((inputs.oneTimeCost !== '' && !/^\d+(?:\.\d+)?$/.test(String(inputs.oneTimeCost))) ||
        (inputs.adjustment !== '' && !/^-?\d+(?:\.\d+)?$/.test(String(inputs.adjustment)))) {
      error.value = 'Use plain decimal USD amounts: non-negative one-time cost (or leave empty), and a signed adjustment. Do not include currency symbols, commas or exponents.'
      return false
    }
    pending.value = true
    error.value = ''
    success.value = ''
    try {
      const { data } = await axios.post(`/api/migration-dashboard/projects/${record.value.projectId}/business-case/save/`, {
        revision: record.value.revision,
        intakeVersion: record.value.intakeVersion,
        sourceVersion: record.value.sourceVersion,
        details: details.value,
        financialInputs: { ...inputs, adjustment: inputs.adjustment === '' ? '0' : inputs.adjustment },
        action,
        ...extra
      })
      apply(data)
      success.value = action === 'submit' ? 'Business Case submitted to the existing approval chain.' :
        action === 'revise' ? 'Revision opened. Review the sources and save before resubmitting.' :
          action === 'refresh' ? 'Source data and financial calculation refreshed.' : 'Business Case saved.'
      return true
    } catch (failure) {
      showError(failure)
      return false
    } finally {
      pending.value = false
    }
  }
  return { record, details, financialInputs, loading, pending, error, success, dirty, load, save }
}
