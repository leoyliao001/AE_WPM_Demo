<template>
  <mc-button appearance="neutral" variant="outlined" fit="small" label="Permissions & editing rules" @click="open = true" />
  <Teleport to="body">
    <mc-dialog :open="open" :heading="`${title} - Permissions & editing rules`" dimension="medium" showclosebutton @closing="open = false">
      <div class="rules-help">
        <p class="rules-help__intro">This guide explains access and editing rules. Opening it does not save, unlock or change any project data.</p>
        <slot />
      </div>
    </mc-dialog>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-dialog'

defineProps({ title: { type: String, required: true } })
const open = ref(false)
</script>

<style scoped>
.rules-help {
  max-height: 65vh;
  overflow-y: auto;
  padding: 4px 16px 8px 0;
  color: #243746;
  font-size: 14px;
  line-height: 1.65;
  overflow-wrap: anywhere;
}
.rules-help__intro {
  margin: 0 0 20px;
  color: #56626c;
}
.rules-help :deep(section + section) {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #dfe7ed;
}
.rules-help :deep(h3) {
  margin: 0 0 8px;
  color: #003f6e;
  font-size: 16px;
}
.rules-help :deep(p),
.rules-help :deep(ul),
.rules-help :deep(ol) {
  margin: 8px 0;
}
.rules-help :deep(ul),
.rules-help :deep(ol) {
  padding-left: 22px;
}
.rules-help :deep(li + li) {
  margin-top: 6px;
}
</style>
