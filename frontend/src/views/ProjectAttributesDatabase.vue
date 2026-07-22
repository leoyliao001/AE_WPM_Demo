<template>
  <PageShell
    title="Project Attributes Database"
    subtitle="Choose a reference table to browse or maintain. These tables power intake, dashboards, and migration tools."
    tag="Central data layer"
    back-label="Back to Welcome"
  >
    <section class="table-grid" aria-label="Attribute tables">
      <mc-card
        v-for="(item, index) in tables"
        :key="item.id"
        class="table-card"
        :style="{ '--card-accent': item.accent, '--card-delay': `${index * 80}ms` }"
        variant="bordered"
        fit="medium"
        contentalignment="middle"
        clickable
        :heading="item.title"
        :body="item.description"
        @click="openTable(item.route)"
      >
        <div slot="image" class="table-icon-wrap">
          <span class="table-icon-badge">
            <mc-icon :icon="item.icon" size="24" />
          </span>
        </div>
        <mc-button
          slot="actions"
          appearance="primary"
          variant="filled"
          fit="small"
          :label="item.actionLabel"
          trailingicon="mi-arrow-right"
          tabindex="-1"
        />
      </mc-card>
    </section>
  </PageShell>
</template>

<script setup>
import { useRouter } from 'vue-router'
import PageShell from '../components/PageShell.vue'
import '@maersk-global/mds-components-core/mc-card'
import '@maersk-global/mds-components-core/mc-icon'
import '@maersk-global/mds-components-core/mc-button'

const router = useRouter()

const tables = [
  {
    id: 'fpo-mapping',
    title: 'FPO Mapping',
    description:
      'Cascading L1–L4 process / FPO dictionary used across opportunity assessment and migration tools.',
    icon: 'mi-list-bullets',
    accent: '#0077B8',
    route: '/fpo-mapping',
    actionLabel: 'Open FPO Mapping'
  },
  {
    id: 'product-ownership',
    title: 'Product Ownership',
    description:
      'Product, Manager, Region, and Migration Manager mapping — maintain ownership assignments.',
    icon: 'mi-users',
    accent: '#0F766E',
    route: '/product-ownership',
    actionLabel: 'Open Product Ownership'
  },
  {
    id: 'gsc-site-mapping',
    title: 'GSC Site Mapping',
    description:
      'Region, Area, Supporting GSC Sites, and All options — maintain location / site mappings.',
    icon: 'mi-globe',
    accent: '#F3880E',
    route: '/gsc-site-mapping',
    actionLabel: 'Open GSC Site Mapping'
  }
]

const openTable = (route) => {
  router.push(route)
}
</script>

<style scoped>
.table-grid {
  display: grid;
  gap: 22px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.table-card {
  --card-accent: #0077b8;
  animation: fade-up 0.45s ease both;
  animation-delay: var(--card-delay, 0ms);
  min-height: 220px;
  transition: transform 0.22s ease;
}

.table-card:hover {
  transform: translateY(-4px);
}

.table-card::part(container) {
  background: #fff;
  border-color: rgba(22, 22, 22, 0.08);
  border-radius: 14px;
  box-shadow: 0 1px 2px rgba(22, 22, 22, 0.04);
  height: 100%;
  overflow: hidden;
  position: relative;
  transition:
    border-color 0.22s ease,
    box-shadow 0.22s ease;
}

.table-card::part(container)::before {
  background: var(--card-accent);
  content: '';
  height: 3px;
  left: 0;
  position: absolute;
  top: 0;
  width: 100%;
}

.table-card:hover::part(container) {
  border-color: color-mix(in srgb, var(--card-accent) 40%, transparent);
  box-shadow:
    0 12px 32px rgba(22, 22, 22, 0.08),
    0 0 0 1px color-mix(in srgb, var(--card-accent) 12%, transparent);
}

.table-card::part(header-container) {
  text-align: left;
}

.table-card::part(body-container) {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 13px;
  line-height: 1.5;
  text-align: left;
}

.table-icon-wrap {
  display: flex;
  justify-content: flex-start;
  padding: 4px 0 8px;
}

.table-icon-badge {
  align-items: center;
  background: color-mix(in srgb, var(--card-accent, #0077b8) 12%, white);
  border-radius: 12px;
  color: var(--card-accent, #0077b8);
  display: inline-flex;
  height: 48px;
  justify-content: center;
  width: 48px;
}

@keyframes fade-up {
  from {
    opacity: 0;
    transform: translateY(12px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 1100px) {
  .table-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .table-grid {
    grid-template-columns: 1fr;
  }
}
</style>
