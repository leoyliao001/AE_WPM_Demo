<template>
  <div
    class="page-shell"
    :class="{
      'page-shell--full-width': fullWidth,
      'page-shell--atmosphere': atmosphere
    }"
  >
    <div v-if="atmosphere" class="page-shell__glow" aria-hidden="true" />
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
  showHeader: { type: Boolean, default: true },
  fullWidth: { type: Boolean, default: false },
  /** Soft Maersk-blue atmospheric background (hub / landing-style pages). */
  atmosphere: { type: Boolean, default: false }
})
</script>

<style scoped>
.page-shell {
  background: #fff;
  /* Fill app-main scrollport; grow with content (avoid 100vh gap under header) */
  flex: 1 0 auto;
  min-height: 100%;
  overflow-x: clip;
  position: relative;
}

.page-shell--atmosphere {
  background:
    radial-gradient(ellipse 58% 42% at 8% 0%, rgba(66, 176, 213, 0.16) 0%, transparent 62%),
    radial-gradient(ellipse 48% 36% at 96% 12%, rgba(0, 119, 184, 0.09) 0%, transparent 55%),
    radial-gradient(ellipse 70% 48% at 50% 100%, rgba(66, 176, 213, 0.12) 0%, transparent 62%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.72) 0%, rgba(248, 252, 254, 0.88) 100%),
    repeating-linear-gradient(
      0deg,
      transparent 0,
      transparent 31px,
      rgba(66, 176, 213, 0.035) 31px,
      rgba(66, 176, 213, 0.035) 32px
    ),
    repeating-linear-gradient(
      90deg,
      transparent 0,
      transparent 31px,
      rgba(66, 176, 213, 0.035) 31px,
      rgba(66, 176, 213, 0.035) 32px
    ),
    linear-gradient(168deg, #f4fafc 0%, #eef6fa 45%, #e8f2f7 100%);
}

.page-shell__glow {
  background:
    radial-gradient(circle at 78% 72%, rgba(66, 176, 213, 0.12) 0%, transparent 42%),
    linear-gradient(
      125deg,
      transparent 40%,
      rgba(255, 255, 255, 0.45) 48%,
      transparent 56%
    );
  bottom: 0;
  left: 0;
  pointer-events: none;
  position: absolute;
  right: 0;
  top: 0;
  z-index: 0;
}

.page-shell__glow::before,
.page-shell__glow::after {
  border: 1px solid rgba(66, 176, 213, 0.14);
  border-radius: 50%;
  content: '';
  pointer-events: none;
  position: absolute;
}

.page-shell__glow::before {
  height: 280px;
  opacity: 0.55;
  right: -80px;
  top: 48px;
  width: 280px;
}

.page-shell__glow::after {
  bottom: 12%;
  height: 420px;
  left: -160px;
  opacity: 0.35;
  width: 420px;
}

.page-content {
  margin: 0 auto;
  max-width: 1180px;
  padding: 40px 24px 72px;
  position: relative;
  z-index: 1;
}

.page-shell--full-width .page-content {
  margin: 0;
  max-width: none;
  padding: 28px 20px 48px;
  width: 100%;
}

.page-shell--full-width .page-subtitle {
  max-width: none;
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
