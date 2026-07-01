export const migrationProductSummaries = [
  { id: 1, product: 'Ocean OPS', fte: 24, netBenefitUsd: 1250000 },
  { id: 2, product: 'Customs', fte: 18, netBenefitUsd: 860000 },
  { id: 3, product: 'Air', fte: 12, netBenefitUsd: 540000 },
  { id: 4, product: 'Contract Logistics', fte: 31, netBenefitUsd: 1980000 }
]

export const migrationTableRows = [
  {
    id: 1,
    site: 'Shanghai',
    product: 'Ocean OPS',
    migrationName: 'APAC Ocean Consolidation',
    status: 'In Progress',
    nextStep: 'Complete data mapping',
    artifactsPct: 68,
    timelinePct: 55,
    fteAllocation: 8
  },
  {
    id: 2,
    site: 'Rotterdam',
    product: 'Customs',
    migrationName: 'EU Customs Modernization',
    status: 'Planning',
    nextStep: 'Stakeholder sign-off',
    artifactsPct: 22,
    timelinePct: 18,
    fteAllocation: 5
  },
  {
    id: 3,
    site: 'Singapore',
    product: 'Air',
    migrationName: 'Air Freight Digitization',
    status: 'At Risk',
    nextStep: 'Resolve integration blockers',
    artifactsPct: 41,
    timelinePct: 62,
    fteAllocation: 4
  },
  {
    id: 4,
    site: 'Chicago',
    product: 'Contract Logistics',
    migrationName: 'Americas CL Rollout',
    status: 'On Track',
    nextStep: 'UAT preparation',
    artifactsPct: 79,
    timelinePct: 71,
    fteAllocation: 11
  },
  {
    id: 5,
    site: 'Mumbai',
    product: 'LCL',
    migrationName: 'India LCL Migration',
    status: 'In Progress',
    nextStep: 'Training material review',
    artifactsPct: 53,
    timelinePct: 48,
    fteAllocation: 6
  }
]

export const migrationTableColumns = [
  { id: 'site', label: 'Site', noWrap: true },
  { id: 'product', label: 'Product', noWrap: true },
  { id: 'migrationName', label: 'Migration name', noWrap: true },
  { id: 'status', label: 'Status', noWrap: true },
  { id: 'nextStep', label: 'Next required step', noWrap: false },
  { id: 'artifactsPct', label: 'Completion artifacts %', noWrap: true },
  { id: 'timelinePct', label: 'Completion timeline %', noWrap: true },
  { id: 'fteAllocation', label: 'FTE allocation', noWrap: true }
]

export const ldDashboardRows = [
  {
    id: 1,
    projectName: 'APAC Ocean Consolidation',
    product: 'Ocean OPS',
    tasks: 'Process mapping, SOP alignment, trainer onboarding',
    timeline: 'Q2 2026 – Q3 2026',
    fte: 6
  },
  {
    id: 2,
    projectName: 'EU Customs Modernization',
    product: 'Customs',
    tasks: 'Compliance training, system walkthrough',
    timeline: 'Q3 2026 – Q4 2026',
    fte: 4
  },
  {
    id: 3,
    projectName: 'Air Freight Digitization',
    product: 'Air',
    tasks: 'Role-based curriculum, assessment design',
    timeline: 'Q2 2026 – Q3 2026',
    fte: 3
  },
  {
    id: 4,
    projectName: 'Americas CL Rollout',
    product: 'Contract Logistics',
    tasks: 'Warehouse ops training, change management',
    timeline: 'Q4 2026 – Q1 2027',
    fte: 8
  }
]

export const ldDashboardColumns = [
  { id: 'projectName', label: 'Project name', noWrap: true },
  { id: 'product', label: 'Product', noWrap: true },
  { id: 'tasks', label: 'Tasks to be migrated (Scoping overview)', noWrap: false },
  { id: 'timeline', label: 'Timeline for L&D stage', noWrap: true },
  { id: 'fte', label: 'FTE', noWrap: true }
]

export const projectMilestones = [
  {
    id: 'gantt',
    title: 'Gantt',
    description: 'Migration timeline, dependencies, and critical path.',
    icon: 'mi-calendar',
    accent: '#0077B8'
  },
  {
    id: 'approvals',
    title: 'Approvals',
    description: 'Governance checkpoints and sign-off status.',
    icon: 'mi-file-check',
    accent: '#42B0D5'
  },
  {
    id: 'business-case',
    title: 'Business Case',
    description: 'Benefits, assumptions, and investment rationale.',
    icon: 'mi-chart-bars-vertical',
    accent: '#003F6E'
  },
  {
    id: 'cost',
    title: 'Cost Computation',
    description: 'Run-rate, transition cost, and savings model.',
    icon: 'mi-chart-line-up',
    accent: '#6DAA28'
  },
  {
    id: 'training',
    title: 'Training',
    description: 'L&D plan, readiness, and completion tracking.',
    icon: 'mi-monitor',
    accent: '#F3880E'
  }
]

export const projectMilestoneDetails = {
  gantt: {
    title: 'Gantt',
    summary: 'High-level migration schedule with phase gates and dependencies.',
    items: [
      { label: 'Discovery', value: 'Jan – Mar 2026', status: 'Complete' },
      { label: 'Design & Build', value: 'Apr – Aug 2026', status: 'In Progress' },
      { label: 'UAT & Training', value: 'Sep – Oct 2026', status: 'Planned' },
      { label: 'Go-Live', value: 'Nov 2026', status: 'Planned' }
    ]
  },
  approvals: {
    title: 'Approvals',
    summary: 'Track governance approvals required before each migration phase.',
    items: [
      { label: 'Steering Committee', value: 'Approved', status: 'Complete' },
      { label: 'IT Security Review', value: 'Approved with conditions', status: 'Complete' },
      { label: 'Regional Ops Sign-off', value: 'Pending', status: 'In Progress' },
      { label: 'Final Go-Live Approval', value: 'Not started', status: 'Planned' }
    ]
  },
  'business-case': {
    title: 'Business Case',
    summary: 'Opportunity assessment and expected business outcomes.',
    items: [
      { label: 'Annual run-rate savings', value: '$1.25M', status: 'On Track' },
      { label: 'Productivity uplift', value: '18%', status: 'On Track' },
      { label: 'Payback period', value: '14 months', status: 'On Track' },
      { label: 'Strategic priority', value: 'High', status: 'Confirmed' }
    ]
  },
  cost: {
    title: 'Cost Computation',
    summary: 'Transition investment versus net benefit by workstream.',
    items: [
      { label: 'One-time migration cost', value: '$420K', status: 'Estimated' },
      { label: 'Annual operating savings', value: '$1.25M', status: 'Forecast' },
      { label: 'Net benefit (3-year)', value: '$2.9M', status: 'Forecast' },
      { label: 'FTE redeployment', value: '32 FTE', status: 'Planned' }
    ]
  },
  training: {
    title: 'Training',
    summary: 'Learning & development readiness for migrated processes.',
    items: [
      { label: 'Curriculum designed', value: '85%', status: 'In Progress' },
      { label: 'Trainers certified', value: '12 / 15', status: 'In Progress' },
      { label: 'End-user completion', value: '0%', status: 'Not started' },
      { label: 'L&D timeline', value: 'Q2 – Q4 2026', status: 'Planned' }
    ]
  }
}

export const chatbotSuggestions = [
  'What documents are required for a migration request?',
  'How is FTE allocation calculated?',
  'What are the approval steps before go-live?',
  'Show me risks for Ocean OPS migration'
]
