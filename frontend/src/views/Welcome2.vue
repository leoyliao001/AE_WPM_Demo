<template>
  <div class="fsm-page">
    <div class="page-content">
      <header class="page-header">
        <mc-tag appearance="info" fit="small" label="Migration Portal" />
        <h1 class="page-title">Future Service Model</h1>
        <p class="page-subtitle">
          Integrated cost, capability, and country-level analytics to identify where Area work can shift to GSC —
          from volume and FTE trends through process readiness to movable tasks by country.
        </p>
        <router-link class="back-link" to="/">
          <mc-button appearance="neutral" variant="plain" fit="small" label="Back to Welcome" icon="mi-arrow-left" />
        </router-link>
      </header>

      <Welcome2Analytics />
    </div>
  </div>
</template>

<script setup>
import Welcome2Analytics from '../components/welcome2/Welcome2Analytics.vue'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-tag'
</script>

<style scoped>
.fsm-page {
  background: #fff;
  min-height: 100vh;
  overflow-x: clip;
}

.page-content {
  margin: 0 auto;
  max-width: 1240px;
  min-height: 100vh;
  padding: 56px 32px 72px;
}

.page-header {
  animation: fade-up 0.55s ease both;
  margin-bottom: 8px;
  max-width: 720px;
}

.back-link {
  display: inline-block;
  margin-top: 16px;
  text-decoration: none;
}

.page-title {
  color: var(--mds_brand_appearance_neutral_default_text-color, #161616);
  font-family: 'Maersk Headline', 'Maersk Text', sans-serif;
  font-size: clamp(32px, 4.5vw, 48px);
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.1;
  margin: 14px 0 12px;
}

.page-subtitle {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 15px;
  line-height: 1.6;
  margin: 0;
  max-width: 640px;
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

@media (max-width: 600px) {
  .page-content {
    padding: 32px 16px 48px;
  }
}
</style>
