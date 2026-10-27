<template>
  <div>
    <p class="bc-note">Calculated by the server from locked Scope FTE and Cost Rates. All results are in {{ financials?.currency || 'USD' }}. No estimate is substituted for missing data.</p>
    <p v-if="stale" class="bc-warning" role="status">Unsaved inputs are not reflected below. Save / refresh to recalculate before submitting.</p>
    <p v-if="!financials?.ready" class="bc-warning">Financial calculation is not ready.</p>
    <ul v-if="financials?.errors?.length" class="bc-error" aria-label="Financial calculation errors"><li v-for="(message, index) in financials.errors" :key="index">{{ message }}</li></ul>
    <ul v-if="financials?.warnings?.length" class="bc-warning" aria-label="Financial calculation warnings"><li v-for="(message, index) in financials.warnings" :key="index">{{ message }}</li></ul>
    <div class="bc-metrics">
      <article v-for="metric in metrics" :key="metric.key">
        <span>{{ metric.label }}</span><strong>{{ display(financials?.metrics?.[metric.key], metric.unit) }}</strong>
      </article>
    </div>
    <div class="bc-scroll">
      <table>
        <caption>Annual cost comparison · {{ financials?.currency || 'USD' }}</caption>
        <thead><tr><th>Job level</th><th>Locked FTE</th><th>Source rate / FTE</th><th>Destination rate / FTE</th><th>Current annual cost</th><th>Future annual cost</th></tr></thead>
        <tbody><tr v-for="(row, index) in financials?.rows || []" :key="index">
          <th>{{ row.jobLevel }}</th><td>{{ display(row.fte) }}</td><td>{{ display(row.sourceRate) }}</td><td>{{ display(row.destinationRate) }}</td><td>{{ display(row.currentCost) }}</td><td>{{ display(row.futureCost) }}</td>
        </tr><tr v-if="!financials?.rows?.length"><td colspan="6">No calculated cost rows available.</td></tr></tbody>
      </table>
    </div>
    <details class="bc-rate-basis">
      <summary>Cost rate basis · year and version</summary>
      <p>Cost year is determined by the Intake target start date. Exactly one source country and one destination site are supported; missing allocations must be resolved at source.</p>
      <div class="bc-scroll"><table>
        <thead><tr><th>Rate ID</th><th>Exact location</th><th>Job level</th><th>Annual cost</th><th>Currency</th><th>USD rate</th><th>Cost year</th><th>Version</th></tr></thead>
        <tbody><tr v-for="rate in financials?.rateBasis || []" :key="rate.id"><td>{{ rate.id }}</td><td>{{ rate.location }}</td><td>{{ rate.jobLevel }}</td><td>{{ display(rate.annualCost) }}</td><td>{{ rate.currency }}</td><td>{{ display(rate.usdRate) }}</td><td>{{ rate.year }}</td><td>{{ rate.version }}</td></tr>
          <tr v-if="!financials?.rateBasis?.length"><td colspan="8">No rate basis available.</td></tr>
        </tbody>
      </table></div>
    </details>
  </div>
</template>

<script setup>
defineProps({ financials: Object, stale: Boolean })
const metrics = [
  { key: 'currentAnnualCost', label: 'Current annual cost', unit: 'USD' },
  { key: 'futureAnnualCost', label: 'Future annual cost', unit: 'USD' },
  { key: 'annualGrossBenefit', label: 'Annual gross benefit', unit: 'USD' },
  { key: 'benefitPercent', label: 'Benefit', unit: '%' },
  { key: 'netFirstYearBenefit', label: 'Net first-year benefit', unit: 'USD' },
  { key: 'recurringAnnualBenefit', label: 'Recurring annual benefit', unit: 'USD' },
  { key: 'paybackMonths', label: 'Payback', unit: 'months' },
  { key: 'adjustedOneTimeCost', label: 'Adjusted one-time cost', unit: 'USD' }
]
function display(value, unit = '') {
  if (value === null || value === undefined || value === '') return '—'
  return `${value}${unit ? ` ${unit}` : ''}`
}
</script>
