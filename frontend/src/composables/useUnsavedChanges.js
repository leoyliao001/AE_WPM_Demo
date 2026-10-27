import { onBeforeUnmount, onMounted } from 'vue'
import { onBeforeRouteLeave, onBeforeRouteUpdate } from 'vue-router'

export function useUnsavedChanges(dirty, pending) {
  const canLeave = () => !pending.value && (!dirty.value || window.confirm('Discard unsaved changes?'))
  const beforeUnload = (event) => {
    if (!dirty.value && !pending.value) return
    event.preventDefault()
    event.returnValue = ''
  }
  onBeforeRouteLeave(canLeave)
  onBeforeRouteUpdate(canLeave)
  onMounted(() => window.addEventListener('beforeunload', beforeUnload))
  onBeforeUnmount(() => window.removeEventListener('beforeunload', beforeUnload))
  return { canLeave }
}
