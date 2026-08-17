import {
  Document,
  Packer,
  Paragraph,
  Table,
  TableRow,
  TableCell,
  TextRun,
  ImageRun,
  HeadingLevel,
  AlignmentType,
  BorderStyle,
  WidthType,
  ShadingType,
  Header,
  Footer,
  PageNumber,
  convertInchesToTwip
} from 'docx'

const MAERSK_BLUE = '0077B8'
const DARK_BLUE = '003F6E'
const LIGHT_GREY = 'F3F7FB'
const MID_GREY = 'D0D8E0'
const TEXT_GREY = '5B6770'
const FONT_FAMILY = 'Maersk Text'

const t = (text, options = {}) =>
  new TextRun({
    text,
    font: options.font || FONT_FAMILY,
    ...options
  })

const hr = () =>
  new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 10, color: MAERSK_BLUE } },
    spacing: { after: 0, before: 0 }
  })

const sectionTitle = (text) =>
  new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 260, after: 110 },
    children: [t(text, { color: DARK_BLUE, bold: true, size: 20 })]
  })

const labelValue = (label, value) =>
  new Paragraph({
    children: [
      t(`${label}: `, { bold: true, size: 20, color: DARK_BLUE }),
      t(value || '—', { size: 20, color: '111111' })
    ],
    spacing: { after: 70 }
  })

const bodyText = (text) =>
  new Paragraph({
    children: [t(text || '—', { size: 20, color: '111111' })],
    spacing: { after: 70 }
  })

const spacer = (size = 200) => new Paragraph({ spacing: { before: size, after: 0 } })

const kvTable = (pairs = []) => {
  const headerRow = new TableRow({
    tableHeader: true,
    children: ['Topic', 'Details'].map(
      (text) =>
        new TableCell({
          children: [
            new Paragraph({
              children: [t(text, { bold: true, size: 20, color: 'FFFFFF' })],
              alignment: AlignmentType.LEFT
            })
          ],
          shading: { type: ShadingType.SOLID, color: DARK_BLUE },
          margins: { top: 80, bottom: 80, left: 120, right: 120 }
        })
    )
  })

  const rows = pairs.map(
    ([topic, detail]) =>
      new TableRow({
        children: [
          new TableCell({
            children: [
              new Paragraph({
                children: [t(topic || '—', { size: 20, color: DARK_BLUE, bold: true })],
                alignment: AlignmentType.LEFT
              })
            ],
            shading: { type: ShadingType.SOLID, color: LIGHT_GREY },
            margins: { top: 80, bottom: 80, left: 120, right: 120 }
          }),
          new TableCell({
            children: [
              new Paragraph({
                children: [
                  t(detail || '—', { size: 20, color: '111111' })
                ],
                alignment: AlignmentType.LEFT
              })
            ],
            margins: { top: 80, bottom: 80, left: 120, right: 120 }
          })
        ]
      })
  )

  return new Table({
    rows: [headerRow, ...rows],
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 6, color: MID_GREY },
      bottom: { style: BorderStyle.SINGLE, size: 6, color: MID_GREY },
      left: { style: BorderStyle.SINGLE, size: 6, color: MID_GREY },
      right: { style: BorderStyle.SINGLE, size: 6, color: MID_GREY },
      insideH: { style: BorderStyle.SINGLE, size: 3, color: MID_GREY },
      insideV: { style: BorderStyle.SINGLE, size: 3, color: MID_GREY }
    }
  })
}

const imageToPngArrayBuffer = async (svgText, width = 338, height = 112) =>
  await new Promise((resolve, reject) => {
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const ctx = canvas.getContext('2d')
    if (!ctx) {
      reject(new Error('Unable to create canvas for logo rendering'))
      return
    }

    const blob = new Blob([svgText], { type: 'image/svg+xml' })
    const url = URL.createObjectURL(blob)
    const img = new Image()
    img.onload = async () => {
      try {
        ctx.clearRect(0, 0, width, height)
        ctx.drawImage(img, 0, 0, width, height)
        URL.revokeObjectURL(url)
        const pngBlob = await new Promise((res) => canvas.toBlob(res, 'image/png'))
        if (!pngBlob) {
          reject(new Error('Unable to convert logo to PNG'))
          return
        }
        const buffer = await pngBlob.arrayBuffer()
        resolve(buffer)
      } catch (error) {
        reject(error)
      }
    }
    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('Unable to load logo image for header'))
    }
    img.src = url
  })

const loadMaerskLogoData = async () => {
  try {
    const templateLogoResponse = await fetch('/maersk-logo-template.png')
    if (templateLogoResponse.ok) {
      return await templateLogoResponse.arrayBuffer()
    }
  } catch {
    // ignore and continue to fallback assets
  }

  try {
    const pngResponse = await fetch('/maersk-logo.png')
    if (pngResponse.ok) {
      return await pngResponse.arrayBuffer()
    }
  } catch {
    // ignore and fallback to SVG
  }

  const svgResponse = await fetch('/maersk-logo.svg')
  if (!svgResponse.ok) {
    throw new Error('Maersk logo file not found in /public (expected maersk-logo.png or maersk-logo.svg).')
  }
  const svgText = await svgResponse.text()
  return await imageToPngArrayBuffer(svgText)
}

const listToText = (values) => (Array.isArray(values) ? values.filter(Boolean).join(', ') : '') || '—'

const makeContextDefinition = (project) => {
  const scope = project.proposedScope || 'the defined migration scope'
  return (
    `This business case defines the migration intent for ${project.projectName || 'the project'} ` +
    `(${project.migrationRequestId || 'N/A'}). It outlines why the initiative is needed, the operating context, ` +
    `the role and delivery setup, key risks, and the expected outcome. The primary scope covers ${scope}.`
  )
}

const makeBackground = (project, preparedDate) => {
  return (
    `The request was submitted by ${project.requestor || 'N/A'} on ${project.requestedDate || preparedDate}. ` +
    `It is categorized as "${project.migrationType || 'N/A'}" for the ${project.function || 'N/A'} function, ` +
    `covering ${listToText(project.products)} in region ${project.region || 'N/A'}. ` +
    `Areas in scope: ${listToText(project.areas)}. Countries in scope: ${listToText(project.countries)}.`
  )
}

const makeSummary = (project) => {
  const status = (project.status || 'new').replace(/_/g, ' ')
  const fte = project.fteNumber || 'N/A'
  return (
    `In summary, this initiative is currently in "${status}" status with an estimated ${fte} FTE in scope. ` +
    `The business case confirms the migration direction, identifies operational risks, and supports execution readiness ` +
    `for the next governance decision gate.`
  )
}

export async function generateBusinessCaseDocx(project) {
  const logoData = await loadMaerskLogoData()

  const today = new Date().toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'long',
    year: 'numeric'
  })

  const areas = listToText(project.areas)
  const countries = listToText(project.countries)
  const products = listToText(project.products)
  const languages = listToText(project.languageDependencies)
  const locationStrategies = (
    project.locationStrategyCustom
      ? project.customLocationStrategies ?? []
      : project.defaultLocationStrategies ?? []
  ).join(', ') || '—'

  const roleOverviewRows = [
    ['Requestor', project.requestor || '—'],
    ['Function', project.function || '—'],
    ['Region', project.region || '—'],
    ['Products', products],
    ['Location Strategy', locationStrategies],
    ['Language Dependencies', languages],
    ['Workforce Snapshot', `FTE: ${project.fteNumber || '—'} | JL2: ${project.jl2 || '—'} | JL3: ${project.jl3 || '—'} | JL4: ${project.jl4 || '—'}`]
  ]

  const doc = new Document({
    numbering: undefined,
    styles: {
      default: {
        document: {
          run: {
            font: FONT_FAMILY,
            size: 20,
            color: '111111'
          },
          paragraph: {
            spacing: {
              line: 300
            }
          }
        }
      }
    },
    sections: [
      {
        properties: {
          page: {
            margin: {
              top: convertInchesToTwip(0.6),
              right: convertInchesToTwip(0.75),
              bottom: convertInchesToTwip(0.75),
              left: convertInchesToTwip(0.75)
            }
          }
        },
        headers: {
          default: new Header({
            children: [
              new Paragraph({
                children: [
                  new ImageRun({
                    data: logoData,
                    transformation: { width: 211, height: 73 }
                  })
                ],
                alignment: AlignmentType.RIGHT,
                spacing: { after: 40 }
              }),
              new Paragraph({
                children: [
                  t('Migration Business Case Memo', { bold: true, size: 18, color: DARK_BLUE })
                ],
                alignment: AlignmentType.LEFT,
                spacing: { after: 50 }
              }),
              hr()
            ]
          })
        },
        footers: {
          default: new Footer({
            children: [
              hr(),
              new Paragraph({
                children: [
                  t('CONFIDENTIAL  ·  ', { size: 16, color: '9E9E9E' }),
                  t('Page ', { size: 16, color: '9E9E9E' }),
                  new TextRun({ children: [PageNumber.CURRENT], size: 16, color: '9E9E9E', font: FONT_FAMILY }),
                  t(' of ', { size: 16, color: '9E9E9E' }),
                  new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 16, color: '9E9E9E', font: FONT_FAMILY })
                ],
                alignment: AlignmentType.CENTER,
                spacing: { before: 40 }
              })
            ]
          })
        },
        children: [
          // ── Cover block ──────────────────────────────────────────────
          new Paragraph({
            children: [
              t('Business Case Memo', { bold: true, size: 36, color: DARK_BLUE })
            ],
            alignment: AlignmentType.LEFT,
            spacing: { before: 0, after: 80 }
          }),
          new Paragraph({
            children: [
              t(project.projectName || 'Untitled Project', { bold: true, size: 30, color: MAERSK_BLUE })
            ],
            alignment: AlignmentType.LEFT,
            spacing: { after: 80 }
          }),
          new Paragraph({
            children: [
              t(`${project.migrationRequestId}  ·  `, { size: 20, color: '757575' }),
              t(`Prepared: ${today}`, { size: 20, color: TEXT_GREY })
            ],
            spacing: { after: 240 }
          }),

          new Paragraph({
            children: [
              t('Prepared for internal migration governance and decision support.', {
                size: 19,
                italics: true,
                color: TEXT_GREY
              })
            ],
            spacing: { after: 150 }
          }),

          hr(),

          // ── 1. Definition ─────────────────────────────────────────────
          sectionTitle('1. Definition'),
          bodyText(makeContextDefinition(project)),

          // ── 2. Background ─────────────────────────────────────────────
          sectionTitle('2. Background'),
          bodyText(makeBackground(project, today)),
          labelValue('Migration Request ID', project.migrationRequestId),
          labelValue('Requested Date', project.requestedDate || today),
          labelValue('Requestor', project.requestor),
          labelValue('Current Status', (project.status || '—').replace(/_/g, ' ')),
          labelValue('Migration Type', project.migrationType),
          labelValue('Region', project.region),
          labelValue('Areas', areas),
          labelValue('Countries', countries),
          spacer(80),

          // ── 3. Role Overview ──────────────────────────────────────────
          sectionTitle('3. Role Overview'),
          kvTable(roleOverviewRows),
          spacer(90),

          new Paragraph({
            children: [t('Scope Description', { bold: true, size: 20, color: DARK_BLUE })],
            spacing: { after: 40 }
          }),
          bodyText(project.proposedScope),

          // ── 4. Risks & Considerations ────────────────────────────────
          sectionTitle('4. Risks & Considerations'),
          new Paragraph({
            children: [t('Risks', { bold: true, size: 20, color: DARK_BLUE })],
            spacing: { after: 40 }
          }),
          bodyText(project.risks || 'No specific risks were provided in the intake submission.'),

          new Paragraph({
            children: [t('Considerations', { bold: true, size: 20, color: DARK_BLUE })],
            spacing: { after: 40 }
          }),
          bodyText(
            `Location strategy: ${locationStrategies}. Language dependency: ${languages}. ` +
            `Workforce distribution (JL2/JL3/JL4): ${project.jl2 || '—'}/${project.jl3 || '—'}/${project.jl4 || '—'} ` +
            `with total ${project.jobLevelTotal ?? '—'}.`
          ),
          spacer(80),

          // ── 5. Summary ────────────────────────────────────────────────
          sectionTitle('5. Summary'),
          bodyText(makeSummary(project)),

          // ── 6. Appendix ───────────────────────────────────────────────
          sectionTitle('6. Appendix'),
          bodyText(''),
          spacer(160),

          hr(),
          new Paragraph({
            children: [
              t('This document is generated from Migration Intake database values and aligned with Maersk internal memo standards.', {
                size: 16,
                color: '9E9E9E',
                italics: true
              })
            ],
            alignment: AlignmentType.CENTER,
            spacing: { before: 160 }
          })
        ]
      }
    ]
  })

  const blob = await Packer.toBlob(doc)
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `Business_Case_${project.migrationRequestId ?? 'project'}.docx`
  a.click()
  URL.revokeObjectURL(url)
}
