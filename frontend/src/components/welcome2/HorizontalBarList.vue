<template>
  <div class="bar-list">
    <div v-for="item in items" :key="item.label" class="bar-row">
      <div class="bar-label" :title="item.label">{{ item.label }}</div>
      <div class="bar-track-wrap">
        <div v-if="item.segments" class="bar-track bar-track--stacked" :style="{ width: `${item.scalePct || 100}%` }">
          <div
            v-for="seg in item.segments"
            :key="seg.key"
            class="bar-seg"
            :style="{ width: `${seg.pct}%`, background: seg.color, borderRadius: seg.radius }"
            :title="seg.title"
          />
        </div>
        <div v-else class="bar-track">
          <div class="bar-fill" :style="{ width: `${item.pct}%`, background: item.color || '#0077b8' }" />
        </div>
      </div>
      <div class="bar-value">{{ item.value }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  items: { type: Array, required: true }
})
</script>

<style scoped>
.bar-row {
  align-items: center;
  display: flex;
  gap: 10px;
  margin-bottom: 7px;
}

.bar-label {
  color: var(--mds_brand_appearance_neutral_default_text-color, #334155);
  flex-shrink: 0;
  font-size: 12px;
  overflow: hidden;
  text-align: right;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 118px;
}

.bar-label--wide {
  width: 210px;
}

.bar-track-wrap {
  flex: 1;
  min-width: 0;
}

.bar-track {
  background: #f1f5f9;
  border-radius: 5px;
  height: 23px;
  overflow: hidden;
}

.bar-track--stacked {
  background: transparent;
  display: flex;
}

.bar-fill,
.bar-seg {
  height: 100%;
}

.bar-value {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  flex-shrink: 0;
  font-size: 11px;
  width: 128px;
}
</style>
