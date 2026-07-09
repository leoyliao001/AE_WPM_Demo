/** Area → default Location Strategy options (GSC sites from mapping table) */
export const customLocationStrategyOptions = [
  'Chengdu',
  'Vietnam',
  'Manila',
  'Qingdao',
  'Chennai',
  'Mumbai',
  'Pune',
  'Brazil',
  'Chongqing',
  'Mexico',
  'Poland'
]

export const areaLocationMapping = {
  GCA: { supportingSites: ['Chengdu', 'Qingdao'] },
  Mekong: { supportingSites: ['Manila', 'Vietnam'] },
  NEA: { supportingSites: ['Chengdu', 'Chongqing'] },
  Oceania: { supportingSites: ['Manila'] },
  SEA: { supportingSites: ['Manila'] },
  CSE: { supportingSites: ['Manila', 'Mumbai'] },
  EME: { supportingSites: ['Chennai', 'Pune'] },
  NDC: { supportingSites: ['Chennai', 'Poland'] },
  NEC: { supportingSites: ['Mumbai', 'Pune'] },
  SWE: { supportingSites: ['Chennai', 'Poland'] },
  'UK&I': { supportingSites: ['Mumbai', 'Poland'] },
  EAA: { supportingSites: ['Chennai', 'Mumbai'] },
  IBS: { supportingSites: ['Mumbai', 'Pune'] },
  PAK: { supportingSites: ['Manila'] },
  SAA: { supportingSites: ['Pune'] },
  SAI: { supportingSites: ['Chennai', 'Mumbai'] },
  UAE: { supportingSites: ['Pune'] },
  WAF: { supportingSites: ['Chennai', 'Mumbai'] },
  CAC: { supportingSites: ['Manila', 'Mexico'] },
  ECSA: { supportingSites: ['Brazil', 'Mumbai'] },
  WCSA: { supportingSites: ['Manila', 'Mexico'] },
  CAA: { supportingSites: ['Chennai', 'Mexico'] },
  MEX: { supportingSites: ['Manila', 'Mexico'] },
  USA: { supportingSites: ['Chennai', 'Mexico'] }
}

export const getDefaultLocationStrategiesForArea = (area) =>
  areaLocationMapping[area]?.supportingSites ?? []

export const getDefaultLocationStrategiesForAreas = (areas) => {
  const sites = new Set()
  for (const area of areas) {
    getDefaultLocationStrategiesForArea(area).forEach((site) => sites.add(site))
  }
  return [...sites].sort()
}

/** @deprecated Use customLocationStrategyOptions */
export const customGscSiteOptions = customLocationStrategyOptions

export const MAX_APPROVAL_FILE_BYTES = 4 * 1024 * 1024

export const APPROVAL_FILE_ACCEPT =
  '.eml,.msg,.mbox,.doc,.docx,.pdf,image/jpeg,image/png,image/gif,image/webp,image/bmp'
