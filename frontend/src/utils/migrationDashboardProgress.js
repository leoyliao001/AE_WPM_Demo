const STATUS_LABELS = {
  new: 'New',
  in_review: 'In review',
  planning: 'Planning',
  in_progress: 'In progress',
  at_risk: 'At risk',
  completed: 'Completed'
}

const STATUS_PROGRESS = {
  new: 15,
  in_review: 30,
  planning: 45,
  in_progress: 70,
  at_risk: 55,
  completed: 100
}

const STATUS_APPEARANCE = {
  new: 'info',
  in_review: 'warning',
  planning: 'neutral',
  in_progress: 'info',
  at_risk: 'error',
  completed: 'success'
}

export const formatStatusLabel = (status) =>
  STATUS_LABELS[status] ?? status.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

export const statusAppearance = (status) => STATUS_APPEARANCE[status] ?? 'neutral'

export const overallProgress = (status) => STATUS_PROGRESS[status] ?? 10

export const buildProgressSteps = (status) => {
  const activeIndex = {
    new: 1,
    in_review: 1,
    planning: 2,
    in_progress: 3,
    at_risk: 3,
    completed: 4
  }[status] ?? 1

  const steps = [
    { id: 'intake', label: 'Intake submitted', description: 'Migration request captured in PAD.' },
    { id: 'review', label: 'Initial review', description: 'WPM team validates scope and ownership.' },
    { id: 'planning', label: 'Migration planning', description: 'Artifacts, timeline, and site readiness.' },
    { id: 'execution', label: 'Migration execution', description: 'Cutover activities across selected sites.' },
    { id: 'golive', label: 'Go-live', description: 'Steady-state handover and benefits tracking.' }
  ]

  return steps.map((step, index) => {
    if (index < activeIndex) {
      return { ...step, state: 'complete' }
    }
    if (index === activeIndex) {
      return { ...step, state: status === 'completed' && index === steps.length - 1 ? 'complete' : 'active' }
    }
    return { ...step, state: 'pending' }
  })
}

export const buildDetailSections = (project) => [
  {
    id: 'request',
    title: 'Request Information',
    accent: '#0077B8',
    icon: 'mi-file',
    items: [
      { label: 'Migration Request ID', value: project.migrationRequestId },
      { label: 'Requested Date', value: project.requestedDate },
      { label: 'Requestor', value: project.requestor },
      { label: 'Status', value: formatStatusLabel(project.status) }
    ]
  },
  {
    id: 'project',
    title: 'Project Details',
    accent: '#42B0D5',
    icon: 'mi-map',
    items: [
      { label: 'Project name', value: project.projectName },
      { label: 'Migration type', value: project.migrationType },
      { label: 'Region', value: project.region },
      { label: 'Area', value: (project.areas ?? []).join(', ') || '—' },
      { label: 'Country', value: (project.countries ?? []).join(', ') || '—' },
      {
        label: 'Area ↔ Country',
        value: (project.areaCountryPairs ?? []).length
          ? project.areaCountryPairs.map((pair) => `${pair.area} → ${pair.country}`).join('; ')
          : '—'
      },
      { label: 'Location Strategy', value: (project.locationStrategyCustom
        ? project.customLocationStrategies
        : project.defaultLocationStrategies ?? []).join(', ') || '—' },
      {
        label: 'Location Strategy mode',
        value: project.locationStrategyCustom ? 'Custom' : 'Default'
      }
    ]
  },
  {
    id: 'scope',
    title: 'Scope & Function',
    accent: '#003F6E',
    icon: 'mi-briefcase',
    items: [
      { label: 'Function', value: project.function },
      { label: 'Product', value: (project.products ?? []).join(', ') || '—' },
      { label: 'Proposed scope', value: project.proposedScope || '—', multiline: true }
    ]
  },
  {
    id: 'workforce',
    title: 'Workforce and Language',
    accent: '#F3880E',
    icon: 'mi-users',
    items: [
      {
        label: 'Language dependency',
        value: (project.languageDependencies ?? []).join(', ') || '—'
      },
      { label: 'FTE number', value: project.fteNumber },
      { label: 'JL2', value: project.jl2 },
      { label: 'JL3', value: project.jl3 },
      { label: 'JL4', value: project.jl4 },
      { label: 'Job level total', value: String(project.jobLevelTotal ?? '—') }
    ]
  },
  {
    id: 'risk',
    title: 'Risk Assessment',
    accent: '#E85454',
    icon: 'mi-exclamation-triangle',
    items: [{ label: 'Risks', value: project.risks || '—', multiline: true }]
  }
]
