export const STORAGE_KEY = 'automation_idea_records_v1'

export function mapInitiativeToProject(initiative) {
  if (!initiative || !initiative.id) return null

  const initiativeName = pickInitiativeName(initiative)

  return {
    id: initiative.id || 'N/A',
    name: initiativeName || 'Untitled Project',
    team: initiative.gscTeamName || initiative.yourTeam || 'N/A',
    automationStatus: initiative.automationStatus || initiative.projectStatus || 'N/A',
    approvalStage: 'brd',
    approvals: {
      ci: {
        status: getCIApprovalStatus(initiative),
        date: initiative.ciStatusDate || null,
        by: initiative.ciEmail || 'N/A'
      },
      po: {
        status: getPOApprovalStatus(initiative),
        date: initiative.poRemark ? new Date().toISOString() : null,
        by: initiative.poEmail || 'N/A'
      },
      dm: {
        status: getDMApprovalStatus(initiative),
        date: initiative.dmStatusDate || null,
        by: initiative.deliveryManager || 'N/A'
      },
      ciSignOff: {
        status: getCISignOffStatus(initiative),
        date:
          pickInitiativeRaw(initiative, [
            'ciSignOffDate',
            'CISignoffDate',
            'CISignOffDate',
            'CI_x0020_Sign_x0020_Off_x0020_Date'
          ]) || null,
        by: initiative.ciSm || initiative.ciEmail || 'N/A'
      },
      executionLeader: {
        status: getExecutionLeaderStatus(initiative),
        date: initiative.executionLeaderDate || null,
        by: initiative.eeLead || 'N/A'
      }
    },
    documents: getInitiativeDocuments(initiative),
    spItemId: initiative.spItemId,
    rawInitiative: initiative
  }
}

export function pickInitiativeName(initiative) {
  const candidates = [
    initiative.initiativeName,
    initiative.projectName,
    initiative.yourInitiative,
    initiative.initiativeTitle,
    initiative.title,
    initiative.name
  ]
  const found = candidates.find((v) => v !== undefined && v !== null && String(v).trim() !== '')
  return found ? String(found).trim() : ''
}

export function getCIApprovalStatus(initiative) {
  const status = String(initiative.projectStatus || initiative.ciStatus || '').trim()
  return status ? 'approved' : 'pending'
}

export function getPOApprovalStatus(initiative) {
  const remark = String(initiative.poRemark || initiative.poStatus || '').trim()
  return remark ? 'approved' : 'pending'
}

export function getDMApprovalStatus(initiative) {
  const dmStatus = String(initiative.dmStatus || initiative.signoff || '')
    .trim()
    .toLowerCase()
  const automationStatus = String(initiative.automationStatus || '')
    .trim()
    .toLowerCase()
  const dmEndDateRaw = pickInitiativeRaw(initiative, [
    'projectEndDate',
    'plannedEndDate',
    'ProjectEndDate',
    'PlannedEndDate',
    'endDate',
    'EndDate'
  ])
  const hasDMEndDate = dmEndDateRaw !== null && String(dmEndDateRaw).trim() !== ''
  const isDMComplete = dmStatus === 'complete' || dmStatus === 'completed'
  const isAutomationComplete =
    automationStatus === 'hypercare' ||
    automationStatus === 'complete' ||
    automationStatus === 'completed'
  if (isDMComplete || isAutomationComplete || hasDMEndDate) return 'approved'
  return 'pending'
}

export function getCISignOffStatus(initiative) {
  const ciSignOffDateRaw = pickInitiativeRaw(initiative, [
    'CISignoffDate',
    'ciSignOffDate',
    'CISignOffDate',
    'CI_x0020_Sign_x0020_Off_x0020_Date'
  ])
  const hasCISignOffDate = ciSignOffDateRaw !== null && String(ciSignOffDateRaw).trim() !== ''
  const signoffStatus = String(initiative.signoff || initiative.Signoff || '')
    .trim()
    .toLowerCase()
  const isSignoffComplete =
    signoffStatus === 'approved' || signoffStatus === 'complete' || signoffStatus === 'completed'
  return hasCISignOffDate || isSignoffComplete ? 'approved' : 'pending'
}

export function getExecutionLeaderStatus(initiative) {
  const automationStatus = String(initiative.automationStatus || '')
    .trim()
    .toLowerCase()
  const isValueRealized =
    automationStatus.includes('value realized') || automationStatus.includes('value realised')
  return isValueRealized ? 'approved' : 'pending'
}

export function getInitiativeDocuments(initiative) {
  const docs = []
  if (initiative.attachments && Array.isArray(initiative.attachments)) {
    initiative.attachments.forEach((att) => {
      docs.push({
        name: att.name || 'Attachment',
        url: att.url || '#',
        type: getFileType(att.name || ''),
        uploadedBy: att.uploadedBy || 'N/A'
      })
    })
  }
  if (docs.length === 0 && initiative.attachmentUrl) {
    String(initiative.attachmentUrl || '')
      .split(/\r?\n|;/)
      .map((x) => String(x || '').trim())
      .filter((x) => /^https?:\/\//i.test(x))
      .forEach((url, i) => {
        const nameFromPath = decodeURIComponent(url.split('?')[0].split('/').pop() || '').trim()
        docs.push({
          name: nameFromPath || `Attachment ${i + 1}`,
          url,
          type: getFileType(nameFromPath || ''),
          uploadedBy: 'N/A'
        })
      })
  }
  return docs
}

export function getFileType(filename) {
  const ext = (filename.split('.').pop() || '').toLowerCase()
  const typeMap = {
    pdf: 'pdf',
    doc: 'doc',
    docx: 'doc',
    xls: 'xlsx',
    xlsx: 'xlsx',
    ppt: 'pptx',
    pptx: 'pptx',
    txt: 'txt',
    jpg: 'jpg',
    png: 'jpg',
    gif: 'jpg'
  }
  return typeMap[ext] || 'txt'
}

export function getApprovalStatusLabel(status) {
  const statuses = {
    approved: 'Approved',
    pending: 'Pending',
    disabled: 'Disabled',
    hold: 'On Hold',
    rejected: 'Rejected'
  }
  return statuses[status] || status
}

export function getDocumentIcon(type) {
  const icons = { pdf: '📄', doc: '📝', docx: '📝', xlsx: '📊', pptx: '📈', txt: '📃' }
  return icons[type] || '📎'
}

export function formatDate(date) {
  if (!date) return 'N/A'
  const d = new Date(date)
  if (Number.isNaN(d.getTime())) return 'N/A'
  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const year = String(d.getFullYear())
  return `${day}/${month}/${year}`
}

export function pickInitiativeValue(initiative, keys) {
  if (!initiative || !Array.isArray(keys)) return 'N/A'
  for (const key of keys) {
    const value = initiative[key]
    if (value !== undefined && value !== null && String(value).trim() !== '') {
      return String(value).trim()
    }
  }
  return 'N/A'
}

export function pickInitiativeRaw(initiative, keys) {
  if (!initiative || !Array.isArray(keys)) return null
  for (const key of keys) {
    const value = initiative[key]
    if (value !== undefined && value !== null && String(value).trim() !== '') {
      return value
    }
  }
  return null
}

export function formatInitiativeDate(initiative, keys) {
  const value = pickInitiativeRaw(initiative, keys)
  if (value === null || value === undefined || String(value).trim() === '') return 'N/A'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return formatDate(value)
}

export function normalizeEmail(value) {
  return String(value || '').trim().toLowerCase()
}

const STAGE_DEADLINES = {
  assessment: 15,
  brd: 15,
  development: 105,
  signoff: 7,
  valueRealized: 15
}

function parseDisplayDate(value) {
  const v = String(value || '').trim()
  const parts = v.split('/')
  if (parts.length === 3) {
    const day = Number(parts[0])
    const month = Number(parts[1])
    const year = Number(parts[2])
    if (!Number.isNaN(day) && !Number.isNaN(month) && !Number.isNaN(year)) {
      return new Date(year, month - 1, day)
    }
  }
  return new Date(v)
}

function calcDurationDays(start, end) {
  if (start === 'N/A' || end === 'N/A') return null
  const s = parseDisplayDate(start)
  const e = parseDisplayDate(end)
  if (isNaN(s.getTime()) || isNaN(e.getTime())) return null
  const days = Math.round((e - s) / (1000 * 60 * 60 * 24))
  return days >= 0 ? days : null
}

function calcDuration(start, end) {
  const days = calcDurationDays(start, end)
  return days === null ? '—' : `${days}d`
}

function getDeadlineBadge(start, end, deadlineDays) {
  const days = calcDurationDays(start, end)
  if (days === null) return null
  const withinDeadline = days <= deadlineDays
  return {
    label: withinDeadline ? 'Within Time' : 'Delayed',
    appearance: withinDeadline ? 'info' : 'error',
    title: withinDeadline
      ? `Within deadline (${days}/${deadlineDays} days)`
      : `Beyond deadline (${days}/${deadlineDays} days)`
  }
}

export function buildApprovalChainSteps(project) {
  if (!project) return []
  const approvals = project.approvals
  const steps = [
    { role: 'Assessment', abbr: 'CI', approval: approvals.ci },
    { role: 'BRD', abbr: 'PO', approval: approvals.po },
    { role: 'Development', abbr: 'DM', approval: approvals.dm },
    { role: 'Sign Off', abbr: 'CISM', approval: approvals.ciSignOff },
    { role: 'Value Realised', abbr: 'EL', approval: approvals.executionLeader }
  ]

  return steps.map((step, index) => {
    let stepStatus = step.approval.status
    const isValueRealizedStage = step.abbr === 'EL'
    const shouldDisable =
      isValueRealizedStage &&
      approvals.executionLeader.status !== 'approved' &&
      approvals.ciSignOff.status !== 'approved'
    if (shouldDisable) stepStatus = 'disabled'
    return {
      ...step,
      status: stepStatus,
      statusLabel: getApprovalStatusLabel(stepStatus),
      isLast: index === steps.length - 1
    }
  })
}

export function buildApprovalDetail(project, formState = {}) {
  if (!project) return null

  const initiative = project.rawInitiative || {}
  const approvals = project.approvals
  const currentUserEmail = normalizeEmail(localStorage.getItem('intake_requestor_email') || '')

  const ciApprover = pickInitiativeValue(initiative, ['ciApprover', 'CIApprover', 'ciEmail', 'CIEmail'])
  const requestedDate = formatInitiativeDate(initiative, ['requestedDate', 'submittedDate', 'createdDate'])
  const ciStatusDate = formatInitiativeDate(initiative, ['ciStatusDate', 'CIStatusDate', 'ci_status_date'])
  const ciComments = pickInitiativeValue(initiative, ['ciComments', 'ciComment', 'ciRemark', 'ciRemarks'])
  const poEmail = pickInitiativeValue(initiative, ['poEmail', 'POEmail', 'poOwnerEmail'])
  const poComments = pickInitiativeValue(initiative, ['poComments', 'poComment', 'POComments'])
  const poStatusDate = formatInitiativeDate(initiative, ['poStatusDate', 'POStatusDate', 'poRemarkDate'])
  const dmEmail = pickInitiativeValue(initiative, ['deliveryManagerEmail', 'dmEmail', 'deliveryManager'])
  const projectStartDate = formatInitiativeDate(initiative, ['projectStartDate', 'startDate', 'ProjectStartDate'])
  const projectEndDate = formatInitiativeDate(initiative, ['projectEndDate', 'endDate', 'ProjectEndDate'])
  const developerComments = pickInitiativeValue(initiative, ['developerComments', 'dmComment', 'DMComment'])
  const emailSentToCI = formatInitiativeDate(initiative, [
    'EmailSenttoCI',
    'emailSentToCI',
    'ciSignOffEmailSentDate'
  ])
  const ciSignOffDate = formatInitiativeDate(initiative, [
    'CISignoffDate',
    'ciSignOffDate',
    'CISignOffDate'
  ])
  const ciSignOffSavedComment = pickInitiativeValue(initiative, [
    'CIFinalComment',
    'ciSignOffComment',
    'ciFinalComments'
  ])
  const emailSentToEL = formatInitiativeDate(initiative, ['EmailsenttoEL', 'emailSentToEL', 'elEmailSentDate'])
  const emailSentToELRaw = pickInitiativeRaw(initiative, [
    'EmailsenttoEL',
    'emailSentToEL',
    'elEmailSentDate'
  ])
  const hasEmailSentToEL = emailSentToELRaw !== null && String(emailSentToELRaw).trim() !== ''
  const elApprovedDate = formatInitiativeDate(initiative, ['executionLeaderDate', 'elApprovedDate'])
  const elFinalVL = pickInitiativeValue(initiative, ['elFinalVL', 'executionLeaderEmail'])
  const elSavedComment = pickInitiativeValue(initiative, ['elComment', 'ELComment', 'pidDetails'])
  const elSavedPid = pickInitiativeValue(initiative, ['pidDetails', 'PIDDetails'])
  const assessmentArea = pickInitiativeValue(initiative, [
    'yourArea',
    'regionArea',
    'area',
    'accountCountry',
    'region'
  ])
  const assessmentRequestedBy = pickInitiativeValue(initiative, [
    'requestorName',
    'requesterName',
    'requestedBy',
    'requestorEmail'
  ])

  const ciSignOffDateRaw = pickInitiativeRaw(initiative, ['CISignoffDate', 'ciSignOffDate', 'CISignOffDate'])
  const hasCISignOffDate = ciSignOffDateRaw !== null && String(ciSignOffDateRaw).trim() !== ''
  const hasDMEndDate = projectEndDate !== 'N/A' && String(projectEndDate).trim() !== ''
  const ciSOApproved = approvals.ciSignOff.status === 'approved'
  const elApproved = approvals.executionLeader.status === 'approved'
  const elOwnerEmail = normalizeEmail(elFinalVL)
  const isELOwner = Boolean(elOwnerEmail) && Boolean(currentUserEmail) && elOwnerEmail === currentUserEmail
  const ciApproverEmail = normalizeEmail(ciApprover)
  const cismEmail = normalizeEmail(pickInitiativeValue(initiative, ['ciSm', 'CISM', 'cism']))
  const isSignOffAuthorised =
    Boolean(currentUserEmail) &&
    (currentUserEmail === ciApproverEmail || currentUserEmail === cismEmail)
  const signOffLocked = !hasDMEndDate || !isSignOffAuthorised
  const signOffLockMsg = !hasDMEndDate
    ? 'Awaiting DM End Date'
    : 'Only CI Approver or CISM can approve sign-off'
  const canMarkValueRealized = !elApproved && hasCISignOffDate && isELOwner
  const elLockMessage = !hasCISignOffDate ? 'Awaiting Sign Off Date' : 'Allowed only for EL Final VL'

  return {
    meta: {
      initiative: project.name || pickInitiativeName(initiative) || 'N/A',
      estimatedFteSaving: pickInitiativeValue(initiative, [
        'estimatedFteSaving',
        'estimatedFTESaving',
        'estimatedFte'
      ]),
      finalFte: pickInitiativeValue(initiative, ['finalFte', 'finalFTE', 'FinalFTE'])
    },
    signOff: {
      approved: ciSOApproved,
      locked: signOffLocked,
      lockMessage: signOffLockMsg,
      hasEmailSentToEL,
      emailSentToEL,
      savedComment: ciSignOffSavedComment,
      comment: formState.ciSignOffComment || '',
      recipients: formState.execLeaderRecipients || ''
    },
    valueRealized: {
      approved: elApproved,
      canMark: canMarkValueRealized,
      lockMessage: elLockMessage,
      savedComment: elSavedComment,
      savedPid: elSavedPid,
      pid: formState.elPidDetails || '',
      comment: formState.elComment || ''
    },
    rows: [
      {
        key: 'assessment',
        stage: 'Assessment',
        responsible: 'CI',
        startDate: requestedDate,
        endDate: ciStatusDate,
        duration: calcDuration(requestedDate, ciStatusDate),
        email: ciApprover,
        status: approvals.ci.status,
        deadline: getDeadlineBadge(requestedDate, ciStatusDate, STAGE_DEADLINES.assessment),
        summary: ciComments,
        expandable: true,
        details: { area: assessmentArea, requestedBy: assessmentRequestedBy, comment: ciComments }
      },
      {
        key: 'brd',
        stage: 'BRD',
        responsible: 'PO/BI',
        startDate: ciStatusDate,
        endDate: poStatusDate,
        duration: calcDuration(ciStatusDate, poStatusDate),
        email: poEmail,
        status: approvals.po.status,
        deadline: getDeadlineBadge(ciStatusDate, poStatusDate, STAGE_DEADLINES.brd),
        summary: poComments,
        expandable: false,
        details: { comment: poComments }
      },
      {
        key: 'development',
        stage: 'Development',
        responsible: 'DM',
        startDate: projectStartDate,
        endDate: projectEndDate,
        duration: calcDuration(projectStartDate, projectEndDate),
        email: dmEmail,
        status: approvals.dm.status,
        deadline: getDeadlineBadge(projectStartDate, projectEndDate, STAGE_DEADLINES.development),
        summary: developerComments,
        expandable: false,
        details: { comment: developerComments }
      },
      {
        key: 'signoff',
        stage: 'Sign-off',
        responsible: 'CI',
        startDate: emailSentToCI,
        endDate: ciSignOffDate,
        duration: calcDuration(emailSentToCI, ciSignOffDate),
        email: ciApprover,
        status: approvals.ciSignOff.status,
        deadline: getDeadlineBadge(emailSentToCI, ciSignOffDate, STAGE_DEADLINES.signoff),
        summary: ciSignOffSavedComment || 'Pending action',
        expandable: true,
        actionType: 'signoff'
      },
      {
        key: 'valueRealized',
        stage: 'Value Realised',
        responsible: 'EL',
        startDate: emailSentToEL,
        endDate: elApprovedDate,
        duration: calcDuration(emailSentToEL, elApprovedDate),
        email: elApproved ? elFinalVL : 'N/A',
        status: canMarkValueRealized ? approvals.executionLeader.status : 'disabled',
        deadline: getDeadlineBadge(emailSentToEL, elApprovedDate, STAGE_DEADLINES.valueRealized),
        summary: elSavedComment || 'Pending action',
        expandable: true,
        actionType: 'valueRealized'
      }
    ]
  }
}

export function persistInitiativeToStorage(initiative) {
  const items = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  const index = items.findIndex((item) => String(item.id) === String(initiative.id))
  if (index >= 0) items[index] = { ...items[index], ...initiative }
  else items.push(initiative)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
}

export function loadInitiativesFromStorage() {
  return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
}
