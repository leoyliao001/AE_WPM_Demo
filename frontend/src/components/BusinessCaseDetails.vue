<template>
  <div class="bc-fields">
    <label v-for="field in fields" :key="field.key">{{ field.label }}{{ field.required ? ' · Required to submit' : '' }}
      <textarea v-model="details[field.key]" :disabled="disabled" rows="3" />
    </label>
  </div>
</template>

<script setup>
import { businessCaseDetailFields as fields } from '../composables/useBusinessCase.js'
defineProps({ details: { type: Object, required: true }, disabled: Boolean })
</script>
