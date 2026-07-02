export const costPositionKpis = [
  { id: 'total', label: 'Total Cost / month', value: '$2.30M', sub: '2.01M transactions', accent: '#6c757d' },
  { id: 'save', label: 'Modelled at full shift', value: '$796K', sub: 'per month, GSC-handled tasks', accent: '#475569' },
  { id: 'area-cpt', label: 'Area cost / transaction', value: '$2.59', sub: '24% of volume', accent: '#F3880E' },
  { id: 'gsc-cpt', label: 'GSC cost / transaction', value: '$0.72', sub: '76% of volume', accent: '#00A989' }
]

export const volumeSplit = {
  total: '2.01M txns',
  segments: [
    { label: 'Areas', pct: 24, detail: '489K', tone: 'area' },
    { label: 'GSC', pct: 76, detail: '1.52M', tone: 'gsc' }
  ]
}

export const costSplit = {
  total: '$2.30M',
  segments: [
    { label: 'Areas', pct: 52, detail: '$1.20M', tone: 'area' },
    { label: 'GSC', pct: 48, detail: '$1.10M', tone: 'gsc' }
  ]
}

export const trendMonths = ['Feb', 'Mar', 'Apr']

export const trendData = {
  cpt: {
    total: [1.19, 1.17, 1.15],
    area: [2.5, 2.44, 2.45],
    gsc: [0.73, 0.72, 0.72],
    insight:
      'Blended cost per transaction: $1.19 (Feb) → $1.17 (Mar) → $1.15 (Apr), a 3.7% decrease. Area was $2.50 → $2.45; GSC was $0.73 → $0.72.'
  },
  total_cost: {
    total: [1979144, 2311025, 2298619],
    area: [1082567, 1247741, 1200285],
    gsc: [896577, 1063285, 1098334],
    insight:
      'Total cost: $1.98M (Feb) → $2.31M (Mar) → $2.30M (Apr), up 16% over the period. Volume rose 21% over the same period.'
  },
  total_vol: {
    total: [1664403, 1980308, 2007711],
    area: [432995, 510721, 489353],
    gsc: [1231408, 1469587, 1518358],
    insight: 'Volume: 1.66M (Feb) → 1.98M (Mar) → 2.01M (Apr), up 21%. GSC volume rose 23%; Area volume rose 13%.'
  },
  total_fte: {
    total: [1040.6, 1120.5, 1132.1],
    area: [322.6, 347.4, 351.0],
    gsc: [718.0, 773.1, 781.1],
    insight:
      'FTE: 1,041 (Feb) → 1,121 (Mar) → 1,132 (Apr), up 9%, against 21% volume growth over the same period.'
  }
}

export const capabilityTiers = [
  {
    id: 'ready',
    title: 'Ready to scale',
    tasks: 142,
    fte: 146,
    areaCost: 545000,
    saving: 417000,
    color: '#334155',
    note: 'GSC already performs the large majority of this work across most countries — operational rollout, not capability build.'
  },
  {
    id: 'partial',
    title: 'Partially capable',
    tasks: 74,
    fte: 137,
    areaCost: 497000,
    saving: 351000,
    color: '#64748b',
    note: 'GSC handles a substantial share but coverage is uneven; expansion needs process alignment and country-by-country readiness.'
  },
  {
    id: 'early',
    title: 'Early capability',
    tasks: 29,
    fte: 19,
    areaCost: 77000,
    saving: 40000,
    color: '#94a3b8',
    note: 'GSC handles only a small share; meaningful migration requires building capability, training and tooling first.'
  }
]

export const quadrantSummary = {
  Q1: { tasks: 23, areaFte: 180, areaCost: 677530, save: 467046, color: '#334155', name: 'High GSC share · High Area cost' },
  Q2: { tasks: 185, areaFte: 79, areaCost: 276349, save: 226021, color: '#64748b', name: 'High GSC share · Low Area cost' },
  Q3: { tasks: 5, areaFte: 30, areaCost: 119874, save: 82312, color: '#94a3b8', name: 'Low GSC share · High Area cost' },
  Q4: { tasks: 49, areaFte: 14, areaCost: 46990, save: 32577, color: '#b8c2cf', name: 'Low GSC share · Low Area cost' }
}

export const bubbleTasks = [
  { task: 'Amend Vessel Details', gsc: 74.6, areaCost: 33065, vol: 53398, q: 'Q1', save: 25233 },
  { task: 'Booking Request', gsc: 77.9, areaCost: 29646, vol: 51525, q: 'Q1', save: 21237 },
  { task: 'Container Maritime Tracking', gsc: 66.1, areaCost: 78997, vol: 69685, q: 'Q1', save: 44091 },
  { task: 'Invoice Query', gsc: 78.3, areaCost: 46064, vol: 83910, q: 'Q1', save: 33949 },
  { task: 'Release Delivery Order', gsc: 77.2, areaCost: 49029, vol: 88024, q: 'Q1', save: 37481 },
  { task: 'Port System/Terminal Query', gsc: 53.4, areaCost: 47898, vol: 50386, q: 'Q1', save: 43780 },
  { task: 'Cargo Rolled Over', gsc: 59.9, areaCost: 60450, vol: 29046, q: 'Q1', save: 21731 },
  { task: 'Booking Amendment Request', gsc: 79.4, areaCost: 19371, vol: 33152, q: 'Q1', save: 12748 },
  { task: 'Amend Container Count', gsc: 78.3, areaCost: 10397, vol: 22023, q: 'Q1', save: 8906 },
  { task: 'B/L Enquiry', gsc: 85.0, areaCost: 13755, vol: 44065, q: 'Q1', save: 12295 },
  { task: 'Advanced Manifest Query', gsc: 71.8, areaCost: 7955, vol: 13723, q: 'Q2', save: 7208 },
  { task: 'Amend Payterm/Payer', gsc: 94.4, areaCost: 5616, vol: 40250, q: 'Q2', save: 4239 },
  { task: 'Release BL Request - Counter', gsc: 49.2, areaCost: 31596, vol: 42565, q: 'Q3', save: 40337 },
  { task: 'Container Damaged by Customer', gsc: 29.3, areaCost: 27857, vol: 13271, q: 'Q3', save: 17490 },
  { task: 'Onboarding-Lead & Execute-Lite', gsc: 16.5, areaCost: 15914, vol: 491, q: 'Q3', save: 764 },
  { task: 'Breakdown Activation', gsc: 0.9, areaCost: 4223, vol: 3974, q: 'Q4', save: 7344 },
  { task: 'Additional Charges Incurred', gsc: 48.3, areaCost: 3556, vol: 2878, q: 'Q4', save: 2775 }
]

export const shiftDefaults = { areaVol: 371817, areaFte: 258.7, areaCpu: 2.587, gscCpu: 0.723 }

export const opportunityKpis = [
  { label: 'Area FTE (resources)', value: '350', sub: '31% of total FTE' },
  { label: 'Area Cost / month', value: '$1.20M', sub: '52% of total cost' },
  { label: 'Area Volume', value: '489K', sub: '24% of total volume' }
]

export const areaCountries = [
  { country: 'Germany', fte: 17.1, cost: 103183, volume: 12406, redesignCost: 86133 },
  { country: 'United States', fte: 10.4, cost: 88091, volume: 17250, redesignCost: 69370 },
  { country: 'Spain', fte: 15.3, cost: 78322, volume: 16377, redesignCost: 64523 },
  { country: 'Italy', fte: 11.7, cost: 74861, volume: 20549, redesignCost: 62528 },
  { country: 'United Kingdom', fte: 11.4, cost: 58993, volume: 6730, redesignCost: 52589 },
  { country: 'China', fte: 20.6, cost: 52115, volume: 19263, redesignCost: 30971 },
  { country: 'Australia', fte: 7.0, cost: 45806, volume: 7039, redesignCost: 41636 },
  { country: 'Brazil', fte: 16.9, cost: 37244, volume: 29839, redesignCost: 29447 },
  { country: 'India', fte: 22.3, cost: 35743, volume: 33923, redesignCost: 27936 },
  { country: 'Turkey', fte: 8.0, cost: 35394, volume: 16049, redesignCost: 32784 }
]

export const processBreakdown = [
  { name: 'Cargo/Container', fte: 139.9, cost: 514145, volume: 180474, dArea: 399441, dDual: 114124, dGsc: 581 },
  { name: 'Documentation', fte: 51.6, cost: 192085, volume: 91280, dArea: 187376, dDual: 0, dGsc: 4709 },
  { name: 'Booking', fte: 43.2, cost: 175090, volume: 71539, dArea: 169460, dDual: 3084, dGsc: 2545 },
  { name: 'Charges, Invoice & Payment', fte: 41.7, cost: 135487, volume: 57912, dArea: 135461, dDual: 0, dGsc: 26 },
  { name: 'Prior To Booking', fte: 13.3, cost: 53245, volume: 20320, dArea: 52595, dDual: 649, dGsc: 0 },
  { name: 'Lead & Execute', fte: 4.7, cost: 20303, volume: 879, dArea: 20303, dDual: 0, dGsc: 0 },
  { name: 'Online Help', fte: 5.5, cost: 18440, volume: 7023, dArea: 18436, dDual: 0, dGsc: 4 },
  { name: 'Collections', fte: 1.3, cost: 4874, volume: 1564, dArea: 4862, dDual: 0, dGsc: 12 }
]

export const designOwnership = [
  { name: 'Designed Area', cost: 994745, fte: 263.5, tasks: 218, color: '#475569' },
  { name: 'Dual (either)', cost: 117857, fte: 35.5, tasks: 9, color: '#94a3b8' },
  { name: 'Unmapped', cost: 79803, fte: 47.4, tasks: 4, color: '#cbd5e1' },
  { name: 'Designed GSC', cost: 7881, fte: 3.7, tasks: 26, color: '#0f172a' }
]

export const complianceItems = [
  { label: 'Designed Area (adherent)', cost: 994745, pct: 83, color: '#475569' },
  { label: 'Dual-owned (either valid)', cost: 117857, pct: 10, color: '#94a3b8' },
  { label: 'Unmapped tasks', cost: 79803, pct: 7, color: '#cbd5e1' },
  { label: 'Designed GSC, run in Area (non-adherent)', cost: 7881, pct: 0.7, color: '#0f172a' }
]

export const designChangeProcesses = [
  { process: 'Booking', l3: 'Issue Resolution (CM)', system: 'Case Management', nsub: 11, ntask: 56, areaFte: 43.2, areaCost: 175090, save: 133349, gscShare: 84.0, gscCountries: 136, gapCountries: 6, tier: 'Ready to scale', tierColor: '#334155' },
  { process: 'Documentation', l3: 'Issue Resolution (CM)', system: 'Case Management', nsub: 21, ntask: 87, areaFte: 51.6, areaCost: 192085, save: 170146, gscShare: 81.5, gscCountries: 140, gapCountries: 5, tier: 'Ready to scale', tierColor: '#334155' },
  { process: 'Charges, Invoice & Payment', l3: 'Issue Resolution (CM)', system: 'Case Management', nsub: 9, ntask: 39, areaFte: 41.7, areaCost: 135487, save: 107948, gscShare: 76.7, gscCountries: 151, gapCountries: 2, tier: 'Ready to scale', tierColor: '#334155' },
  { process: 'Online Help', l3: 'Issue Resolution (CM)', system: 'Case Management', nsub: 6, ntask: 29, areaFte: 5.5, areaCost: 18440, save: 13091, gscShare: 76.2, gscCountries: 124, gapCountries: 8, tier: 'Ready to scale', tierColor: '#334155' },
  { process: 'Cargo/Container', l3: 'Issue Resolution (CM)', system: 'Case Management', nsub: 16, ntask: 71, areaFte: 139.9, areaCost: 514145, save: 336404, gscShare: 70.5, gscCountries: 142, gapCountries: 4, tier: 'Ready to scale', tierColor: '#334155' },
  { process: 'Collections', l3: 'Issue Resolution (CM)', system: 'Case Management', nsub: 6, ntask: 36, areaFte: 1.3, areaCost: 4874, save: 2915, gscShare: 69.7, gscCountries: 91, gapCountries: 17, tier: 'Partial capability', tierColor: '#64748b' },
  { process: 'Prior To Booking', l3: 'Issue Resolution (CM)', system: 'Case Management', nsub: 20, ntask: 59, areaFte: 13.3, areaCost: 53245, save: 37876, gscShare: 59.6, gscCountries: 123, gapCountries: 11, tier: 'Partial capability', tierColor: '#64748b' },
  { process: 'Lead & Execute', l3: 'Onboarding', system: 'IONIS', nsub: 2, ntask: 5, areaFte: 4.7, areaCost: 20303, save: 1638, gscShare: 12.5, gscCountries: 13, gapCountries: 69, tier: 'Early capability', tierColor: '#94a3b8' },
  { process: 'Lead', l3: 'Onboarding', system: 'IONIS', nsub: 0, ntask: 3, areaFte: 0.4, areaCost: 2853, save: 295, gscShare: 5.4, gscCountries: 3, gapCountries: 32, tier: 'Early capability', tierColor: '#94a3b8' },
  { process: 'Execute', l3: 'Onboarding', system: 'IONIS', nsub: 2, ntask: 4, areaFte: 0.6, areaCost: 2496, save: 636, gscShare: 7.3, gscCountries: 5, gapCountries: 73, tier: 'Early capability', tierColor: '#94a3b8' }
]

export const countryMoveCandidates = [
  { country: 'India', movableTasks: 141, areaFte: 22.3, movableCost: 33000, saving: 58000 },
  { country: 'Brazil', movableTasks: 155, areaFte: 16.9, movableCost: 33000, saving: 49000 },
  { country: 'Argentina', movableTasks: 109, areaFte: 9.0, movableCost: 30000, saving: 40000 },
  { country: 'Italy', movableTasks: 159, areaFte: 11.7, movableCost: 71000, saving: 36000 },
  { country: 'Vietnam', movableTasks: 177, areaFte: 25.1, movableCost: 24000, saving: 35000 },
  { country: 'United States', movableTasks: 144, areaFte: 10.4, movableCost: 74000, saving: 28000 },
  { country: 'China', movableTasks: 132, areaFte: 20.6, movableCost: 48000, saving: 28000 },
  { country: 'Turkey', movableTasks: 139, areaFte: 8.0, movableCost: 33000, saving: 27000 },
  { country: 'Spain', movableTasks: 153, areaFte: 15.3, movableCost: 70000, saving: 26000 },
  { country: 'Egypt', movableTasks: 99, areaFte: 10.3, movableCost: 22000, saving: 25000 },
  { country: 'Malaysia', movableTasks: 148, areaFte: 10.7, movableCost: 18000, saving: 22000 },
  { country: 'Germany', movableTasks: 132, areaFte: 17.1, movableCost: 88000, saving: 18000 },
  { country: 'Australia', movableTasks: 125, areaFte: 7.0, movableCost: 41000, saving: 12000 },
  { country: 'United Kingdom', movableTasks: 126, areaFte: 11.4, movableCost: 51000, saving: 9000 },
  { country: 'France', movableTasks: 119, areaFte: 3.6, movableCost: 17000, saving: 5000 }
]

export const areaCountryColumns = [
  { id: 'country', label: 'Country', noWrap: true },
  { id: 'fte', label: 'Area FTE', noWrap: true },
  { id: 'cost', label: 'Area Cost', noWrap: true },
  { id: 'volume', label: 'Area Volume', noWrap: true },
  { id: 'redesignCost', label: 'Cost on GSC-handled tasks', noWrap: true }
]

export const processTableColumns = [
  { id: 'name', label: 'Process', noWrap: true },
  { id: 'fte', label: 'Area FTE', noWrap: true },
  { id: 'cost', label: 'Area Cost', noWrap: true },
  { id: 'volume', label: 'Volume', noWrap: true },
  { id: 'dArea', label: 'Designed Area', noWrap: true },
  { id: 'dDual', label: 'Dual', noWrap: true },
  { id: 'dGsc', label: 'Designed GSC', noWrap: true }
]

export const designReadinessColumns = [
  { id: 'l3', label: 'L3 Process', noWrap: true },
  { id: 'process', label: 'Process', noWrap: true },
  { id: 'system', label: 'System', noWrap: true },
  { id: 'nsub', label: 'Subprocesses', noWrap: true },
  { id: 'ntask', label: 'Tasks', noWrap: true },
  { id: 'areaFte', label: 'Area FTE', noWrap: true },
  { id: 'areaCost', label: 'Area Cost', noWrap: true },
  { id: 'save', label: 'Cost Saving', noWrap: true },
  { id: 'gscShare', label: 'GSC Share', noWrap: true },
  { id: 'gscCountries', label: 'GSC Countries', noWrap: true },
  { id: 'gapCountries', label: 'Country Gap', noWrap: true },
  { id: 'tier', label: 'Tier', noWrap: true }
]

export const countryMoveColumns = [
  { id: 'country', label: 'Country', noWrap: true },
  { id: 'movableTasks', label: 'Movable Tasks', noWrap: true },
  { id: 'areaFte', label: 'Area FTE', noWrap: true },
  { id: 'movableCost', label: 'Movable Area Cost', noWrap: true },
  { id: 'saving', label: 'Cost Saving', noWrap: true }
]

export const processTaskDetailColumns = [
  { id: 'task', label: 'Task', noWrap: true },
  { id: 'sub', label: 'Subprocess', noWrap: true },
  { id: 'system', label: 'System', noWrap: true },
  { id: 'areaFte', label: 'Area FTE', noWrap: true },
  { id: 'areaCost', label: 'Area Cost', noWrap: true },
  { id: 'save', label: 'Cost Saving', noWrap: true },
  { id: 'gscShare', label: 'GSC Share', noWrap: true },
  { id: 'gap', label: 'Country Gap', noWrap: true }
]

export const countryTaskDetailColumns = [
  { id: 'task', label: 'Task', noWrap: true },
  { id: 'areaFte', label: 'Area FTE', noWrap: true },
  { id: 'areaCost', label: 'Area Cost', noWrap: true },
  { id: 'save', label: 'Cost Saving', noWrap: true },
  { id: 'gscShare', label: 'GSC Share', noWrap: true },
  { id: 'tier', label: 'Tier', noWrap: true }
]

export const tierLabels = {
  1: 'Ready to scale',
  2: 'Partial capability',
  3: 'Early capability',
  4: 'New capability'
}
