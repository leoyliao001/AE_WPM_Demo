import intakeOptions from '../../../backend/api/data/intake_options.json'

/** Region → Area mapping from Region Area Mapping File.xlsx */
export const regionAreaMapping = intakeOptions.regionAreaMapping

export const regions = Object.keys(regionAreaMapping)

export const getAreasForRegion = (region) => regionAreaMapping[region] ?? []
