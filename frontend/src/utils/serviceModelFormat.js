export function formatMoney(value) {
  const n = Number(value)
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000) return `$${Math.round(n / 1_000)}K`
  return `$${Math.round(n)}`
}

export function formatNumber(value) {
  return Number(value).toLocaleString('en-US')
}

export function formatTrendValue(metric, value) {
  if (metric === 'cpt') return `$${Number(value).toFixed(2)}`
  if (metric === 'total_fte') return String(Math.round(value))
  if (metric === 'total_vol') return formatNumber(value)
  return formatMoney(value)
}
