<template>
  <div class="welcome-page">
    <div class="page-content">
      <header class="welcome-header">
        <mc-tag appearance="info" fit="small" label="Migration Portal" />
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

      <section class="data-source-section" aria-label="Data foundation">
        <div class="connector">
          <div class="connector-line" />
          <span class="connector-node" />
          <mc-icon class="connector-arrow" icon="mi-arrow-up" size="20" />
        </div>

        <mc-card
          class="database-card"
          variant="bordered"
          fit="medium"
          heading="Project Attributes Database"
          subheading="Central data layer"
          body="All tools above read from and write to this shared attribute store — your single source of truth for project metadata."
          contentalignment="middle"
          clickable
          @click="onDatabaseClick"
        >
          <div slot="image" class="database-icon-wrap">
            <span class="database-icon-badge">
              <mc-icon icon="mi-database" size="24" />
            </span>
          </div>
          <mc-button
            slot="actions"
            appearance="primary"
            variant="filled"
            fit="small"
            label="Explore database"
            icon="mi-database"
            tabindex="-1"
          />
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
    title: 'Individual Project Dashboard',
    description: 'Opportunity assessment and milestone detail screens.',
    icon: 'mi-file-check',
    accent: '#003F6E',
    route: '/project-dashboard'
  },
  {
    id: 'future-service-model',
    title: 'Future Service Model',
    description: 'Cost, readiness, and country-level analytics for GSC transition planning.',
    icon: 'mi-chart-line-up',
    accent: '#0F766E',
    route: '/future-service-model'
  },
  {
    id: 'final-ci-review',
    title: 'Final CI Review',
    description: 'Review automation initiatives, track approvals, and capture value realisation.',
    icon: 'mi-flow',
    accent: '#5A9FD4',
    route: '/final-ci-review'
  },
  {
    id: 'fpo-mapping',
    title: 'FPO Mapping',
    description: 'Cascading L1–L4 process / FPO dictionary grid powered by Handsontable.',
    icon: 'mi-list-bullets',
    accent: '#0077B8',
    route: '/fpo-mapping'
  }
]

const onCardClick = (item) => {
  if (item.empty || !item.route) return
  router.push(item.route)
}

const onDatabaseClick = () => {
  // 预留：跳转至 Project Attributes Database
}
</script>

<style scoped>
.welcome-page {
  background: #fff;
  flex-shrink: 0;
  position: relative;
  width: 100%;
}

.page-content {
  margin: 0 auto;
  max-width: 1140px;
  padding: 56px 32px 72px;
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
  margin: 14px 0 12px;
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

.card-icon-wrap,
.database-icon-wrap {
  display: flex;
  justify-content: flex-start;
  padding: 4px 0 8px;
}

.card-icon-badge,
.database-icon-badge {
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

.data-source-section {
  align-items: center;
  display: flex;
  flex-direction: column;
  margin-top: 56px;
}

.connector {
  align-items: center;
  display: flex;
  flex-direction: column;
  height: 56px;
  margin-bottom: 8px;
  position: relative;
  width: 100%;
}

.connector-line {
  background: linear-gradient(
    180deg,
    transparent 0%,
    rgba(0, 119, 184, 0.35) 40%,
    rgba(0, 119, 184, 0.85) 100%
  );
  height: 100%;
  width: 2px;
}

.connector-node {
  background: #0077b8;
  border: 3px solid #fff;
  border-radius: 50%;
  box-shadow: 0 0 0 4px rgba(0, 119, 184, 0.15);
  height: 10px;
  position: absolute;
  top: 0;
  width: 10px;
}

.connector-arrow {
  animation: pulse-up 2s ease-in-out infinite;
  color: #0077b8;
  margin-top: -6px;
}

.database-card {
  --card-accent: #0077b8;
  animation: fade-up 0.55s ease 0.45s both;
  max-width: 520px;
  width: 100%;
}

.database-card::part(container) {
  background: linear-gradient(135deg, #0077b8 0%, #003f6e 100%);
  border: none;
  border-radius: 16px;
  box-shadow:
    0 16px 40px rgba(0, 63, 110, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.12);
  color: #fff;
  overflow: hidden;
  position: relative;
  transition:
    transform 0.22s ease,
    box-shadow 0.22s ease;
}

.database-card::part(container)::after {
  background: radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.18), transparent 55%);
  content: '';
  inset: 0;
  pointer-events: none;
  position: absolute;
}

.database-card:hover::part(container) {
  box-shadow:
    0 20px 48px rgba(0, 63, 110, 0.34),
    inset 0 1px 0 rgba(255, 255, 255, 0.12);
  transform: translateY(-2px);
}

.database-card::part(header-container),
.database-card::part(body-container) {
  color: rgba(255, 255, 255, 0.92);
  position: relative;
  text-align: center;
  z-index: 1;
}

.database-card::part(header-container) {
  font-size: 18px;
  font-weight: 600;
}

.database-card::part(body-container) {
  font-size: 13px;
  line-height: 1.55;
  opacity: 0.88;
}

.database-icon-wrap {
  justify-content: center;
  position: relative;
  z-index: 1;
}

.database-icon-badge {
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
}

.database-card::part(actions-container) {
  justify-content: center;
  position: relative;
  z-index: 1;
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

@keyframes pulse-up {
  0%,
  100% {
    opacity: 0.7;
    transform: translateY(0);
  }

  50% {
    opacity: 1;
    transform: translateY(-3px);
  }
}

@media (max-width: 900px) {
  .card-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 600px) {
  .page-content {
    padding: 32px 16px 48px;
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
