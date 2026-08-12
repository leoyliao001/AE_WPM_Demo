import { computed, ref } from 'vue'

export const ATMOSPHERE_MODES = ['photo', 'plain', 'night']

const STORAGE_KEY = 'ae-wpm-atmosphere-bg'

const normalizeMode = (raw) => {
  if (raw === 'photo' || raw === 'plain' || raw === 'night') return raw
  // Legacy boolean / 0-1 values
  if (raw === '0' || raw === 'false') return 'plain'
  if (raw === '1' || raw === 'true') return 'photo'
  return null
}

const readMode = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const mode = normalizeMode(raw)
    if (mode) return mode

    // Migrate older Welcome-only key if present.
    if (raw == null) {
      const legacy = normalizeMode(localStorage.getItem('ae-wpm-welcome-bg'))
      if (legacy) return legacy
    }
  } catch {
    /* ignore */
  }
  return 'photo'
}

const atmosphereMode = ref(readMode())

const persist = (value) => {
  try {
    localStorage.setItem(STORAGE_KEY, value)
  } catch {
    /* ignore */
  }
}

export const useAtmospherePreference = () => {
  const isPhoto = computed(() => atmosphereMode.value === 'photo')
  const isPlain = computed(() => atmosphereMode.value === 'plain')
  const isNight = computed(() => atmosphereMode.value === 'night')
  /** Photo layer on for sunny photo or night (dimmed) modes. */
  const showAtmosphere = computed(() => atmosphereMode.value !== 'plain')

  const cycleAtmosphere = () => {
    const index = ATMOSPHERE_MODES.indexOf(atmosphereMode.value)
    const next = ATMOSPHERE_MODES[(index + 1) % ATMOSPHERE_MODES.length]
    atmosphereMode.value = next
    persist(next)
  }

  /** @deprecated use cycleAtmosphere — kept for older call sites */
  const toggleAtmosphere = cycleAtmosphere

  const setAtmosphereMode = (value) => {
    const mode = normalizeMode(value) || (value ? 'photo' : 'plain')
    atmosphereMode.value = mode
    persist(mode)
  }

  return {
    atmosphereMode,
    isPhoto,
    isPlain,
    isNight,
    showAtmosphere,
    cycleAtmosphere,
    toggleAtmosphere,
    setAtmosphereMode
  }
}
