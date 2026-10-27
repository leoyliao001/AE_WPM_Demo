import intakeOptions from '../../../backend/api/data/intake_options.json'

/** Area -> Country mapping from Region Area Mapping File.xlsx */
export const areaCountryMapping = intakeOptions.areaCountryMapping

export const getCountriesForAreas = (areas) => {
  const countries = new Set()
  for (const area of areas) {
    for (const country of areaCountryMapping[area] ?? []) {
      countries.add(country)
    }
  }
  return [...countries].sort()
}

export const filterValidCountries = (areas, countries) => {
  const valid = new Set(getCountriesForAreas(areas))
  return countries.filter((country) => valid.has(country))
}

export const buildAreaCountryPairs = (areas, countries) => {
  const countrySet = new Set(countries)
  const pairs = []
  for (const area of areas) {
    for (const country of areaCountryMapping[area] ?? []) {
      if (countrySet.has(country)) {
        pairs.push({ area, country })
      }
    }
  }
  return pairs.sort((a, b) => a.area.localeCompare(b.area) || a.country.localeCompare(b.country))
}