<template>
  <div class="welcome-page">
    <main class="welcome-scroll">
      <section class="hero-section">
        <div class="hero-copy">
          <p class="eyebrow">WPM PULSE <span>-</span> DIGITAL HUB</p>
          <h1>Moving work.<br />Moving forward.<br />Together.</h1>
          <p class="hero-description">
            The global home for the migration lifecycle - from location decision to stable run.
          </p>
          <div class="hero-actions">
            <button type="button" class="button button--primary" @click="go('/migration-intake')">
              Start a migration <span aria-hidden="true">&#8594;</span>
            </button>
          </div>
          <div class="hero-highlights" aria-label="WPM Pulse benefits">
            <div v-for="highlight in heroHighlights" :key="highlight.title" class="hero-highlight">
              <span class="hero-highlight__icon"><mc-icon :icon="highlight.icon" size="17" /></span>
              <span>
                <strong>{{ highlight.title }}</strong>
                <small>{{ highlight.description }}</small>
              </span>
            </div>
          </div>
        </div>
        <div class="hero-image" role="img" aria-label="Colleagues collaborating around a table" />
      </section>

      <section class="hub-section" aria-labelledby="explore-heading">
        <div class="section-heading">
          <div>
            <p class="eyebrow eyebrow--dark">WPM PULSE</p>
            <h2 id="explore-heading">Explore the hub</h2>
          </div>
          <p class="section-note">Everything you need to make workplace migration simpler, clearer and more connected.</p>
        </div>

        <div class="explore-grid">
          <article
            v-for="(card, index) in exploreCards"
            :key="card.title"
            class="explore-card"
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
              <div class="card-actions" :class="{ 'card-actions--split': card.actions.length > 1 }">
                <button
                  v-for="action in card.actions"
                  :key="action.label"
                  type="button"
                  class="card-link"
                  @click="go(action.route)"
                >
                  {{ action.label }} <span aria-hidden="true">&#8594;</span>
                </button>
              </div>
            </div>
          </article>
        </div>

        <div class="quick-links" aria-label="More WPM Pulse resources">
          <button
            v-for="link in quickLinks"
            :key="link.title"
            type="button"
            class="quick-link"
            :class="{ 'quick-link--inactive': !link.route }"
            @click="link.route && go(link.route)"
          >
            <span class="quick-link__icon"><mc-icon :icon="link.icon" size="20" /></span>
            <span>
              <strong>{{ link.title }}</strong>
              <small>{{ link.description }}</small>
            </span>
            <span v-if="link.route" class="quick-link__arrow" aria-hidden="true">&#8594;</span>
          </button>
        </div>
      </section>

    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import '@maersk-global/mds-components-core/mc-icon'

const router = useRouter()

const heroHighlights = [
  { icon: 'mi-globe', title: 'Global visibility', description: 'One place for every migration' },
  { icon: 'mi-users', title: 'Better collaboration', description: 'Connect teams and partners' },
  { icon: 'mi-chart-bars-vertical', title: 'Confident decisions', description: 'From data to impact' }
]

const exploreCards = [
  {
    kicker: 'Track your migrations',
    title: 'Migration Hub',
    description: 'Track your active migrations and review their progress.',
    actions: [{ label: 'My migrations', route: '/project-dashboard' }],
    icon: 'mi-file-arrows-square',
    image: '/port-twilight.webp'
  },
  {
    kicker: 'Dashboards and insight',
    title: 'Portfolio & Dashboards',
    description: 'Enterprise view of every migration, programme and project.',
    actions: [{ label: 'Open', route: '/migration-dashboard' }],
    icon: 'mi-chart-bars-vertical',
    image: '/aefc68e4-4be4-4ebf-a3b1-38b9915c8db7.webp'
  },
  {
    kicker: 'GSC locations and guardrails',
    title: 'Location Strategy',
    description: 'Make confident placement decisions with clear location insight.',
    actions: [{ label: 'Open', route: '/gsc-site-mapping' }],
    icon: 'mi-map',
    image: '/c05f31e9-c833-4481-8bfa-754f8317ebcf.webp'
  },
  {
    kicker: 'Your delivery network',
    title: 'Success Partners',
    description: 'Your HR, Finance, Tech, Legal and TA partners and focal points.',
    actions: [{ label: 'Open', route: '/migration-chatbot' }],
    icon: 'mi-users',
    image: '/Collaboration.png'
  }
]

const quickLinks = [
  { title: 'Playbook & Standards', description: 'Lifecycle stages, artefacts, templates', icon: 'mi-file-arrows-square', route: '' },
  { title: 'Governance & Approvals', description: 'ELT approval route and forums', icon: 'mi-shield-check', route: '/approval-workflow' },
  { title: 'Pulse Assistant', description: 'Ask anything about process or status', icon: 'mi-chatbot', route: '/migration-chatbot' }
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
.hero-section { background: linear-gradient(120deg, #eaf6fa 0%, #f8fcfd 50%, #edf7fa 100%); border-bottom: 1px solid var(--line); display: grid; grid-template-columns: 1fr 1fr; min-height: clamp(350px, 42vh, 430px); }
.hero-copy { align-self: center; background: transparent; max-width: 620px; padding: 16px clamp(28px, 4vw, 64px) 16px clamp(44px, 8vw, 140px); }
.eyebrow, .card-kicker { color: var(--blue); font-size: 10px; font-weight: 800; letter-spacing: .14em; margin: 0; text-transform: uppercase; }
.eyebrow span { color: var(--cyan); }
.hero-copy h1 { color: var(--navy); font-family: 'Maersk Headline', 'Maersk Text', sans-serif; font-size: clamp(40px, 3vw, 50px); font-weight: 700; letter-spacing: -.025em; line-height: .94; margin: 12px 0 13px; }
.hero-description { color: #60758a; font-size: 15px; line-height: 1.55; margin: 0; max-width: 430px; }
.hero-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
.button { border: 1px solid var(--navy); border-radius: 3px; cursor: pointer; font: 700 12px 'Maersk Text', sans-serif; padding: 11px 16px; transition: transform .2s ease, box-shadow .2s ease; }
.button:hover { box-shadow: 0 5px 12px rgba(11, 43, 75, .16); transform: translateY(-2px); }
.button--primary { background: var(--navy); color: #fff; }
.button--secondary { background: #fff; color: var(--navy); }
.button span, .card-link span { margin-left: 7px; }
.hero-highlights { display: flex; gap: 16px; margin-top: 22px; }
.hero-highlight { align-items: center; color: var(--navy); display: flex; flex: 1 1 0; gap: 8px; min-width: 0; }
.hero-highlight__icon { align-items: center; background: #edf7fb; border-radius: 50%; color: var(--blue); display: flex; flex: 0 0 30px; height: 30px; justify-content: center; }
.hero-highlight > span:last-child { min-width: 0; }
.hero-highlight strong, .hero-highlight small { display: block; }
.hero-highlight strong { font-size: 11px; white-space: nowrap; }
.hero-highlight small { color: var(--muted); font-size: 10px; line-height: 1.3; margin-top: 3px; }
.hero-image { background: linear-gradient(110deg, rgba(11, 43, 75, .08), transparent 35%), url('/Collaboration-Hero.jpg') center 35% / cover; min-height: clamp(350px, 42vh, 430px); clip-path: polygon(10% 0, 100% 0, 100% 100%, 0 100%); }
.hub-section { padding: 20px 0 22px; }
.section-heading { align-items: end; display: grid; gap: 24px; grid-template-columns: minmax(220px, .8fr) minmax(280px, 1.2fr); margin-bottom: 20px; padding: 0 clamp(32px, 5vw, 80px); }
.eyebrow--dark { color: var(--blue); }
.section-heading h2 { color: var(--navy); font-size: 25px; letter-spacing: -.01em; margin: 6px 0 0; }
.section-note { color: var(--muted); font-size: 14px; line-height: 1.5; margin: 0; max-width: 470px; }
.explore-grid { display: grid; gap: 12px; grid-template-columns: repeat(4, minmax(0, 1fr)); }
.explore-card { animation: reveal .55s ease both; animation-delay: var(--card-delay); background: #fff; border: 1px solid var(--line); border-radius: 6px; box-shadow: 0 5px 14px rgba(18, 50, 75, .05); overflow: hidden; transition: box-shadow .2s ease, transform .2s ease; }
.explore-card:hover { box-shadow: 0 12px 24px rgba(18, 50, 75, .14); transform: translateY(-3px); }
.explore-card__visual { position: relative; }
.explore-card__image { background-position: center; background-size: cover; height: 96px; }
.explore-card__icon { align-items: center; background: #edf7fb; border: 4px solid #fff; border-radius: 50%; bottom: -17px; color: var(--blue); display: flex; height: 38px; justify-content: center; left: 16px; position: absolute; width: 38px; }
.explore-card__body { padding: 14px 16px 13px; }
.card-kicker { font-size: 10px; letter-spacing: .08em; }
.explore-card h3 { color: var(--navy); font-size: 15px; margin: 7px 0 6px; }
.explore-card p:not(.card-kicker) { color: var(--muted); font-size: 12px; line-height: 1.45; margin: 0; min-height: 35px; }
.card-actions { align-items: stretch; border-top: 1px solid #e6edf1; display: flex; gap: 16px; margin-top: auto; padding-top: 7px; }
.card-actions--split { gap: 10px; }
.card-link { align-items: center; background: transparent; border: 0; border-radius: 0; color: var(--navy); cursor: pointer; display: flex; flex: 1 1 0; font: 700 12px 'Maersk Text', sans-serif; justify-content: space-between; margin: 0; min-height: 44px; min-width: 0; padding: 0; text-align: left; transition: color .2s ease; }
.card-link span { align-items: center; border: 1px solid #d6e3e9; border-radius: 50%; color: var(--blue); display: inline-flex; height: 26px; justify-content: center; transition: background .2s ease, border-color .2s ease, color .2s ease; width: 26px; }
.card-link:hover { color: var(--blue); }
.card-link:hover span { background: #eaf5fa; border-color: #b9dce9; }
.card-link:focus-visible { border-radius: 3px; outline: 3px solid color-mix(in srgb, var(--blue) 35%, white); outline-offset: 2px; }
.quick-links { background: var(--line); border-bottom: 1px solid var(--line); display: grid; gap: 1px; grid-template-columns: repeat(3, minmax(0, 1fr)); margin-top: 1px; }
.quick-link { align-items: center; background: rgba(255, 255, 255, .76); border: 0; border-radius: 0; color: var(--navy); cursor: pointer; display: flex; gap: 13px; min-width: 0; padding: 18px clamp(20px, 3vw, 48px); text-align: left; transition: border-color .2s ease, background .2s ease, transform .2s ease; }
.quick-link:hover { border-color: #9ccde0; }
.quick-link:hover { background: #fff; transform: translateY(-2px); }
.quick-link--inactive { cursor: default; }
.quick-link--inactive:hover { border-color: var(--line); transform: none; }
.quick-link__icon { align-items: center; background: #edf7fb; border-radius: 6px; color: var(--blue); display: flex; flex: 0 0 36px; height: 36px; justify-content: center; }
.quick-link strong, .quick-link small { display: block; }
.quick-link strong { font-size: 12px; }
.quick-link small { color: var(--muted); font-size: 11px; margin-top: 4px; }
.quick-link__arrow { color: var(--blue); font-size: 17px; margin-left: auto; }
@keyframes reveal { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
@media (min-width: 821px) {
  .hub-section { display: flex; flex: 1 1 auto; flex-direction: column; justify-content: space-evenly; min-height: 0; }
  .section-heading { margin-bottom: 0; }
  .explore-grid { flex: 0 0 clamp(220px, 26vh, 260px); min-height: clamp(220px, 26vh, 260px); }
  .quick-links { margin-top: 0; }
  .explore-card { display: flex; flex-direction: column; height: 100%; min-height: 0; }
  .explore-card__image { flex: 0 0 116px; }
  .explore-card__body { display: flex; flex: 1; flex-direction: column; min-height: 0; }
  .card-actions { align-self: stretch; }
}
@media (prefers-reduced-motion: reduce) { .explore-card { animation: none; } .button:hover, .explore-card:hover { transform: none; } }
@media (max-width: 820px) { .hero-section { grid-template-columns: 1fr; } .hero-copy { padding: 40px 24px 34px; } .hero-image { clip-path: none; min-height: 230px; } .hero-highlights { flex-wrap: wrap; gap: 14px 20px; } .explore-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .section-heading { align-items: start; grid-template-columns: 1fr; } .section-note { text-align: left; } }
@media (max-width: 520px) { .hero-copy h1 { font-size: 40px; } .hero-highlights { display: grid; grid-template-columns: 1fr; } .explore-grid, .quick-links { grid-template-columns: 1fr; } }
</style>
