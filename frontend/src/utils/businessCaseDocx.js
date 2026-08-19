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
  VerticalAlign,
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
    spacing: { before: 320, after: 130 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: MAERSK_BLUE, space: 4 } },
    children: [t(text, { color: DARK_BLUE, bold: true, size: 22 })]
  })

const subTitle = (text) =>
  new Paragraph({
    children: [t(text, { bold: true, size: 20, color: MAERSK_BLUE })],
    spacing: { before: 60, after: 60 }
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

const TABLE_BORDERS = {
  top: { style: BorderStyle.SINGLE, size: 6, color: MID_GREY },
  bottom: { style: BorderStyle.SINGLE, size: 6, color: MID_GREY },
  left: { style: BorderStyle.SINGLE, size: 6, color: MID_GREY },
  right: { style: BorderStyle.SINGLE, size: 6, color: MID_GREY },
  insideH: { style: BorderStyle.SINGLE, size: 3, color: MID_GREY },
  insideV: { style: BorderStyle.SINGLE, size: 3, color: MID_GREY }
}

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
          verticalAlign: VerticalAlign.CENTER,
          shading: { type: ShadingType.SOLID, color: DARK_BLUE },
          margins: { top: 100, bottom: 100, left: 140, right: 140 }
        })
    )
  })

  const rows = pairs.map(
    ([topic, detail], index) =>
      new TableRow({
        children: [
          new TableCell({
            children: [
              new Paragraph({
                children: [t(topic || '—', { size: 20, color: DARK_BLUE, bold: true })],
                alignment: AlignmentType.LEFT
              })
            ],
            verticalAlign: VerticalAlign.CENTER,
            shading: { type: ShadingType.SOLID, color: LIGHT_GREY },
            margins: { top: 100, bottom: 100, left: 140, right: 140 }
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
            verticalAlign: VerticalAlign.CENTER,
            shading: index % 2 === 1 ? { type: ShadingType.SOLID, color: LIGHT_GREY } : undefined,
            margins: { top: 100, bottom: 100, left: 140, right: 140 }
          })
        ]
      })
  )

  return new Table({
    rows: [headerRow, ...rows],
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: TABLE_BORDERS
  })
}

const bulletList = (items = []) =>
  items
    .filter(Boolean)
    .map(
      (text) =>
        new Paragraph({
          children: [t('•', { size: 20, color: MAERSK_BLUE, bold: true }), t(`  ${text}`, { size: 20, color: '111111' })],
          indent: { left: 320, hanging: 220 },
          spacing: { after: 60 }
        })
    )

const checklistItem = (label, checked = false) =>
  new Paragraph({
    children: [
      t(checked ? '☑' : '☐', { size: 20, color: MAERSK_BLUE, bold: true }),
      t(`  ${label}`, { size: 20, color: '111111' })
    ],
    indent: { left: 320, hanging: 220 },
    spacing: { after: 50 }
  })

const dataTable = (headers = [], rows = []) => {
  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map(
      (text) =>
        new TableCell({
          children: [
            new Paragraph({
              children: [t(text, { bold: true, size: 20, color: 'FFFFFF' })],
              alignment: AlignmentType.LEFT
            })
          ],
          verticalAlign: VerticalAlign.CENTER,
          shading: { type: ShadingType.SOLID, color: DARK_BLUE },
          margins: { top: 100, bottom: 100, left: 140, right: 140 }
        })
    )
  })

  const bodyRows = rows.map(
    (cells, index) =>
      new TableRow({
        children: cells.map(
          (value) =>
            new TableCell({
              children: [
                new Paragraph({
                  children: [t(value || '—', { size: 20, color: '111111' })],
                  alignment: AlignmentType.LEFT
                })
              ],
              verticalAlign: VerticalAlign.CENTER,
              shading: index % 2 === 1 ? { type: ShadingType.SOLID, color: LIGHT_GREY } : undefined,
              margins: { top: 100, bottom: 100, left: 140, right: 140 }
            })
        )
      })
  )

  return new Table({
    rows: [headerRow, ...bodyRows],
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: TABLE_BORDERS
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

// Key Drivers checklist has no dedicated intake field — rendered unchecked, matching the template.
const KEY_DRIVER_OPTIONS = [
  'Cost Optimization',
  'Capacity Constraints',
  'Business Continuity',
  'Vendor Dependency Reduction',
  'Standardization',
  'Service Improvement',
  'New Capability Requirement',
  'Other'
]

const DEFAULT_RISK_ROWS = [
  ['Knowledge transfer dependency', ''],
  ['Attrition during transition', ''],
  ['Hiring challenges', ''],
  ['System/process complexity', ''],
  ['Business disruption risk', '']
]

const resolveLocationStrategies = (project) =>
  listToText(
    project.locationStrategyCustom ? project.customLocationStrategies : project.defaultLocationStrategies
  )

const makePurposeOfRequest = (project) => {
  const scope = project.proposedScope || 'the defined migration scope'
  const currentLocation = listToText(project.countries)
  const futureLocation = resolveLocationStrategies(project)
  return (
    `This business case seeks approval to migrate ${scope} from ${currentLocation} to ${futureLocation}. ` +
    `The migration includes ${project.fteNumber || 'N/A'} FTE supporting ${project.function || 'the'} function ` +
    `and is expected to improve operational resilience, scalability, and cost efficiency.`
  )
}

const makeCurrentStateRows = (project) => [
  ['Current operating model', `${project.migrationType || 'N/A'} for the ${project.function || 'N/A'} function.`],
  ['Current ownership/location', `${listToText(project.areas)} (${listToText(project.countries)})`],
  ['Existing challenges', project.risks || 'No specific challenges recorded in the intake submission.'],
  [
    'Why change is required now',
    `Requested by ${project.requestor || 'N/A'} on ${project.requestedDate || '—'}, ` +
      `currently in "${(project.status || 'new').replace(/_/g, ' ')}" status.`
  ]
]

const makeScopeRows = (project) => {
  const currentLocation = listToText(project.countries)
  const futureLocation = resolveLocationStrategies(project)
  const products = (project.products || []).filter(Boolean)

  if (!products.length) {
    return [[project.proposedScope || '—', currentLocation, futureLocation, project.fteNumber || '—']]
  }

  const rows = products.map((product) => [product, currentLocation, futureLocation, ''])
  rows.push(['Total', '', '', project.fteNumber || '—'])
  return rows
}

const makeRiskRows = (project) => {
  const items = (project.risks || '')
    .split(/\r?\n|;/)
    .map((item) => item.trim())
    .filter(Boolean)
  if (!items.length) return DEFAULT_RISK_ROWS
  return items.map((item) => [item, ''])
}

const makeAssumptions = (project) => [
  project.migrationTypeValue === '1:1-transfer'
    ? 'Migration follows a 1:1 FTE transfer model.'
    : 'Migration follows a new/additional scope resourcing model.',
  'Required systems access can be provisioned on time.',
  'Business SMEs will support knowledge transfer.',
  'Hiring timelines are achievable.'
]

const makeRecommendation = (project) => {
  const status = (project.status || 'new').replace(/_/g, ' ')
  return (
    `Based on the expected operational, strategic, and financial benefits, approval is requested to proceed with ` +
    `the proposed migration of ${project.projectName || 'this project'} (${project.migrationRequestId || 'N/A'}), ` +
    `currently in "${status}" status with ${project.fteNumber || 'N/A'} FTE in scope.`
  )
}

export async function generateBusinessCaseDocx(project) {
  const logoData = await loadMaerskLogoData()

  const today = new Date().toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'long',
    year: 'numeric'
  })

  const locationStrategies = resolveLocationStrategies(project)

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
                    type: 'png',
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
              t('Migration Business Case', { bold: true, size: 40, color: DARK_BLUE })
            ],
            alignment: AlignmentType.LEFT,
            spacing: { before: 0, after: 80 }
          }),
          new Paragraph({
            children: [
              t(project.projectName || 'Untitled Project', { bold: true, size: 28, color: MAERSK_BLUE })
            ],
            alignment: AlignmentType.LEFT,
            spacing: { after: 60 }
          }),
          new Paragraph({
            children: [
              t('Prepared for internal migration governance and decision support.', {
                size: 18,
                italics: true,
                color: TEXT_GREY
              })
            ],
            spacing: { after: 180 }
          }),

          hr(),

          // ── To / From / Date / Ref ───────────────────────────────────
          spacer(140),
          labelValue('To', 'Migration Governance Committee'),
          labelValue('From', project.requestor),
          labelValue('Date', today),
          labelValue('Ref', project.migrationRequestId),
          spacer(100),

          hr(),

          // ── 1. Purpose of Request ────────────────────────────────────
          sectionTitle('1. Purpose of Request'),
          bodyText(makePurposeOfRequest(project)),

          // ── 2. Background & Business Need ────────────────────────────
          sectionTitle('2. Background & Business Need'),
          subTitle('Current State'),
          kvTable(makeCurrentStateRows(project)),
          spacer(100),

          subTitle('Key Drivers'),
          bodyText('Check all that apply:'),
          ...KEY_DRIVER_OPTIONS.map((driver) => checklistItem(driver)),
          spacer(90),

          // ── 3. Proposed Scope ─────────────────────────────────────────
          sectionTitle('3. Proposed Scope'),
          subTitle('Activities in Scope'),
          dataTable(['Process / Activity', 'Current Location', 'Future Location', 'FTE'], makeScopeRows(project)),
          spacer(100),

          subTitle('Migration Approach'),
          labelValue('Wave approach', 'To be determined based on the migration plan.'),
          labelValue('Proposed timeline', 'Refer to the project Gantt plan for the detailed schedule.'),
          labelValue('Knowledge transfer approach', 'To be defined with the receiving GSC site.'),
          spacer(90),

          // ── 4. Expected Benefits ──────────────────────────────────────
          sectionTitle('4. Expected Benefits'),
          subTitle('Strategic Benefits'),
          ...bulletList([
            `Alignment with GSC strategy: ${locationStrategies}`,
            'Improved business continuity',
            'Reduced vendor dependency',
            'Better standardization and governance',
            'Greater scalability'
          ]),
          spacer(80),

          subTitle('Operational Benefits'),
          ...bulletList([
            'Process improvements',
            'Improved service levels',
            'Enhanced capability coverage',
            'Future automation opportunities'
          ]),
          spacer(80),

          subTitle('Financial Benefits'),
          dataTable(
            ['Item', 'Annual Impact'],
            [
              ['Current Cost', '—'],
              ['Future Cost', '—'],
              ['Savings / Cost Avoidance', '—'],
              ['One-Time Costs', '—'],
              ['Break-Even (if applicable)', '—']
            ]
          ),
          spacer(90),

          // ── 5. Risks & Considerations ─────────────────────────────────
          sectionTitle('5. Risks & Considerations'),
          dataTable(['Risk / Consideration', 'Mitigation'], makeRiskRows(project)),
          spacer(90),

          // ── 6. Assumptions ─────────────────────────────────────────────
          sectionTitle('6. Assumptions'),
          ...bulletList(makeAssumptions(project)),
          spacer(90),

          // ── 7. Recommendation ─────────────────────────────────────────
          sectionTitle('7. Recommendation'),
          bodyText(makeRecommendation(project)),

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
