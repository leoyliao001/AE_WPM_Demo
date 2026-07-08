/** Region → Area mapping from Region Area Mapping File.xlsx */
export const regionAreaMapping = {
  APA: ['GCA', 'Mekong', 'NEA', 'Oceania', 'SEA'],
  EUR: ['CSE', 'EME', 'NDC', 'NEC', 'SWE', 'UK&I'],
  IMEA: ['EAA', 'IBS', 'PAK', 'SAA', 'SAI', 'UAE', 'WAF'],
  LAM: ['CAC', 'ECSA', 'WCSA'],
  NAM: ['CAA', 'MEX', 'USA']
}

export const regions = Object.keys(regionAreaMapping)

export const getAreasForRegion = (region) => regionAreaMapping[region] ?? []
