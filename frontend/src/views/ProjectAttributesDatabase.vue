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
}

@media (min-width: 1100px) {
  .table-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.table-card {
  animation: card-in 420ms ease both;
  animation-delay: var(--card-delay, 0ms);
}

.table-card::part(container) {
  border-radius: 16px;
  min-height: 220px;
  overflow: hidden;
  position: relative;
  transition: transform 180ms ease, box-shadow 180ms ease;
}

.table-card::part(container)::before {
  background: var(--card-accent, #0077b8);
  content: '';
  height: 4px;
  left: 0;
  position: absolute;
  right: 0;
  top: 0;
}

.table-card:hover::part(container) {
  box-shadow: 0 10px 28px rgba(22, 22, 22, 0.1);
  transform: translateY(-2px);
}

.table-icon-wrap {
  display: flex;
  justify-content: center;
  margin-bottom: 8px;
}

.table-icon-badge {
  align-items: center;
  background: color-mix(in srgb, var(--card-accent, #0077b8) 14%, white);
  border-radius: 14px;
  color: var(--card-accent, #0077b8);
  display: inline-flex;
  height: 52px;
  justify-content: center;
  width: 52px;
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
