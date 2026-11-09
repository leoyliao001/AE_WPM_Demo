<template>
  <PageShell
    title="User Name List"
    subtitle="Search the directory list and maintain matching records."
    tag="Project Attributes"
    back-to="/project-attributes"
    back-label="Back to Admin"
    full-width
  >
    <form class="search-form" @submit.prevent="search">
      <label>
        <span>Display name</span>
        <input v-model="filters.display_name" type="search" maxlength="255" autocomplete="off" />
      </label>
      <label>
        <span>Email</span>
        <input v-model="filters.mail" type="search" maxlength="255" autocomplete="off" />
      </label>
      <mc-button appearance="primary" variant="filled" :disabled="loading" label="Search" type="button" @click="search" />
    </form>

    <p v-if="error" class="message error" role="alert">{{ error }}</p>
    <p v-if="!searched" class="message">Enter a name or email, then select Search.</p>
    <template v-else>
      <div class="results-toolbar">
        <span>{{ resultCount }} result{{ resultCount === 1 ? '' : 's' }}<span v-if="hasMore"> (showing first 500)</span><span v-if="selectedIds.size"> · {{ selectedIds.size }} selected</span></span>
        <div class="actions">
          <mc-button appearance="neutral" variant="outlined" label="Add row" :disabled="saving || deleting" @click="addRow" />
          <mc-button appearance="primary" variant="filled" :label="saving ? 'Saving…' : `Save (${changedRows.length})`" :disabled="saving || deleting || !changedRows.length" @click="save" />
          <mc-button appearance="neutral" variant="outlined" icon="mi-trash" :label="deleting ? 'Deleting…' : 'Delete selected'" :disabled="saving || deleting || !selectedIds.size || changedRows.length" @click="deleteSelected" />
        </div>
      </div>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th class="select-column"><input type="checkbox" aria-label="Select all saved results" :checked="allPersistedSelected" :disabled="!persistedIds.length || deleting" @change="setAllSelected($event.target.checked)" /></th>
              <th>Display name</th><th>Email</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in rows" :key="row.id ?? row._key">
              <td class="select-column"><input type="checkbox" :aria-label="`Select row ${index + 1} for deletion`" :checked="row.id ? selectedIds.has(row.id) : false" :disabled="!row.id || deleting" @change="toggleSelection(row.id, $event.target.checked)" /></td>
              <td><input v-model="row.display_name" :aria-label="`Display name row ${index + 1}`" maxlength="255" /></td>
              <td><input v-model="row.mail" :aria-label="`Email row ${index + 1}`" maxlength="255" /></td>
            </tr>
            <tr v-if="!rows.length"><td colspan="3" class="empty">No matching records.</td></tr>
          </tbody>
        </table>
      </div>
      <p v-if="loading" class="message">Searching…</p>
    </template>
  </PageShell>
</template>

<script setup>
import { computed, ref } from 'vue'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'
import '@maersk-global/mds-components-core/mc-button'

const filters = ref({ display_name: '', mail: '' })
const rows = ref([])
const selectedIds = ref(new Set())
const originalRows = ref(new Map())
const resultCount = ref(0)
const hasMore = ref(false)
const searched = ref(false)
const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const error = ref('')

const persistedIds = computed(() => rows.value.filter((row) => row.id).map((row) => row.id))
const allPersistedSelected = computed(() =>
  persistedIds.value.length > 0 && persistedIds.value.every((id) => selectedIds.value.has(id))
)

const changedRows = computed(() => rows.value.filter((row) => {
  if (!row.id) return true
  const original = originalRows.value.get(row.id)
  return original && (row.display_name !== original.display_name || row.mail !== original.mail)
}))

async function search() {
  if (!filters.value.display_name.trim() && !filters.value.mail.trim()) {
    error.value = 'Enter a display name or email to search.'
    searched.value = false
    return
  }
  loading.value = true
  error.value = ''
  try {
    const { data } = await axios.get('/api/user-name-list/', { params: filters.value })
    rows.value = data.rows.map((row) => ({ ...row }))
    selectedIds.value = new Set()
    originalRows.value = new Map(rows.value.map((row) => [row.id, { ...row }]))
    resultCount.value = data.count
    hasMore.value = data.has_more
    searched.value = true
  } catch (requestError) {
    error.value = requestError?.response?.data?.error || requestError.message || 'Search failed.'
  } finally {
    loading.value = false
  }
}

function addRow() {
  rows.value.unshift({ id: null, _key: crypto.randomUUID(), display_name: '', mail: '' })
}

async function save() {
  const changes = changedRows.value
  if (!changes.length) return
  if (changes.some((row) => !row.display_name.trim())) {
    error.value = 'Display name is required for every row.'
    return
  }
  saving.value = true
  error.value = ''
  try {
    const { data } = await axios.post('/api/user-name-list/data/', { uniqueData: changes })
    if (data.error_count) {
      for (const saved of data.saved_records) {
        const row = changes[saved.index]
        row.id = saved.id
        originalRows.value.set(saved.id, { id: saved.id, display_name: row.display_name, mail: row.mail })
      }
      error.value = data.errors.map((item) => item.error).join(' ')
    } else {
      await search()
    }
  } catch (requestError) {
    error.value = requestError?.response?.data?.error || requestError.message || 'Save failed.'
  } finally {
    saving.value = false
  }
}

function toggleSelection(id, checked) {
  const next = new Set(selectedIds.value)
  if (checked) next.add(id)
  else next.delete(id)
  selectedIds.value = next
}

function setAllSelected(checked) {
  selectedIds.value = checked ? new Set(persistedIds.value) : new Set()
}

async function deleteSelected() {
  const ids = [...selectedIds.value]
  if (!ids.length || saving.value || deleting.value || changedRows.value.length) return
  if (!window.confirm(`Permanently delete ${ids.length} selected record(s)? This cannot be undone.`)) return

  deleting.value = true
  error.value = ''
  try {
    const { data } = await axios.delete('/api/user-name-list/data/delete/', {
      data: { removedIds: ids }
    })
    selectedIds.value = new Set()
    await search()
    if (data.error_count) {
      error.value = data.errors.map((item) => item.error).join(' ')
    }
  } catch (requestError) {
    error.value = requestError?.response?.data?.error || requestError.message || 'Delete failed.'
  } finally {
    deleting.value = false
  }
}
</script>

<style scoped>
.search-form, .results-toolbar, .actions { display: flex; align-items: end; gap: 12px; }
.search-form { flex-wrap: wrap; margin-bottom: 20px; }
.search-form label { display: grid; gap: 5px; min-width: min(250px, 100%); }
.search-form label span { color: #52616b; font-size: 13px; }
input { box-sizing: border-box; width: 100%; min-height: 38px; border: 1px solid #aeb8bf; border-radius: 3px; padding: 7px 9px; font: inherit; }
.results-toolbar { justify-content: space-between; margin: 12px 0; color: #52616b; font-size: 14px; }
.actions { align-items: center; }
.table-scroll { overflow: auto; max-height: 65vh; border: 1px solid #d5dadd; }
table { width: 100%; border-collapse: collapse; }
th { position: sticky; top: 0; z-index: 1; background: #f2f5f6; text-align: left; }
th, td { min-width: 240px; padding: 8px; border-bottom: 1px solid #dfe4e7; }
.select-column { min-width: 44px; width: 44px; text-align: center; }
.select-column input { width: 16px; min-height: 16px; margin: 0; }
td input { min-width: 220px; }
.empty { color: #6b7780; text-align: center; padding: 24px; }
.message { color: #52616b; }
.error { color: #b42318; }
@media (max-width: 640px) {
  .search-form { align-items: stretch; flex-direction: column; }
  .results-toolbar { align-items: flex-start; flex-direction: column; }
  .actions { flex-wrap: wrap; }
}
</style>