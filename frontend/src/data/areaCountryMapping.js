/** Area -> Country mapping from Region Area Mapping File.xlsx */
export const areaCountryMapping = {
  "CAA": ["Canada"],
  "CAC": ["Anguilla", "Antigua and Barbuda", "Aruba", "Bahamas", "Barbados", "Belize", "Bermuda Island", "Bonaire Sint Eustatius and Saba", "Cayman Islands", "Colombia", "Costa Rica", "Cuba", "Curacao", "Dominica", "Dominican Republic", "El Salvador", "Grenada", "Guatemala", "Guyana", "Haiti", "Honduras", "Jamaica", "Montserrat", "Netherl. Antilles", "Nicaragua", "Panama", "Puerto Rico", "Saint Barthelemy", "Saint Martin (French Part)", "Saint Vincent and the Grenadines", "Sint Maarten", "St Kitts-Nevis", "St Lucia", "Suriname", "Trinidad and Tobago", "Turks and Caicos", "Venezuela", "Virgin Islands (Br.)", "Virgin Islands (US)"],
  "CSE": ["Albania", "Bosnia and Herzegovina", "Croatia", "Cyprus", "Czech Republic", "Greece", "Hungary", "Italy", "Macedonia", "Malta", "Montenegro", "San Marino", "Serbia", "Slovakia", "Slovenia"],
  "EAA": ["Burundi", "Djibouti", "Eritrea", "Ethiopia", "Kenya", "Rwanda", "Somalia", "South Sudan", "Sudan", "Tanzania", "Uganda"],
  "ECSA": ["Argentina", "Brazil", "Paraguay", "Uruguay"],
  "EME": ["Armenia", "Azerbaijan", "Bulgaria", "Egypt", "Georgia", "Israel", "Kazakhstan", "Kyrgyzstan", "Lebanon", "Libya", "Moldova", "Romania", "Syria", "Tajikistan", "Turkey", "Turkmenistan", "Ukraine", "Uzbekistan"],
  "GCA": ["China", "Hong Kong", "Macau", "Mongolia", "Taiwan"],
  "IBS": ["Bangladesh", "Bhutan", "India", "Maldives", "Nepal", "Sri Lanka"],
  "MEX": ["Mexico"],
  "Mekong": ["Cambodia", "Laos", "Myanmar (Burma)", "Thailand", "Vietnam"],
  "NDC": ["Denmark", "Estonia", "Faroe Islands", "Finland", "Iceland", "Latvia", "Lithuania", "Norway", "Sweden"],
  "NEA": ["Japan", "North Korea", "South Korea"],
  "NEC": ["Austria", "Belgium", "Germany", "Liechtenstein", "Luxemburg", "Netherlands", "Poland", "Switzerland"],
  "Oceania": ["American Samoa", "Australia", "Cook Islands", "Fed St of Micronesia", "Fiji Islands", "French Polynesia", "Kiribati", "Marshall Islands", "Nauru", "New Caledonia", "New Zealand", "Niue", "Palau", "Papua New Guinea", "Samoa", "Solomon Islands", "Tonga", "Tuvalu", "Vanuatu", "Wallis & Futuna"],
  "PAK": ["Afghanistan", "Pakistan"],
  "SAA": ["Bahrain", "Iraq", "Jordan", "Kuwait", "Saudi Arabia", "Yemen"],
  "SAI": ["Botswana", "Comoro Islands", "Lesotho", "Madagascar", "Malawi", "Mauritius", "Mozambique", "Namibia", "Seychelles", "South Africa", "Swaziland", "Zambia", "Zimbabwe"],
  "SEA": ["Brunei", "Indonesia", "Malaysia", "Philippines", "Singapore", "Timor Leste"],
  "SWE": ["Algeria", "Andorra", "France", "French Guiana", "Gibraltar", "Guadeloupe", "Martinique", "Mayotte", "Monaco", "Morocco", "Portugal", "Reunion", "Spain", "Tunisia"],
  "UAE": ["Iran", "Oman", "Qatar", "United Arab Emirates"],
  "UK&I": ["Falkland Island", "Guernsey", "Ireland", "Isle of Man", "Jersey", "Saint Helena", "United Kingdom"],
  "USA": ["Guam", "Northern Mariana Islands", "United States"],
  "WAF": ["Angola", "Benin", "Burkina Faso", "Cameroon", "Cape Verde Island", "Central African Republic", "Chad", "Congo", "Congo, Dem. Rep. of", "Equatorial Guinea", "Gabon", "Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Ivory Coast", "Liberia", "Mali", "Mauritania", "Niger", "Nigeria", "Sao Tome and Principe", "Senegal", "Sierra Leone", "Togo"],
  "WCSA": ["Bolivia", "Chile", "Ecuador", "Peru"],
}

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