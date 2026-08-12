<template>
  <button
    type="button"
    class="bg-toggle"
    :class="`bg-toggle--${mode}`"
    :aria-label="ariaLabel"
    :title="ariaLabel"
    @click="$emit('cycle')"
  >
    <mc-icon class="bg-toggle__icon" :icon="icon" size="16" />
    <span class="bg-toggle__label">{{ label }}</span>
  </button>
</template>

<script setup>
import { computed } from 'vue'
import '@maersk-global/mds-components-core/mc-icon'

const props = defineProps({
  mode: {
    type: String,
    default: 'photo',
    validator: (value) => ['photo', 'plain', 'night'].includes(value)
  }
})

defineEmits(['cycle'])

const label = computed(() => {
  if (props.mode === 'plain') return 'Plain'
  if (props.mode === 'night') return 'Night'
  return 'Photo'
})

const icon = computed(() => {
  if (props.mode === 'plain') return 'mi-eye-slash'
  if (props.mode === 'night') return 'mi-moon'
  return 'mi-image'
})

const ariaLabel = computed(() => {
  if (props.mode === 'plain') return 'Background: plain. Click for night mode.'
  if (props.mode === 'night') return 'Background: night. Click for photo mode.'
  return 'Background: photo. Click for plain mode.'
})
</script>

<style scoped>
.bg-toggle {
  align-items: center;
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.42);
  border: 1px solid rgba(255, 255, 255, 0.55);
  border-radius: 999px;
  bottom: 18px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.65) inset,
    0 6px 18px rgba(0, 63, 110, 0.1);
  color: rgba(0, 63, 110, 0.72);
  cursor: pointer;
  display: inline-flex;
  font-family: 'Maersk Text', sans-serif;
  font-size: 11px;
  font-weight: 600;
  gap: 6px;
  left: 18px;
  letter-spacing: 0.02em;
  line-height: 1;
  opacity: 0.72;
  padding: 8px 12px 8px 10px;
  position: absolute;
  transition:
    opacity 0.2s ease,
    background 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    color 0.2s ease,
    transform 0.2s ease;
  z-index: 3;
}

.bg-toggle:hover {
  background: rgba(255, 255, 255, 0.72);
  border-color: rgba(0, 119, 184, 0.22);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.8) inset,
    0 8px 22px rgba(0, 63, 110, 0.14);
  opacity: 1;
  transform: translateY(-1px);
}

.bg-toggle:focus-visible {
  outline: 2px solid rgba(0, 119, 184, 0.45);
  outline-offset: 2px;
  opacity: 1;
}

.bg-toggle--plain {
  background: rgba(248, 250, 252, 0.88);
  border-color: rgba(22, 22, 22, 0.1);
  color: rgba(22, 22, 22, 0.55);
}

.bg-toggle--night {
  background: rgba(12, 24, 44, 0.72);
  border-color: rgba(148, 183, 224, 0.28);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.08) inset,
    0 6px 18px rgba(0, 0, 0, 0.35);
  color: rgba(210, 228, 248, 0.88);
}

.bg-toggle--night:hover {
  background: rgba(18, 34, 60, 0.9);
  border-color: rgba(148, 183, 224, 0.45);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.1) inset,
    0 8px 22px rgba(0, 0, 0, 0.4);
  color: #e8f1fb;
}

.bg-toggle__icon {
  color: inherit;
  display: inline-flex;
}

.bg-toggle__label {
  white-space: nowrap;
}

@media (max-width: 600px) {
  .bg-toggle {
    bottom: 12px;
    left: 12px;
    opacity: 0.85;
  }
}
</style>
