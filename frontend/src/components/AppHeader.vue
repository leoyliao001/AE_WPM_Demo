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
    <div class="app-header-divider" aria-hidden="true" />
  </header>
</template>

<script setup>
import { useRoute } from 'vue-router'
import '@maersk-global/mds-components-core/mc-top-bar'
import '@maersk-global/mds-components-core/mc-icon'

const route = useRoute()

const navItems = [
  { label: 'Welcome', to: '/', icon: 'mi-house' },
  { label: 'Future Service Model', to: '/future-service-model', icon: 'mi-chart-line-up' },
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
  padding: 0 8px;
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
  }

  .nav-link span {
    display: none;
  }

  .nav-link {
    padding: 8px;
  }
}
</style>
