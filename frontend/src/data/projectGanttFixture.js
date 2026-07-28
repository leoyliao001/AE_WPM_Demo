/**
 * Project Gantt fixture — field names match `gant graph.xlsx` (sheet: Project Gantt).
 * Timeline weeks are 1-based (wk01 = 1 … wk44 = 44).
 * Calendar weeks start at (intake submission ISO week) + 1.
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

export const PROJECT_GANTT_TIMELINE_COUNT = 44
export const PROJECT_GANTT_DEFAULT_CALENDAR_START = 9

const timelineWeeks = Array.from({ length: PROJECT_GANTT_TIMELINE_COUNT }, (_, index) => {
  const n = index + 1
  return `wk${String(n).padStart(2, '0')}`
})

/** Monday of an ISO week (UTC-safe date parts). */
const mondayOfIsoWeek = (year, week) => {
  // ISO week 1: week containing Jan 4
  const jan4 = new Date(Date.UTC(year, 0, 4))
  const day = jan4.getUTCDay() || 7
  const monday = new Date(jan4)
  monday.setUTCDate(jan4.getUTCDate() - day + 1 + (week - 1) * 7)
  return monday
}

const isoWeekParts = (date) => {
  const tmp = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
  const dayNum = tmp.getUTCDay() || 7
  tmp.setUTCDate(tmp.getUTCDate() + 4 - dayNum)
  const yearStart = new Date(Date.UTC(tmp.getUTCFullYear(), 0, 1))
  const week = Math.ceil(((tmp - yearStart) / 86400000 + 1) / 7)
  return { year: tmp.getUTCFullYear(), week }
}

/**
 * Build Gantt week columns.
 * @param {number|Date|string|null} startOrDate - calendar start week number, or intake createdAt
 */
export const buildProjectGanttWeeks = (startOrDate = PROJECT_GANTT_DEFAULT_CALENDAR_START) => {
  let startMonday

  if (startOrDate instanceof Date || typeof startOrDate === 'string') {
    const d = startOrDate instanceof Date ? startOrDate : new Date(startOrDate)
    if (!Number.isNaN(d.getTime())) {
      const { year, week } = isoWeekParts(d)
      startMonday = mondayOfIsoWeek(year, week)
      startMonday.setUTCDate(startMonday.getUTCDate() + 7) // work week + 1
    }
  }

  if (!startMonday) {
    const weekNum = Number(startOrDate)
    const safeWeek =
      Number.isFinite(weekNum) && weekNum >= 1 && weekNum <= 53
        ? weekNum
        : PROJECT_GANTT_DEFAULT_CALENDAR_START
    startMonday = mondayOfIsoWeek(new Date().getFullYear(), safeWeek)
  }

  return timelineWeeks.map((timelineWeek, index) => {
    const day = new Date(startMonday)
    day.setUTCDate(startMonday.getUTCDate() + index * 7)
    const { year, week } = isoWeekParts(
      new Date(day.getUTCFullYear(), day.getUTCMonth(), day.getUTCDate())
    )
    return {
      index: index + 1,
      timelineWeek,
      calendarWeek: `Wk${week}`,
      calendarWeekNumber: week,
      calendarYear: year
    }
  })
}

export const projectGanttWeeks = buildProjectGanttWeeks(PROJECT_GANTT_DEFAULT_CALENDAR_START)

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
