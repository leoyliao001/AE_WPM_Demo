<template>
  <div class="welcome-page">
    <div class="page-content">
      <header class="welcome-header">
        <h1 class="welcome-title">Welcome</h1>
        <p class="welcome-subtitle">
          Photo-background demo — choose a tool below to manage migrations, reporting, and learning.
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
          :tabindex="item.empty ? -1 : 0"
          :heading="item.empty ? undefined : item.title"
          :body="item.empty ? undefined : item.description"
          @click="onCardClick(item)"
          @keydown.enter.prevent="onCardClick(item)"
          @keydown.space.prevent="onCardClick(item)"
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
  },
  {
    id: 'coming-soon',
    empty: true
  }
]

const onCardClick = (item) => {
  if (item.empty || !item.route) return
  router.push(item.route)
}
</script>

<style scoped>
.welcome-page {
  background:
    linear-gradient(
      165deg,
      rgba(0, 42, 72, 0.5) 0%,
      rgba(0, 55, 90, 0.22) 38%,
      rgba(0, 36, 64, 0.4) 100%
    ),
    url('/sea_bridge.png') center 38% / cover no-repeat;
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
  padding: 48px 32px 120px;
  position: relative;
  z-index: 1;
}

.welcome-header {
  animation: fade-up 0.55s ease both;
  margin-bottom: 36px;
  max-width: 560px;
  padding: 4px 2px;
}

.welcome-title {
  color: #fff;
  font-family: 'Maersk Headline', 'Maersk Text', sans-serif;
  font-size: clamp(36px, 5vw, 52px);
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.1;
  margin: 0 0 12px;
  text-shadow: 0 2px 16px rgba(0, 20, 40, 0.45);
}

.welcome-subtitle {
  color: rgba(255, 255, 255, 0.9);
  font-size: 15px;
  line-height: 1.6;
  margin: 0;
  max-width: 520px;
  text-shadow: 0 1px 10px rgba(0, 20, 40, 0.4);
}

.card-grid {
  display: grid;
  gap: 22px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  perspective: 1200px;
}

.tool-card {
  --card-accent: #0077b8;
  animation: fade-up 0.55s ease both;
  animation-delay: var(--card-delay, 0ms);
  min-height: 210px;
}

.tool-card::part(container) {
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  background: rgba(255, 255, 255, 0.32);
  border-color: rgba(255, 255, 255, 0.45);
  border-radius: 14px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.55) inset,
    0 2px 3px rgba(0, 30, 60, 0.06),
    0 10px 20px rgba(0, 30, 60, 0.1),
    0 22px 44px rgba(0, 30, 60, 0.12);
  height: 100%;
  overflow: hidden;
  position: relative;
  transform-origin: center center;
  transition:
    border-color 0.28s ease,
    box-shadow 0.28s cubic-bezier(0.22, 1, 0.36, 1),
    background 0.28s ease,
    transform 0.28s cubic-bezier(0.22, 1, 0.36, 1);
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
  background: rgba(255, 255, 255, 0.48);
  border-color: color-mix(in srgb, var(--card-accent) 36%, transparent);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.7) inset,
    0 4px 8px rgba(0, 30, 60, 0.08),
    0 14px 28px rgba(0, 30, 60, 0.12),
    0 28px 56px rgba(0, 30, 60, 0.16),
    0 0 0 1px color-mix(in srgb, var(--card-accent) 14%, transparent);
  transform: translateY(-8px) scale(1.02);
}

.tool-card:not(.tool-card--empty):focus-visible {
  outline: none;
}

.tool-card:not(.tool-card--empty):focus-visible::part(container) {
  background: rgba(255, 255, 255, 0.48);
  border-color: color-mix(in srgb, var(--card-accent) 55%, transparent);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.7) inset,
    0 4px 8px rgba(0, 30, 60, 0.08),
    0 14px 28px rgba(0, 30, 60, 0.12),
    0 0 0 3px color-mix(in srgb, var(--card-accent) 35%, white);
  transform: translateY(-4px);
}

.tool-card--empty::part(container) {
  align-items: center;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.28);
  border: 1.5px dashed rgba(255, 255, 255, 0.65);
  border-radius: 14px;
  box-shadow: 0 10px 28px rgba(0, 30, 60, 0.12);
  display: flex;
  justify-content: center;
}

.empty-slot-text {
  color: rgba(255, 255, 255, 0.92);
  font-size: 13px;
  margin: 0;
  text-shadow: 0 1px 6px rgba(0, 20, 40, 0.35);
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
  border: 1px solid color-mix(in srgb, var(--card-accent, #0077b8) 16%, transparent);
  border-radius: 12px;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.75),
    0 2px 6px color-mix(in srgb, var(--card-accent, #0077b8) 18%, transparent);
  color: var(--card-accent, #0077b8);
  display: inline-flex;
  height: 48px;
  justify-content: center;
  transition:
    transform 0.28s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.28s ease;
  width: 48px;
}

.tool-card:not(.tool-card--empty):hover .card-icon-badge {
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    0 4px 12px color-mix(in srgb, var(--card-accent, #0077b8) 28%, transparent);
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

@media (prefers-reduced-motion: reduce) {
  .welcome-header,
  .tool-card {
    animation: none;
  }

  .tool-card:not(.tool-card--empty):hover::part(container),
  .tool-card:not(.tool-card--empty):focus-visible::part(container),
  .tool-card:not(.tool-card--empty):hover .card-icon-badge {
    transform: none;
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
