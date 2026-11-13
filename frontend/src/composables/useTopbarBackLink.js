import { onBeforeUnmount, shallowRef, unref, watch } from 'vue'

export const topbarBackLink = shallowRef(null)

export function useTopbarBackLink(to, label) {
  const owner = Symbol('topbar-back-link')

  watch(
    () => [unref(to), unref(label)],
    ([target, text]) => {
      if (target) topbarBackLink.value = { to: target, label: text, owner }
      else if (topbarBackLink.value?.owner === owner) topbarBackLink.value = null
    },
    { immediate: true }
  )

  onBeforeUnmount(() => {
    if (topbarBackLink.value?.owner === owner) topbarBackLink.value = null
  })
}