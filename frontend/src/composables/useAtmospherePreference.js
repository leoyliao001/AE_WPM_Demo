import { ref } from 'vue'

const STORAGE_KEY = 'ae-wpm-atmosphere-bg'

const readPreference = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    // Migrate older Welcome-only key if present.
    if (raw == null) {
      const legacy = localStorage.getItem('ae-wpm-welcome-bg')
      if (legacy === '0' || legacy === 'false') return false
      if (legacy === '1' || legacy === 'true') return true
    }
    if (raw === '0' || raw === 'false') return false
    if (raw === '1' || raw === 'true') return true
  } catch {
    /* ignore */
  }
  return true
}

const showAtmosphere = ref(readPreference())

const persist = (value) => {
  try {
    localStorage.setItem(STORAGE_KEY, value ? '1' : '0')
  } catch {
    /* ignore */
  }
}

export const useAtmospherePreference = () => {
  const toggleAtmosphere = () => {
    showAtmosphere.value = !showAtmosphere.value
    persist(showAtmosphere.value)
  }

  const setAtmosphere = (value) => {
    showAtmosphere.value = Boolean(value)
    persist(showAtmosphere.value)
  }

  return {
    showAtmosphere,
    toggleAtmosphere,
    setAtmosphere
  }
}
