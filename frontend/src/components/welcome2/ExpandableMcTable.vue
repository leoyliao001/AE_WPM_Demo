<template>
  <div class="expandable-table-wrap">
    <mc-table
      ref="tableRef"
      expand
      expandpadding="none"
      :data.prop="rows"
      :columns.prop="columns"
      :datakey="datakey"
      :caption="caption"
      fit="small"
      height="auto"
      outerborderstyle="solid"
      horizontallinestyle="solid"
    />
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import '@maersk-global/mds-components-core/mc-table'

const props = defineProps({
  rows: { type: Array, required: true },
  columns: { type: Array, required: true },
  nestedColumns: { type: Array, required: true },
  datakey: { type: String, default: 'id' },
  caption: { type: String, default: '' },
  nestedCaption: { type: String, default: '' },
  nestedTitle: { type: Function, default: null },
  resolveNestedRows: { type: Function, required: true }
})

const tableRef = ref(null)

const clearExpandSlots = (table) => {
  table.querySelectorAll('[data-mds-expand-slot]').forEach((node) => node.remove())
}

const triggerExpandSlotChange = (table, rowId) => {
  const slotEl = table.shadowRoot?.querySelector(`slot[name="${rowId}_expanded"]`)
  if (slotEl?.assignedElements().length) {
    slotEl.dispatchEvent(new Event('slotchange'))
  }
}

const syncExpandSlots = async () => {
  await customElements.whenDefined('mc-table')
  await nextTick()
  await nextTick()

  const table = tableRef.value
  if (!table) return

  table.expand = true
  table.datakey = props.datakey
  table.data = [...props.rows]
  table.columns = props.columns

  if (typeof table.updateComplete?.then === 'function') {
    await table.updateComplete
  }

  clearExpandSlots(table)

  const visibleRows = table.getVisibleRows?.() || []
  visibleRows.forEach((visibleRow) => {
    const sourceRow =
      props.rows.find((row) => String(row[props.datakey]) === String(visibleRow.id)) ||
      visibleRow.original

    const panel = document.createElement('div')
    panel.slot = `${visibleRow.id}_expanded`
    panel.setAttribute('data-mds-expand-slot', 'true')
    panel.className = 'mds-expand-panel'

    if (props.nestedTitle) {
      const title = document.createElement('p')
      title.className = 'mds-expand-panel__title'
      title.textContent = props.nestedTitle(sourceRow)
      panel.appendChild(title)
    }

    const nestedRows = props.resolveNestedRows(sourceRow)

    if (nestedRows.length) {
      const nestedTable = document.createElement('mc-table')
      nestedTable.data = nestedRows
      nestedTable.columns = props.nestedColumns
      nestedTable.datakey = 'id'
      nestedTable.caption = props.nestedCaption
      nestedTable.fit = 'small'
      nestedTable.height = 'auto'
      nestedTable.outerborderstyle = 'solid'
      nestedTable.horizontallinestyle = 'solid'
      panel.appendChild(nestedTable)
    } else {
      const empty = document.createElement('p')
      empty.className = 'mds-expand-panel__empty'
      empty.textContent = 'No task-level detail available.'
      panel.appendChild(empty)
    }

    table.appendChild(panel)
  })

  if (typeof table.updateComplete?.then === 'function') {
    await table.updateComplete
  }

  visibleRows.forEach((visibleRow) => {
    triggerExpandSlotChange(table, visibleRow.id)
  })
}

onMounted(syncExpandSlots)

watch(
  () => [props.rows, props.nestedColumns, props.datakey],
  syncExpandSlots,
  { deep: true }
)

onBeforeUnmount(() => {
  if (tableRef.value) {
    clearExpandSlots(tableRef.value)
  }
})
</script>

<style>
.mds-expand-panel {
  background: #f8fafc;
  padding: 10px 14px 14px;
}

.mds-expand-panel__title {
  color: #6c757d;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  margin: 0 0 8px;
  text-transform: uppercase;
}

.mds-expand-panel__empty {
  color: #6c757d;
  font-size: 12px;
  margin: 0;
}
</style>
