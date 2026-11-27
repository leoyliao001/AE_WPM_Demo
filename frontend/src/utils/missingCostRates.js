export function parseMissingCostRates(errors) {
  const rates = new Map()
  for (const message of errors || []) {
    const match = /^Missing (\d{4}) (JL[1-4]) cost rate for (.+)\.$/.exec(message)
    if (!match) continue
    const [, year, jobLevel, location] = match
    const key = `${year}:${jobLevel}:${location}`
    if (!rates.has(key)) rates.set(key, { key, year: Number(year), jobLevel, location })
  }
  return [...rates.values()]
}
