import intakeOptions from '../../../backend/api/data/intake_options.json'

/** Function → Product mapping from Function Product Mapping.xlsx */
export const functionProductMapping = intakeOptions.functionProductMapping

export const functions = Object.keys(functionProductMapping)

export const getProductsForFunction = (fn) => functionProductMapping[fn] ?? []
