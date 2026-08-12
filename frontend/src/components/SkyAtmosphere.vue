<template>
  <div
    class="sky-atmosphere"
    :class="{ 'sky-atmosphere--night': variant === 'night' }"
    aria-hidden="true"
  >
    <div
      class="sky-photo"
      :style="{ backgroundImage: `url('${src}')` }"
    />
    <div class="sky-tint" />
    <div class="sky-softlight" />
    <div class="sky-vignette" />
    <div v-if="variant === 'night'" class="sky-stars" />
  </div>
</template>

<script setup>
defineProps({
  /** Public path, e.g. `/welcome-sky.jpg` */
  src: {
    type: String,
    required: true
  },
  /** `day` (default) or `night` dark overlays */
  variant: {
    type: String,
    default: 'day',
    validator: (value) => ['day', 'night'].includes(value)
  }
})
</script>

<style scoped>
/* Same layer stack + drift as Welcome.vue */
.sky-atmosphere {
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  position: absolute;
  z-index: 0;
}

.sky-photo {
  background-position: center 42%;
  background-repeat: no-repeat;
  background-size: cover;
  height: 100%;
  inset: -2%;
  position: absolute;
  transform: scale(1.03);
  width: 100%;
  animation: sky-drift 48s ease-in-out infinite alternate;
}

.sky-atmosphere--night .sky-photo {
  filter: brightness(0.38) saturate(0.75) contrast(1.08);
}

.sky-tint {
  background:
    linear-gradient(
      180deg,
      rgba(255, 255, 255, 0.42) 0%,
      rgba(236, 248, 252, 0.22) 28%,
      rgba(66, 176, 213, 0.12) 62%,
      rgba(0, 119, 184, 0.18) 100%
    ),
    radial-gradient(
      ellipse 55% 40% at 82% 12%,
      rgba(255, 244, 210, 0.35) 0%,
      transparent 60%
    );
  inset: 0;
  position: absolute;
}

.sky-atmosphere--night .sky-tint {
  background:
    linear-gradient(
      180deg,
      rgba(6, 14, 32, 0.55) 0%,
      rgba(8, 24, 52, 0.42) 35%,
      rgba(10, 36, 72, 0.5) 70%,
      rgba(4, 12, 28, 0.72) 100%
    ),
    radial-gradient(
      ellipse 50% 36% at 78% 14%,
      rgba(120, 160, 220, 0.18) 0%,
      transparent 62%
    );
}

.sky-softlight {
  background: radial-gradient(
    ellipse 70% 50% at 50% 0%,
    rgba(255, 255, 255, 0.55) 0%,
    transparent 65%
  );
  inset: 0;
  position: absolute;
}

.sky-atmosphere--night .sky-softlight {
  background: radial-gradient(
    ellipse 55% 40% at 70% 8%,
    rgba(160, 190, 255, 0.14) 0%,
    transparent 70%
  );
}

.sky-vignette {
  background: radial-gradient(
    ellipse 85% 75% at 50% 40%,
    transparent 40%,
    rgba(0, 63, 110, 0.08) 100%
  );
  inset: 0;
  position: absolute;
}

.sky-atmosphere--night .sky-vignette {
  background: radial-gradient(
    ellipse 80% 70% at 50% 40%,
    transparent 35%,
    rgba(0, 4, 16, 0.55) 100%
  );
}

.sky-stars {
  background-image:
    radial-gradient(1.5px 1.5px at 12% 18%, rgba(255, 255, 255, 0.85), transparent),
    radial-gradient(1px 1px at 28% 42%, rgba(255, 255, 255, 0.7), transparent),
    radial-gradient(1.5px 1.5px at 46% 14%, rgba(255, 255, 255, 0.9), transparent),
    radial-gradient(1px 1px at 62% 36%, rgba(255, 255, 255, 0.65), transparent),
    radial-gradient(1.5px 1.5px at 78% 22%, rgba(255, 255, 255, 0.8), transparent),
    radial-gradient(1px 1px at 88% 48%, rgba(255, 255, 255, 0.55), transparent),
    radial-gradient(1px 1px at 18% 62%, rgba(255, 255, 255, 0.5), transparent),
    radial-gradient(1.5px 1.5px at 34% 78%, rgba(255, 255, 255, 0.7), transparent),
    radial-gradient(1px 1px at 54% 68%, rgba(255, 255, 255, 0.6), transparent),
    radial-gradient(1px 1px at 72% 82%, rgba(255, 255, 255, 0.55), transparent),
    radial-gradient(1.5px 1.5px at 91% 70%, rgba(255, 255, 255, 0.75), transparent);
  inset: 0;
  opacity: 0.85;
  position: absolute;
}

@keyframes sky-drift {
  from {
    transform: scale(1.03) translate3d(0, 0, 0);
  }

  to {
    transform: scale(1.07) translate3d(-1.2%, -0.6%, 0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .sky-photo {
    animation: none;
  }
}
</style>
