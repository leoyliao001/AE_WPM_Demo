<template>
  <header class="app-header">
    <mc-top-bar
      class="app-top-bar"
      logosize="auto"
    >
      <router-link slot="link" class="home-link" to="/" aria-label="Home" />

      <nav slot="actions" class="app-nav" aria-label="Main navigation">
        <router-link
          v-if="topbarBackLink"
          class="topbar-back-link"
          :to="topbarBackLink.to"
        >
          <mc-button
            appearance="neutral"
            variant="plain"
            fit="small"
            :label="topbarBackLink.label"
            icon="mi-arrow-left"
          />
        </router-link>
        <template v-for="item in navItems" :key="item.to">
          <div
            v-if="item.label === 'Admin'"
            class="nav-admin"
          >
            <button
              v-if="isSuperAdmin"
              class="nav-link nav-admin__trigger"
              :class="{ 'nav-link--active': isActive(item) }"
              type="button"
              aria-haspopup="menu"
              :aria-expanded="adminMenuOpen"
              @click="toggleAdminMenu"
              @keydown.esc="closeAdminMenu"
            >
              <mc-icon v-if="item.icon" :icon="item.icon" size="20" />
              <span>{{ item.label }}</span>
            </button>
            <router-link
              v-else
              :to="item.to"
              class="nav-link"
              :class="{ 'nav-link--active': isActive(item) }"
            >
              <mc-icon v-if="item.icon" :icon="item.icon" size="20" />
              <span>{{ item.label }}</span>
            </router-link>
            <nav v-if="isSuperAdmin && adminMenuOpen" class="admin-menu" aria-label="Admin menu" role="menu">
              <router-link
                v-for="adminItem in adminMenuItems"
                :key="adminItem.to"
                :to="adminItem.to"
                class="admin-menu__item"
                role="menuitem"
                @click="closeAdminMenu"
              >
                {{ adminItem.label }}
              </router-link>
            </nav>
          </div>
          <router-link
            v-else
            :to="item.to"
            class="nav-link"
            :class="{ 'nav-link--active': isActive(item) }"
          >
            <mc-icon v-if="item.icon" :icon="item.icon" size="20" />
            <span>{{ item.label }}</span>
          </router-link>
        </template>
      </nav>
    </mc-top-bar>
    <div class="app-user-panel" aria-live="polite">
      <span
        v-if="azureAuthState.status === 'loading' || azureAuthState.status === 'redirecting'"
        class="user-status"
      >Signing in...</span>
      <div
        v-else-if="azureAuthState.user"
        class="user-menu"
        :title="azureAuthState.user.name || azureAuthState.user.username"
      >
        <button
          class="user-badge user-menu__trigger"
          type="button"
          aria-label="Open personal approvals menu"
          aria-haspopup="menu"
          :aria-expanded="userMenuOpen"
          @click="toggleUserMenu"
          @keydown.esc="closeUserMenu"
        >
          <span class="user-badge__name">{{ azureAuthState.user.username || azureAuthState.user.name }}</span>
        </button>
        <nav v-if="userMenuOpen" class="admin-menu" aria-label="Personal menu" role="menu">
          <router-link
            to="/approval-cycle"
            class="admin-menu__item"
            role="menuitem"
            @click="closeUserMenu"
          >
            Approval Cycle
          </router-link>
        </nav>
      </div>
      <span
        v-else-if="azureAuthState.error"
        class="user-status user-status--error"
        :title="azureAuthState.error"
      >SSO unavailable</span>
    </div>
    <div class="app-header-divider" aria-hidden="true" />
  </header>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import '@maersk-global/mds-components-core/mc-top-bar'
import '@maersk-global/mds-components-core/mc-icon'
import { azureAuthState } from '../auth/azureAuth.js'
import { topbarBackLink } from '../composables/useTopbarBackLink.js'
import { fetchMyAttributesAccess } from '../utils/attributesAccess.js'

const route = useRoute()
const isSuperAdmin = ref(false)
const adminMenuOpen = ref(false)
const userMenuOpen = ref(false)

const adminMenuItems = [
  { label: 'Project Attributes Database', to: '/project-attributes' },
  { label: 'Approval Cycle', to: { path: '/approval-cycle', query: { scope: 'all' } } }
]

const baseNavItems = [
  { label: 'Welcome', to: '/', icon: 'mi-house' },
  // Hidden for now: Future Service Model, Final CI Review
  { label: 'Intake', to: '/migration-intake', icon: 'mi-file-arrows-square' },
  { label: 'Dashboard', to: '/migration-dashboard', icon: 'mi-chart-bars-vertical' },
  { label: 'Chatbot', to: '/migration-chatbot', icon: 'mi-chatbot' }
]

const databaseNavItem = {
  label: 'Admin',
  to: '/project-attributes',
  icon: 'mi-database',
  matchPaths: [
    '/project-attributes',
    '/fpo-mapping',
    '/product-ownership',
    '/gsc-site-mapping',
    '/service-catalogue',
    '/working-hours',
    '/migration-intake-submissions',
    '/project-gantt-attributes',
    '/bpm-rofo',
    '/bpm-actual',
    '/attributes-access-control',
    '/scope-statements-database',
    '/stakeholder-registrations-database',
    '/approval-workflow',
    '/input-for-approval'
  ]
}

const navItems = computed(() => {
  if (!isSuperAdmin.value) return baseNavItems
  return [...baseNavItems, databaseNavItem]
})

const refreshSuperAdmin = async () => {
  const access = await fetchMyAttributesAccess({ force: true })
  isSuperAdmin.value = !!access?.is_super_admin
}

const toggleAdminMenu = () => {
  if (isSuperAdmin.value) adminMenuOpen.value = !adminMenuOpen.value
}

const closeAdminMenu = () => {
  adminMenuOpen.value = false
}

const toggleUserMenu = () => {
  userMenuOpen.value = !userMenuOpen.value
}

const closeUserMenu = () => {
  userMenuOpen.value = false
}

const closeAdminMenuOnOutsideClick = (event) => {
  if (!event.target.closest('.nav-admin')) closeAdminMenu()
  if (!event.target.closest('.user-menu')) closeUserMenu()
}

const closeAdminMenuOnEscape = (event) => {
  if (event.key === 'Escape') closeAdminMenu()
}

const isActive = (item) => {
  if (Array.isArray(item.matchPaths)) {
    return item.matchPaths.some(
      (path) => route.path === path || route.path.startsWith(`${path}/`)
    )
  }
  if (item.to === '/') {
    return route.path === '/'
  }
  return route.path === item.to || route.path.startsWith(`${item.to}/`)
}

onMounted(() => {
  refreshSuperAdmin()
  document.addEventListener('click', closeAdminMenuOnOutsideClick)
  document.addEventListener('keydown', closeAdminMenuOnEscape)
})
onUnmounted(() => {
  document.removeEventListener('click', closeAdminMenuOnOutsideClick)
  document.removeEventListener('keydown', closeAdminMenuOnEscape)
})
watch(
  () => azureAuthState.user?.username || azureAuthState.user?.name || azureAuthState.status,
  () => {
    refreshSuperAdmin()
  }
)
</script>

<style scoped>
.app-header {
  background: var(--mds_brand_appearance_neutral_default_background-color, #fff);
  padding-left: 12px;
  padding-right: 12px;
  position: sticky;
  top: 0;
  z-index: 1000;
}

.app-top-bar {
  display: block;
}

.app-header-divider {
  background: var(--mds_brand_appearance_neutral_weak_border-color, #d9dee3);
  box-shadow: none;
  height: 1px;
  pointer-events: none;
  width: 100%;
}

.home-link {
  display: block;
  height: 100%;
  text-decoration: none;
}

.topbar-back-link {
  align-items: center;
  display: inline-flex;
  flex: 0 0 auto;
  left: 140px;
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  text-decoration: none;
  z-index: 1;
}

.app-nav {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 4px 16px;
  height: 100%;
  padding: 0 220px 0 8px;
}

.app-user-panel {
  align-items: center;
  display: flex;
  inset: 0 20px auto auto;
  min-height: 100%;
  pointer-events: none;
  position: absolute;
}

.user-badge,
.user-status {
  align-items: center;
  background: #eef6fb;
  border: 1px solid #c6d9e6;
  border-radius: 999px;
  color: #174a68;
  display: inline-flex;
  font-size: 12px;
  gap: 8px;
  max-width: 280px;
  padding: 6px 12px;
}

.user-menu {
  pointer-events: auto;
  position: relative;
}

.user-menu__trigger {
  background: transparent;
  border-color: transparent;
  border-radius: 4px;
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  cursor: pointer;
  font-family: inherit;
  font-size: 13px;
  gap: 8px;
  padding: 6px 8px;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.user-menu__trigger:hover,
.user-menu__trigger:focus-visible {
  background: #f3f6f7;
  color: var(--mds_brand_appearance_primary_default_link-color, #0077b8);
  outline: none;
}

.user-menu__trigger::after {
  border-bottom: 1.5px solid currentColor;
  border-right: 1.5px solid currentColor;
  content: '';
  flex: 0 0 6px;
  height: 6px;
  transform: translateY(-2px) rotate(45deg);
  width: 6px;
}

.user-menu__trigger .user-badge__name {
  font-weight: 500;
}

.nav-admin {
  align-items: center;
  display: inline-flex;
  position: relative;
}

.nav-admin__trigger {
  background: transparent;
  border: 0;
  cursor: pointer;
  font-family: inherit;
}

.nav-admin__trigger::after {
  border-bottom: 1.5px solid currentColor;
  border-right: 1.5px solid currentColor;
  content: '';
  height: 6px;
  margin-left: 2px;
  transform: translateY(-2px) rotate(45deg);
  width: 6px;
}

.admin-menu {
  background: var(--mds_brand_appearance_neutral_default_background-color, #fff);
  border: 1px solid var(--mds_brand_appearance_neutral_weak_border-color, #d9dee3);
  border-radius: 2px;
  box-shadow: 0 4px 14px rgb(20 20 20 / 12%);
  min-width: 220px;
  padding: 4px;
  position: absolute;
  right: 0;
  top: calc(100% + 6px);
  z-index: 1001;
}

.admin-menu__item {
  border-left: 2px solid transparent;
  border-radius: 2px;
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  display: block;
  font-size: 13px;
  padding: 9px 12px;
  text-decoration: none;
  transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
  white-space: nowrap;
}

.admin-menu__item:hover,
.admin-menu__item:focus-visible {
  background: #f3f6f7;
  border-left-color: var(--mds_brand_appearance_primary_default_link-color, #0077b8);
  color: var(--mds_brand_appearance_primary_default_link-color, #0077b8);
  outline: none;
}

.user-badge__name {
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-status--error {
  background: #fff4e8;
  border-color: #f0c48b;
  color: #8a4f00;
}

.nav-link {
  align-items: center;
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  display: inline-flex;
  font-size: 13px;
  font-weight: 500;
  gap: 6px;
  padding: 6px 4px;
  text-decoration: none;
  transition: color 0.15s ease;
  white-space: nowrap;
}

.nav-link:hover {
  color: var(--mds_brand_appearance_primary_default_link-color, #0077b8);
}

.nav-link--active {
  color: var(--mds_brand_appearance_primary_default_link-color, #0077b8);
}

.nav-link--active mc-icon {
  color: inherit;
}

@media (max-width: 900px) {
  .app-nav {
    gap: 4px 10px;
    padding-right: 150px;
  }

  .nav-link span {
    display: none;
  }

  .nav-link {
    padding: 8px;
  }

  .user-badge,
  .user-status {
    max-width: 140px;
    padding-left: 10px;
    padding-right: 10px;
  }
}

@media (max-width: 640px) {
  .app-header {
    padding-right: 8px;
  }

  .app-nav {
    padding-right: 96px;
  }

  .user-badge,
  .user-status {
    font-size: 11px;
    max-width: 92px;
  }
}
</style>
