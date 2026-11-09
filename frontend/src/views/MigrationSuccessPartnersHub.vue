<template>
  <div class="msp-hub">
    <section class="msp-hero">
      <div class="msp-breadcrumb"><RouterLink to="/">WPM Pulse - Digital Hub</RouterLink><span aria-hidden="true">›</span> Migration Success Partners Hub</div>
      <p class="msp-eyebrow">MSP WORKSPACE</p>
      <h1>Migration Success Partners Hub</h1>
      <p class="msp-intro">One place for partner teams to plan, track and sign off their part of every migration - from capability readiness and talent acquisition to business impact.</p>
    </section>

    <main class="msp-content">
      <section class="partner-grid" aria-label="Migration success partner workspaces">
        <RouterLink to="/migration-success-partners/learning-development" class="partner-card">
          <span class="card-band card-band--learning" />
          <span class="card-body">
            <span class="card-heading">
              <span class="card-icon card-icon--learning" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="m2 8 10-5 10 5-10 5L2 8Z"/><path d="M6 10v5c0 1.7 2.7 3 6 3s6-1.3 6-3v-5M22 8v6"/></svg></span>
              <span><span class="card-kicker">LEARNING &amp; DEVELOPMENT</span><strong class="card-title">L&amp;D</strong></span>
            </span>
            <span class="card-description">Foundational training, knowledge transfer and training scores for every approved migration, cohort by cohort.</span>
            <span class="card-stats"><span><b>{{ activeMigrations }}</b><small>Approved or pipeline</small></span><span><b>—</b><small>L&amp;D readiness · not tracked</small></span><span><b>{{ upcomingTargetEnds }}</b><small>Approved target ends in 90 days</small></span></span>
          </span>
          <span class="card-footer"><span>GSC L&amp;D · Area trainers</span><span class="card-action">Open L&amp;D <span aria-hidden="true">→</span></span></span>
        </RouterLink>

        <RouterLink to="/migration-success-partners/talent-acquisition" class="partner-card">
          <span class="card-band card-band--taa" />
          <span class="card-body">
            <span class="card-heading">
              <span class="card-icon card-icon--taa" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6M16 11l2 2 4-4"/></svg></span>
              <span><span class="card-kicker">TALENT ACQUISITION</span><strong class="card-title">TAA</strong></span>
            </span>
            <span class="card-description">Approved and pipeline FTEs per project, with execution, Area and HR / TAA views to drive hiring through to onboarding.</span>
            <span class="card-stats"><span><b>{{ approvedProjects }}</b><small>Approved projects</small></span><span><b>{{ approvedFtes }}</b><small>Approved FTEs</small></span><span><b>{{ pipelineFtes }}</b><small>Pipeline FTEs</small></span></span>
          </span>
          <span class="card-footer"><span>HR · TAA · GSC Execution</span><span class="card-action">Open TAA <span aria-hidden="true">→</span></span></span>
        </RouterLink>

        <article class="partner-card partner-card--soon" aria-label="Business Impact Analysis, coming soon">
          <span class="card-band card-band--bia" />
          <span class="card-body">
            <span class="card-heading">
              <span class="card-icon card-icon--bia" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M3 20h18M5 11h3v7H5zM10.5 7h3v11h-3zM16 4h3v14h-3z"/></svg></span>
              <span><span class="card-kicker">BUSINESS IMPACT</span><strong class="card-title">Business Impact Analysis</strong></span>
            </span>
            <span class="card-description">Assess the operational, customer and financial impact of each migration and capture mitigations before go-live.</span>
            <span class="card-status"><span>In design</span></span>
          </span>
          <span class="card-footer"><span>Area · Finance · Process owners</span><span class="card-action card-action--disabled">Coming soon</span></span>
        </article>
      </section>

      <section class="msp-principles" aria-label="Partner workspace principles">
        <article><span aria-hidden="true">✓</span><div><b>One project view</b><small>Same projects across every partner</small></div></article>
        <article><span aria-hidden="true">▤</span><div><b>Data entered once</b><small>Reused end-to-end</small></div></article>
        <article><span aria-hidden="true">♙</span><div><b>Clear ownership</b><small>Each partner updates its own fields</small></div></article>
        <article><span aria-hidden="true">+</span><div><b>Pipeline visibility</b><small>Plan ahead before approval</small></div></article>
      </section>
    </main>
    <p v-if="loading" class="hub-feedback" role="status">Loading project metrics...</p>
    <p v-else-if="error" class="hub-feedback hub-feedback--error" role="alert">{{ error }} <button type="button" @click="loadProjects">Retry</button></p>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'

const projects = ref([])
const loading = ref(false)
const error = ref('')
const approvedProjects = computed(() => projects.value.filter(project => project.approvalStatus === 'Approved').length)
const activeMigrations = computed(() => projects.value.filter(project => ['Approved', 'Pipeline'].includes(project.approvalStatus)).length)
const approvedFtes = computed(() => projects.value.reduce((sum, project) => sum + (project.approvedFte ?? 0), 0))
const pipelineFtes = computed(() => projects.value.reduce((sum, project) => sum + (project.pipelineFte ?? 0), 0))
const upcomingTargetEnds = computed(() => {
  const today = new Date()
  const horizon = new Date(today)
  horizon.setDate(horizon.getDate() + 90)
  return projects.value.filter(project => {
    if (project.approvalStatus !== 'Approved' || !project.targetEndDate) return false
    const targetEnd = new Date(`${project.targetEndDate}T00:00:00`)
    return targetEnd >= today && targetEnd <= horizon
  }).length
})

async function loadProjects() {
  loading.value = true
  error.value = ''
  try {
    projects.value = (await axios.get('/api/migration-dashboard/resources/')).data.rows
  } catch (caught) {
    error.value = caught.response?.data?.error || 'Unable to load project metrics.'
  } finally {
    loading.value = false
  }
}

onMounted(loadProjects)
</script>

<style scoped>
.msp-hub { --blue: #0073ab; --navy: #00243d; --ink: #101828; --muted: #475467; --line: #dde3ea; background: #f4f7fa; color: var(--ink); flex: 1 0 auto; min-height: 100%; }
.msp-hero { background: linear-gradient(120deg, #00243d, #004a77 56%, #0879ad); color: #fff; min-height: 258px; overflow: hidden; padding: 34px max(24px, calc((100vw - 1320px) / 2)) 68px; position: relative; }
.msp-hero::after { background: radial-gradient(circle, rgba(66, 176, 213, .32), transparent 67%); border-radius: 50%; content: ''; height: 520px; position: absolute; right: -120px; top: -150px; width: 520px; }
.msp-breadcrumb, .msp-eyebrow, .msp-hero h1, .msp-intro { position: relative; z-index: 1; }
.msp-breadcrumb { align-items: center; color: rgba(255,255,255,.86); display: flex; flex-wrap: wrap; font-size: 12px; gap: 8px; margin-bottom: 14px; }
.msp-breadcrumb a { color: #bfe6f5; text-decoration: none; }
.msp-breadcrumb a:hover { text-decoration: underline; }
.msp-eyebrow { color: #8fd3ec; font-size: 11px; font-weight: 800; letter-spacing: 1.4px; margin: 0; }
.msp-hero h1 { font-family: 'Maersk Headline', 'Maersk Text', sans-serif; font-size: 34px; line-height: 1.15; margin: 7px 0 8px; }
.msp-intro { color: #d6e9f3; font-size: 15px; line-height: 1.5; margin: 0; max-width: 720px; }
.msp-content { margin: -44px auto 0; max-width: 1320px; padding: 0 24px 40px; position: relative; z-index: 2; }
.partner-grid { display: grid; gap: 22px; grid-template-columns: repeat(3, minmax(0, 1fr)); }
.partner-card { background: #fff; border: 1px solid var(--line); border-radius: 8px; box-shadow: 0 6px 20px rgba(16,24,40,.07); color: inherit; display: flex; flex-direction: column; min-width: 0; overflow: hidden; text-align: left; text-decoration: none; transition: border-color .18s ease, box-shadow .18s ease, transform .18s ease; }
.partner-grid > .partner-card { min-height: 325px; }
a.partner-card:hover { border-color: #9fd0e8; box-shadow: 0 12px 28px rgba(16,24,40,.13); transform: translateY(-3px); }
a.partner-card:focus-visible { outline: 3px solid #42b0d5; outline-offset: 3px; }
.card-band { flex: 0 0 8px; }
.card-band--learning { background: linear-gradient(90deg, #7c3aed, #42b0d5); }
.card-band--taa { background: linear-gradient(90deg, #0073ab, #16a34a); }
.card-band--bia { background: linear-gradient(90deg, #f59e0b, #dc2626); }
.card-body { display: flex; flex: 1; flex-direction: column; padding: 22px 24px 18px; }
.card-heading { align-items: center; display: flex; gap: 14px; margin-bottom: 12px; min-height: 52px; }
.card-icon { align-items: center; border-radius: 12px; display: flex; flex: 0 0 52px; height: 52px; justify-content: center; }
.card-icon svg { fill: none; height: 26px; stroke: currentColor; stroke-linecap: round; stroke-linejoin: round; stroke-width: 2; width: 26px; }
.card-icon--learning { background: #efe7fd; color: #7c3aed; }
.card-icon--taa { background: #e3f5ea; color: #167a3e; }
.card-icon--bia { background: #fff0cf; color: #9a6200; }
.card-kicker { color: var(--blue); display: block; font-size: 10px; font-weight: 800; letter-spacing: 1.1px; }
.card-title { color: #080f18; display: block; font-size: 20px; line-height: 1.2; margin-top: 2px; }
.card-description { color: var(--muted); font-size: 13px; line-height: 1.5; min-height: 58px; }
.card-stats { border-top: 1px solid #eef1f4; display: grid; gap: 8px; grid-template-columns: repeat(3, minmax(0, 1fr)); margin-top: auto; padding-top: 14px; }
.card-stats b { color: #080f18; display: block; font-size: 22px; }
.card-stats small { color: var(--muted); display: block; font-size: 11px; line-height: 1.3; }
.card-status { align-items: flex-start; border-top: 1px solid #eef1f4; display: flex; margin-top: auto; padding-top: 14px; }
.card-status span { background: #fff0cf; border-radius: 10px; color: #9a6200; font-size: 11px; font-weight: 700; padding: 3px 9px; }
.card-footer { align-items: center; background: #f8fafc; border-top: 1px solid #eef1f4; color: var(--muted); display: flex; font-size: 11px; gap: 10px; justify-content: space-between; min-height: 64px; padding: 12px 20px; }
.card-action { align-items: center; background: var(--navy); border-radius: 18px; color: #fff; display: inline-flex; flex: 0 0 auto; font-size: 12px; font-weight: 700; gap: 6px; justify-content: center; min-height: 34px; padding: 0 15px; }
a.partner-card:hover .card-action { background: var(--blue); }
.card-action--disabled { background: #c3ccd5; }
.partner-card--soon { cursor: default; }
.msp-principles { display: grid; gap: 14px; grid-template-columns: repeat(4, minmax(0, 1fr)); margin-top: 24px; }
.msp-principles article { align-items: center; background: #fff; border: 1px solid var(--line); border-radius: 8px; display: flex; gap: 12px; min-width: 0; padding: 12px 14px; }
.msp-principles article > span { align-items: center; background: #e8f4fa; border-radius: 7px; color: var(--blue); display: flex; flex: 0 0 36px; font-size: 20px; height: 36px; justify-content: center; }
.msp-principles b, .msp-principles small { display: block; }
.msp-principles b { font-size: 12px; }
.msp-principles small { color: var(--muted); font-size: 11px; line-height: 1.35; margin-top: 3px; }
.hub-feedback { color: var(--muted); font-size: 12px; margin: 0 auto; max-width: 1320px; padding: 0 24px 18px; }
.hub-feedback--error { color: #b42318; }
.hub-feedback button { background: none; border: 0; color: #0073ab; cursor: pointer; font: inherit; font-weight: 700; }
@media (max-width: 900px) { .partner-grid { gap: 14px; grid-template-columns: 1fr; } .partner-card { min-height: 290px; } .msp-principles { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 520px) { .msp-hero { min-height: 260px; padding: 26px 20px 68px; } .msp-hero h1 { font-size: 28px; } .msp-intro { font-size: 14px; } .msp-content { padding-inline: 16px; } .card-body { padding: 18px 18px 16px; } .card-footer { padding-inline: 14px; } .msp-principles { grid-template-columns: 1fr; } }
@media (prefers-reduced-motion: reduce) { a.partner-card { transition: none; } a.partner-card:hover { transform: none; } }
</style>