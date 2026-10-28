import { utils } from 'xlsx'

export function buildStakeholderWorkbook(registration, exportedAt = new Date().toISOString()) {
  const workbook = utils.book_new()
  const members = registration.teamMembers || []
  const people = new Map(members.map(person => [person.id, person]))
  const assignments = registration.assignments || {}
  const roles = (registration.groups || []).flatMap(group => group.roles.map(role => ({ ...role, group: group.label })))
  const personValues = id => {
    const person = people.get(id)
    return [id || '', person?.fullName || '', person?.email || '', person?.title || '', person?.organization || '', person?.location || '']
  }
  const state = (role, assignment) => assignment.lockedAt ? 'Locked' : assignment.notApplicable ? 'Not applicable' :
    (role.code === 'msp_focals' ? assignment.mspRows?.length : assignment.personIds?.length) ? 'Draft' : 'Unassigned'
  function addSheet(name, rows, widths) {
    const sheet = utils.aoa_to_sheet(rows)
    sheet['!cols'] = widths.map(wch => ({ wch }))
    sheet['!autofilter'] = { ref: sheet['!ref'] }
    utils.book_append_sheet(workbook, sheet, name)
  }
  addSheet('Overview', [
    ['Field', 'Value'],
    ['Project ID', registration.projectId],
    ['Migration Request ID', registration.migrationRequestId],
    ['Project name', registration.projectName],
    ['Requestor', registration.requestor],
    ['Phase', 'Initiate'],
    ['Saved record', registration.saved ? 'Yes' : 'No'],
    ['Last saved at', registration.updatedAt || ''],
    ['Exported at', exportedAt],
    ['Export basis', 'Current page data, including local draft changes; export does not save or lock the registry.'],
    ['Required roles', roles.filter(role => role.required).length],
    ['Project Team members', members.length],
  ], [26, 100])
  const personHeaders = ['Person ID', 'Full name', 'Email', 'Title', 'Organization', 'Location']
  const roleRows = [['Group', 'Role code', 'Role', 'Description', 'Required', 'Multiple people', 'Assignment rule', 'Status', 'MSP', ...personHeaders, 'Notes', 'Locked at', 'Locked by']]
  for (const role of roles) {
    const assignment = assignments[role.code] || {}
    const entries = assignment.notApplicable ? [] : role.code === 'msp_focals'
      ? (assignment.mspRows || []).flatMap(row => (row.personIds?.length ? row.personIds : ['']).map(id => ({ id, msp: row.mspName })))
      : (assignment.personIds || []).map(id => ({ id, msp: '' }))
    for (const entry of entries.length ? entries : [{ id: '', msp: '' }]) {
      roleRows.push([
        role.group, role.code, role.label, role.description || '', role.required ? 'Yes' : 'No',
        role.multiple ? 'Yes' : 'No', role.assignmentRule || '', state(role, assignment), entry.msp || '',
        ...personValues(entry.id), assignment.notes || '', assignment.lockedAt || '', assignment.lockedBy || '',
      ])
    }
  }
  addSheet('Stakeholder Roles', roleRows, [24, 28, 32, 60, 12, 16, 32, 20, 26, 38, 28, 36, 28, 28, 24, 60, 28, 36])
  addSheet('Project Team', [personHeaders, ...members.map(person => personValues(person.id))], [38, 28, 36, 28, 28, 24])
  const msp = assignments.msp_focals || {}
  addSheet('MSP Focals', [
    ['MSP', ...personHeaders, 'Status', 'Notes', 'Locked at', 'Locked by'],
    ...(msp.notApplicable ? [] : (msp.mspRows || [])).flatMap(row => (row.personIds?.length ? row.personIds : ['']).map(id => [
      row.mspName || '', ...personValues(id), msp.lockedAt ? 'Locked' : id ? 'Draft' : 'Unassigned',
      msp.notes || '', msp.lockedAt || '', msp.lockedBy || '',
    ])),
  ], [28, 38, 28, 36, 28, 28, 24, 20, 60, 28, 36])
  addSheet('Change Log', [
    ['Timestamp', 'Changed by', 'Action', 'Role code', 'Role', 'Details', 'Full audit entry (JSON)'],
    ...(registration.auditLog || []).map(entry => [
      entry.at || '', entry.by || '', entry.action || '', entry.roleCode || '',
      roles.find(role => role.code === entry.roleCode)?.label || '', entry.details || '', JSON.stringify(entry),
    ]),
  ], [28, 36, 24, 28, 32, 70, 100])
  return workbook
}
