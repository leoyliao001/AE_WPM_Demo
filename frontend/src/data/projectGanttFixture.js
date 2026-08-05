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

/** Legend tips for Standard / Plan / Actual bar types (Excel column J). */
export const projectGanttBarTypes = [
  {
    id: 'standard',
    label: 'Standard',
    hint: 'Standard cycle (fixed)',
    color: '#8E9BA8'
  },
  {
    id: 'plan',
    label: 'Plan',
    hint: 'Editable plan',
    color: '#1E8BB5'
  },
  {
    id: 'actual',
    label: 'Actual',
    hint: 'Auto from completion · green if within Plan, pink if beyond',
    color: '#6DBF80',
    lateColor: '#E57F90'
  }
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

const range = (startWeek, endWeek) => ({ startWeek, endWeek })

/** Task names from Excel; each step has Standard / Plan / Actual ranges. */
export const projectGanttTasks = [
  {
    id: 'business-case',
    name: 'Business Case (Memo)',
    standard: range(1, 5),
    plan: range(1, 5),
    actual: null,
    completedAt: null
  },
  {
    id: 'fbp-approval',
    name: 'FBP approval',
    standard: range(1, 5),
    plan: range(1, 5),
    actual: null,
    completedAt: null
  },
  {
    id: 'functional-head',
    name: 'Functional head approval',
    standard: range(3, 5),
    plan: range(3, 5),
    actual: null,
    completedAt: null
  },
  {
    id: 'elt-approval',
    name: 'ELT approg',
    standard: range(3, 5),
    plan: range(3, 5),
    actual: null,
    completedAt: null
  },
  {
    id: 'gsc-head',
    name: 'GSC Head -1 approval',
    standard: range(3, 5),
    plan: range(3, 5),
    actual: null,
    completedAt: null
  },
  {
    id: 'opportunity-assessment',
    name: 'Opportunity Assessment (Detailed task scoping)',
    standard: range(1, 5),
    plan: range(1, 5),
    actual: null,
    completedAt: null
  },
  {
    id: 'pid-approval',
    name: 'PID Approval',
    standard: range(6, 12),
    plan: range(6, 12),
    actual: null,
    completedAt: null
  },
  {
    id: 'hiring-request',
    name: 'Hiring Request approval',
    standard: range(6, 12),
    plan: range(6, 12),
    actual: null,
    completedAt: null
  },
  {
    id: 'resource-mobilization',
    name: 'Resource mobilization',
    standard: range(13, 23),
    plan: range(13, 23),
    actual: null,
    completedAt: null
  },
  {
    id: 'neo-training',
    name: 'NEO + GSC L&D business & training stage',
    standard: range(24, 27),
    plan: range(24, 27),
    actual: null,
    completedAt: null
  },
  {
    id: 'knowledge-transfer',
    name: 'Knowledge Transfer Business + System Training sessions + Assessments',
    standard: range(28, 30),
    plan: range(28, 30),
    actual: null,
    completedAt: null
  },
  {
    id: 'volume-transfer',
    name: 'Volume Transfer/Ramp-up stage',
    standard: range(31, 36),
    plan: range(31, 36),
    actual: null,
    completedAt: null
  },
  {
    id: 'hypercare',
    name: 'Hypercare stage',
    standard: range(37, 41),
    plan: range(37, 41),
    actual: null,
    completedAt: null
  },
  {
    id: 'hypercare-exit',
    name: 'Hypercare Exit Success Criteria Review',
    standard: range(42, 42),
    plan: range(42, 42),
    actual: null,
    completedAt: null
  },
  {
    id: 'sign-off',
    name: 'Migration Sign-off recommendation',
    standard: range(43, 43),
    plan: range(43, 43),
    actual: null,
    completedAt: null
  },
  {
    id: 'capacity-release',
    name: 'Recommended soonest Capacity Release',
    standard: range(44, 44),
    plan: range(44, 44),
    actual: null,
    completedAt: null
  }
]

export const projectGanttNotes = [
  {
    title: 'PID approval',
    items: [
      'request window is first 15 days of the month',
      'reply period of that request: by end of the respective month',
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
  barTypes: projectGanttBarTypes,
  tasks: projectGanttTasks,
  meta: projectGanttMeta,
  notes: projectGanttNotes,
  todayWeek: projectGanttTodayWeek
}
