<template>
  <div class="bc-fields bc-fields--columns">
    <label>One-time cost (USD)<input v-model="inputs.oneTimeCost" :disabled="disabled" type="text" inputmode="decimal" placeholder="Not provided" /></label>
    <label>Adjustment (USD)<input v-model="inputs.adjustment" :disabled="disabled" type="text" inputmode="decimal" /></label>
    <label>Adjustment reason<textarea v-model="inputs.adjustmentReason" :disabled="disabled" rows="2" /></label>
  </div>
</template>
<script setup>
defineProps({ inputs: { type: Object, required: true }, disabled: Boolean })
</script>
