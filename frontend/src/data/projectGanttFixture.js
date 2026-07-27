/**
 * Project Gantt fixture — field names match `gant graph.xlsx` (sheet: Project Gantt).
 * Timeline weeks are 1-based (wk01 = 1 … wk44 = 44).
 */

/** Excel row-3 / row-4 headers (columns A–J). */
export const projectGanttFieldLabels = {
  projectPhase: 'Project Phase',
  scope: 'Scope',
  migratableFte: 'Migratable FTE',
  learningCurve: 'Learning Curve',
  tlTmHc: 'TL/TM HC',
  mngrHc: 'Mngr. HC',
  totalWoBuffer: 'Total wo/buffer',
  total: 'Total',
  migrationKeySteps:
    'Migration Key Steps -  A view at expected critical outcomes, items and activities.',
  calendarWeeks: 'Calendar weeks',
  timelineWeeks: 'Timeline weeks'
}

const calendarWeeks = [
  'Wk9', 'Wk10', 'Wk11', 'Wk12', 'Wk13', 'Wk14', 'Wk15', 'Wk16',
  'Wk17', 'Wk18', 'Wk19', 'Wk20', 'Wk21', 'Wk22', 'Wk23', 'Wk24',
  'Wk25', 'Wk26', 'Wk27', 'Wk28', 'Wk29', 'Wk30', 'Wk31', 'Wk32',
  'Wk33', 'Wk34', 'Wk35', 'Wk36', 'Wk37', 'Wk38', 'Wk39', 'Wk40',
  'Wk41', 'Wk42', 'Wk43', 'Wk44', 'Wk45', 'Wk46', 'Wk47', 'Wk48',
  'Wk49', 'Wk50', 'Wk51', 'Wk52'
]

const timelineWeeks = [
  'wk01', 'wk02', 'wk03', 'wk04', 'wk05', 'wk06', 'wk07', 'wk08',
  'wk09', 'wk10', 'wk11', 'wk12', 'wk13', 'wk14', 'wk15', 'wk16',
  'wk17', 'wk18', 'wk19', 'wk20', 'wk21', 'wk22', 'wk23', 'wk24',
  'wk25', 'wk26', 'wk27', 'wk28', 'wk29', 'wk30', 'wk31', 'wk32',
  'wk33', 'wk34', 'wk35', 'wk36', 'wk37', 'wk38', 'wk39', 'wk40',
  'wk41', 'wk42', 'wk43', 'wk44'
]

export const projectGanttWeeks = timelineWeeks.map((timelineWeek, index) => ({
  index: index + 1,
  timelineWeek,
  calendarWeek: calendarWeeks[index] || ''
}))

/** Top legend + phase summary — attachment strip, slightly more vivid. */
export const projectGanttPhases = [
  { id: 'opportunity', label: 'Opportunity Assessment', color: '#6E6E6E', startWeek: 1, endWeek: 5 },
  { id: 'onboarding', label: 'Resource Onboarding', color: '#0086E6', startWeek: 6, endWeek: 23 },
  { id: 'gss-training', label: 'GSS Training', color: '#A3450A', startWeek: 24, endWeek: 27 },
  { id: 'knowledge-transfer', label: 'Knowledge Transfer', color: '#FFA008', startWeek: 28, endWeek: 30 },
  { id: 'volume-rampup', label: 'Volume Ramp-up', color: '#1A9EBE', startWeek: 31, endWeek: 36 },
  { id: 'hypercare', label: 'Hypercare', color: '#001A75', startWeek: 37, endWeek: 41 },
  { id: 'closure', label: 'Project Closure', color: '#00C853', startWeek: 42, endWeek: 44 }
]

export const projectGanttMeta = {
  projectPhase: 'Phase 1 ',
  scope: 'Project',
  migratableFte: 1,
  learningCurve: 1,
  tlTmHc: 1,
  mngrHc: 1,
  totalWoBuffer: 3,
  total: 4
}

/** Task names copied from Excel column I; phaseId maps to legend status. */
export const projectGanttTasks = [
  { id: 'business-case', name: 'Business Case (Memo)', startWeek: 1, endWeek: 5, phaseId: 'opportunity' },
  { id: 'fbp-approval', name: 'FBP approval', startWeek: 1, endWeek: 5, phaseId: 'opportunity' },
  { id: 'functional-head', name: 'Functional head approval', startWeek: 3, endWeek: 5, phaseId: 'opportunity' },
  { id: 'elt-approval', name: 'ELT approg', startWeek: 3, endWeek: 5, phaseId: 'opportunity' },
  { id: 'gsc-head', name: 'GSC Head -1 approval', startWeek: 3, endWeek: 5, phaseId: 'opportunity' },
  {
    id: 'opportunity-assessment',
    name: 'Opportunity Assessment (Detailed task scoping)',
    startWeek: 1,
    endWeek: 5,
    phaseId: 'opportunity'
  },
  { id: 'pid-approval', name: 'PID Approval', startWeek: 6, endWeek: 12, phaseId: 'onboarding' },
  { id: 'hiring-request', name: 'Hiring Request approval', startWeek: 6, endWeek: 12, phaseId: 'onboarding' },
  { id: 'resource-mobilization', name: 'Resource mobilization', startWeek: 13, endWeek: 23, phaseId: 'onboarding' },
  {
    id: 'neo-training',
    name: 'NEO + GSC L&D business & training stage',
    startWeek: 24,
    endWeek: 27,
    phaseId: 'gss-training'
  },
  {
    id: 'knowledge-transfer',
    name: 'Knowledge Transfer Business + System Training sessions + Assessments',
    startWeek: 28,
    endWeek: 30,
    phaseId: 'knowledge-transfer'
  },
  {
    id: 'volume-transfer',
    name: 'Volume Transfer/Ramp-up stage',
    startWeek: 31,
    endWeek: 36,
    phaseId: 'volume-rampup'
  },
  { id: 'hypercare', name: 'Hypercare stage', startWeek: 37, endWeek: 41, phaseId: 'hypercare' },
  {
    id: 'hypercare-exit',
    name: 'Hypercare Exit Success Criteria Review',
    startWeek: 42,
    endWeek: 42,
    phaseId: 'closure'
  },
  {
    id: 'sign-off',
    name: 'Migration Sign-off recommendation',
    startWeek: 43,
    endWeek: 43,
    phaseId: 'closure'
  },
  {
    id: 'capacity-release',
    name: 'Recommended soonest Capacity Release',
    startWeek: 44,
    endWeek: 44,
    phaseId: 'closure'
  }
]

export const projectGanttNotes = [
  {
    title: 'PID approval',
    items: [
      'request window is first 15 days of the monht',
      'reply period of that request: by end of the respective monht',
      'create the hiring approval request: approved every two weeks of each month',
      'workday requisition - that takes about a week'
    ]
  }
]

export const projectGanttTodayWeek = 1

export const projectGanttFixture = {
  fieldLabels: projectGanttFieldLabels,
  title: projectGanttFieldLabels.migrationKeySteps,
  weeks: projectGanttWeeks,
  phases: projectGanttPhases,
  tasks: projectGanttTasks,
  meta: projectGanttMeta,
  notes: projectGanttNotes,
  todayWeek: projectGanttTodayWeek
}
