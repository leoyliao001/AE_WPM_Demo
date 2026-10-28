import { utils, writeFile } from 'xlsx'

export function buildArtefactWorkbook(record, sections) {
  const workbook = utils.book_new()
  const overview = [
    ['Field', 'Value'], ['Project', record.projectName], ['Request ID', record.migrationRequestId],
    ['Status', record.status], ['Revision', record.revision],
    ['Scope population (locked Final FTE)', record.source.population ?? 'Not available'],
    ['Exported at', new Date().toISOString()], ['Basis', 'Current page draft. Export does not save or confirm.'],
  ]
  for (const [name, rows] of [['Overview', overview], ...sections]) {
    const sheet = utils.aoa_to_sheet(rows)
    sheet['!cols'] = rows[0].map(() => ({ wch: 28 }))
    sheet['!autofilter'] = { ref: sheet['!ref'] }
    utils.book_append_sheet(workbook, sheet, name)
  }
  const audit = utils.json_to_sheet(record.auditLog.flatMap(entry => {
    const changes = JSON.stringify({ old: entry.old, new: entry.new })
    const parts = changes.match(/[\s\S]{1,16000}/gu) || ['']
    return parts.map((part, index) => ({
      Revision: entry.revision, Action: entry.action, By: entry.by, At: entry.at,
      Reason: entry.reason, 'Changes part': `${index + 1}/${parts.length}`, Changes: part,
    }))
  }))
  utils.book_append_sheet(workbook, audit, 'Audit Log')
  return workbook
}

export function exportArtefact(record, title, sections) {
  const workbook = buildArtefactWorkbook(record, sections)
  const filename = `${record.migrationRequestId}-${title}`.replace(/[<>:"/\\|?*\u0000-\u001f]/g, '_')
  writeFile(workbook, `${filename}.xlsx`, { compression: true })
}
