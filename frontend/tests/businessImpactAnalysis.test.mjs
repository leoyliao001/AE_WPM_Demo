import assert from 'node:assert/strict'
import test from 'node:test'
import * as XLSX from 'xlsx'
import { biaExportSections, questionnaireProgress } from '../src/utils/businessImpactAnalysis.js'
import { buildArtefactWorkbook } from '../src/utils/projectArtefactExport.js'

function fixture() {
  const questionnaire = {
    id: 'process-1', process: { name: 'Invoicing', path: 'Ocean / Finance / Invoicing', activities: ['Validate'] },
    answers: {
      processType: 'new', sla: '24h', peakDays: '1–3', peakMonths: 'December', languageFte: 'None',
      startUtc: '22:00', endUtc: '06:00', operatingDays: ['Monday'], applications: ['SAP'],
      secondSite: 'no', retainSupport: 'no', otherInformation: 'None',
    },
    flags: [], mitigations: [], reviews: {}, status: 'draft',
  }
  const record = {
    projectName: 'Test', migrationRequestId: 'BIA-TEST', status: 'draft', revision: 1,
    source: { population: 12, ready: true, verticals: ['Ocean'], region: 'EUR', areas: ['NEU'],
      sites: ['Pune'], subprocesses: 'Invoice processing', reviewers: { area: [{ name: 'SME', email: 'area@example.com' }] } },
    questionnaires: [questionnaire], reviewRoles: { area: { label: 'Area' } },
    flagLabels: { second_site: 'Second site recommended' }, auditLog: [],
  }
  return { questionnaire, record }
}

test('requires exactly ten answers and locked project Final FTE; supports overnight shifts', () => {
  const { questionnaire: q, record } = fixture()
  assert.equal(questionnaireProgress(q, record.source).answered, 10)
  q.answers.otherInformation = ''
  assert.equal(questionnaireProgress(q, record.source).answered, 9)
  assert.deepEqual(questionnaireProgress(q, record.source).blockers, ['Q10'])
  record.source.ready = false
  assert.equal(questionnaireProgress(q, record.source).answered, 8)
  assert.ok(questionnaireProgress(q, record.source).blockers.includes('Q4'))
})

test('existing process, contingency support, flag ownership and mitigation gate submission', () => {
  const { questionnaire: q, record } = fixture()
  q.answers.processType = 'existing'
  q.answers.retainSupport = 'yes'
  q.flags = [{ id: 'second_site', owner: '', dueDate: '' }]
  let blockers = questionnaireProgress(q, record.source).blockers
  assert.ok(blockers.includes('Q7'))
  assert.ok(blockers.includes('Q9'))
  assert.ok(blockers.includes('Attention flag owner / target date'))
  assert.ok(blockers.includes('At least one mitigation action for flagged risks'))
  q.answers.currentGsc = 'Chengdu'
  q.answers.retainedDetails = '1 FTE for 3 months'
  q.flags[0] = { id: 'second_site', owner: 'risk@example.com', dueDate: '2027-01-01' }
  q.mitigations = [{ id: 'a1', description: 'Backup site', owner: 'risk@example.com', dueDate: '2027-01-01', status: 'open' }]
  assert.deepEqual(questionnaireProgress(q, record.source).blockers, [])
})

test('Excel roundtrip includes all answers, flags, mitigations, review actor and source snapshots without mutation', () => {
  const { questionnaire: q, record } = fixture()
  q.flags = [{ id: 'second_site', owner: 'risk@example.com', dueDate: '2027-01-01' }]
  q.mitigations = [{ id: 'a1', description: 'Backup coverage', owner: 'risk@example.com', dueDate: '2027-01-01', status: 'open' }]
  q.reviews.area = { by: 'admin@example.com', at: '2026-10-28T08:00:00Z', comment: 'Checked', adminOverride: true }
  record.auditLog = [{ revision: 1, action: 'save', old: {}, new: { questionnaires: [q], source: record.source } }]
  const before = JSON.stringify(record)
  const workbook = buildArtefactWorkbook(record, biaExportSections(record))
  const result = XLSX.read(XLSX.write(workbook, { type: 'buffer', bookType: 'xlsx' }), { type: 'buffer' })
  assert.deepEqual(result.SheetNames, ['Overview', 'Questionnaires', 'Attention Flags', 'Mitigations', 'Joint Review', 'Audit Log'])
  const answers = XLSX.utils.sheet_to_json(result.Sheets.Questionnaires)
  assert.equal(answers.find(row => row.Question === '7. Current GSC').Answer, 'None - new process')
  assert.equal(answers.find(row => row.Question.startsWith('4. Project total')).Answer, 12)
  assert.equal(answers.find(row => row.Question === '10. Other BCP information').Answer, 'None')
  assert.equal(XLSX.utils.sheet_to_json(result.Sheets.Mitigations)[0].Action, 'Backup coverage')
  assert.equal(XLSX.utils.sheet_to_json(result.Sheets['Joint Review'])[0]['Admin override'], 'Yes')
  assert.equal(JSON.stringify(record), before)
})
