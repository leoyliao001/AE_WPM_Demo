<template>
  <PageShell
    title="L&D Dashboard"
    subtitle="Learning and development scoping overview across migration projects."
    tag="L&D Dashboard"
    back-label="Back to Welcome"
  >
    <section class="table-panel">
      <div class="panel-head">
        <h2>Training & Scoping Overview</h2>
        <p>Project-level L&D tasks, timelines, and FTE requirements for migration readiness.</p>
      </div>

      <div class="table-wrap">
        <mc-table
          :data.prop="tableRows"
          :columns.prop="tableColumns"
          datakey="id"
          caption="L&D dashboard table"
          fit="medium"
          height="auto"
          outerborderstyle="solid"
          horizontallinestyle="solid"
        />
      </div>
    </section>
  </PageShell>
</template>

<script setup>
import PageShell from '../components/PageShell.vue'
import { ldDashboardRows, ldDashboardColumns } from '../data/mockData'
import '@maersk-global/mds-components-core/mc-table'

const tableRows = ldDashboardRows
const tableColumns = ldDashboardColumns
</script>

<style scoped>
.table-panel {
  background: #fff;
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(22, 22, 22, 0.04);
  padding: 22px 20px;
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

.table-wrap {
  overflow-x: auto;
}
</style>
