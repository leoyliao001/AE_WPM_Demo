<template>
  <div class="page-shell">
    <div class="page-content">
      <header v-if="showHeader" class="page-header">
        <router-link v-if="backTo" class="back-link" :to="backTo">
          <mc-button
            class="back-button"
            appearance="neutral"
            variant="plain"
            fit="small"
            :label="backLabel"
            icon="mi-arrow-left"
          />
        </router-link>

        <div class="header-main">
          <mc-tag v-if="tag" :appearance="tagAppearance" fit="small" :label="tag" />
          <h1 class="page-title">{{ title }}</h1>
          <p v-if="subtitle" class="page-subtitle">{{ subtitle }}</p>
        </div>

        <slot name="header-extra" />
      </header>

      <main class="page-main">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-tag'

defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  tag: { type: String, default: '' },
  tagAppearance: { type: String, default: 'info' },
  backTo: { type: String, default: '/' },
  backLabel: { type: String, default: 'Back to Welcome' },
  showHeader: { type: Boolean, default: true }
})
</script>

<style scoped>
.page-shell {
  background: #fff;
  min-height: 100vh;
  overflow-x: clip;
  position: relative;
}

.page-content {
  margin: 0 auto;
  max-width: 1180px;
  padding: 40px 24px 72px;
  position: relative;
  z-index: 1;
}

.page-header {
  align-items: flex-start;
  display: flex;
  flex-direction: column;
  text-align: left;
  width: 100%;
}

.back-link {
  align-self: flex-start;
  display: inline-flex;
  justify-content: flex-start;
  margin-bottom: 20px;
  text-decoration: none;
}

.header-main {
  margin-bottom: 28px;
  width: 100%;
}

.page-title {
  color: var(--mds_brand_appearance_neutral_default_text-color, #161616);
  font-family: 'Maersk Headline', 'Maersk Text', sans-serif;
  font-size: clamp(28px, 4vw, 40px);
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.15;
  margin: 12px 0 10px;
}

.page-subtitle {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 15px;
  line-height: 1.6;
  margin: 0;
  max-width: 760px;
}

.page-main {
  display: flex;
  flex-direction: column;
  gap: 24px;
  width: 100%;
}
</style>

<style>
.page-shell .back-link mc-button.back-button::part(button) {
  justify-content: flex-start;
  padding-inline-start: 0;
  text-align: left;
}
</style>
