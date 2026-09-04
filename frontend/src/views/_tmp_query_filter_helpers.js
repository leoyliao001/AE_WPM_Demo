// Helper exported if needed elsewhere - not currently used
export function mapSectionToStatus(section) {
  const s = String(section || '').toLowerCase()
  if (s === 'highlights') return 'completed'
  if (s === 'focus') return 'at_risk'
  if (s === 'levers') return 'in_progress'
  return ''
}
