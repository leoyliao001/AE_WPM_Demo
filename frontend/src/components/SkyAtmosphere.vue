<template>
  <div class="sky-atmosphere" aria-hidden="true">
    <div
      class="sky-photo"
      :style="{ backgroundImage: `url('${src}')` }"
    />
    <div class="sky-tint" />
    <div class="sky-softlight" />
    <div class="sky-vignette" />
  </div>
</template>

<script setup>
defineProps({
  /** Public path, e.g. `/welcome-sky.jpg` */
  src: {
    type: String,
    required: true
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

.sky-softlight {
  background: radial-gradient(
    ellipse 70% 50% at 50% 0%,
    rgba(255, 255, 255, 0.55) 0%,
    transparent 65%
  );
  inset: 0;
  position: absolute;
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
