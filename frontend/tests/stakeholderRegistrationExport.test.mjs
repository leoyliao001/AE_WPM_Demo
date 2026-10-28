import assert from 'node:assert/strict'
import test from 'node:test'
import * as XLSX from 'xlsx'
import { buildStakeholderWorkbook } from '../src/utils/stakeholderRegistrationExport.js'

const rows = (workbook, sheet) => XLSX.utils.sheet_to_json(workbook.Sheets[sheet], { header: 1 })

test('exports all assignments, multiple people, MSPs, team details and the full audit log', () => {
  const registration = {
    projectId: 549, migrationRequestId: 'TEST-549', projectName: 'Test project', requestor: 'owner@example.com',
    saved: true, updatedAt: '2026-10-28T00:00:00Z',
    groups: [{ label: 'Leadership', roles: [
      { code: 'lead', label: 'Lead', required: true, multiple: true, assignmentRule: 'Sponsor' },
      { code: 'optional', label: 'Optional', required: false },
      { code: 'missing', label: 'Missing', required: true },
      { code: 'msp_focals', label: 'MSP Focals', multiple: true },
    ] }],
    teamMembers: [
      { id: 'one', fullName: '=Literal name', email: 'one@example.com', title: 'Manager', organization: 'Ops', location: 'Pune' },
      { id: 'two', fullName: 'Second person', email: 'two@example.com' },
    ],
    assignments: {
      lead: { personIds: ['one', 'two'], notes: 'Line one\nLine two', lockedAt: '2026-10-28', lockedBy: 'owner@example.com' },
      optional: { notApplicable: true },
      msp_focals: { mspRows: [{ mspName: 'MSP A', personIds: ['one'] }, { mspName: 'MSP B', personIds: [] }] },
    },
    auditLog: Array.from({ length: 12 }, (_, i) => ({ at: `event-${i}`, by: 'owner@example.com', action: 'save', roleCode: 'lead', details: `Edit ${i}` })),
  }
  const original = JSON.stringify(registration)
  const workbook = buildStakeholderWorkbook(registration, '2026-10-28T12:00:00Z')
  assert.deepEqual(workbook.SheetNames, ['Overview', 'Stakeholder Roles', 'Project Team', 'MSP Focals', 'Change Log'])
  const roles = XLSX.utils.sheet_to_json(workbook.Sheets['Stakeholder Roles'])
  assert.equal(roles.length, 6)
  assert.equal(roles[0].Status, 'Locked')
  assert.equal(roles[0]['Full name'], '=Literal name')
  assert.equal(roles[0].Notes, 'Line one\nLine two')
  assert.equal(roles[1].Email, 'two@example.com')
  assert.equal(roles[2].Status, 'Not applicable')
  assert.equal(roles[3].Status, 'Unassigned')
  assert.equal(rows(workbook, 'Project Team').length, 3)
  assert.equal(rows(workbook, 'MSP Focals').length, 3)
  assert.equal(rows(workbook, 'Change Log').length, 13)
  assert.equal(JSON.stringify(registration), original)
  const downloaded = XLSX.read(XLSX.write(workbook, { type: 'buffer', bookType: 'xlsx' }), { type: 'buffer' })
  assert.equal(downloaded.Sheets['Stakeholder Roles'].K2.t, 's')
  assert.equal(downloaded.Sheets['Stakeholder Roles'].K2.f, undefined)
  assert.equal(rows(downloaded, 'Overview').find(row => row[0] === 'Exported at')[1], '2026-10-28T12:00:00Z')
  assert.equal(rows(downloaded, 'Change Log').length, 13)
})

test('exports empty and unassigned registries with headers rather than omitting roles', () => {
  const workbook = buildStakeholderWorkbook({
    groups: [{ label: 'Group', roles: [{ code: 'empty', label: 'Empty role', required: true }] }],
  })
  assert.equal(rows(workbook, 'Stakeholder Roles').length, 2)
  assert.equal(XLSX.utils.sheet_to_json(workbook.Sheets['Stakeholder Roles'])[0].Status, 'Unassigned')
  for (const sheet of ['Project Team', 'MSP Focals', 'Change Log']) assert.equal(rows(workbook, sheet).length, 1)
})
