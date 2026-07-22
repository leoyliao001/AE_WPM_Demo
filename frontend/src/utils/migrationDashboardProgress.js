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

const MIGRATION_MILESTONE_DEFINITIONS = [
  { id: 'intake', label: 'Intake submitted', shortLabel: 'Intake', icon: 'mi-file', accent: '#0077B8' },
  {
    id: 'opportunity',
    label: 'Opportunity assessment',
    shortLabel: 'Opportunity',
    icon: 'mi-check-circle',
    accent: '#42B0D5'
  },
  { id: 'business_case', label: 'Business case', shortLabel: 'Business', icon: 'mi-briefcase', accent: '#003F6E' },
  { id: 'approvals', label: 'Approvals', shortLabel: 'Approvals', icon: 'mi-file-check', accent: '#6DAA28' },
  { id: 'training', label: 'Training', shortLabel: 'Training', icon: 'mi-monitor', accent: '#F3880E' },
  { id: 'gantt', label: 'Gantt', shortLabel: 'Gantt', icon: 'mi-chart-bars-vertical', accent: '#7B61FF' },
  { id: 'golive', label: 'Go-live', shortLabel: 'Go-live', icon: 'mi-flag', accent: '#E85454' }
]

const MILESTONE_TAG_APPEARANCE = {
  complete: 'success',
  active: 'info',
  pending: 'neutral',
  at_risk: 'error'
}

const resolveMilestoneStatus = (index, activeIndex, projectStatus) => {
  if (projectStatus === 'completed' || index < activeIndex) {
    return {
      state: 'complete',
      statusLabel: 'Complete',
      statusIcon: 'mi-check-circle',
      tagAppearance: MILESTONE_TAG_APPEARANCE.complete
    }
  }

  if (index === activeIndex) {
    if (projectStatus === 'at_risk') {
      return {
        state: 'at_risk',
        statusLabel: 'At risk',
        statusIcon: 'mi-exclamation-triangle',
        tagAppearance: MILESTONE_TAG_APPEARANCE.at_risk
      }
    }

    return {
      state: 'active',
      statusLabel: 'Up to date',
      statusIcon: 'mi-arrow-clockwise',
      tagAppearance: MILESTONE_TAG_APPEARANCE.active
    }
  }

  return {
    state: 'pending',
    statusLabel: 'Pending',
    statusIcon: 'mi-clock',
    tagAppearance: MILESTONE_TAG_APPEARANCE.pending
  }
}

const MILESTONE_ACTIVE_INDEX = {
  new: 1,
  in_review: 3,
  planning: 4,
  in_progress: 5,
  at_risk: 5,
  completed: 6
}

export const countCompletedMilestones = (status) => {
  const activeIndex = MILESTONE_ACTIVE_INDEX[status] ?? 1
  if (status === 'completed') return MIGRATION_MILESTONE_DEFINITIONS.length
  return Math.max(0, activeIndex)
}

export const migrationMilestoneTotal = MIGRATION_MILESTONE_DEFINITIONS.length

export const buildMigrationMilestones = (status) => {
  const activeIndex = MILESTONE_ACTIVE_INDEX[status] ?? 1

  return MIGRATION_MILESTONE_DEFINITIONS.map((milestone, index) => ({
    ...milestone,
    ...resolveMilestoneStatus(index, activeIndex, status)
  }))
}

/** @deprecated Use buildMigrationMilestones */
export const buildProgressSteps = (status) => buildMigrationMilestones(status)

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
      },
      ...(project.locationStrategyCustom
        ? [
            {
              label: 'Custom strategy justification',
              value: project.customLocationStrategyJustification || '—',
              multiline: true
            },
            {
              label: 'Approval attachment',
              value: project.customApprovalFile?.name
                ? `${project.customApprovalFile.name}${
                    project.customApprovalFile.size
                      ? ` (${Math.round(project.customApprovalFile.size / 1024)} KB)`
                      : ''
                  }`
                : '—'
            }
          ]
        : [])
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
    accent: '#42B0D5',
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
    accent: '#F3880E',
    icon: 'mi-exclamation-triangle',
    items: [{ label: 'Risks', value: project.risks || '—', multiline: true }]
  }
]
