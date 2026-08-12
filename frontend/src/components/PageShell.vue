<template>
  <div
    class="page-shell"
    :class="{
      'page-shell--full-width': fullWidth,
      'page-shell--atmosphere': atmosphere,
      'page-shell--plain': atmosphere && isPlain,
      'page-shell--night': atmosphere && isNight
    }"
  >
    <SkyAtmosphere
      v-if="atmosphere && showAtmosphere"
      :src="atmosphereSrc"
      :variant="isNight ? 'night' : 'day'"
    />
    <!-- Scroll only this layer so the photo stays pinned to the viewport -->
    <div class="page-shell__scroll">
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

    <AtmosphereToggle
      v-if="atmosphere"
      :mode="atmosphereMode"
      @cycle="cycleAtmosphere"
    />
  </div>
</template>

<script setup>
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-tag'
import SkyAtmosphere from './SkyAtmosphere.vue'
import AtmosphereToggle from './AtmosphereToggle.vue'
import { SKY_PHOTOS } from '../data/skyPhotos'
import { useAtmospherePreference } from '../composables/useAtmospherePreference'

defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  tag: { type: String, default: '' },
  tagAppearance: { type: String, default: 'info' },
  backTo: { type: String, default: '/' },
  backLabel: { type: String, default: 'Back to Welcome' },
  showHeader: { type: Boolean, default: true },
  fullWidth: { type: Boolean, default: false },
  /** Same viewport-locked photo atmosphere as Welcome. */
  atmosphere: { type: Boolean, default: false },
  /** Public image path — vary per page via SKY_PHOTOS. */
  atmosphereSrc: { type: String, default: SKY_PHOTOS.welcome }
})

const {
  atmosphereMode,
  isPlain,
  isNight,
  showAtmosphere,
  cycleAtmosphere
} = useAtmospherePreference()
</script>

<style scoped>
.page-shell {
  background: #fff;
  flex: 1 0 auto;
  min-height: 100%;
  overflow-x: clip;
  position: relative;
}

/*
  Atmosphere: shell fills the main viewport and does NOT scroll.
  SkyAtmosphere stays absolute over the shell; only .page-shell__scroll scrolls.
*/
.page-shell--atmosphere {
  background: #dff3fa;
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  isolation: isolate;
  min-height: 0;
  overflow: hidden;
  width: 100%;
}

.page-shell--plain {
  background: #fff;
}

.page-shell--night {
  background: #0a1628;
}

.page-shell--plain .page-title,
.page-shell--night .page-title {
  text-shadow: none;
}

.page-shell--night .page-title {
  color: #f2f6fb;
}

.page-shell--night .page-subtitle {
  color: rgba(210, 222, 236, 0.78);
}

.page-shell__scroll {
  position: relative;
  z-index: 1;
}

.page-shell--atmosphere .page-shell__scroll {
  flex: 1 1 auto;
  min-height: 0;
  overflow-x: clip;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-y: contain;
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
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.45);
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

.page-shell--night .back-link mc-button.back-button::part(button) {
  color: rgba(226, 236, 248, 0.92);
}
</style>
