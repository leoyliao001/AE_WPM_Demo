<template>
  <div class="welcome-page">
    <div class="welcome-scroll">
      <div class="welcome-layout">
        <aside class="principles-panel" aria-label="Work Placement Principles">
          <div class="principles-panel__head">
            <span class="principles-panel__badge">
              <mc-icon icon="mi-light-bulb" size="22" />
            </span>
            <div class="principles-panel__head-text">
              <span class="principles-panel__eyebrow">Principles</span>
              <h2 class="principles-panel__count">5 Work Placement Principles</h2>
            </div>
          </div>

          <ol class="principles-list">
            <li
              v-for="principle in principles"
              :key="principle.number"
              class="principle-card"
              :style="{ '--card-accent': principle.accent }"
            >
              <span class="principle-card__number">{{ principle.number }}</span>
              <div class="principle-card__body">
                <span class="principle-card__eyebrow">Principle {{ principle.number }}</span>
                <h3 class="principle-card__title">{{ principle.title }}</h3>
                <p class="principle-card__desc">{{ principle.description }}</p>
              </div>
            </li>
          </ol>
        </aside>

        <div class="page-content">
        <header class="welcome-header">
          <h1 class="welcome-title">WPM Pulse</h1>
          <p class="welcome-subtitle">
            Welcome — your home for GSC migration governance, from intake and
            opportunity assessment through approvals, Gantt scheduling, and toll-gate
            tracking, all powered by a shared project database.
          </p>
        </header>

        <section
          v-for="group in menuGroups"
          :key="group.id"
          class="tool-group"
          :aria-label="group.title"
        >
          <h2 class="tool-group__title">
            <mc-icon :icon="group.icon" size="18" />
            {{ group.title }}
          </h2>

          <div class="card-grid">
            <mc-card
              v-for="(item, index) in group.items"
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
              @click="onCardClick(item)"
              @keydown.enter.prevent="onCardClick(item)"
              @keydown.space.prevent="onCardClick(item)"
            >
              <template v-if="!item.empty">
                <div slot="image" class="card-icon-wrap">
                  <span class="card-icon-badge">
                    <mc-icon :icon="item.icon" size="20" />
                  </span>
                </div>
                <p class="card-description">{{ item.description }}</p>
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
          </div>
        </section>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import '@maersk-global/mds-components-core/mc-card'
import '@maersk-global/mds-components-core/mc-icon'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-tag'

const router = useRouter()

const principles = [
  {
    number: 1,
    title: 'Standardization',
    description: 'Enable standardization, avoid business disruption & consistently improve customer outcomes.',
    accent: '#0077B8'
  },
  {
    number: 2,
    title: 'Scaling',
    description: 'Scale the process and minimize GSC/Area handovers to ensure clear process ownership.',
    accent: '#6DAA28'
  },
  {
    number: 3,
    title: 'Health Metrics',
    description: 'Perform better on enterprise health metrics and control environment.',
    accent: '#42B0D5'
  },
  {
    number: 4,
    title: 'Stakeholder',
    description: 'Reduce need for in-person external stakeholder interactions.',
    accent: '#F3880E'
  },
  {
    number: 5,
    title: 'Cost Reduction',
    description: 'Reduce cost to serve leading to positive P&L impact.',
    accent: '#003F6E'
  }
]

const menuItems = [
  {
    id: 'migration-request',
    title: 'Raise a Migration Request',
    description: 'Submit migration intake details to the Project Attributes Database.',
    icon: 'mi-file-arrows-square',
    accent: '#0077B8',
    route: '/migration-intake',
    section: 'primary'
  },
  {
    id: 'migration-chatbot',
    title: 'Migration Chatbot',
    description: 'Get instant answers and guided migration support.',
    icon: 'mi-chatbot',
    accent: '#6DAA28',
    route: '/migration-chatbot',
    section: 'primary'
  },
  {
    id: 'migration-dashboard',
    title: 'Migration Dashboard',
    description: 'Product summary and detailed migration tracking overview.',
    icon: 'mi-chart-bars-vertical',
    accent: '#42B0D5',
    route: '/migration-dashboard',
    section: 'primary'
  },
  {
    id: 'ld-dashboard',
    title: 'L&D Dashboard',
    description: 'Learning, scoping tasks, and training timeline by project.',
    icon: 'mi-monitor',
    accent: '#F3880E',
    route: '/ld-dashboard',
    section: 'learning'
  },
  {
    id: 'project-dashboard',
    title: 'My Projects',
    description: 'Projects under your account — open a project to track migration progress.',
    icon: 'mi-file-check',
    accent: '#003F6E',
    route: '/project-dashboard',
    section: 'learning'
  },
  {
    id: 'toll-gates',
    title: 'Toll Gates',
    description: 'Migration lifecycle grouped into Initiating, Planning, Executing, Monitor & Control, and Closing.',
    icon: 'mi-flag',
    accent: '#7B61FF',
    route: '/toll-gates',
    section: 'learning'
  }
]

const menuGroups = computed(() => [
  {
    id: 'primary',
    title: 'Primary Tools',
    icon: 'mi-star',
    items: menuItems.filter((item) => item.section === 'primary')
  },
  {
    id: 'learning',
    title: 'Learning & Management',
    icon: 'mi-book-open',
    items: menuItems.filter((item) => item.section === 'learning')
  }
])

const onCardClick = (item) => {
  if (item.empty || !item.route) return
  router.push(item.route)
}
</script>

<style scoped>
.welcome-page {
  --mb: #42b0d5;
  --mm: #0077b8;
  --md: #003f6e;
  background: #fff;
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  isolation: isolate;
  min-height: 0;
  overflow: hidden;
  position: relative;
  width: 100%;
}

.welcome-scroll {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  justify-content: safe center;
  min-height: 0;
  overflow-x: clip;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-y: contain;
  position: relative;
  z-index: 1;
}

.welcome-layout {
  align-items: stretch;
  display: flex;
  gap: 24px;
  margin: 0 auto;
  padding: 40px 24px;
  transform: translateY(-24px);
  width: 100%;
}

.principles-panel {
  animation: fade-up 0.55s ease both;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96) 0%, rgba(251, 252, 253, 0.94) 100%);
  border: 1px solid rgba(22, 22, 22, 0.07);
  border-radius: 16px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 2px 3px rgba(15, 23, 42, 0.05),
    0 10px 22px rgba(15, 23, 42, 0.06);
  display: flex;
  flex: 0 0 296px;
  flex-direction: column;
  padding: 22px;
}

.principles-panel__head {
  align-items: center;
  display: flex;
  gap: 14px;
  margin-bottom: 20px;
}

.principles-panel__badge {
  align-items: center;
  background: color-mix(in srgb, #0077b8 12%, white);
  border: 1px solid color-mix(in srgb, #0077b8 16%, transparent);
  border-radius: 12px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.75);
  color: #0077b8;
  display: inline-flex;
  flex-shrink: 0;
  height: 44px;
  justify-content: center;
  width: 44px;
}

.principles-panel__head-text {
  min-width: 0;
}

.principles-panel__eyebrow {
  color: #0077b8;
  display: block;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.principles-panel__count {
  color: #161616;
  font-size: 15px;
  font-weight: 700;
  line-height: 1.3;
  margin: 2px 0 0;
}

.principles-list {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  gap: 10px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.principle-card {
  --card-accent: #0077b8;
  align-items: flex-start;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96) 0%, rgba(251, 252, 253, 0.94) 100%);
  border: 1px solid rgba(22, 22, 22, 0.06);
  border-radius: 12px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 2px 3px rgba(15, 23, 42, 0.04),
    0 6px 14px rgba(15, 23, 42, 0.05);
  display: flex;
  gap: 12px;
  overflow: hidden;
  padding: 14px 14px 14px 16px;
  position: relative;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.principle-card::before {
  background: var(--card-accent);
  content: '';
  height: 100%;
  left: 0;
  position: absolute;
  top: 0;
  width: 3px;
}

.principle-card:hover {
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 4px 8px rgba(15, 23, 42, 0.06),
    0 12px 22px rgba(15, 23, 42, 0.08);
  transform: translateY(-2px);
}

.principle-card__number {
  align-items: center;
  background: color-mix(in srgb, var(--card-accent) 12%, white);
  border: 1px solid color-mix(in srgb, var(--card-accent) 20%, transparent);
  border-radius: 999px;
  color: var(--card-accent);
  display: flex;
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 700;
  height: 26px;
  justify-content: center;
  width: 26px;
}

.principle-card__body {
  min-width: 0;
}

.principle-card__eyebrow {
  color: var(--card-accent);
  display: block;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.principle-card__title {
  color: #161616;
  font-size: 14px;
  font-weight: 700;
  line-height: 1.3;
  margin: 3px 0 4px;
}

.principle-card__desc {
  color: #6c757d;
  font-size: 12.5px;
  line-height: 1.55;
  margin: 0;
}

.page-content {
  flex: 1 1 auto;
  margin: 0;
  max-width: none;
  min-width: 0;
  padding: 0;
  position: relative;
  width: 100%;
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
  column-gap: 20px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  perspective: 1200px;
  row-gap: 20px;
  width: 100%;
}

.tool-group {
  margin-bottom: 32px;
}

.tool-group:last-child {
  margin-bottom: 0;
}

.tool-group__title {
  align-items: center;
  color: #161616;
  display: flex;
  font-size: 15px;
  font-weight: 700;
  gap: 8px;
  margin: 0 0 16px;
}

.tool-card {
  --card-accent: #0077b8;
  animation: fade-up 0.55s ease both;
  animation-delay: var(--card-delay, 0ms);
  min-height: 190px;
  width: 100%;
}

.tool-card::part(container) {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94) 0%, rgba(251, 252, 253, 0.92) 100%);
  border-color: rgba(22, 22, 22, 0.08);
  border-radius: 14px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 2px 3px rgba(15, 23, 42, 0.05),
    0 10px 22px rgba(15, 23, 42, 0.08),
    0 22px 44px rgba(0, 63, 110, 0.12),
    0 28px 56px -12px rgba(0, 63, 110, 0.14);
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
  background: #fff;
  border-color: color-mix(in srgb, var(--card-accent) 36%, transparent);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 4px 8px rgba(15, 23, 42, 0.06),
    0 14px 28px rgba(15, 23, 42, 0.1),
    0 28px 56px rgba(0, 63, 110, 0.16),
    0 40px 72px -16px rgba(0, 63, 110, 0.18),
    0 0 0 1px color-mix(in srgb, var(--card-accent) 14%, transparent);
  transform: translateY(-8px) scale(1.02);
}

.tool-card:not(.tool-card--empty):focus-visible {
  outline: none;
}

.tool-card:not(.tool-card--empty):focus-visible::part(container) {
  border-color: color-mix(in srgb, var(--card-accent) 55%, transparent);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 4px 8px rgba(15, 23, 42, 0.06),
    0 14px 28px rgba(15, 23, 42, 0.1),
    0 0 0 3px color-mix(in srgb, var(--card-accent) 35%, white);
  transform: translateY(-4px);
}

.tool-card--empty::part(container) {
  align-items: center;
  background: rgba(255, 255, 255, 0.55);
  border: 1.5px dashed rgba(22, 22, 22, 0.14);
  border-radius: 14px;
  box-shadow: none;
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

.card-description {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 13px;
  line-height: 1.5;
  margin: 0;
  text-align: left;
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
  border-radius: 10px;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.75),
    0 2px 6px color-mix(in srgb, var(--card-accent, #0077b8) 18%, transparent);
  color: var(--card-accent, #0077b8);
  display: inline-flex;
  height: 40px;
  justify-content: center;
  transition:
    transform 0.28s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.28s ease;
  width: 40px;
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

@media (max-width: 1100px) {
  .welcome-layout {
    flex-direction: column;
  }

  .principles-panel {
    flex-basis: auto;
    width: 100%;
  }

  .card-grid {
    column-gap: 28px;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .welcome-layout {
    padding: 32px 16px;
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
