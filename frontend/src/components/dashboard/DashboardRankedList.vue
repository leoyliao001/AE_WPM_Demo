<template>
  <div class="ranked-list" :class="{ 'ranked-list--compact': compact }">
    <button
      v-for="(item, index) in items"
      :key="item.key || `${item.label}-${index}`"
      type="button"
      class="ranked-list__row"
      :class="{
        'ranked-list__row--active': activeKey === item.key,
        'ranked-list__row--muted': item.muted
      }"
      @click="onRowClick(item)"
    >
      <span v-if="!compact" class="ranked-list__rank">{{ index + 1 }}</span>
      <span class="ranked-list__label" :title="item.label">{{ item.label }}</span>
      <div class="ranked-list__track">
        <div
          class="ranked-list__fill"
          :style="{
            width: `${item.pct}%`,
            background: item.color || '#0077b8'
          }"
        />
      </div>
      <span class="ranked-list__metric">{{ compact ? item.shareLabel : item.valueLabel }}</span>
    </button>
  </div>
</template>

<script setup>
defineProps({
  items: { type: Array, default: () => [] },
  activeKey: { type: String, default: '' },
  compact: { type: Boolean, default: false }
})

const emit = defineEmits(['select'])

const onRowClick = (item) => {
  if (!item.muted) emit('select', item.key)
}
</script>

<style scoped>
.ranked-list {
  display: grid;
  gap: 8px;
}

.ranked-list__row {
  align-items: center;
  background: transparent;
  border: 0;
  cursor: pointer;
  display: grid;
  gap: 10px;
  grid-template-columns: auto minmax(0, 1fr) auto;
  padding: 2px 0;
  text-align: left;
  transition: opacity 0.18s ease;
  width: 100%;
}

.ranked-list--compact .ranked-list__row {
  gap: 12px;
  grid-template-columns: minmax(88px, 0.9fr) minmax(0, 1.6fr) auto;
  padding: 6px 0;
}

.ranked-list__row:hover:not(.ranked-list__row--muted) .ranked-list__label {
  color: #0077b8;
}

.ranked-list__row--active .ranked-list__label {
  color: #0077b8;
  font-weight: 700;
}

.ranked-list__row--muted {
  cursor: default;
  opacity: 0.65;
}

.ranked-list__rank {
  align-items: center;
  background: color-mix(in srgb, #0077b8 10%, white);
  border-radius: 999px;
  color: #0077b8;
  display: inline-flex;
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 700;
  height: 24px;
  justify-content: center;
  width: 24px;
}

.ranked-list__label {
  color: var(--mds_brand_appearance_neutral_default_text-color, #334155);
  font-size: 13px;
  font-weight: 500;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ranked-list--compact .ranked-list__label {
  font-size: 12px;
}

.ranked-list__track {
  background: #eef2f6;
  border-radius: 999px;
  height: 6px;
  min-width: 0;
  overflow: hidden;
}

.ranked-list--compact .ranked-list__track {
  height: 8px;
}

.ranked-list__fill {
  border-radius: 999px;
  height: 100%;
  min-width: 3px;
  transition: width 0.22s ease;
}

.ranked-list__metric {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  flex-shrink: 0;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  min-width: 36px;
  text-align: right;
  white-space: nowrap;
}

.ranked-list--compact .ranked-list__metric {
  color: #161616;
  font-size: 12px;
  font-weight: 600;
  min-width: 32px;
}
</style>
