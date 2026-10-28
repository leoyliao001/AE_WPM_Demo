import assert from 'node:assert/strict'
import test from 'node:test'
import * as XLSX from 'xlsx'
import { buildArtefactWorkbook } from '../src/utils/projectArtefactExport.js'

test('exports project metadata and structured artefact sheets without changing source', () => {
  const record = {
    projectName: 'Test', migrationRequestId: 'TEST', status: 'draft', revision: 1,
    source: { population: 12 }, auditLog: [{ revision: 1, action: 'save', by: 'owner@example.com', old: {}, new: { rows: [] } }],
  }
  const before = JSON.stringify(record)
  const workbook = buildArtefactWorkbook(record, [
    ['Execution', [['PID', 'Hiring type'], ['PID-1', 'External']]],
    ['Area', [['PID', 'Area PID'], ['PID-1', 'AREA-1']]],
  ])
  assert.deepEqual(workbook.SheetNames, ['Overview', 'Execution', 'Area', 'Audit Log'])
  const roundtrip = XLSX.read(XLSX.write(workbook, { type: 'buffer', bookType: 'xlsx' }), { type: 'buffer' })
  assert.equal(XLSX.utils.sheet_to_json(roundtrip.Sheets.Execution)[0].PID, 'PID-1')
  assert.equal(JSON.stringify(record), before)
})

test('exports large audit snapshots safely within Excel cell limits with lossless JSON parts', () => {
  const entry = {
    revision: 10, action: 'save', old: {},
    new: { rows: Array.from({ length: 1000 }, (_, id) => ({ id, remarks: 'x'.repeat(500) })) },
  }
  const workbook = buildArtefactWorkbook({
    source: { population: 1000 }, auditLog: [entry],
  }, [])
  const bytes = XLSX.write(workbook, { type: 'buffer', bookType: 'xlsx' })
  const read = XLSX.read(bytes, { type: 'buffer' })
  const audit = XLSX.utils.sheet_to_json(read.Sheets['Audit Log'])
  assert.ok(audit.length > 1)
  assert.ok(audit.every(row => row.Changes.length <= 32000))
  assert.deepEqual(JSON.parse(audit.map(row => row.Changes).join('')), { old: entry.old, new: entry.new })
})
