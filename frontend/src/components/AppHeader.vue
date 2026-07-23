<template>
  <header class="app-header">
    <mc-top-bar
      class="app-top-bar"
      product="AE WPM Demo"
      productshort="WPM"
      logosize="auto"
    >
      <router-link slot="link" class="home-link" to="/" aria-label="AE WPM Demo home" />

      <nav slot="actions" class="app-nav" aria-label="Main navigation">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-link"
          :class="{ 'nav-link--active': isActive(item.to) }"
        >
          <mc-icon v-if="item.icon" :icon="item.icon" size="20" />
          <span>{{ item.label }}</span>
        </router-link>
      </nav>
    </mc-top-bar>
    <div class="app-user-panel" aria-live="polite">
      <span
        v-if="azureAuthState.status === 'loading' || azureAuthState.status === 'redirecting'"
        class="user-status"
      >Signing in...</span>
      <div
        v-else-if="azureAuthState.user"
        class="user-badge"
        :title="azureAuthState.user.name || azureAuthState.user.username"
      >
        <span class="user-badge__name">{{ azureAuthState.user.username || azureAuthState.user.name }}</span>
      </div>
      <span v-else-if="azureAuthState.error" class="user-status user-status--error">SSO unavailable</span>
    </div>
    <div class="app-header-divider" aria-hidden="true" />
  </header>
</template>

<script setup>
import { useRoute } from 'vue-router'
import '@maersk-global/mds-components-core/mc-top-bar'
import '@maersk-global/mds-components-core/mc-icon'
import { azureAuthState } from '../auth/azureAuth.js'

const route = useRoute()

const navItems = [
  { label: 'Welcome', to: '/', icon: 'mi-house' },
  // Hidden for now: Future Service Model, Final CI Review
  { label: 'Intake', to: '/migration-intake', icon: 'mi-file-arrows-square' },
  { label: 'Dashboard', to: '/migration-dashboard', icon: 'mi-chart-bars-vertical' },
  { label: 'L&D', to: '/ld-dashboard', icon: 'mi-monitor' },
  { label: 'Project', to: '/project-dashboard', icon: 'mi-file-check' },
  { label: 'Chatbot', to: '/migration-chatbot', icon: 'mi-chatbot' }
]

const isActive = (path) => {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path === path || route.path.startsWith(`${path}/`)
}
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
