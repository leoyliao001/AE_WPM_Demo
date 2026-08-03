<template>
  <div class="welcome-page">
    <div class="page-content">
      <header class="welcome-header">
        <h1 class="welcome-title">Welcome</h1>
        <p class="welcome-subtitle">
          Choose a tool below to manage migrations, reporting, and learning — all powered by a shared project database.
        </p>
      </header>

      <section class="card-grid" aria-label="Migration tools">
        <mc-card
          v-for="(item, index) in menuItems"
          :key="item.id"
          class="tool-card"
          :class="{ 'tool-card--empty': item.empty }"
          :style="{ '--card-accent': item.accent, '--card-delay': `${index * 70}ms` }"
          variant="bordered"
          fit="medium"
          contentalignment="middle"
          :clickable="!item.empty"
          :heading="item.empty ? undefined : item.title"
          :body="item.empty ? undefined : item.description"
          @click="onCardClick(item)"
        >
          <template v-if="!item.empty">
            <div slot="image" class="card-icon-wrap">
              <span class="card-icon-badge">
                <mc-icon :icon="item.icon" size="24" />
              </span>
            </div>
            <mc-button
              slot="actions"
              appearance="neutral"
              variant="plain"
              fit="small"
              label="Open"
              trailingicon="mi-arrow-right"
              tabindex="-1"
            />
          </template>
          <div v-else class="empty-slot">
            <mc-tag appearance="neutral" fit="small" label="Coming soon" />
            <p class="empty-slot-text">More tools will be added here</p>
          </div>
        </mc-card>
      </section>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import '@maersk-global/mds-components-core/mc-card'
import '@maersk-global/mds-components-core/mc-icon'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-tag'

const router = useRouter()

const menuItems = [
  {
    id: 'migration-request',
    title: 'Raise a Migration Request',
    description: 'Submit migration intake details to the Project Attributes Database.',
    icon: 'mi-file-arrows-square',
    accent: '#0077B8',
    route: '/migration-intake'
  },
  {
    id: 'migration-chatbot',
    title: 'Migration Chatbot',
    description: 'Get instant answers and guided migration support.',
    icon: 'mi-chatbot',
    accent: '#6DAA28',
    route: '/migration-chatbot'
  },
  {
    id: 'migration-dashboard',
    title: 'Migration Dashboard',
    description: 'Product summary and detailed migration tracking overview.',
    icon: 'mi-chart-bars-vertical',
    accent: '#42B0D5',
    route: '/migration-dashboard'
  },
  {
    id: 'ld-dashboard',
    title: 'L&D Dashboard',
    description: 'Learning, scoping tasks, and training timeline by project.',
    icon: 'mi-monitor',
    accent: '#F3880E',
    route: '/ld-dashboard'
  },
  {
    id: 'project-dashboard',
    title: 'My Projects',
    description: 'Projects under your account — open a project to track migration progress.',
    icon: 'mi-file-check',
    accent: '#003F6E',
    route: '/project-dashboard'
  }
  // Hidden for now: Future Service Model, Final CI Review
]

const onCardClick = (item) => {
  if (item.empty || !item.route) return
  router.push(item.route)
}
</script>

<style scoped>
.welcome-page {
  background: #fff;
  /* Own the vertical scroll so bottom sections stay reachable */
  flex: 1 1 auto;
  min-height: 0;
  overflow-x: clip;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-y: contain;
  position: relative;
  width: 100%;
}

.page-content {
  margin: 0 auto;
  max-width: 1140px;
  padding: 56px 32px 120px;
  position: relative;
  z-index: 1;
}

.welcome-header {
  animation: fade-up 0.55s ease both;
  margin-bottom: 44px;
  max-width: 640px;
}

.welcome-title {
  color: var(--mds_brand_appearance_neutral_default_text-color, #161616);
  font-family: 'Maersk Headline', 'Maersk Text', sans-serif;
  font-size: clamp(36px, 5vw, 52px);
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.1;
  margin: 0 0 12px;
}

.welcome-subtitle {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 15px;
  line-height: 1.6;
  margin: 0;
  max-width: 520px;
}

.card-grid {
  display: grid;
  gap: 22px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.tool-card {
  --card-accent: #0077b8;
  animation: fade-up 0.55s ease both;
  animation-delay: var(--card-delay, 0ms);
  min-height: 210px;
  transition: transform 0.22s ease;
}

.tool-card:not(.tool-card--empty):hover {
  transform: translateY(-4px);
}

.tool-card::part(container) {
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

.tool-card:not(.tool-card--empty)::part(container)::before {
  background: var(--card-accent);
  content: '';
  height: 3px;
  left: 0;
  position: absolute;
  top: 0;
  width: 100%;
}

.tool-card:not(.tool-card--empty):hover::part(container) {
  border-color: color-mix(in srgb, var(--card-accent) 40%, transparent);
  box-shadow:
    0 12px 32px rgba(22, 22, 22, 0.08),
    0 0 0 1px color-mix(in srgb, var(--card-accent) 12%, transparent);
}

.tool-card--empty::part(container) {
  align-items: center;
  background: rgba(255, 255, 255, 0.55);
  border: 1.5px dashed rgba(22, 22, 22, 0.14);
  border-radius: 14px;
  display: flex;
  justify-content: center;
}

.tool-card::part(header-container) {
  text-align: left;
}

.tool-card::part(body-container) {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 13px;
  line-height: 1.5;
  text-align: left;
}

.tool-card::part(actions-container) {
  opacity: 0;
  transform: translateY(4px);
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}

.tool-card:not(.tool-card--empty):hover::part(actions-container) {
  opacity: 1;
  transform: translateY(0);
}

.card-icon-wrap {
  display: flex;
  justify-content: flex-start;
  padding: 4px 0 8px;
}

.card-icon-badge {
  align-items: center;
  background: color-mix(in srgb, var(--card-accent, #0077b8) 12%, white);
  border-radius: 12px;
  color: var(--card-accent, #0077b8);
  display: inline-flex;
  height: 48px;
  justify-content: center;
  transition: transform 0.22s ease;
  width: 48px;
}

.tool-card:not(.tool-card--empty):hover .card-icon-badge {
  transform: scale(1.06);
}

.empty-slot {
  align-items: center;
  display: flex;
  flex-direction: column;
  gap: 10px;
  justify-content: center;
  padding: 24px;
  text-align: center;
  width: 100%;
}

.empty-slot-text {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #9aa0a6);
  font-size: 13px;
  margin: 0;
}

@keyframes fade-up {
  from {
    opacity: 0;
    transform: translateY(16px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 900px) {
  .card-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 600px) {
  .page-content {
    padding: 32px 16px 96px;
  }

  .card-grid {
    grid-template-columns: 1fr;
  }

  .tool-card::part(actions-container) {
    opacity: 1;
    transform: none;
  }
}
</style>
