<template>
  <header class="app-header">
    <mc-top-bar
      class="app-top-bar"
      logosize="auto"
    >
      <router-link slot="link" class="home-link" to="/" aria-label="Home" />

      <nav
        slot="actions"
        class="app-nav"
        :class="{ 'app-nav--scrollable': navHasOverflow }"
        aria-label="Main navigation"
      >
        <button
          v-if="navHasOverflow"
          class="app-nav__scroll-button"
          type="button"
          aria-label="Scroll navigation left"
          :disabled="!navCanScrollLeft"
          @click="scrollNav(-1)"
        >
          <span class="app-nav__scroll-arrow app-nav__scroll-arrow--left" aria-hidden="true" />
        </button>
        <div
          ref="navScroller"
          class="app-nav__scroller"
          tabindex="0"
          aria-label="Navigation items"
          @scroll="updateNavScrollState"
        >
          <div ref="navItemsContainer" class="app-nav__items">
            <div v-if="topbarBackLink || topbarNotice" class="topbar-leading-actions">
              <router-link
                v-if="topbarBackLink"
                class="topbar-back-link"
                :to="topbarBackLink.to"
                :aria-label="topbarBackLink.label"
              >
                <mc-button
                  appearance="neutral"
                  variant="plain"
                  fit="small"
                  :label="topbarBackLink.label"
                  icon="mi-arrow-left"
                />
              </router-link>
              <button
                v-if="topbarNotice"
                class="topbar-notice-trigger"
                type="button"
                aria-label="Open resource guidance"
                data-tooltip="Click to see reminder"
                aria-haspopup="dialog"
                :aria-expanded="noticeDialogOpen"
                @click="openNoticeDialog"
              >
                <mc-icon icon="mi-exclamation-circle-solid" color="#d8899b" size="24" />
              </button>
            </div>
            <template v-for="item in navItems" :key="item.to">
              <div
                v-if="item.disabled"
                class="nav-link nav-link--placeholder"
                aria-disabled="true"
              >
                {{ item.label }}
              </div>
              <div
                v-else-if="item.label === 'Admin'"
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
          </div>
        </div>
        <button
          v-if="navHasOverflow"
          class="app-nav__scroll-button"
          type="button"
          aria-label="Scroll navigation right"
          :disabled="!navCanScrollRight"
          @click="scrollNav(1)"
        >
          <span class="app-nav__scroll-arrow app-nav__scroll-arrow--right" aria-hidden="true" />
        </button>
      </nav>
    </mc-top-bar>
    <mc-dialog
      :open="noticeDialogOpen"
      :heading="topbarNotice?.heading || 'Resource guidance'"
      dimension="medium"
      showclosebutton
      @closing="closeNoticeDialog"
    >
      <div v-if="topbarNotice" class="topbar-notice-content">
        <section v-if="topbarNotice.blockers?.length" class="topbar-notice-section">
          <h3>Why resources cannot be confirmed</h3>
          <ul>
            <li v-for="blocker in topbarNotice.blockers" :key="blocker.key">
              {{ blocker.message }}
              <router-link v-if="blocker.to" class="topbar-notice-link" :to="blocker.to" @click="closeNoticeDialog">
                Open Scope
              </router-link>
            </li>
          </ul>
        </section>
        <section v-if="topbarNotice.warnings?.length" class="topbar-notice-section">
          <h3>Needs attention</h3>
          <ul>
            <li v-for="warning in topbarNotice.warnings" :key="warning.key">{{ warning.message }}</li>
          </ul>
        </section>
      </div>
    </mc-dialog>
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
            :to="personalApprovalTo"
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
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import '@maersk-global/mds-components-core/mc-top-bar'
import '@maersk-global/mds-components-core/mc-icon'
import '@maersk-global/mds-components-core/mc-dialog'
import { azureAuthState } from '../auth/azureAuth.js'
import { topbarBackLink } from '../composables/useTopbarBackLink.js'
import { topbarNotice } from '../composables/useTopbarNotice.js'
import { fetchMyAttributesAccess } from '../utils/attributesAccess.js'

const route = useRoute()
const isSuperAdmin = ref(false)
const adminMenuOpen = ref(false)
const userMenuOpen = ref(false)
const noticeDialogOpen = ref(false)
const navScroller = ref(null)
const navItemsContainer = ref(null)
const navHasOverflow = ref(false)
const navCanScrollLeft = ref(false)
const navCanScrollRight = ref(false)
let navResizeObserver

const openNoticeDialog = () => {
  noticeDialogOpen.value = true
}

const closeNoticeDialog = () => {
  noticeDialogOpen.value = false
}

const approvalReturnQuery = computed(() => {
  if (route.path.startsWith('/approval-cycle')) {
    const { scope, ...context } = route.query
    return context
  }
  return { from: 'app-header', returnTo: route.fullPath }
})

const personalApprovalTo = computed(() => ({
  path: '/approval-cycle',
  query: approvalReturnQuery.value
}))

const adminMenuItems = computed(() => [
  { label: 'Project Attributes Database', to: '/project-attributes' },
  {
    label: 'Approval Cycle',
    to: { path: '/approval-cycle', query: { ...approvalReturnQuery.value, scope: 'all' } }
  }
])

const baseNavItems = [
  { label: 'Home', to: '/', icon: 'mi-house' },
  // Hidden for now: Future Service Model, Final CI Review
  { label: 'Start a Migration', to: '/migration-intake', icon: 'mi-file-arrows-square' },
  { label: 'Dashboard', to: '/migration-dashboard', icon: 'mi-chart-bars-vertical' },
  { label: 'Pulse Assistant', to: '/migration-chatbot', icon: 'mi-chatbot' },
  { label: 'Playbook&Toolkit', disabled: true }
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

const updateNavScrollState = () => {
  const scroller = navScroller.value
  if (!scroller) return

  const hasOverflow = scroller.scrollWidth > scroller.clientWidth + 1
  if (navHasOverflow.value !== hasOverflow) {
    navHasOverflow.value = hasOverflow
    nextTick(updateNavScrollState)
    return
  }

  navCanScrollLeft.value = scroller.scrollLeft > 1
  navCanScrollRight.value = scroller.scrollLeft + scroller.clientWidth < scroller.scrollWidth - 1
}

const scrollNav = (direction) => {
  const scroller = navScroller.value
  if (!scroller) return
  scroller.scrollBy({
    left: direction * Math.max(160, scroller.clientWidth * 0.75),
    behavior: 'smooth'
  })
}

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
  window.addEventListener('resize', updateNavScrollState)
  nextTick(() => {
    updateNavScrollState()
    if (typeof ResizeObserver !== 'undefined') {
      navResizeObserver = new ResizeObserver(updateNavScrollState)
      if (navScroller.value) navResizeObserver.observe(navScroller.value)
      if (navItemsContainer.value) navResizeObserver.observe(navItemsContainer.value)
    }
  })
})
onUnmounted(() => {
  document.removeEventListener('click', closeAdminMenuOnOutsideClick)
  document.removeEventListener('keydown', closeAdminMenuOnEscape)
  window.removeEventListener('resize', updateNavScrollState)
  navResizeObserver?.disconnect()
})
watch(navItems, () => nextTick(updateNavScrollState))
watch(
  () => route.fullPath,
  () => nextTick(updateNavScrollState)
)
watch(
  () => azureAuthState.user?.username || azureAuthState.user?.name || azureAuthState.status,
  () => {
    refreshSuperAdmin()
  }
)
watch(
  () => route.fullPath,
  closeNoticeDialog
)
watch(topbarNotice, (notice) => {
  if (!notice) closeNoticeDialog()
})
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
  text-decoration: none;
}

.topbar-leading-actions {
  align-items: center;
  display: flex;
  flex: 0 0 auto;
  gap: 8px;
}

.topbar-notice-trigger {
  background: transparent;
  border: 0;
  border-radius: 0;
  color: #d8899b;
  cursor: pointer;
  display: grid;
  flex: 0 0 auto;
  height: 40px;
  place-items: center;
  padding: 0;
  position: relative;
  width: 40px;
}

.topbar-notice-trigger mc-icon {
  animation: topbar-notice-fade 3s ease-in-out infinite;
}

.topbar-notice-trigger:hover {
  color: #c96e83;
}

.topbar-notice-trigger:focus-visible {
  color: #c96e83;
  outline: 2px solid #d8899b;
  outline-offset: 1px;
}

.topbar-notice-trigger::after {
  background: #263c4d;
  border-radius: 4px;
  color: #fff;
  content: attr(data-tooltip);
  font-size: 12px;
  left: 50%;
  opacity: 0;
  padding: 6px 8px;
  pointer-events: none;
  position: absolute;
  top: calc(100% + 6px);
  transform: translateX(-50%);
  transition: opacity 0.05s linear;
  white-space: nowrap;
  z-index: 1101;
}

.topbar-notice-trigger:hover::after,
.topbar-notice-trigger:focus-visible::after {
  opacity: 1;
}

.topbar-notice-content {
  color: #344b5e;
  font-size: 14px;
  line-height: 1.55;
  max-height: min(60vh, 520px);
  overflow: auto;
}

.topbar-notice-section + .topbar-notice-section {
  border-top: 1px solid #d9e1e6;
  margin-top: 16px;
  padding-top: 12px;
}

.topbar-notice-section h3 {
  color: #263c4d;
  font-size: 14px;
  margin: 0 0 8px;
}

.topbar-notice-section ul {
  margin: 0;
  padding-left: 20px;
}

.topbar-notice-section li + li {
  margin-top: 8px;
}

.topbar-notice-link {
  color: var(--mds_brand_appearance_primary_default_link-color, #0077b8);
  display: inline-block;
  margin-left: 6px;
}

@keyframes topbar-notice-fade {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.08; }
}

@media (prefers-reduced-motion: reduce) {
  .topbar-notice-trigger mc-icon {
    animation-duration: 3.4s;
  }
}

.app-nav {
  align-items: center;
  box-sizing: border-box;
  display: flex;
  flex: 0 1 auto;
  height: 100%;
  max-width: calc(100vw - 155px);
  min-width: 0;
  padding: 0 220px 0 8px;
  width: calc(100vw - 155px);
}

.app-nav__scroller {
  align-items: center;
  display: flex;
  flex: 1 1 auto;
  height: 100%;
  min-width: 0;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none;
  scroll-behavior: smooth;
}

.app-nav__scroller::-webkit-scrollbar {
  display: none;
}

.app-nav__items {
  align-items: center;
  display: flex;
  flex: 0 0 auto;
  gap: 4px 16px;
  height: 100%;
  white-space: nowrap;
}

.app-nav__scroll-button {
  align-items: center;
  background: #fff;
  border: 1px solid var(--mds_brand_appearance_neutral_weak_border-color, #d9dee3);
  border-radius: 4px;
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  cursor: pointer;
  display: grid;
  flex: 0 0 28px;
  height: 32px;
  justify-items: center;
  padding: 0;
}

.app-nav__scroll-button:hover:not(:disabled),
.app-nav__scroll-button:focus-visible {
  color: var(--mds_brand_appearance_primary_default_link-color, #0077b8);
}

.app-nav__scroll-button:focus-visible {
  outline: 2px solid var(--mds_brand_appearance_primary_default_link-color, #0077b8);
  outline-offset: 1px;
}

.app-nav__scroll-button:disabled {
  cursor: default;
  opacity: 0.4;
}

.app-nav__scroll-arrow {
  border-bottom: 2px solid currentColor;
  border-right: 2px solid currentColor;
  height: 7px;
  width: 7px;
}

.app-nav__scroll-arrow--left {
  transform: translateX(2px) rotate(135deg);
}

.app-nav__scroll-arrow--right {
  transform: translateX(-2px) rotate(-45deg);
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

.app-nav--scrollable .admin-menu {
  position: fixed;
  right: 12px;
  top: 64px;
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

.nav-link--placeholder {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  cursor: default;
}

@media (max-width: 900px) {
  .app-nav {
    padding-right: 150px;
  }

  .app-nav__items {
    gap: 4px 10px;
  }

  .app-nav__items .nav-link {
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
