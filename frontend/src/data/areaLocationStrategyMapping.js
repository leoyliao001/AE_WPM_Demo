import intakeOptions from '../../../backend/api/data/intake_options.json'

/** Area → default Location Strategy options (GSC sites from mapping table) */
export const customLocationStrategyOptions = intakeOptions.customLocationStrategyOptions

export const areaLocationMapping = intakeOptions.areaLocationMapping

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
