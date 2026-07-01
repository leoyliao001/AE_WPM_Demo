<template>
  <PageShell
    title="Migration Dashboard"
    subtitle="1st overview — product-level summary and detailed migration tracking across sites."
    tag="Migration Dashboard"
    back-label="Back to Welcome"
  >
    <div class="dashboard-layout">
      <aside class="summary-panel">
        <div class="panel-head">
          <h2>Product Summary</h2>
          <p>Compact view of FTE and net estimated cost benefit per product.</p>
        </div>

        <div class="summary-cards">
          <mc-card
            v-for="item in summaries"
            :key="item.id"
            class="summary-card"
            variant="bordered"
            fit="medium"
            :heading="item.product"
            contentalignment="middle"
          >
            <div class="summary-metrics">
              <div class="metric">
                <span class="metric-label">FTE in migration</span>
                <strong class="metric-value">{{ item.fte }}</strong>
              </div>
              <div class="metric">
                <span class="metric-label">Net est. benefit (USD)</span>
                <strong class="metric-value metric-value--benefit">
                  {{ formatUsd(item.netBenefitUsd) }}
                </strong>
              </div>
            </div>
          </mc-card>
        </div>
      </aside>

      <section class="table-panel">
        <div class="panel-head">
          <h2>Migration Overview</h2>
          <p>Detailed migration table across sites, status, completion, and FTE allocation.</p>
        </div>

        <div class="table-wrap">
          <mc-table
            :data.prop="tableRows"
            :columns.prop="tableColumns"
            datakey="id"
            caption="Migration dashboard detail table"
            fit="medium"
            height="auto"
            outerborderstyle="solid"
            horizontallinestyle="solid"
          />
        </div>
      </section>
    </div>
  </PageShell>
</template>

<script setup>
import PageShell from '../components/PageShell.vue'
import {
  migrationProductSummaries,
  migrationTableRows,
  migrationTableColumns
} from '../data/mockData'
import '@maersk-global/mds-components-core/mc-card'
import '@maersk-global/mds-components-core/mc-table'

const summaries = migrationProductSummaries
const tableRows = migrationTableRows.map((row) => ({
  ...row,
  artifactsPct: `${row.artifactsPct}%`,
  timelinePct: `${row.timelinePct}%`
}))
const tableColumns = migrationTableColumns

const formatUsd = (value) =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0
  }).format(value)
</script>

<style scoped>
.dashboard-layout {
  display: grid;
  gap: 24px;
  grid-template-columns: 320px minmax(0, 1fr);
}

.panel-head h2 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 6px;
}

.panel-head p {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 13px;
  line-height: 1.5;
  margin: 0 0 16px;
}

.summary-panel,
.table-panel {
  background: #fff;
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(22, 22, 22, 0.04);
  padding: 22px 20px;
}

.summary-cards {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.summary-card::part(container) {
  border-radius: 12px;
}

.summary-metrics {
  display: grid;
  gap: 12px;
  padding-top: 4px;
}

.metric-label {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  display: block;
  font-size: 12px;
  margin-bottom: 4px;
}

.metric-value {
  color: var(--mds_brand_appearance_neutral_default_text-color, #161616);
  font-size: 20px;
}

.metric-value--benefit {
  color: #0077b8;
}

.table-wrap {
  overflow-x: auto;
}

@media (max-width: 960px) {
  .dashboard-layout {
    grid-template-columns: 1fr;
  }
}
</style>
