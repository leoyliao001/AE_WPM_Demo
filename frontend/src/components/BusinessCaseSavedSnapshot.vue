<template>
  <details class="bc-snapshot bc-no-print">
    <summary>Saved page snapshots · {{ snapshots.length }} complete versions</summary>
    <p class="bc-note">Read-only database copies captured on successful save, refresh, submit or revision. Live source changes do not overwrite these copies. Approval reflects the state at capture, not subsequent decisions.</p>
    <p v-if="!snapshot || !Object.keys(snapshot).length" class="bc-note">No complete snapshot has been captured yet. Older records are not backfilled from today's source data. The next successful save will capture a complete version.</p>
    <template v-else>
      <label>Saved version
        <select v-model="selectedRevision">
          <option v-for="item in snapshots" :key="item.revision" :value="item.revision">Revision {{ item.revision }} · {{ item.savedAt }} · {{ item.action }}</option>
        </select>
      </label>
      <template v-if="selected">
        <p class="bc-note">Captured {{ selected.savedAt }} · {{ selected.savedBy }} · {{ selected.status }}</p>
        <details v-for="section in sections" :key="section.key">
          <summary>{{ section.label }}</summary>
          <pre>{{ JSON.stringify(selected[section.key], null, 2) }}</pre>
        </details>
      </template>
    </template>
  </details>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({ snapshot: Object, history: Array })
const snapshots = computed(() => {
  const entries = new Map((props.history || []).filter(item => item.pageSnapshot).map(item => [item.pageSnapshot.revision, item.pageSnapshot]))
  if (props.snapshot?.revision) entries.set(props.snapshot.revision, props.snapshot)
  return [...entries.values()].sort((a, b) => b.revision - a.revision)
})
const selectedRevision = ref(null)
watch(snapshots, values => { selectedRevision.value = values[0]?.revision ?? null }, { immediate: true })
const selected = computed(() => snapshots.value.find(item => item.revision === selectedRevision.value))
const sections = [
  { key: 'intake', label: 'Project overview / Intake' },
  { key: 'scope', label: 'Scope & migration plan' },
  { key: 'details', label: 'Business justification' },
  { key: 'financialInputs', label: 'Financial inputs' },
  { key: 'financials', label: 'Financial results & cost rate basis' },
  { key: 'approval', label: 'Approval state at capture' }
]
</script>
