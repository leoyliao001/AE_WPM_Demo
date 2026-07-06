<template>
  <div class="stage-table">
    <table class="stage-table__grid">
      <caption class="stage-table__caption">Approval stages</caption>
      <thead>
        <tr>
          <th scope="col">Stage</th>
          <th scope="col">Owner</th>
          <th scope="col">Start</th>
          <th scope="col">End</th>
          <th scope="col">Duration</th>
          <th scope="col">Deadline</th>
          <th scope="col">Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.key">
          <th scope="row" class="stage-table__stage">{{ row.stage }}</th>
          <td>{{ row.responsible }}</td>
          <td class="stage-table__date">{{ row.startDate }}</td>
          <td class="stage-table__date">{{ row.endDate }}</td>
          <td class="stage-table__duration">{{ row.duration }}</td>
          <td>
            <span
              v-if="row.deadline"
              class="stage-table__deadline"
              :class="`stage-table__deadline--${row.deadline.appearance}`"
              :title="row.deadline.title"
            >
              {{ row.deadline.label }}
            </span>
            <span v-else class="stage-table__muted">—</span>
          </td>
          <td>
            <mc-tag
              fit="small"
              :appearance="statusAppearance(row.status)"
              :label="statusLabel(row.status)"
            />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({
  rows: { type: Array, default: () => [] }
})

function statusLabel(status) {
  if (status === 'approved') return 'Approved'
  if (status === 'pending') return 'Pending'
  return 'Locked'
}

function statusAppearance(status) {
  if (status === 'approved') return 'info'
  if (status === 'pending') return 'warning'
  return 'neutral'
}
</script>

<style scoped>
.stage-table {
  background: #fff;
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 12px;
  overflow: hidden;
  width: 100%;
}

.stage-table__caption {
  height: 1px;
  margin: -1px;
  overflow: hidden;
  padding: 0;
  position: absolute;
  width: 1px;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.stage-table__grid {
  border-collapse: collapse;
  font-size: 13px;
  line-height: 1.4;
  width: 100%;
}

.stage-table__grid thead th,
.stage-table__grid tbody th,
.stage-table__grid tbody td {
  text-align: left;
}

.stage-table__grid thead th {
  background: #f6f7f9;
  border-bottom: 1px solid rgba(22, 22, 22, 0.08);
  color: #161616;
  font-size: 12px;
  font-weight: 600;
  padding: 10px 14px;
  white-space: nowrap;
}

.stage-table__grid tbody th,
.stage-table__grid tbody td {
  border-bottom: 1px solid rgba(22, 22, 22, 0.06);
  color: #161616;
  padding: 11px 14px;
  vertical-align: middle;
}

.stage-table__grid tbody tr:last-child th,
.stage-table__grid tbody tr:last-child td {
  border-bottom: 0;
}

.stage-table__grid tbody tr:hover th,
.stage-table__grid tbody tr:hover td {
  background: rgba(0, 119, 184, 0.02);
}

.stage-table__stage {
  font-weight: 600;
}

.stage-table__date {
  color: #3d454d;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.stage-table__duration {
  color: #3d454d;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.stage-table__muted {
  color: #adb5bd;
}

.stage-table__deadline {
  color: #3d454d;
  white-space: nowrap;
}

.stage-table__deadline--info {
  color: #0077b8;
}

.stage-table__deadline--error {
  color: #c62828;
}
</style>

<style>
.stage-table mc-tag {
  display: inline-flex !important;
  justify-content: flex-start !important;
  position: static !important;
  vertical-align: middle;
}
</style>
