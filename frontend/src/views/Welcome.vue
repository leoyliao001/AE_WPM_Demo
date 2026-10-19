<template>
  <div class="welcome-page">
    <main class="welcome-scroll">
      <section class="hero-section">
        <div class="hero-copy">
          <h1 class="hero-title">WPM Pulse <span>-</span> Digital Hub</h1>
          <h2 class="hero-slogan">Right Work<br />Right Place<br />Right Ownership</h2>
          <p class="hero-description">
            From location decision to realised value, in one governed workflow
          </p>
          <div class="hero-actions">
            <button type="button" class="button button--primary" @click="go('/migration-intake')">
              Start a migration <span aria-hidden="true">&#8594;</span>
            </button>
          </div>
          <div class="hero-highlights" aria-label="WPM Pulse benefits">
            <div v-for="highlight in heroHighlights" :key="highlight.title" class="hero-highlight">
              <span class="hero-highlight__icon" aria-hidden="true"><mc-icon :icon="highlight.icon" size="18" /></span>
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
            <p class="eyebrow eyebrow--dark">Explore the hub</p>
            <h2 id="explore-heading">Everything you need, in one place</h2>
          </div>
          <p class="section-note">From the location decision to stable run — plan, govern, deliver and measure every migration.</p>
        </div>

        <div id="explore-cards" ref="exploreGrid" class="explore-grid" @scroll="updateExploreScrollbar">
          <article
            v-for="(card, index) in exploreCards"
            :key="card.title"
            class="explore-card"
            :class="{ 'explore-card--linked': card.actions.some(({ route }) => route) }"
            :style="{ '--card-delay': `${index * 70}ms` }"
            @click="navigateCard(card, $event)"
          >
            <div class="explore-card__visual">
              <div class="explore-card__image" :style="{ backgroundImage: `url(${card.image})` }" />
              <span class="explore-card__icon"><mc-icon :icon="card.icon" size="18" /></span>
            </div>
            <div class="explore-card__body">
              <p class="card-kicker">{{ card.kicker }}</p>
              <RouterLink
                v-if="card.actions.some(({ route }) => route)"
                class="explore-card__title-link"
                :to="card.actions.find(({ route }) => route).route"
              >
                <h3>{{ card.title }}</h3>
              </RouterLink>
              <h3 v-else>{{ card.title }}</h3>
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
        <div
          v-if="exploreScrollbar.visible"
          ref="exploreScrollbarTrack"
          class="explore-scrollbar"
          role="scrollbar"
          aria-label="Explore hub cards"
          aria-controls="explore-cards"
          aria-orientation="horizontal"
          :aria-valuemin="0"
          :aria-valuemax="Math.round(exploreScrollbar.maxScroll)"
          :aria-valuenow="Math.round(exploreScrollbar.scrollLeft)"
          tabindex="0"
          @pointerdown.prevent="startExploreScrollbarDrag"
          @pointermove="dragExploreScrollbar"
          @pointerup="stopExploreScrollbarDrag"
          @pointercancel="stopExploreScrollbarDrag"
          @keydown="handleExploreScrollbarKeydown"
        >
          <span class="explore-scrollbar__thumb" :style="exploreScrollbarThumbStyle" />
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
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import '@maersk-global/mds-components-core/mc-icon'

const router = useRouter()
const exploreGrid = ref(null)
const exploreScrollbarTrack = ref(null)
const exploreScrollbar = ref({ visible: false, maxScroll: 0, scrollLeft: 0, thumbWidth: 0, thumbOffset: 0 })
let exploreScrollbarResizeObserver
let exploreScrollbarDragOffset = 0

const exploreScrollbarThumbStyle = computed(() => ({
  width: `${exploreScrollbar.value.thumbWidth}px`,
  transform: `translateX(${exploreScrollbar.value.thumbOffset}px)`
}))

const updateExploreScrollbar = () => {
  const grid = exploreGrid.value
  if (!grid) return
  const maxScroll = Math.max(0, grid.scrollWidth - grid.clientWidth)
  const trackWidth = exploreScrollbarTrack.value?.clientWidth ?? grid.clientWidth
  const thumbWidth = maxScroll === 0
    ? trackWidth
    : Math.min(trackWidth, Math.max(48, trackWidth * grid.clientWidth / grid.scrollWidth))
  const maxThumbOffset = Math.max(0, trackWidth - thumbWidth)
  const scrollLeft = Math.min(maxScroll, grid.scrollLeft)

  exploreScrollbar.value = {
    visible: maxScroll > 0,
    maxScroll,
    scrollLeft,
    thumbWidth,
    thumbOffset: maxScroll === 0 ? 0 : maxThumbOffset * scrollLeft / maxScroll
  }
}

const startExploreScrollbarDrag = (event) => {
  if (!exploreScrollbar.value.visible) return
  const track = event.currentTarget
  const rect = track.getBoundingClientRect()
  exploreScrollbarDragOffset = event.target === track
    ? exploreScrollbar.value.thumbWidth / 2
    : event.clientX - rect.left - exploreScrollbar.value.thumbOffset
  track.setPointerCapture(event.pointerId)
  dragExploreScrollbar(event)
}

const dragExploreScrollbar = (event) => {
  const track = event.currentTarget
  if (!track.hasPointerCapture(event.pointerId)) return
  const rect = track.getBoundingClientRect()
  const maxThumbOffset = rect.width - exploreScrollbar.value.thumbWidth
  const thumbOffset = Math.max(0, Math.min(maxThumbOffset, event.clientX - rect.left - exploreScrollbarDragOffset))
  if (maxThumbOffset > 0 && exploreGrid.value) {
    exploreGrid.value.scrollLeft = exploreScrollbar.value.maxScroll * thumbOffset / maxThumbOffset
  }
}

const stopExploreScrollbarDrag = (event) => {
  if (event.currentTarget.hasPointerCapture(event.pointerId)) {
    event.currentTarget.releasePointerCapture(event.pointerId)
  }
}

const handleExploreScrollbarKeydown = (event) => {
  const grid = exploreGrid.value
  if (!grid) return
  const pageStep = grid.clientWidth * 0.8
  const keyScroll = {
    ArrowLeft: -48,
    ArrowRight: 48,
    PageDown: pageStep,
    PageUp: -pageStep,
    Home: -grid.scrollLeft,
    End: grid.scrollWidth - grid.clientWidth - grid.scrollLeft
  }[event.key]
  if (keyScroll !== undefined) {
    event.preventDefault()
    grid.scrollLeft = Math.max(0, Math.min(grid.scrollWidth - grid.clientWidth, grid.scrollLeft + keyScroll))
  }
}

const navigateCard = (card, event) => {
  if (event.target.closest('a, button')) return
  const destination = card.actions.find(({ route }) => route)?.route
  if (destination) go(destination)
}

onMounted(async () => {
  updateExploreScrollbar()
  await nextTick()
  updateExploreScrollbar()
  exploreScrollbarResizeObserver = new ResizeObserver(updateExploreScrollbar)
  if (exploreGrid.value) exploreScrollbarResizeObserver.observe(exploreGrid.value)
  if (exploreScrollbarTrack.value) exploreScrollbarResizeObserver.observe(exploreScrollbarTrack.value)
})

onBeforeUnmount(() => exploreScrollbarResizeObserver?.disconnect())

const heroHighlights = [
  { icon: 'mi-shield-check', title: 'Govern', description: 'Toll gates, approvals & audit-ready evidence' },
  { icon: 'mi-arrow-right', title: 'Execute', description: 'One standard lifecycle for every migration' },
  { icon: 'mi-users', title: 'Engage', description: 'Business, MSPs & partners connected' },
  { icon: 'mi-chart-bars-vertical', title: 'Measure', description: 'Portfolio insight & value realised' }
]

const exploreCards = [
  {
    kicker: 'Track your migrations',
    title: 'Migration Hub',
    description: 'Create, plan and track migrations through every phase and toll gate.',
    tags: ['Intake', 'Project plan', 'RAID', 'Readiness'],
    actions: [{ label: 'My migrations', route: '/project-dashboard' }],
    icon: 'mi-file-arrows-square',
    image: '/port-twilight.webp'
  },
  {
    kicker: 'Dashboards and insight',
    title: 'Portfolio & Insights',
    description: 'Enterprise view of migrations, FTE volumes, risks, compliance and value.',
    tags: ['Portfolio health', 'Site capacity', 'Benefits'],
    actions: [{ label: 'Open Dashboards', route: '/migration-dashboard' }],
    icon: 'mi-chart-bars-vertical',
    image: '/aefc68e4-4be4-4ebf-a3b1-38b9915c8db7.webp'
  },
  {
    kicker: 'Governance & approvals',
    title: 'Approval & Toll Gates',
    description: 'Submit, review and approve decisions with full, audit-ready evidence.',
    tags: ['ELT approvals', 'Toll gates', 'Decision log'],
    actions: [{ label: 'My Approval', route: '/toll-gates' }],
    icon: 'mi-shield-check',
    image: '/sea_bridge.png'
  },
  {
    kicker: 'Your delivery network',
    title: 'Success Partners',
    description: 'Your HR, Finance, Tech, Legal, TA and MSP focal points in one network.',
    tags: ['Focal points', 'RASCI', 'Forums'],
    actions: [{ label: 'Find a Partner', route: '/migration-chatbot' }],
    icon: 'mi-users',
    image: '/Collaboration.png'
  },
  {
    kicker: 'GSC locations and guardrails',
    title: 'Location Strategy',
    description: 'Place work in the right GSC site using principles, tenets and guardrails.',
    tags: ['Principles', 'Tenets', 'Red lines', 'Exceptions'],
    actions: [{ label: 'Explore Strategy', route: '/gsc-site-mapping?from=welcome' }],
    icon: 'mi-map',
    image: '/c05f31e9-c833-4481-8bfa-754f8317ebcf.webp'
  },
  {
    kicker: 'Standards & resources',
    title: 'Playbook & Toolkit',
    description: 'The enterprise standard: lifecycle, artefacts, tasks and templates.',
    tags: ['Playbook', 'Artefacts', 'Templates', 'Glossary'],
    actions: [{ label: 'Open Playbook', route: '' }],
    icon: 'mi-file-arrows-square',
    image: '/ocean-freight-shipping.jpeg'
  }
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
.hero-section { background: linear-gradient(120deg, #eaf6fa 0%, #f8fcfd 50%, #edf7fa 100%); border-bottom: 1px solid var(--line); display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); min-height: clamp(350px, 42vh, 430px); }
.hero-copy { align-self: center; background: transparent; min-width: 0; padding: 16px clamp(24px, 2vw, 32px) 16px 24px; }
.eyebrow, .card-kicker { color: var(--blue); font-size: 10px; font-weight: 800; letter-spacing: .14em; margin: 0; text-transform: uppercase; }
.hero-title { color: var(--navy); font-family: 'Maersk Headline', 'Maersk Text', sans-serif; font-size: clamp(28px, 4vw, 40px); font-weight: 700; letter-spacing: -.02em; line-height: 1.15; margin: 0 0 12px; }
.hero-title span { color: inherit; }
.eyebrow span { color: var(--cyan); }
.hero-slogan { color: var(--blue); font-family: 'Maersk Headline', 'Maersk Text', sans-serif; font-size: clamp(18px, 2vw, 24px); font-weight: 700; letter-spacing: -.025em; line-height: 1.08; margin: 0 0 13px 12px; }
.hero-description { color: #60758a; font-size: 15px; line-height: 1.55; margin: 0; max-width: 430px; }
.hero-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
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
.hero-image { background: linear-gradient(110deg, rgba(11, 43, 75, .08), transparent 35%), url('/Collaboration-Hero.jpg') center 35% / cover; min-height: clamp(350px, 42vh, 430px); min-width: 0; clip-path: polygon(10% 0, 100% 0, 100% 100%, 0 100%); }
.hub-section { padding: 20px 0 22px; }
.section-heading { align-items: center; display: grid; gap: 24px; grid-template-columns: minmax(220px, .8fr) minmax(280px, 1.2fr); margin-bottom: 20px; padding: 0 clamp(24px, 2vw, 32px); }
.eyebrow--dark { color: var(--blue); }
.section-heading h2 { color: var(--navy); font-size: 25px; letter-spacing: -.01em; margin: 6px 0 0; }
.section-note { color: var(--muted); font-size: 14px; justify-self: end; line-height: 1.5; margin: 0; max-width: 470px; text-align: right; }
.explore-grid { display: grid; gap: 12px; grid-auto-columns: 340px; grid-auto-flow: column; grid-template-columns: none; grid-template-rows: 230px; overflow-x: auto; overscroll-behavior-inline: contain; padding: 0 clamp(24px, 2vw, 32px) 8px; scroll-padding-inline: clamp(24px, 2vw, 32px); scroll-snap-type: x proximity; scrollbar-width: none; }
.explore-grid::-webkit-scrollbar { display: none; }
.explore-scrollbar { background: #f1f6f8; border-radius: 999px; cursor: pointer; height: 6px; margin: 2px clamp(24px, 2vw, 32px) 0; overflow: hidden; position: relative; touch-action: none; transition: background .2s ease; }
.explore-scrollbar__thumb { background: linear-gradient(90deg, #d2e8ef, #c4e0e9); border: 1px solid #f1f6f8; border-radius: 999px; cursor: grab; height: 100%; left: 0; min-width: 48px; opacity: .6; position: absolute; top: 0; transition: background .2s ease, border-color .2s ease, opacity .2s ease; }
.explore-scrollbar:hover { background: #e8f0f3; }
.explore-scrollbar:hover .explore-scrollbar__thumb,
.explore-scrollbar:focus-visible .explore-scrollbar__thumb { background: linear-gradient(90deg, #b9dce7, #a8d2e0); border-color: #e8f0f3; opacity: 1; }
.explore-scrollbar:active .explore-scrollbar__thumb { cursor: grabbing; }
.explore-scrollbar:focus-visible { outline: 2px solid color-mix(in srgb, var(--blue) 45%, white); outline-offset: 3px; }
@media (hover: none) { .explore-scrollbar__thumb { opacity: .8; } }
.explore-card { animation: reveal .55s ease both; animation-delay: var(--card-delay); background: #fff; border: 1px solid var(--line); border-radius: 6px; box-shadow: 0 5px 14px rgba(18, 50, 75, .05); overflow: hidden; scroll-snap-align: start; transition: box-shadow .2s ease, transform .2s ease; }
.explore-card--linked { cursor: pointer; }
.explore-card__title-link { color: inherit; text-decoration: none; }
.explore-card__title-link:focus-visible { border-radius: 2px; outline: 2px solid color-mix(in srgb, var(--blue) 45%, white); outline-offset: 2px; }
.explore-card:hover { box-shadow: 0 12px 24px rgba(18, 50, 75, .14); transform: translateY(-3px); }
.explore-card__visual { position: relative; }
.explore-card__image { background-position: center; background-size: cover; height: 96px; }
.explore-card__icon { align-items: center; background: #edf7fb; border: 4px solid #fff; border-radius: 50%; bottom: -17px; color: var(--blue); display: flex; height: 38px; justify-content: center; left: 16px; position: absolute; width: 38px; }
.explore-card__body { padding: 14px 16px 13px; }
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
.hub-principles { display: grid; flex: 0 0 auto; gap: 12px; grid-template-columns: repeat(5, minmax(0, 1fr)); margin: 24px clamp(24px, 2vw, 32px) 0; }
.hub-principle { align-items: center; background: linear-gradient(145deg, #fff 0%, #f8fbfc 100%); border: 1px solid #e1ebef; border-radius: 10px; box-shadow: 0 3px 10px rgba(18, 50, 75, .045); display: flex; gap: 11px; min-width: 0; padding: 12px; transition: border-color .2s ease, box-shadow .2s ease, transform .2s ease; }
.hub-principle:hover { border-color: #c9e1e9; box-shadow: 0 6px 16px rgba(18, 50, 75, .09); transform: translateY(-2px); }
.hub-principle__icon { align-items: center; background: linear-gradient(145deg, #e6f5fa, #d9eef5); border: 1px solid #d8edf4; border-radius: 9px; color: var(--blue); display: flex; flex: 0 0 34px; height: 34px; justify-content: center; width: 34px; }
.hub-principle__copy { min-width: 0; }
.hub-principle h3 { color: var(--navy); font-size: 12px; line-height: 1.2; margin: 0 0 4px; }
.hub-principle p { color: #60758a; font-size: 10px; line-height: 1.35; margin: 0; }
@keyframes reveal { from { opacity: 0; } to { opacity: 1; } }
@media (min-width: 821px) {
  .hub-section { display: flex; flex: 1 0 auto; flex-direction: column; justify-content: flex-start; min-height: 0; padding-bottom: 0; }
  .section-heading { margin-bottom: 24px; }
  .explore-grid { flex: 0 0 auto; grid-template-rows: 230px; }
  .hub-principles { margin-top: auto; margin-bottom: 24px; }
  .explore-card { display: flex; flex-direction: column; height: 100%; min-height: 0; }
  .explore-card__image { flex: 0 0 116px; }
  .explore-card__body { display: flex; flex: 1; flex-direction: column; min-height: 0; }
  .card-actions { align-self: stretch; }
}
@media (prefers-reduced-motion: reduce) { .explore-card { animation: none; } .button:hover, .explore-card:hover { transform: none; } }
@media (max-width: 820px) { .hero-section { grid-template-columns: 1fr; } .hero-copy { padding: 40px 24px 34px; } .hero-image { clip-path: none; min-height: 230px; } .hero-highlights { gap: 14px 20px; } .explore-grid { grid-auto-columns: minmax(280px, 78vw); grid-template-rows: minmax(250px, auto); } .section-heading { align-items: start; grid-template-columns: 1fr; } .section-note { text-align: left; } }
@media (max-width: 820px) { .hub-principles { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 520px) { .hero-title { font-size: 26px; } .hero-slogan { font-size: 18px; } .hero-highlights { grid-template-columns: repeat(2, minmax(0, 1fr)); } .explore-grid { grid-auto-columns: minmax(280px, 84vw); } .hub-principles { grid-template-columns: 1fr; } }
@media (min-width: 821px) and (max-height: 850px) {
  .hero-section,
  .hero-image { min-height: 260px; }
  .hero-copy { padding: 10px 20px 10px 24px; }
  .hero-title { font-size: 30px; line-height: 1.05; margin-bottom: 6px; }
  .hero-slogan { font-size: 16px; line-height: 1.02; margin-bottom: 7px; }
  .hero-description { font-size: 13px; line-height: 1.35; }
  .hero-actions { margin-top: 8px; }
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
  .explore-grid { grid-template-rows: 220px; gap: 8px; padding-bottom: 8px; }
  .explore-card__image { flex-basis: 68px; height: 68px; }
  .explore-card__icon { height: 32px; width: 32px; }
  .explore-card__body { padding: 8px 12px 7px; }
  .card-kicker { font-size: 8px; }
  .explore-card h3 { font-size: 13px; margin: 4px 0; }
  .explore-card p:not(.card-kicker) { font-size: 10px; line-height: 1.3; min-height: 26px; }
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
  .hero-section,
  .hero-image { min-height: 210px; }
  .hero-copy { padding-top: 6px; padding-bottom: 6px; }
  .hero-title { font-size: 26px; margin-bottom: 4px; }
  .hero-slogan { font-size: 14px; line-height: 1; margin-bottom: 5px; }
  .hero-description { font-size: 11px; line-height: 1.25; }
  .hero-actions { margin-top: 5px; }
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
  .explore-grid { grid-template-rows: 206px; gap: 6px; padding-bottom: 6px; }
  .explore-card__image { flex-basis: 52px; height: 52px; }
  .explore-card__icon { height: 28px; width: 28px; }
  .explore-card__body { padding: 6px 9px 5px; }
  .card-kicker { font-size: 7px; }
  .explore-card h3 { font-size: 11px; margin: 3px 0; }
  .explore-card p:not(.card-kicker) { font-size: 9px; line-height: 1.2; min-height: 22px; }
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
