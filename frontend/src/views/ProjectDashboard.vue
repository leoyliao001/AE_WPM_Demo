<template>
  <PageShell
    title="Individual Project Dashboard"
    subtitle="Opportunity assessment and main milestones — each opens a dedicated detail screen."
    tag="Project Dashboard"
    back-label="Back to Welcome"
  >
    <section class="opportunity-card">
      <div class="opportunity-head">
        <mc-icon icon="mi-chart-arrow-up-right" size="24" />
        <div>
          <h2>Opportunity Assessment</h2>
          <p>APAC Ocean Consolidation — high-priority migration with strong net benefit potential.</p>
        </div>
      </div>
      <div class="opportunity-stats">
        <div v-for="stat in opportunityStats" :key="stat.label" class="stat">
          <span class="stat-label">{{ stat.label }}</span>
          <strong class="stat-value">{{ stat.value }}</strong>
        </div>
      </div>
    </section>

    <section class="milestones-section">
      <div class="panel-head">
        <h2>Main Milestones</h2>
        <p>Select a milestone to open its detail screen.</p>
      </div>

      <div class="milestone-grid">
        <mc-card
          v-for="item in milestones"
          :key="item.id"
          class="milestone-card"
          :style="{ '--card-accent': item.accent }"
          variant="bordered"
          fit="medium"
          contentalignment="middle"
          clickable
          :heading="item.title"
          :body="item.description"
          @click="openMilestone(item.id)"
        >
          <div slot="image" class="milestone-icon">
            <mc-icon :icon="item.icon" size="24" />
          </div>
          <mc-button
            slot="actions"
            appearance="neutral"
            variant="plain"
            fit="small"
            label="View details"
            trailingicon="mi-arrow-right"
            tabindex="-1"
          />
        </mc-card>
      </div>
    </section>
  </PageShell>
</template>

<script setup>
import { useRouter } from 'vue-router'
import PageShell from '../components/PageShell.vue'
import { projectMilestones } from '../data/mockData'
import '@maersk-global/mds-components-core/mc-card'
import '@maersk-global/mds-components-core/mc-icon'
import '@maersk-global/mds-components-core/mc-button'

const router = useRouter()
const milestones = projectMilestones

const opportunityStats = [
  { label: 'Net benefit (3-yr)', value: '$2.9M' },
  { label: 'FTE impacted', value: '32' },
  { label: 'Strategic priority', value: 'High' },
  { label: 'Target go-live', value: 'Nov 2026' }
]

const openMilestone = (id) => {
  router.push(`/project-dashboard/${id}`)
}
</script>

<style scoped>
.opportunity-card {
  background: linear-gradient(135deg, #0077b8 0%, #003f6e 100%);
  border-radius: 16px;
  color: #fff;
  padding: 24px;
}

.opportunity-head {
  align-items: flex-start;
  display: flex;
  gap: 14px;
  margin-bottom: 20px;
}

.opportunity-head h2 {
  font-size: 20px;
  margin: 0 0 6px;
}

.opportunity-head p {
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
  opacity: 0.9;
}

.opportunity-stats {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.stat {
  background: rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  padding: 14px 16px;
}

.stat-label {
  display: block;
  font-size: 12px;
  margin-bottom: 6px;
  opacity: 0.85;
}

.stat-value {
  font-size: 22px;
}

.panel-head h2 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 6px;
}

.panel-head p {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 13px;
  margin: 0 0 16px;
}

.milestone-grid {
  display: grid;
  gap: 18px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.milestone-card {
  --card-accent: #0077b8;
  min-height: 180px;
}

.milestone-card::part(container) {
  border-radius: 14px;
  height: 100%;
  position: relative;
}

.milestone-card::part(container)::before {
  background: var(--card-accent);
  content: '';
  height: 3px;
  left: 0;
  position: absolute;
  top: 0;
  width: 100%;
}

.milestone-icon {
  color: var(--card-accent);
  display: flex;
  justify-content: flex-start;
  padding: 4px 0 8px;
}

@media (max-width: 900px) {
  .opportunity-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .milestone-grid {
    grid-template-columns: 1fr;
  }
}
</style>
