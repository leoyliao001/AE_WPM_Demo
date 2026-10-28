export function questionnaireProgress(questionnaire, source) {
  const a = questionnaire.answers
  const questions = [
    Boolean(a.processType),
    Boolean(questionnaire.process.name && source.verticals.length && source.subprocesses),
    Boolean(a.sla && a.peakDays && a.peakMonths && source.region),
    Boolean(source.ready && a.languageFte),
    Boolean(a.startUtc && a.endUtc && a.operatingDays?.length),
    Boolean(a.applications?.length),
    Boolean(source.sites.length && (a.processType === 'new' || a.currentGsc)),
    Boolean(a.secondSite),
    Boolean(a.retainSupport === 'no' || a.retainSupport === 'yes' && a.retainedDetails),
    Boolean(a.otherInformation),
  ]
  const blockers = questions.flatMap((done, i) => done ? [] : [`Q${i + 1}`])
  if (questionnaire.flags.some(flag => !flag.owner || !flag.dueDate)) blockers.push('Attention flag owner / target date')
  if (questionnaire.mitigations.some(action => !action.description || !action.owner || !action.dueDate)) blockers.push('Mitigation description / owner / target date')
  if (questionnaire.flags.length && !questionnaire.mitigations.length) blockers.push('At least one mitigation action for flagged risks')
  return { questions, answered: questions.filter(Boolean).length, blockers }
}

export function biaExportSections(record) {
  const source = record.source
  return [
    ['Questionnaires', [
      ['Process', 'Process path', 'Status', 'Question', 'Answer'],
      ...record.questionnaires.flatMap(q => {
        const a = q.answers
        return [
          ['1. New or existing', a.processType],
          ['2. Vertical', source.verticals.join(', ')], ['2. Process', q.process.name],
          ['2. Subprocesses / project Scope', source.subprocesses],
          ['2. In-scope process activities', q.process.activities.join(', ')],
          ['3. SLA', a.sla], ['3. Region / Area', `${source.region} / ${source.areas.join(', ')}`],
          ['3. Peak days', a.peakDays], ['3. Peak months', a.peakMonths],
          ['4. Project total locked Final FTE (not a per-process allocation)', source.population ?? 'Not available'],
          ['4. Language-dependent FTE', a.languageFte],
          ['5. Operating hours UTC', `${a.startUtc || ''} - ${a.endUtc || ''}`],
          ['5. Operating days', a.operatingDays?.join(', ')],
          ['6. Applications', a.applications?.join(', ')],
          ['7. Current GSC', a.processType === 'new' ? 'None - new process' : a.currentGsc],
          ['7. Expected GSC', source.sites.join(', ')],
          ['8. Two-site recommendation', a.secondSite], ['8. Rationale', a.secondSiteReason],
          ['9. Retained contingency support', a.retainSupport], ['9. Details', a.retainedDetails],
          ['10. Other BCP information', a.otherInformation],
          ['Submitted by', q.submittedBy], ['Submitted at', q.submittedAt],
          ['Signed off by', q.signedOffBy], ['Signed off at', q.signedOffAt],
        ].map(([question, answer]) => [q.process.name, q.process.path, q.status, question, answer ?? ''])
      }),
    ]],
    ['Attention Flags', [
      ['Process', 'Flag', 'Owner', 'Target date'],
      ...record.questionnaires.flatMap(q => q.flags.map(flag => [q.process.name, record.flagLabels[flag.id], flag.owner, flag.dueDate])),
    ]],
    ['Mitigations', [
      ['Process', 'Action', 'Owner', 'Target date', 'Status'],
      ...record.questionnaires.flatMap(q => q.mitigations.map(action => [q.process.name, action.description, action.owner, action.dueDate, action.status])),
    ]],
    ['Joint Review', [
      ['Process', 'Role', 'Assigned reviewers', 'Reviewed by', 'Reviewed at', 'Comment', 'Admin override'],
      ...record.questionnaires.flatMap(q => Object.entries(record.reviewRoles).map(([role, definition]) => [
        q.process.name, definition.label, source.reviewers[role].map(p => `${p.name} <${p.email}>`).join('; '),
        q.reviews[role]?.by || '', q.reviews[role]?.at || '', q.reviews[role]?.comment || '', q.reviews[role]?.adminOverride ? 'Yes' : 'No',
      ])),
    ]],
  ]
}
