import { onBeforeUnmount, shallowRef, unref, watch } from 'vue'

export const topbarNotice = shallowRef(null)

export function useTopbarNotice(notice) {
  const owner = Symbol('topbar-notice')

  watch(
    () => unref(notice),
    (value) => {
      if (value) topbarNotice.value = { ...value, owner }
      else if (topbarNotice.value?.owner === owner) topbarNotice.value = null
    },
    { immediate: true }
  )

  onBeforeUnmount(() => {
    if (topbarNotice.value?.owner === owner) topbarNotice.value = null
  })
}
