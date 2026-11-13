<template>
  <div class="welcome-page">
    <main class="welcome-scroll">
      <section class="hero-section">
        <div class="hero-copy">
          <h1 class="hero-title">WPM Pulse <span>-</span> Digital Hub</h1>
          <h2 class="hero-slogan">Right Work | Right Place | Right Ownership</h2>
          <p class="hero-description">
            From location decision to realised value, in one governed workflow
          </p>
          <div class="hero-actions">
            <button type="button" class="button button--primary" @click="go('/migration-intake')">
              Start a migration <span aria-hidden="true">&#8594;</span>
            </button>
          </div>
        </div>
        <div class="hero-image" role="img" aria-label="Colleagues collaborating around a table" />
      </section>

      <section class="hub-section" aria-labelledby="explore-heading">
        <div class="section-heading">
          <div>
            <p class="eyebrow eyebrow--dark">Explore the hub</p>
            <h2 id="explore-heading">Everything you need, in one place</h2>
          </div>
          <p class="section-note">From the location decision to stable run — plan, govern, deliver and measure every migration.</p>
        </div>

        <div class="explore-carousel">
        <div class="explore-grid">
          <article
            v-for="(card, index) in exploreCards"
            :key="card.title"
            class="explore-card"
            :class="`explore-card--${card.layout}`"
            :style="{ '--card-delay': `${index * 70}ms` }"
          >
            <div class="explore-card__visual">
              <div class="explore-card__image" :style="{ backgroundImage: `url(${card.image})` }" />
              <span class="explore-card__icon"><mc-icon :icon="card.icon" size="18" /></span>
            </div>
            <div class="explore-card__body">
              <p class="card-kicker">{{ card.kicker }}</p>
              <h3>{{ card.title }}</h3>
              <p>{{ card.description }}</p>
              <ul class="card-tags" :aria-label="`${card.title} topics`">
                <li v-for="tag in card.tags" :key="tag">{{ tag }}</li>
              </ul>
              <div class="card-actions" :class="{ 'card-actions--split': card.actions.length > 1 }">
                <RouterLink
                  v-for="action in card.actions.filter(({ route }) => route)"
                  :key="action.label"
                  class="card-link"
                  :to="action.route"
                >
                  {{ action.label }} <span aria-hidden="true">&#8594;</span>
                </RouterLink>
                <button
                  v-for="action in card.actions.filter(({ route }) => !route)"
                  :key="action.label"
                  type="button"
                  class="card-link card-link--unavailable"
                  disabled
                  :aria-label="`${action.label} (destination not available)`"
                >
                  {{ action.label }} <span aria-hidden="true">&#8594;</span>
                </button>
              </div>
            </div>
          </article>
        </div>
        </div>

        <div class="hub-principles" aria-label="WPM Pulse benefits">
          <article v-for="principle in hubPrinciples" :key="principle.title" class="hub-principle">
            <span class="hub-principle__icon" aria-hidden="true">
              <mc-icon :icon="principle.icon" size="20" />
            </span>
            <div class="hub-principle__copy">
              <h3>{{ principle.title }}</h3>
              <p>{{ principle.description }}</p>
            </div>
          </article>
        </div>
      </section>

    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import '@maersk-global/mds-components-core/mc-icon'

const router = useRouter()

const exploreCards = [
  {
    layout: 'leadership',
    kicker: 'Leadership & stakeholders',
    title: 'Leadership Hub',
    description: 'Executive dashboards to track portfolio health, migration progress, risks and KPIs in one view.',
    tags: ['Portfolio health', 'Site capacity', 'Benefits'],
    actions: [{ label: 'Open Dashboards', route: '/migration-dashboard' }],
    icon: 'mi-chart-bars-vertical',
    image: '/aefc68e4-4be4-4ebf-a3b1-38b9915c8db7.webp'
  },
  {
    layout: 'migration',
    kicker: 'Active migration teams',
    title: 'Migration Hub',
    description: 'Workspace for teams running an active migration: plans, tasks, trackers and status.',
    tags: ['Intake', 'Project plan', 'RAID', 'Readiness'],
    actions: [{ label: 'My migrations', route: '/project-dashboard' }],
    icon: 'mi-file-arrows-square',
    image: '/port-twilight.webp'
  },
  {
    layout: 'partners',
    kicker: 'MSP workspace',
    title: 'Migration Success Partners Hub',
    description: 'Workspace for MSPs to guide, support and follow up on the migrations they partner on.',
    tags: ['Focal points', 'RASCI', 'Forums'],
    actions: [{ label: 'Find a Partner', route: '/migration-success-partners' }],
    icon: 'mi-users',
    image: '/Collaboration.png'
  },
]

const hubPrinciples = [
  { title: 'One lifecycle', description: 'Consistent delivery across every migration type', icon: 'mi-file-arrows-square' },
  { title: 'One governance model', description: 'Approvals and controls built into the flow', icon: 'mi-shield-check' },
  { title: 'One source of truth', description: 'Data captured once, reused end-to-end', icon: 'mi-database' },
  { title: 'One stakeholder network', description: 'Clear ownership and accountability', icon: 'mi-users' },
  { title: 'One portfolio view', description: 'Real-time progress, risk and value', icon: 'mi-chart-bars-vertical' }
]

const go = (route) => router.push(route)
</script>

<style scoped>
.welcome-page {
  --navy: #0b2b4b;
  --blue: #0077b8;
  --cyan: #42b0d5;
  --paper: #f3f6f8;
  --line: #dfe8ed;
  --muted: #6d8193;
  background: var(--paper);
  color: #102d49;
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  width: 100%;
}

.welcome-scroll { display: flex; flex: 1 1 auto; flex-direction: column; min-height: 0; overflow-x: hidden; overflow-y: auto; padding-bottom: 0; }
.hero-section, .hub-section { margin: 0; width: 100%; }
.hero-section { background: linear-gradient(120deg, #eaf6fa 0%, #f8fcfd 50%, #edf7fa 100%); border-bottom: 1px solid var(--line); display: grid; flex-shrink: 0; grid-template-columns: minmax(0, 1.08fr) minmax(0, 1fr); min-height: clamp(290px, 33vh, 350px); }
.hero-copy { align-self: center; background: transparent; min-width: 0; padding: 32px; }
.eyebrow, .card-kicker { color: var(--blue); font-size: 10px; font-weight: 800; letter-spacing: .14em; margin: 0; text-transform: uppercase; }
.hero-title { color: var(--navy); font-family: 'Maersk Headline', 'Maersk Text', sans-serif; font-size: 40px; font-weight: 700; letter-spacing: 0; line-height: 1.15; margin: 0 0 28px; }
.hero-title span { color: inherit; }
.eyebrow span { color: var(--cyan); }
.hero-slogan { color: var(--blue); font-family: 'Maersk Headline', 'Maersk Text', sans-serif; font-size: 22px; font-weight: 700; letter-spacing: 0; line-height: 1.4; margin: 0 0 24px; text-wrap: balance; }
.hero-description { color: #60758a; font-size: 15px; line-height: 1.55; margin: 0; max-width: 460px; }
.hero-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 22px; }
.button { border: 1px solid var(--navy); border-radius: 3px; cursor: pointer; font: 700 12px 'Maersk Text', sans-serif; padding: 11px 16px; transition: transform .2s ease, box-shadow .2s ease; }
.button:hover { box-shadow: 0 5px 12px rgba(11, 43, 75, .16); transform: translateY(-2px); }
.button--primary { background: var(--navy); color: #fff; }
.button--secondary { background: #fff; color: var(--navy); }
.button span, .card-link span { margin-left: 7px; }
.hero-highlights { display: grid; gap: 14px; grid-template-columns: repeat(4, minmax(0, 1fr)); margin-top: 22px; }
.hero-highlight { color: var(--navy); display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.hero-highlight__icon { align-items: center; background: #e4f4fa; border-radius: 7px; color: var(--blue); display: flex; height: 32px; justify-content: center; width: 32px; }
.hero-highlight > span:last-child { min-width: 0; }
.hero-highlight strong, .hero-highlight small { display: block; }
.hero-highlight strong { font-size: 13px; }
.hero-highlight small { color: var(--muted); font-size: 11px; line-height: 1.45; margin-top: 4px; }
.hero-image { background: linear-gradient(110deg, rgba(11, 43, 75, .08), transparent 35%), url('/Collaboration-Hero.jpg') center 35% / cover; min-height: 0; min-width: 0; clip-path: polygon(10% 0, 100% 0, 100% 100%, 0 100%); }
.hub-section { padding: 10px 0 22px; }
.section-heading { align-items: center; display: grid; gap: 16px; grid-template-columns: minmax(220px, .8fr) minmax(280px, 1.2fr); margin-top: 22px; margin-bottom: 10px; padding: 0 clamp(24px, 2vw, 32px); }
.eyebrow--dark { color: var(--blue); }
.section-heading h2 { color: var(--navy); font-size: 23px; letter-spacing: -.01em; margin: 3px 0 0; }
.section-note { color: var(--muted); font-size: 14px; justify-self: end; line-height: 1.5; margin: 0; max-width: 470px; text-align: right; }
.explore-carousel { flex: 0 0 auto; margin-bottom: 10px; min-width: 0; padding: 0 44px; position: relative; }
.explore-grid { display: grid; gap: 12px; grid-auto-flow: row; grid-template-columns: repeat(3, minmax(0, 1fr)); grid-template-rows: minmax(290px, auto); overflow-x: auto; overscroll-behavior-inline: contain; padding: 4px 0 8px; scroll-snap-type: x proximity; scrollbar-width: none; }
.explore-grid::-webkit-scrollbar { display: none; }
.explore-card { animation: reveal .55s ease both; animation-delay: var(--card-delay); background: #fff; border: 1px solid var(--line); border-radius: 6px; box-shadow: 0 5px 14px rgba(18, 50, 75, .05); display: flex; flex-direction: column; overflow: hidden; scroll-snap-align: start; transition: box-shadow .2s ease, transform .2s ease; }
.explore-card:hover { box-shadow: 0 12px 24px rgba(18, 50, 75, .14); transform: translateY(-3px); }
.explore-card__visual { position: relative; }
.explore-card__image { background-position: center; background-size: cover; height: 96px; }
.explore-card__icon { align-items: center; background: #edf7fb; border: 4px solid #fff; border-radius: 50%; bottom: -17px; color: var(--blue); display: flex; height: 38px; justify-content: center; left: 16px; position: absolute; width: 38px; }
.explore-card__body { display: flex; flex: 1; flex-direction: column; padding: 14px 16px 8px; }
.card-kicker { font-size: 10px; letter-spacing: .08em; }
.explore-card h3 { color: var(--navy); font-size: 15px; margin: 7px 0 6px; }
.explore-card p:not(.card-kicker) { color: var(--muted); font-size: 12px; line-height: 1.45; margin: 0; min-height: 35px; }
.card-tags { display: flex; flex-wrap: wrap; gap: 5px; list-style: none; margin: 8px 0 10px; padding: 0; }
.card-tags li { background: #f4f7f9; border: 1px solid #dfe8ed; border-radius: 999px; color: #29445d; font-size: 10px; line-height: 1.4; padding: 2px 8px; white-space: nowrap; }
.card-actions { align-items: stretch; border-top: 1px solid #e6edf1; display: flex; gap: 16px; margin-top: auto; padding-top: 7px; }
.card-actions--split { gap: 10px; }
.card-link { align-items: center; background: transparent; border: 0; border-radius: 0; color: var(--navy); cursor: pointer; display: flex; flex: 1 1 0; font: 700 12px 'Maersk Text', sans-serif; justify-content: space-between; margin: 0; min-height: 44px; min-width: 0; padding: 0; text-align: left; text-decoration: none; transition: color .2s ease; }
.card-link--unavailable { color: var(--muted); cursor: not-allowed; opacity: .72; }
.card-link span { align-items: center; border: 1px solid #d6e3e9; border-radius: 50%; color: var(--blue); display: inline-flex; height: 26px; justify-content: center; transition: background .2s ease, border-color .2s ease, color .2s ease; width: 26px; }
.card-link:hover { color: var(--blue); }
.card-link:hover span { background: #eaf5fa; border-color: #b9dce9; }
.card-link:focus-visible { border-radius: 3px; outline: 3px solid color-mix(in srgb, var(--blue) 35%, white); outline-offset: 2px; }
.hub-principles { border-top: 1px solid #d6e3e9; display: grid; flex: 0 0 auto; gap: 12px; grid-template-columns: repeat(5, minmax(0, 1fr)); margin: 0 clamp(24px, 2vw, 32px); padding-top: 14px; }
.hub-principle { align-items: center; background: linear-gradient(145deg, #fff 0%, #f8fbfc 100%); border: 1px solid #e1ebef; border-radius: 10px; box-shadow: 0 3px 10px rgba(18, 50, 75, .045); display: flex; gap: 11px; min-width: 0; padding: 12px; transition: border-color .2s ease, box-shadow .2s ease, transform .2s ease; }
.hub-principle:hover { border-color: #c9e1e9; box-shadow: 0 6px 16px rgba(18, 50, 75, .09); transform: translateY(-2px); }
.hub-principle__icon { align-items: center; background: linear-gradient(145deg, #e6f5fa, #d9eef5); border: 1px solid #d8edf4; border-radius: 9px; color: var(--blue); display: flex; flex: 0 0 34px; height: 34px; justify-content: center; width: 34px; }
.hub-principle__copy { min-width: 0; }
.hub-principle h3 { color: var(--navy); font-size: 12px; line-height: 1.2; margin: 0 0 4px; }
.hub-principle p { color: #60758a; font-size: 10px; line-height: 1.35; margin: 0; }
@keyframes reveal { from { opacity: 0; } to { opacity: 1; } }
@media (min-width: 821px) {
  .explore-card--migration { grid-area: 1 / 1 / 3 / 2; }
  .explore-card--leadership { grid-area: 1 / 2 / 2 / 3; }
  .explore-card--partners { grid-area: 2 / 2 / 3 / 3; }
  .hero-section { min-height: calc(clamp(290px, 33vh, 350px) + 50px); }
  .hero-copy { padding-top: 32px; padding-bottom: 32px; }
  .hero-title { font-size: 40px; margin-bottom: 28px; }
  .hero-slogan { font-size: 22px; margin-bottom: 24px; }
  .hero-description { font-size: 15px; line-height: 1.55; }
  .hero-actions { margin-top: 22px; }
  .hero-highlights { gap: 10px; margin-top: 14px; }
  .hero-highlight { gap: 4px; }
  .hero-highlight__icon { height: 28px; width: 28px; }
  .hero-highlight small { font-size: 10px; line-height: 1.3; margin-top: 2px; }
  .hub-section { display: flex; flex: 1 0 auto; flex-direction: column; justify-content: flex-start; min-height: 0; padding-bottom: 0; }
  .section-heading { margin-bottom: 10px; }
  .explore-grid { flex: 0 0 auto; grid-template-columns: minmax(0, 1.05fr) minmax(0, .95fr); grid-template-rows: repeat(2, minmax(118px, 1fr)); height: clamp(250px, 31vh, 310px); }
  .hub-principles { margin-top: auto; margin-bottom: 24px; }
  .explore-card { display: flex; flex-direction: column; height: 100%; min-height: 0; position: relative; }
  .explore-card__visual { inset: 0; position: absolute; }
  .explore-card__image { height: 100%; inset: 0; position: absolute; width: 100%; }
  .explore-card__icon, .card-tags { display: none; }
  .explore-card__body { background: #fff; clip-path: polygon(0 0, 100% 0, 82% 100%, 0 100%); display: flex; flex: 1; flex-direction: column; justify-content: center; min-height: 0; padding: 16px 22% 16px 22px; position: relative; width: 76%; }
  .explore-card--migration .explore-card__body { padding-left: 26px; width: 68%; }
  .explore-card--leadership .explore-card__body, .explore-card--partners .explore-card__body { padding: 10px 24% 10px 18px; width: 78%; }
  .explore-card .card-kicker { font-size: 9px; letter-spacing: .1em; }
  .explore-card h3 { font-size: 17px; line-height: 1.2; margin: 3px 0 5px; }
  .explore-card--migration h3 { font-size: 27px; line-height: 1.12; }
  .explore-card p:not(.card-kicker) { font-size: 12px; line-height: 1.42; min-height: 0; }
  .explore-card--migration p:not(.card-kicker) { font-size: 13px; line-height: 1.45; }
  .card-actions { align-self: flex-start; border: 0; margin-top: 9px; padding: 0; }
  .card-link { background: var(--navy); border-radius: 999px; color: #fff; flex: 0 0 auto; justify-content: center; min-height: 34px; padding: 0 18px; }
  .card-link span { display: none; }
  .card-link:hover { background: var(--blue); color: #fff; }
  .explore-card--leadership .card-link, .explore-card--partners .card-link { min-height: 30px; }
}
@media (prefers-reduced-motion: reduce) { .explore-card { animation: none; } .button:hover, .explore-card:hover { transform: none; } }
@media (max-width: 820px) { .hero-section { grid-template-columns: 1fr; } .hero-copy { padding: 40px 24px 34px; } .hero-image { clip-path: none; min-height: 230px; } .hero-highlights { gap: 14px 20px; } .explore-grid { grid-auto-columns: min(340px, calc(100vw - 104px)); grid-auto-flow: column; grid-template-columns: none; grid-template-rows: minmax(290px, auto); } .section-heading { align-items: start; grid-template-columns: 1fr; } .section-note { text-align: left; } }
@media (max-width: 820px) { .hub-principles { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (min-width: 821px) and (max-width: 1100px) { .hero-title { font-size: 32px; } .hero-slogan { font-size: 18px; } }
@media (max-width: 520px) { .hero-title { font-size: 28px; } .hero-slogan { font-size: 18px; margin-left: 0; } .hero-highlights { grid-template-columns: repeat(2, minmax(0, 1fr)); } .hub-principles { grid-template-columns: 1fr; } }
@media (min-width: 821px) and (max-height: 850px) {
  .hero-section { min-height: 280px; }
  .hero-copy { padding: 28px 24px; }
  .hero-title { font-size: 34px; line-height: 1.15; margin-bottom: 24px; }
  .hero-slogan { font-size: 20px; line-height: 1.4; margin-bottom: 20px; }
  .hero-description { font-size: 14px; line-height: 1.5; }
  .hero-actions { margin-top: 18px; }
  .button { padding: 8px 12px; }
  .hero-highlights { gap: 8px; margin-top: 10px; }
  .hero-highlight { gap: 4px; }
  .hero-highlight__icon { height: 26px; width: 26px; }
  .hero-highlight strong { font-size: 11px; }
  .hero-highlight small { font-size: 9px; line-height: 1.25; margin-top: 2px; }
  .hub-section { padding: 4px 0 0; }
  .section-heading { margin-bottom: 10px; }
  .section-heading h2 { font-size: 20px; line-height: 1.15; margin-top: 3px; }
  .section-note { font-size: 12px; line-height: 1.35; }
  .explore-grid { grid-template-rows: repeat(2, minmax(0, 1fr)); gap: 8px; padding-bottom: 8px; }
  .explore-card__icon { height: 32px; width: 32px; }
  .explore-card__body { padding: 8px 12px 7px; }
  .card-kicker { font-size: 8px; }
  .explore-card h3 { font-size: 14px; line-height: 1.2; margin: 3px 0 4px; }
  .explore-card--migration h3 { font-size: 23px; }
  .explore-card--leadership h3, .explore-card--partners h3 { font-size: 13px; }
  .explore-card p:not(.card-kicker) { font-size: 10px; line-height: 1.35; min-height: 0; }
  .card-tags { gap: 3px; margin: 4px 0 5px; }
  .card-tags li { font-size: 8px; padding: 1px 6px; }
  .card-actions { padding-top: 3px; }
  .card-link { font-size: 10px; min-height: 32px; }
  .card-link span { height: 22px; width: 22px; }
  .hub-principles { margin-top: auto; }
  .hub-principles { gap: 8px; }
  .hub-principle { gap: 8px; padding: 9px; }
  .hub-principle__icon { flex-basis: 28px; height: 28px; width: 28px; }
  .hub-principle h3 { font-size: 11px; line-height: 1.15; margin: 0 0 3px; }
  .hub-principle p { font-size: 9px; line-height: 1.2; }
}
@media (min-width: 821px) and (max-height: 700px) {
  .hero-section { min-height: 240px; }
  .hero-copy { padding-top: 24px; padding-bottom: 24px; }
  .hero-title { font-size: 32px; margin-bottom: 20px; }
  .hero-slogan { font-size: 18px; line-height: 1.35; margin-bottom: 16px; }
  .hero-description { font-size: 13px; line-height: 1.45; }
  .hero-actions { margin-top: 16px; }
  .button { padding: 6px 10px; }
  .hero-highlights { gap: 6px; margin-top: 7px; }
  .hero-highlight { gap: 2px; }
  .hero-highlight__icon { height: 22px; width: 22px; }
  .hero-highlight strong { font-size: 10px; }
  .hero-highlight small { font-size: 8px; line-height: 1.15; margin-top: 1px; }
  .hub-section { padding: 4px 0 0; }
  .section-heading { margin-bottom: 6px; }
  .eyebrow--dark { font-size: 8px; }
  .section-heading h2 { font-size: 18px; margin-top: 2px; }
  .section-note { font-size: 10px; line-height: 1.25; }
  .explore-grid { grid-template-rows: repeat(2, minmax(0, 1fr)); gap: 6px; padding-bottom: 6px; }
  .explore-card__icon { height: 28px; width: 28px; }
  .explore-card__body { padding: 6px 9px 5px; }
  .card-kicker { font-size: 7px; }
  .explore-card h3 { font-size: 12px; line-height: 1.2; margin: 3px 0; }
  .explore-card--migration h3 { font-size: 21px; }
  .explore-card--leadership h3, .explore-card--partners h3 { font-size: 12px; }
  .explore-card p:not(.card-kicker) { font-size: 9px; line-height: 1.25; min-height: 0; }
  .card-tags { gap: 2px; margin: 3px 0 4px; }
  .card-tags li { font-size: 7px; padding: 1px 4px; }
  .card-actions { padding-top: 2px; }
  .card-link { font-size: 10px; min-height: 34px; }
  .card-link span { height: 18px; width: 18px; }
  .hub-principles { margin-top: auto; }
  .hub-principle { gap: 8px; padding: 8px; }
  .hub-principle__icon { flex-basis: 26px; height: 26px; width: 26px; }
  .hub-principle h3 { font-size: 10px; line-height: 1.15; margin: 0 0 2px; }
  .hub-principle p { font-size: 9px; line-height: 1.2; }
}
</style>
