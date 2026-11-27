<template>
  <section v-if="missingRates.length" class="bc-editor bc-missing-rates">
    <h3>Complete missing cost rates</h3>
    <p class="bc-note">These are shared rates used by Business Cases with the same location, job level and year. Saved rates are available to all such cases.</p>
    <p v-if="!accessChecked" role="status">Checking Cost Rates access…</p>
    <p v-else-if="!canManage" class="bc-warning">A Cost Rates administrator must add these shared rates. You do not have Cost Rates maintenance access.</p>
    <p v-else-if="hasUnsavedChanges" class="bc-warning">Save or cancel your unsaved Business Case changes before adding a shared rate. The page must reload to recalculate the financials.</p>
    <template v-else>
      <form v-for="rate in missingRates" :key="rate.key" class="bc-rate-entry" @submit.prevent="saveRate(rate)">
        <h4>{{ rate.location }} · {{ rate.jobLevel }} · {{ rate.year }}</h4>
        <fieldset :disabled="disabled || !!savingKey">
          <div class="bc-fields bc-fields--columns">
            <label>Exact location<input :value="rate.location" disabled /></label>
            <label>Job level<input :value="rate.jobLevel" disabled /></label>
            <label>Cost year<input :value="rate.year" disabled /></label>
            <label>Annual cost per FTE (local currency)
              <input v-model="drafts[rate.key].annualCost" type="text" inputmode="decimal" pattern="[0-9]+([.][0-9]{1,4})?" required />
            </label>
            <label>Currency (3 uppercase letters)
              <input v-model="drafts[rate.key].currency" maxlength="3" pattern="[A-Z]{3}" required placeholder="ISO currency code" />
            </label>
            <label>USD exchange rate (USD per currency unit)
              <input v-model="drafts[rate.key].usdRate" type="text" inputmode="decimal" pattern="[0-9]+([.][0-9]{1,8})?" required />
            </label>
            <label>Version<input v-model="drafts[rate.key].version" type="text" required /></label>
          </div>
          <div class="bc-actions">
            <button type="submit" class="bc-primary" :disabled="disabled || !!savingKey">
              {{ savingKey === rate.key ? 'Saving…' : 'Save shared rate' }}
            </button>
          </div>
        </fieldset>
      </form>
    </template>
    <p v-if="error" class="bc-error" role="alert">{{ error }}</p>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import axios from 'axios'
import { parseMissingCostRates } from '../utils/missingCostRates.js'

const props = defineProps({
  errors: { type: Array, default: () => [] },
  canManage: { type: Boolean, default: false },
  accessChecked: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  hasUnsavedChanges: { type: Boolean, default: false }
})
const emit = defineEmits(['saved'])
const drafts = ref({})
const savingKey = ref('')
const error = ref('')

const missingRates = computed(() => parseMissingCostRates(props.errors))

watch(missingRates, (rates) => {
  const previous = drafts.value
  drafts.value = Object.fromEntries(rates.map(rate => [
    rate.key,
    previous[rate.key] || { annualCost: '', currency: '', usdRate: '', version: '' }
  ]))
}, { immediate: true })

async function saveRate(rate) {
  if (!props.canManage || props.disabled || props.hasUnsavedChanges || savingKey.value) return
  const values = drafts.value[rate.key]
  if (!values) return

  savingKey.value = rate.key
  error.value = ''
  try {
    await axios.post('/api/migration-dashboard/cost-rates/', {
      location: rate.location,
      jobLevel: rate.jobLevel,
      year: rate.year,
      annualCost: values.annualCost,
      currency: values.currency,
      usdRate: values.usdRate,
      version: values.version
    })
    emit('saved')
  } catch (failure) {
    error.value = failure.response?.data?.error || failure.message || 'The cost rate could not be saved.'
  } finally {
    savingKey.value = ''
  }
}
</script>
