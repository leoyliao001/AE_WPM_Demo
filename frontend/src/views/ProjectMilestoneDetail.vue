<template>
  <PageShell
    :title="detail.title"
    :subtitle="detail.summary"
    tag="Project Milestone"
    back-to="/project-dashboard"
    back-label="Back to Project Dashboard"
  >
    <section class="detail-panel">
      <mc-table
        :data.prop="rows"
        :columns.prop="columns"
        datakey="id"
        :caption="`${detail.title} milestone details`"
        fit="medium"
        height="auto"
        outerborderstyle="solid"
        horizontallinestyle="solid"
      />
    </section>
  </PageShell>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import PageShell from '../components/PageShell.vue'
import { projectMilestoneDetails } from '../data/mockData'
import '@maersk-global/mds-components-core/mc-table'

const route = useRoute()

const detail = computed(() => {
  const key = route.params.section
  return projectMilestoneDetails[key] || {
    title: 'Milestone',
    summary: 'Detail view for the selected project milestone.',
    items: []
  }
})

const rows = computed(() =>
  detail.value.items.map((item, index) => ({
    id: index + 1,
    label: item.label,
    value: item.value,
    status: item.status
  }))
)

const columns = [
  { id: 'label', label: 'Item', noWrap: true },
  { id: 'value', label: 'Detail', noWrap: false },
  { id: 'status', label: 'Status', noWrap: true }
]
</script>

<style scoped>
.detail-panel {
  background: #fff;
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(22, 22, 22, 0.04);
  overflow-x: auto;
  padding: 20px;
}
</style>
