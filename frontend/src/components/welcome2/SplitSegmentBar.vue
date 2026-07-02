<template>
  <div class="segment-block">
    <div class="segment-head">
      <span>{{ title }}</span>
      <span>{{ total }}</span>
    </div>
    <div class="segment-bar" role="img" :aria-label="title">
      <div
        v-for="seg in segments"
        :key="seg.label"
        class="segment-piece"
        :class="`segment-piece--${seg.tone}`"
        :style="{ width: `${seg.pct}%` }"
      >
        <span class="segment-pct">{{ seg.pct }}%</span>
        <span class="segment-detail">{{ seg.label }} · {{ seg.detail }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  total: { type: String, required: true },
  segments: { type: Array, required: true }
})
</script>

<style scoped>
.segment-block + .segment-block {
  margin-top: 16px;
}

.segment-head {
  color: var(--mds_brand_appearance_neutral_default_text-color, #334155);
  display: flex;
  font-size: 12px;
  font-weight: 700;
  justify-content: space-between;
  margin-bottom: 6px;
}

.segment-bar {
  border-radius: 9px;
  display: flex;
  height: 46px;
  overflow: hidden;
}

.segment-piece {
  align-items: center;
  color: #fff;
  display: flex;
  flex-direction: column;
  font-weight: 700;
  justify-content: center;
  min-width: 0;
}

.segment-piece--area {
  background: #f3880e;
}

.segment-piece--gsc {
  background: #00a989;
}

.segment-pct {
  font-size: 16px;
}

.segment-detail {
  font-size: 10px;
  opacity: 0.9;
}
</style>
