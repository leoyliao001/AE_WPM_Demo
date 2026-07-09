<template>
  <div class="projects-table">
    <div class="projects-table__scroll">
      <table class="projects-table__grid">
        <colgroup>
          <col class="col-request-id" />
          <col class="col-project-name" />
          <col class="col-status" />
          <col class="col-region" />
          <col class="col-migration-type" />
          <col class="col-fte" />
          <col class="col-requestor" />
          <col class="col-requested" />
          <col class="col-progress" />
        </colgroup>
        <thead>
          <tr>
            <th
              v-for="column in columns"
              :key="column.id"
              scope="col"
              :class="{ 'is-sorted': sortColumn === column.id }"
            >
              <button
                type="button"
                class="sort-button"
                :aria-sort="sortAria(column.id)"
                @click="toggleSort(column.id)"
              >
                <span>{{ column.label }}</span>
                <span class="sort-indicator" aria-hidden="true">{{ sortIndicator(column.id) }}</span>
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in pagedRows"
            :key="row.id"
            class="projects-table__row"
            tabindex="0"
            @click="emit('row-click', row.id)"
            @keydown.enter="emit('row-click', row.id)"
          >
            <td class="projects-table__id" :title="row.migrationRequestId">
              {{ row.migrationRequestId }}
            </td>
            <th scope="row" class="projects-table__name" :title="row.projectName">
              {{ row.projectName }}
            </th>
            <td class="projects-table__status">
              <mc-tag
                fit="small"
                :appearance="statusAppearance(row.status)"
                :label="row.statusLabel"
              />
            </td>
            <td class="projects-table__text" :title="row.region">{{ row.region }}</td>
            <td class="projects-table__text" :title="row.migrationType">
              {{ row.migrationType }}
            </td>
            <td class="projects-table__num">{{ row.fteNumber }}</td>
            <td class="projects-table__text" :title="row.requestor">{{ row.requestor }}</td>
            <td class="projects-table__date" :title="row.requestedDate">
              {{ row.requestedDate }}
            </td>
            <td class="projects-table__num">{{ row.progressLabel }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="projects-table__pagination">
      <mc-pagination
        lang="en"
        variant="select"
        showpagesize
        showpagestatus
        showfirstandlastpage
        fit="small"
        :labels.prop="paginationLabels"
        :currentpage.prop="currentPage"
        :totalrecords.prop="rows.length"
        :pagesize.prop="pageSize"
        :pagesizeoptions.prop="pageSizeOptions"
        @pagechange="onPageChange"
        @pagesizechange="onPageSizeChange"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { statusAppearance } from '../utils/migrationDashboardProgress.js'
import '@maersk-global/mds-components-core/mc-tag'
import '@maersk-global/mds-components-core/mc-pagination'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  initialPageSize: { type: Number, default: 6 }
})

const emit = defineEmits(['row-click'])

const columns = [
  { id: 'migrationRequestId', label: 'Request ID', sortKey: 'migrationRequestId', type: 'string' },
  { id: 'projectName', label: 'Project name', sortKey: 'projectName', type: 'string' },
  { id: 'status', label: 'Status', sortKey: 'statusLabel', type: 'string' },
  { id: 'region', label: 'Region', sortKey: 'region', type: 'string' },
  { id: 'migrationType', label: 'Migration type', sortKey: 'migrationType', type: 'string' },
  { id: 'fteNumber', label: 'FTE', sortKey: 'fteNumber', type: 'number' },
  { id: 'requestor', label: 'Requestor', sortKey: 'requestor', type: 'string' },
  { id: 'requestedDate', label: 'Requested', sortKey: 'requestedDate', type: 'string' },
  { id: 'progress', label: 'Progress', sortKey: 'progress', type: 'number' }
]

const currentPage = ref(1)
const pageSize = ref(props.initialPageSize)
const pageSizeOptions = [6, 10, 15]
const sortColumn = ref('')
const sortDirection = ref('asc')

const paginationLabels = {
  previous: 'Previous',
  next: 'Next',
  first: 'First',
  last: 'Last',
  rowsPerPage: 'Items per page',
  pageStatus: '{{recordStart}}-{{recordEnd}} of {{totalRecords}} items'
}

const getSortValue = (row, column) => {
  if (column.sortKey === 'progress') {
    return Number.parseInt(String(row.progressLabel ?? ''), 10) || 0
  }
  if (column.type === 'number') {
    return Number.parseInt(String(row[column.sortKey] ?? ''), 10) || 0
  }
  return String(row[column.sortKey] ?? '').toLowerCase()
}

const sortedRows = computed(() => {
  const column = columns.find((item) => item.id === sortColumn.value)
  if (!column) return props.rows

  const direction = sortDirection.value === 'asc' ? 1 : -1
  return [...props.rows].sort((left, right) => {
    const leftValue = getSortValue(left, column)
    const rightValue = getSortValue(right, column)

    if (column.type === 'number') {
      return (leftValue - rightValue) * direction
    }

    return String(leftValue).localeCompare(String(rightValue), undefined, { numeric: true }) * direction
  })
})

const pagedRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return sortedRows.value.slice(start, start + pageSize.value)
})

watch(
  () => props.rows,
  () => {
    currentPage.value = 1
  }
)

watch(pageSize, () => {
  currentPage.value = 1
})

const toggleSort = (columnId) => {
  if (sortColumn.value === columnId) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = columnId
    sortDirection.value = 'asc'
  }
  currentPage.value = 1
}

const sortIndicator = (columnId) => {
  if (sortColumn.value !== columnId) return '↕'
  return sortDirection.value === 'asc' ? '↑' : '↓'
}

const sortAria = (columnId) => {
  if (sortColumn.value !== columnId) return 'none'
  return sortDirection.value === 'asc' ? 'ascending' : 'descending'
}

const onPageChange = (event) => {
  currentPage.value = Number(event.detail) || 1
}

const onPageSizeChange = (event) => {
  pageSize.value = Number(event.detail) || props.initialPageSize
}
</script>

<style scoped>
.projects-table {
  background: #fff;
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 12px;
  overflow: hidden;
  width: 100%;
}

.projects-table__scroll {
  max-height: 320px;
  overflow: auto;
}

.projects-table__grid {
  border-collapse: collapse;
  font-size: 12px;
  line-height: 1.4;
  min-width: 1080px;
  table-layout: fixed;
  width: 100%;
}

.col-request-id {
  width: 176px;
}

.col-project-name {
  width: 220px;
}

.col-status {
  width: 108px;
}

.col-region {
  width: 72px;
}

.col-migration-type {
  width: 156px;
}

.col-fte {
  width: 56px;
}

.col-requestor {
  width: 96px;
}

.col-requested {
  width: 168px;
}

.col-progress {
  width: 72px;
}

.projects-table__grid thead th,
.projects-table__grid tbody th,
.projects-table__grid tbody td {
  overflow: hidden;
  text-align: left;
  text-overflow: ellipsis;
  vertical-align: middle;
  white-space: nowrap;
}

.projects-table__grid thead th {
  background: #f6f7f9;
  border-bottom: 1px solid rgba(22, 22, 22, 0.08);
  color: #161616;
  font-size: 11px;
  font-weight: 600;
  padding: 0;
  position: sticky;
  top: 0;
  z-index: 1;
}

.projects-table__grid thead th.is-sorted {
  background: #eef6fb;
}

.sort-button {
  align-items: center;
  background: transparent;
  border: 0;
  color: inherit;
  cursor: pointer;
  display: flex;
  font: inherit;
  font-size: 11px;
  font-weight: 600;
  gap: 6px;
  justify-content: space-between;
  padding: 9px 14px;
  text-align: left;
  width: 100%;
}

.sort-button:hover {
  background: rgba(0, 119, 184, 0.06);
}

.sort-indicator {
  color: #0077b8;
  flex-shrink: 0;
  font-size: 10px;
  line-height: 1;
}

.projects-table__grid tbody th,
.projects-table__grid tbody td {
  border-bottom: 1px solid rgba(22, 22, 22, 0.06);
  color: #161616;
  font-size: 12px;
  padding: 10px 14px;
}

.projects-table__grid tbody tr:last-child th,
.projects-table__grid tbody tr:last-child td {
  border-bottom: 0;
}

.projects-table__row {
  cursor: pointer;
}

.projects-table__row:hover th,
.projects-table__row:hover td {
  background: rgba(0, 119, 184, 0.03);
}

.projects-table__name {
  font-weight: 600;
}

.projects-table__id,
.projects-table__text,
.projects-table__date,
.projects-table__num {
  color: #3d454d;
}

.projects-table__id,
.projects-table__date,
.projects-table__num {
  font-variant-numeric: tabular-nums;
}

.projects-table__status {
  overflow: visible;
  white-space: nowrap;
}

.projects-table__pagination {
  background: #fafbfc;
  border-top: 1px solid rgba(22, 22, 22, 0.06);
  padding: 10px 14px 12px;
}
</style>

<style>
.projects-table mc-tag {
  display: inline-flex !important;
  justify-content: flex-start !important;
  max-width: 100%;
  position: static !important;
  vertical-align: middle;
}
</style>
