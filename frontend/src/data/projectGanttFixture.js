/**
 * Project Gantt fixture — field names match `gant graph.xlsx` (sheet: Project Gantt).
 * Timeline weeks are 1-based (wk01 = 1 … wk44 = 44).
 * Calendar weeks start at (intake submission ISO week) + 1.
 */

/** Excel row-3 / row-4 headers (columns A–J). */
export const projectGanttFieldLabels = {
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

/** Legend tips for Plan / Actual bar types. */
export const projectGanttBarTypes = [
  {
    id: 'plan',
    label: 'Plan',
    hint: 'Editable plan',
    color: '#1E8BB5'
  },
  {
    id: 'actual',
    label: 'Actual',
    hint: 'Recorded progress · green if within Plan, pink if beyond',
    color: '#6DBF80',
    lateColor: '#E57F90'
  }
]

export const projectGanttLifecycleStages = [
  {
    id: 'initiate',
    label: 'Initiate',
    description: 'Authorise & define',
    color: '#1f78d1',
    tint: '#edf5fc'
  },
  {
    id: 'plan',
    label: 'Plan',
    description: 'Build the roadmap',
    color: '#14a3a3',
    tint: '#eaf7f6'
  },
  {
    id: 'execute',
    label: 'Execute',
    description: 'Do the work',
    color: '#7a5af8',
    tint: '#f2efff'
  },
  {
    id: 'monitor_control',
    label: 'Monitor & Control',
    description: 'Track & correct',
    color: '#5f9b2d',
    tint: '#f0f6ea'
  },
  {
    id: 'close_realize_value',
    label: 'Close & Realize Value',
    description: 'Finalise & learn',
    color: '#0b5fa5',
    tint: '#edf4f9'
  }
]

/** Migration Key Steps with lifecycle classifications from the reference Gantt. */
export const projectGanttTasks = [
  {
    id: 'business-case',
    name: 'Business Case (Memo)',
    lifecycleStage: 'initiate',
    plan: null,
    actual: null
  },
  {
    id: 'fbp-approval',
    name: 'FBP approval',
    lifecycleStage: 'initiate',
    plan: null,
    actual: null
  },
  {
    id: 'functional-head',
    name: 'Functional head approval',
    lifecycleStage: 'initiate',
    plan: null,
    actual: null
  },
  {
    id: 'elt-approval',
    name: 'ELT approval',
    lifecycleStage: 'initiate',
    plan: null,
    actual: null
  },
  {
    id: 'gsc-head',
    name: 'GSC Head -1 approval',
    lifecycleStage: 'initiate',
    plan: null,
    actual: null
  },
  {
    id: 'opportunity-assessment',
    name: 'Opportunity Assessment (Detailed task scoping)',
    lifecycleStage: 'initiate',
    plan: null,
    actual: null
  },
  {
    id: 'pid-approval',
    name: 'PID Approval',
    lifecycleStage: 'initiate',
    plan: null,
    actual: null
  },
  {
    id: 'hiring-request',
    name: 'Hiring Request approval',
    lifecycleStage: 'initiate',
    plan: null,
    actual: null
  },
  {
    id: 'resource-mobilization',
    name: 'Resource mobilization',
    lifecycleStage: 'execute',
    plan: null,
    actual: null
  },
  {
    id: 'neo-training',
    name: 'NEO + GSC L&D business & training stage',
    lifecycleStage: 'execute',
    plan: null,
    actual: null
  },
  {
    id: 'knowledge-transfer',
    name: 'Knowledge Transfer Business + System Training sessions + Assessments',
    lifecycleStage: 'plan',
    plan: null,
    actual: null
  },
  {
    id: 'volume-transfer',
    name: 'Volume Transfer/Ramp-up stage',
    lifecycleStage: 'execute',
    plan: null,
    actual: null
  },
  {
    id: 'hypercare',
    name: 'Hypercare stage',
    lifecycleStage: 'monitor_control',
    plan: null,
    actual: null
  },
  {
    id: 'hypercare-exit',
    name: 'Hypercare Exit Success Criteria Review',
    lifecycleStage: 'monitor_control',
    plan: null,
    actual: null
  },
  {
    id: 'sign-off',
    name: 'Migration Sign-off recommendation',
    lifecycleStage: 'close_realize_value',
    plan: null,
    actual: null
  },
  {
    id: 'capacity-release',
    name: 'Recommended soonest Capacity Release',
    lifecycleStage: 'close_realize_value',
    plan: null,
    actual: null
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
  lifecycleStages: projectGanttLifecycleStages,
  notes: projectGanttNotes,
  todayWeek: projectGanttTodayWeek
}
