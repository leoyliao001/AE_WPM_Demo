<template>
  <PageShell
    title="Project Attributes Database"
    subtitle="Choose a reference table to browse or maintain. Access is controlled by your SSO email."
    tag="Central data layer"
    back-label="Back to Welcome"
  >
    <mc-notification
      v-if="accessError"
      appearance="error"
      fit="medium"
      heading="Unable to load access"
      :body="accessError"
    />

    <div v-else-if="loadingAccess" class="access-loading">Checking your table permissions…</div>

    <template v-else>
      <p class="access-banner">
        Signed in as <strong>{{ access?.email || 'unknown' }}</strong>
        <span v-if="access?.is_super_admin"> · Super Admin</span>
      </p>

      <section v-if="visibleTables.length" class="table-grid" aria-label="Attribute tables">
        <mc-card
          v-for="(item, index) in visibleTables"
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

      <mc-notification
        v-else
        appearance="warning"
        fit="medium"
        heading="No table access"
        body="Your SSO email is not granted access to any Project Attributes tables. Ask a Super Admin to add you in Access Control."
      />
    </template>
  </PageShell>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import PageShell from '../components/PageShell.vue'
import {
  canAccessAttributesTable,
  clearAttributesAccessCache,
  fetchMyAttributesAccess
} from '../utils/attributesAccess.js'
import '@maersk-global/mds-components-core/mc-card'
import '@maersk-global/mds-components-core/mc-icon'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-notification'

const router = useRouter()
const loadingAccess = ref(true)
const accessError = ref('')
const access = ref(null)

const allTables = [
  {
    id: 'fpo-mapping',
    tableKey: 'fpo_mapping',
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
    tableKey: 'product_ownership',
    title: 'Product Ownership',
    description:
      'Region, Area, and Migration Manager mapping — maintain ownership assignments.',
    icon: 'mi-users',
    accent: '#0F766E',
    route: '/product-ownership',
    actionLabel: 'Open Product Ownership'
  },
  {
    id: 'gsc-site-mapping',
    tableKey: 'gsc_site_mapping',
    title: 'GSC Site Mapping',
    description:
      'Region, Area, Supporting GSC Sites, and All options — maintain location / site mappings.',
    icon: 'mi-globe',
    accent: '#F3880E',
    route: '/gsc-site-mapping',
    actionLabel: 'Open GSC Site Mapping'
  },
  {
    id: 'service-catalogue',
    tableKey: 'service_catalogue',
    title: 'Service Catalogue',
    description:
      'Product / L1–L4 activities catalogue with current ownership — maintain service catalogue reference data.',
    icon: 'mi-layers',
    accent: '#0E7490',
    route: '/service-catalogue',
    actionLabel: 'Open Service Catalogue'
  },
  {
    id: 'working-hours',
    tableKey: 'working_hours',
    title: 'Working Hours',
    description:
      'Area and GSC working hours — maintain aera_working_hours and gsc_working_hours reference data.',
    icon: 'mi-clock',
    accent: '#B45309',
    route: '/working-hours',
    actionLabel: 'Open Working Hours'
  },
  {
    id: 'migration-intake',
    tableKey: 'migration_intake',
    title: 'Migration Intake',
    description:
      'Submitted migration intake forms — browse and maintain project request records online.',
    icon: 'mi-file-arrows-square',
    accent: '#0077B8',
    route: '/migration-intake-submissions',
    actionLabel: 'Open Migration Intake'
  },
  {
    id: 'project-gantt',
    tableKey: 'project_gantt',
    title: 'Project Gantt',
    description:
      'Per-migration Gantt tasks and summary parameters. Enter a Migration ID to load, then edit online.',
    icon: 'mi-calendar',
    accent: '#0070C0',
    route: '/project-gantt-attributes',
    actionLabel: 'Open Project Gantt'
  },
  {
    id: 'access-control',
    tableKey: 'access_control',
    title: 'Access Control',
    description:
      'SSO email permissions for Project Attributes tables. Super Admins can open every table.',
    icon: 'mi-lock',
    accent: '#7B61FF',
    route: '/attributes-access-control',
    actionLabel: 'Open Access Control'
  }
]

const visibleTables = computed(() =>
  allTables.filter((item) => canAccessAttributesTable(access.value, item.tableKey))
)

const openTable = (route) => {
  router.push(route)
}

onMounted(async () => {
  loadingAccess.value = true
  accessError.value = ''
  clearAttributesAccessCache()
  const data = await fetchMyAttributesAccess({ force: true })
  access.value = data
  if (data?.error && !data.authenticated) {
    accessError.value = data.error
  }
  loadingAccess.value = false
})
</script>

<style scoped>
.access-loading {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 14px;
  padding: 24px 0;
}

.access-banner {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 13px;
  margin: 0 0 18px;
}

.table-grid {
  display: grid;
  gap: 22px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  perspective: 1200px;
}

@media (min-width: 1100px) {
  .table-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.table-card {
  --card-accent: #0077b8;
  animation: card-in 420ms ease both;
  animation-delay: var(--card-delay, 0ms);
  transform-style: preserve-3d;
  transition: transform 0.28s cubic-bezier(0.22, 1, 0.36, 1);
}

.table-card:hover {
  transform: translateY(-10px) scale(1.02);
}

.table-card::part(container) {
  background: linear-gradient(180deg, #ffffff 0%, #fbfcfd 100%);
  border-color: rgba(22, 22, 22, 0.08);
  border-radius: 14px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 2px 3px rgba(15, 23, 42, 0.05),
    0 8px 16px rgba(15, 23, 42, 0.07),
    0 18px 36px rgba(0, 63, 110, 0.1),
    0 28px 56px -12px rgba(0, 63, 110, 0.12);
  min-height: 220px;
  overflow: hidden;
  position: relative;
  transition:
    border-color 0.28s ease,
    box-shadow 0.28s cubic-bezier(0.22, 1, 0.36, 1),
    background 0.28s ease;
}

.table-card::part(container)::before {
  background: var(--card-accent, #0077b8);
  content: '';
  height: 3px;
  left: 0;
  position: absolute;
  right: 0;
  top: 0;
}

.table-card:hover::part(container) {
  background: #fff;
  border-color: color-mix(in srgb, var(--card-accent) 36%, transparent);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 4px 8px rgba(15, 23, 42, 0.06),
    0 14px 28px rgba(15, 23, 42, 0.1),
    0 28px 56px rgba(0, 63, 110, 0.16),
    0 40px 72px -16px rgba(0, 63, 110, 0.18),
    0 0 0 1px color-mix(in srgb, var(--card-accent) 14%, transparent);
}

.table-icon-wrap {
  display: flex;
  justify-content: center;
  margin-bottom: 8px;
  padding: 4px 0 8px;
}

.table-icon-badge {
  align-items: center;
  background: color-mix(in srgb, var(--card-accent, #0077b8) 12%, white);
  border: 1px solid color-mix(in srgb, var(--card-accent, #0077b8) 16%, transparent);
  border-radius: 12px;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.75),
    0 2px 6px color-mix(in srgb, var(--card-accent, #0077b8) 18%, transparent);
  color: var(--card-accent, #0077b8);
  display: inline-flex;
  height: 52px;
  justify-content: center;
  transition:
    transform 0.28s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.28s ease;
  width: 52px;
}

.table-card:hover .table-icon-badge {
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    0 6px 16px color-mix(in srgb, var(--card-accent, #0077b8) 36%, transparent);
  transform: translateY(-3px) scale(1.08);
}

@keyframes card-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 720px) {
  .table-grid {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .table-card,
  .table-card:hover,
  .table-card:hover .table-icon-badge {
    transform: none;
  }
}
</style>

<style>
.table-card::part(heading) {
  text-align: center;
}

.table-card::part(body) {
  color: #6c757d;
  font-size: 13px;
  line-height: 1.45;
  text-align: center;
}
</style>
