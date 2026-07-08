/** Area → Location Strategy & default Supporting GSC Sites (from mapping table) */
export const customGscSiteOptions = [
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
  GCA: { locationStrategy: 'APA', supportingSites: ['Chengdu', 'Qingdao'] },
  Mekong: { locationStrategy: 'APA', supportingSites: ['Manila', 'Vietnam'] },
  NEA: { locationStrategy: 'APA', supportingSites: ['Chengdu', 'Chongqing'] },
  Oceania: { locationStrategy: 'APA', supportingSites: ['Manila'] },
  SEA: { locationStrategy: 'APA', supportingSites: ['Manila'] },
  CSE: { locationStrategy: 'EUR', supportingSites: ['Manila', 'Mumbai'] },
  EME: { locationStrategy: 'EUR', supportingSites: ['Chennai', 'Pune'] },
  NDC: { locationStrategy: 'EUR', supportingSites: ['Chennai', 'Poland'] },
  NEC: { locationStrategy: 'EUR', supportingSites: ['Mumbai', 'Pune'] },
  SWE: { locationStrategy: 'EUR', supportingSites: ['Chennai', 'Poland'] },
  'UK&I': { locationStrategy: 'EUR', supportingSites: ['Mumbai', 'Poland'] },
  EAA: { locationStrategy: 'IMEA', supportingSites: ['Chennai', 'Mumbai'] },
  IBS: { locationStrategy: 'IMEA', supportingSites: ['Mumbai', 'Pune'] },
  PAK: { locationStrategy: 'IMEA', supportingSites: ['Manila'] },
  SAA: { locationStrategy: 'IMEA', supportingSites: ['Pune'] },
  SAI: { locationStrategy: 'IMEA', supportingSites: ['Chennai', 'Mumbai'] },
  UAE: { locationStrategy: 'IMEA', supportingSites: ['Pune'] },
  WAF: { locationStrategy: 'IMEA', supportingSites: ['Chennai', 'Mumbai'] },
  CAC: { locationStrategy: 'LAM', supportingSites: ['Manila', 'Mexico'] },
  ECSA: { locationStrategy: 'LAM', supportingSites: ['Brazil', 'Mumbai'] },
  WCSA: { locationStrategy: 'LAM', supportingSites: ['Manila', 'Mexico'] },
  CAA: { locationStrategy: 'NAM', supportingSites: ['Chennai', 'Mexico'] },
  MEX: { locationStrategy: 'NAM', supportingSites: ['Manila', 'Mexico'] },
  USA: { locationStrategy: 'NAM', supportingSites: ['Chennai', 'Mexico'] }
}

export const getLocationStrategyForArea = (area) => areaLocationMapping[area]?.locationStrategy ?? ''

export const getDefaultSupportingSitesForArea = (area) =>
  areaLocationMapping[area]?.supportingSites ?? []

export const getLocationStrategiesForArea = (area) => {
  const strategy = getLocationStrategyForArea(area)
  return strategy ? [strategy] : []
}

export const getLocationStrategiesForAreas = (areas) => {
  const strategies = new Set()
  for (const area of areas) {
    const strategy = getLocationStrategyForArea(area)
    if (strategy) strategies.add(strategy)
  }
  return [...strategies].sort()
}

export const getDefaultSupportingSitesForAreas = (areas) => {
  const sites = new Set()
  for (const area of areas) {
    getDefaultSupportingSitesForArea(area).forEach((site) => sites.add(site))
  }
  return [...sites].sort()
}

export const getAreasForLocationStrategy = (areas, strategy) =>
  areas.filter((area) => getLocationStrategyForArea(area) === strategy)

export const getDefaultSupportingSitesForAreasAndStrategies = (areas, strategies) => {
  const strategySet = new Set(strategies)
  const activeAreas = areas.filter((area) => strategySet.has(getLocationStrategyForArea(area)))
  return getDefaultSupportingSitesForAreas(activeAreas)
}

export const filterValidLocationStrategies = (areas, strategies) => {
  const valid = new Set(getLocationStrategiesForAreas(areas))
  return strategies.filter((strategy) => valid.has(strategy))
}

export const filterAreasByLocationStrategies = (areas, strategies) => {
  const strategySet = new Set(strategies)
  return areas.filter((area) => strategySet.has(getLocationStrategyForArea(area)))
}

export const buildAreaLocationPairs = (areas, strategies) => {
  const strategySet = new Set(strategies)
  return areas
    .map((area) => ({
      area,
      locationStrategy: getLocationStrategyForArea(area)
    }))
    .filter((pair) => pair.locationStrategy && strategySet.has(pair.locationStrategy))
}

export const MAX_APPROVAL_FILE_BYTES = 4 * 1024 * 1024

export const APPROVAL_FILE_ACCEPT =
  '.eml,.msg,.mbox,.doc,.docx,.pdf,image/jpeg,image/png,image/gif,image/webp,image/bmp'
