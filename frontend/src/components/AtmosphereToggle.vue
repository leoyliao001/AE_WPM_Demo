<template>
  <button
    type="button"
    class="bg-toggle"
    :class="{ 'bg-toggle--on': on, 'bg-toggle--off': !on }"
    :aria-pressed="on"
    :title="on ? 'Hide background photo' : 'Show background photo'"
    @click="$emit('toggle')"
  >
    <mc-icon
      class="bg-toggle__icon"
      :icon="on ? 'mi-image' : 'mi-eye-slash'"
      size="16"
    />
    <span class="bg-toggle__label">{{ on ? 'Photo' : 'Plain' }}</span>
  </button>
</template>

<script setup>
import '@maersk-global/mds-components-core/mc-icon'

defineProps({
  on: { type: Boolean, default: true }
})

defineEmits(['toggle'])
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

.bg-toggle--off {
  background: rgba(248, 250, 252, 0.88);
  border-color: rgba(22, 22, 22, 0.1);
  color: rgba(22, 22, 22, 0.55);
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
