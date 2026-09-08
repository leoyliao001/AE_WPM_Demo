<template>
  <span class="pulse-logo" :style="{ '--logo-size': `${size}px` }" aria-hidden="true">
    <svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" focusable="false">
      <defs>
        <linearGradient :id="gradientId" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#5CC9EC" />
          <stop offset="100%" stop-color="#1B8FBF" />
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="48" height="48" rx="12" :fill="`url(#${gradientId})`" />
      <path
        d="M8 25h7.5l3.4-8.4 5.6 15.2 3.9-9.1 2.6 4.3H40"
        fill="none"
        stroke="#fff"
        stroke-width="2.6"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </svg>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  size: { type: Number, default: 40 }
})

// Unique per instance so multiple logos on one page don't share a gradient id.
const gradientId = computed(() => `pulse-logo-grad-${Math.random().toString(36).slice(2, 9)}`)

void props
</script>

<style scoped>
.pulse-logo {
  display: inline-flex;
  flex-shrink: 0;
  height: var(--logo-size, 40px);
  width: var(--logo-size, 40px);
}

.pulse-logo svg {
  border-radius: calc(var(--logo-size, 40px) * 0.25);
  box-shadow: 0 4px 12px rgba(27, 143, 191, 0.35);
  height: 100%;
  width: 100%;
}
</style>
