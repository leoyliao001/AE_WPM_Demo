<template>
  <div class="welcome-page">
    <div class="welcome-scroll">
      <div class="welcome-layout">
        <aside class="welcome-aside">
          <section class="principles-panel" aria-label="Work Placement Principles">
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
          </section>
        </aside>

        <div class="page-content">
          <section class="brand-lockup" aria-label="WPM Pulse">
            <PulseLogo :size="52" />
            <div class="brand-lockup__text">
              <p class="brand-lockup__wordmark">WPM <span>Pulse</span></p>
              <p class="brand-lockup__eyebrow">Workplace Migration Platform</p>
            </div>
          </section>

          <header class="workspace-head">
            <div class="workspace-head__text">
              <h2 class="workspace-head__title">Choose a workspace</h2>
              <p class="workspace-head__sub">{{ workspaceCards.length + 1 }} entry points into the platform</p>
            </div>
            <div class="status-pill">
              <span class="status-pill__dot" aria-hidden="true" />
              <div>
                <p class="status-pill__title">All systems operational</p>
                <p class="status-pill__meta">Last refresh: {{ lastRefresh }}</p>
              </div>
            </div>
          </header>

          <div class="workspace-grid">
            <article
              v-for="(card, index) in workspaceCards"
              :key="card.id"
              class="ws-card"
              :style="{ '--accent': card.accent, '--card-delay': `${index * 70}ms` }"
            >
              <span class="ws-card__icon">
                <mc-icon :icon="card.icon" size="24" />
              </span>
              <div class="ws-card__body">
                <p class="ws-card__eyebrow">{{ card.eyebrow }}</p>
                <h3 class="ws-card__title">{{ card.title }}</h3>
                <p class="ws-card__desc">{{ card.description }}</p>
              </div>
              <div class="ws-card__actions">
                <button
                  v-for="action in card.actions"
                  :key="action.label"
                  type="button"
                  class="ws-action"
                  :class="`ws-action--${action.variant || 'solid'}`"
                  :disabled="!action.route"
                  :title="action.route ? undefined : 'Coming soon'"
                  @click="go(action.route)"
                >
                  {{ action.label }}
                </button>
              </div>
            </article>

            <article class="ws-card ws-card--wide" :style="{ '--accent': msp.accent }">
              <span class="ws-card__icon">
                <mc-icon :icon="msp.icon" size="24" />
              </span>
              <div class="ws-card__body">
                <p class="ws-card__eyebrow">{{ msp.eyebrow }}</p>
                <h3 class="ws-card__title">{{ msp.title }}</h3>
                <p class="ws-card__desc">{{ msp.description }}</p>
              </div>
              <div class="ws-card__partners">
                <p class="ws-card__partners-label">Select partner</p>
                <div class="ws-card__actions">
                  <button
                    v-for="partner in msp.partners"
                    :key="partner.label"
                    type="button"
                    class="ws-action ws-action--solid"
                    :disabled="!partner.route"
                    :title="partner.route ? undefined : 'Coming soon'"
                    @click="go(partner.route)"
                  >
                    {{ partner.label }}
                  </button>
                </div>
                <p class="ws-card__partners-hint">Opens that partner's dedicated dashboard</p>
              </div>
            </article>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import '@maersk-global/mds-components-core/mc-icon'
import PulseLogo from '../components/PulseLogo.vue'

const router = useRouter()

const lastRefresh = computed(() =>
  `today, ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })}`
)

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

const workspaceCards = [
  {
    id: 'executive-view',
    eyebrow: 'Portfolio dashboards',
    title: 'Executive View',
    description: 'Enterprise-level RAG, completion and artefact health across every migration.',
    icon: 'mi-chart-bars-vertical',
    accent: '#42B0D5',
    actions: [{ label: 'Open dashboards', route: '/migration-dashboard' }]
  },
  {
    id: 'wpm-workspace',
    eyebrow: 'Dashboards, portfolio & programme',
    title: 'WPM',
    description:
      'Workplace migration dashboards and management, plus drill-down into any individual project portfolio or programme.',
    icon: 'mi-flag',
    accent: '#0077B8',
    actions: [{ label: 'Open WPM workspace', route: '/toll-gates' }]
  },
  {
    id: 'migration-hub',
    eyebrow: 'Track or start a migration',
    title: 'Migration Hub',
    description: 'Check the status of your active migrations, or raise a new migration request.',
    icon: 'mi-arrow-right',
    accent: '#F3880E',
    actions: [
      { label: 'New migration', route: '/migration-intake' },
      { label: 'My migrations', route: '/project-dashboard', variant: 'outline' }
    ]
  },
  {
    id: 'pulse-assistant',
    eyebrow: 'Migration chatbot',
    title: 'Pulse Assistant',
    description: 'Ask anything about process, artefacts or your project status — answered instantly.',
    icon: 'mi-chatbot',
    accent: '#12857D',
    actions: [{ label: 'Start chat', route: '/migration-chatbot' }]
  }
]

const msp = {
  eyebrow: 'Migration success partners',
  title: 'MSP',
  description: 'Select your dedicated view.',
  icon: 'mi-people',
  accent: '#003F6E',
  partners: [
    { label: 'L&D', route: '/ld-dashboard' },
    { label: 'S&R', route: '' },
    { label: 'TAA', route: '' }
  ]
}

const go = (route) => {
  if (!route) return
  router.push(route)
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
  gap: 28px;
  margin: 0 auto;
  max-width: 1560px;
  padding: 32px 24px 40px;
  width: 100%;
}

.welcome-aside {
  display: flex;
  flex: 0 0 440px;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}

.brand-lockup {
  align-items: center;
  animation: fade-up 0.55s ease both;
  background: linear-gradient(120deg, #0b2b47 0%, #143c60 60%, #0d2c49 100%);
  border-radius: 14px;
  box-shadow: 0 2px 4px rgba(9, 30, 51, 0.16), 0 12px 28px rgba(9, 30, 51, 0.18);
  display: flex;
  gap: 16px;
  margin-bottom: 22px;
  padding: 18px 24px;
}

.brand-lockup__text {
  min-width: 0;
}

.brand-lockup__wordmark {
  color: #fff;
  font-family: 'Maersk Headline', 'Maersk Text', sans-serif;
  font-size: 30px;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.1;
  margin: 0;
}

.brand-lockup__wordmark span {
  color: #5cc9ec;
}

.brand-lockup__eyebrow {
  color: rgba(255, 255, 255, 0.68);
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.16em;
  margin: 5px 0 0;
  text-transform: uppercase;
}

.principles-panel {
  animation: fade-up 0.55s ease both;
  background-color: #0b2b47;
  background-image: url('/Collaboration.png');
  background-position: center;
  background-size: cover;
  border-radius: 16px;
  box-shadow:
    0 2px 4px rgba(9, 30, 51, 0.18),
    0 18px 40px rgba(9, 30, 51, 0.22);
  display: flex;
  flex-direction: column;
  isolation: isolate;
  overflow: hidden;
  padding: 28px 26px;
  position: relative;
}

.principles-panel::before {
  background: linear-gradient(165deg, rgba(8, 27, 45, 0.86) 0%, rgba(10, 34, 56, 0.8) 45%, rgba(8, 27, 45, 0.9) 100%);
  content: '';
  inset: 0;
  position: absolute;
  z-index: -1;
}

.principles-panel__head {
  align-items: center;
  display: flex;
  gap: 14px;
  margin-bottom: 20px;
}

.principles-panel__badge {
  align-items: center;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.28);
  border-radius: 12px;
  color: #7fd6f2;
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
  color: #7fd6f2;
  display: block;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.principles-panel__count {
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  line-height: 1.3;
  margin: 2px 0 0;
}

.principles-list {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  gap: 4px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.principle-card {
  --card-accent: #0077b8;
  align-items: flex-start;
  background: transparent;
  border: none;
  border-radius: 10px;
  box-shadow: none;
  display: flex;
  gap: 14px;
  padding: 12px 12px 12px 16px;
  position: relative;
  transition: background 0.2s ease;
}

.principle-card::before {
  background: var(--card-accent);
  border-radius: 999px;
  content: '';
  height: calc(100% - 20px);
  left: 0;
  position: absolute;
  top: 10px;
  width: 3px;
}

.principle-card:hover {
  background: rgba(255, 255, 255, 0.08);
}

.principle-card__number {
  align-items: center;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid color-mix(in srgb, var(--card-accent) 55%, transparent);
  border-radius: 999px;
  color: #fff;
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
  color: color-mix(in srgb, var(--card-accent) 55%, white);
  display: block;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.principle-card__title {
  color: #fff;
  font-size: 14.5px;
  font-weight: 700;
  line-height: 1.3;
  margin: 3px 0 4px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.35);
}

.principle-card__desc {
  color: rgba(255, 255, 255, 0.76);
  font-size: 12.5px;
  line-height: 1.55;
  margin: 0;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.35);
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

.workspace-head {
  align-items: flex-start;
  animation: fade-up 0.55s ease both;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  justify-content: space-between;
  margin-bottom: 22px;
}

.workspace-head__title {
  color: #161616;
  font-family: 'Maersk Headline', 'Maersk Text', sans-serif;
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin: 0;
}

.workspace-head__sub {
  color: #6c757d;
  font-size: 13.5px;
  margin: 6px 0 0;
}

.status-pill {
  align-items: center;
  background: #fff;
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 12px;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.06);
  display: flex;
  gap: 10px;
  padding: 10px 16px;
}

.status-pill__dot {
  background: #17a34a;
  border-radius: 999px;
  box-shadow: 0 0 0 3px rgba(23, 163, 74, 0.16);
  flex-shrink: 0;
  height: 9px;
  width: 9px;
}

.status-pill__title {
  color: #161616;
  font-size: 12.5px;
  font-weight: 700;
  margin: 0;
}

.status-pill__meta {
  color: #8a9099;
  font-size: 11.5px;
  margin: 2px 0 0;
}

.workspace-grid {
  display: grid;
  gap: 20px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  width: 100%;
}

.ws-card {
  --accent: #0077b8;
  animation: fade-up 0.55s ease both;
  animation-delay: var(--card-delay, 0ms);
  background: #fff;
  border: 1px solid rgba(22, 22, 22, 0.07);
  border-left: 4px solid var(--accent);
  border-radius: 12px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 2px 4px rgba(15, 23, 42, 0.05),
    0 10px 24px rgba(15, 23, 42, 0.07);
  display: grid;
  gap: 4px 16px;
  grid-template-columns: auto 1fr;
  padding: 22px 24px;
  transition: box-shadow 0.25s ease, transform 0.25s ease;
}

.ws-card:hover {
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 6px 14px rgba(15, 23, 42, 0.08),
    0 20px 40px rgba(0, 63, 110, 0.14);
  transform: translateY(-3px);
}

.ws-card--wide {
  align-items: center;
  grid-column: 1 / -1;
  grid-template-columns: auto minmax(0, 1fr) auto;
}

.ws-card__icon {
  align-items: center;
  background: color-mix(in srgb, var(--accent) 12%, white);
  border-radius: 10px;
  color: var(--accent);
  display: inline-flex;
  grid-row: span 2;
  height: 44px;
  justify-content: center;
  width: 44px;
}

.ws-card__body {
  min-width: 0;
}

.ws-card__eyebrow {
  color: var(--accent);
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.1em;
  margin: 0;
  text-transform: uppercase;
}

.ws-card__title {
  color: #161616;
  font-family: 'Maersk Headline', 'Maersk Text', sans-serif;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.01em;
  margin: 4px 0 8px;
}

.ws-card__desc {
  border-bottom: 1px solid rgba(22, 22, 22, 0.08);
  color: #6c757d;
  font-size: 13px;
  line-height: 1.55;
  margin: 0;
  padding-bottom: 14px;
}

.ws-card--wide .ws-card__desc {
  border-bottom: none;
  padding-bottom: 0;
}

.ws-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  grid-column: 2;
  padding-top: 14px;
}

.ws-card--wide .ws-card__actions {
  grid-column: auto;
  padding-top: 0;
}

.ws-card__partners {
  text-align: right;
}

.ws-card__partners-label {
  color: #161616;
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.1em;
  margin: 0 0 10px;
  text-transform: uppercase;
}

.ws-card__partners-hint {
  color: #9aa0a6;
  font-size: 11.5px;
  margin: 10px 0 0;
}

.ws-action {
  background: var(--accent);
  border: 1px solid var(--accent);
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
  font-family: inherit;
  font-size: 13px;
  font-weight: 600;
  min-width: 74px;
  padding: 9px 18px;
  transition: filter 0.2s ease, background 0.2s ease;
}

.ws-action:hover:not(:disabled) {
  filter: brightness(1.08);
}

.ws-action:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--accent) 35%, white);
  outline-offset: 1px;
}

.ws-action--outline {
  background: #fff;
  color: var(--accent);
}

.ws-action--outline:hover:not(:disabled) {
  background: color-mix(in srgb, var(--accent) 8%, white);
  filter: none;
}

.ws-action:disabled {
  background: #f2f4f6;
  border-color: rgba(22, 22, 22, 0.1);
  color: #9aa0a6;
  cursor: not-allowed;
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
  .brand-lockup,
  .principles-panel,
  .workspace-head,
  .ws-card {
    animation: none;
  }

  .ws-card:hover {
    transform: none;
  }
}

@media (max-width: 1240px) {
  .welcome-layout {
    flex-direction: column;
  }

  .welcome-aside {
    flex-basis: auto;
    width: 100%;
  }
}

@media (max-width: 900px) {
  .workspace-grid {
    grid-template-columns: 1fr;
  }

  .ws-card--wide {
    grid-template-columns: auto 1fr;
  }

  .ws-card__partners {
    grid-column: 1 / -1;
    padding-top: 14px;
    text-align: left;
  }
}

@media (max-width: 760px) {
  .welcome-layout {
    padding: 24px 16px 32px;
  }
}
</style>
