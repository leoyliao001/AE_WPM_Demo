import { buildAreaCountryPairs } from '../data/areaCountryMapping'



export const REQUESTOR_PLACEHOLDER = 'LYL114'

export const DEFAULT_MIGRATION_STATUS = 'new'



const pad2 = (value) => String(value).padStart(2, '0')



export const formatLocalDateKey = (date = new Date()) =>

  `${date.getFullYear()}${pad2(date.getMonth() + 1)}${pad2(date.getDate())}`



export const formatRequestedDate = (date = new Date()) =>

  date.toLocaleString(undefined, {

    year: 'numeric',

    month: 'short',

    day: '2-digit',

    hour: '2-digit',

    minute: '2-digit',

    second: '2-digit'

  })



export const generateMigrationRequestId = (date = new Date()) => {

  const dateKey = formatLocalDateKey(date)

  const uniqueCode = String(Math.floor(100000 + Math.random() * 900000))

  return `WPM_PRJ_${dateKey}${uniqueCode}`

}



export const collectValidationErrors = ({

  form,

  customApprovalFileMeta

}) => {

  const missing = []



  if (!form.projectName.trim()) missing.push('Project name')

  if (!form.migrationType) missing.push('Migration type')

  if (!form.region) missing.push('Region')

  if (!form.areas.length) missing.push('Area')

  if (!form.countries.length) missing.push('Country')



  const defaultStrategies = form.defaultLocationStrategies ?? []

  const customStrategies = form.customLocationStrategies ?? []

  const activeStrategies = form.locationStrategyCustom ? customStrategies : defaultStrategies



  if (!activeStrategies.length) missing.push('Location Strategy')

  if (form.locationStrategyCustom && !form.customLocationStrategyJustification.trim()) {

    missing.push('Custom location strategy — Justification')

  }

  if (form.locationStrategyCustom && !customApprovalFileMeta.name) {

    missing.push('Custom location strategy — Approval attachment')

  }

  if (!form.function) missing.push('Function')

  if (!form.products.length) missing.push('Product')

  if (!form.proposedScope.trim()) missing.push('Proposed scope of the project')

  if (!form.languageDependencies.length) missing.push('Language dependency')

  if (!String(form.jl2 ?? '').trim()) missing.push('JL2')

  if (!String(form.jl3 ?? '').trim()) missing.push('JL3')

  if (!String(form.jl4 ?? '').trim()) missing.push('JL4')



  return missing

}



const resolveMigrationTypeLabel = (value, migrationTypes) =>

  migrationTypes.find((item) => item.value === value)?.label ?? value



export const buildSubmissionPreview = ({

  form,

  customApprovalFileMeta,

  migrationTypes,

  requestor = REQUESTOR_PLACEHOLDER,

  status = DEFAULT_MIGRATION_STATUS,

  now = new Date()

}) => {

  const requestedDate = formatRequestedDate(now)

  const migrationRequestId = generateMigrationRequestId(now)



  return {

    migrationRequestId,

    requestedDate,

    requestor,

    status,

    projectName: form.projectName.trim(),

    migrationType: resolveMigrationTypeLabel(form.migrationType, migrationTypes),

    migrationTypeValue: form.migrationType,

    region: form.region,

    areas: [...form.areas],

    countries: [...(form.countries ?? [])],

    areaCountryPairs: buildAreaCountryPairs(form.areas, form.countries ?? []),

    defaultLocationStrategies: form.locationStrategyCustom

      ? []

      : [...(form.defaultLocationStrategies ?? [])],

    customLocationStrategies: form.locationStrategyCustom

      ? [...(form.customLocationStrategies ?? [])]

      : [],

    locationStrategyCustom: form.locationStrategyCustom,

    customLocationStrategyJustification: form.customLocationStrategyJustification.trim(),

    customApprovalFile: customApprovalFileMeta.name

      ? { ...customApprovalFileMeta }

      : null,

    function: form.function,

    products: [...form.products],

    proposedScope: form.proposedScope.trim(),

    languageDependencies: [...form.languageDependencies],

    fteNumber: form.fteNumber,

    jl2: form.jl2 || '0',

    jl3: form.jl3 || '0',

    jl4: form.jl4 || '0',

    jobLevelTotal: Number(form.jl2 || 0) + Number(form.jl3 || 0) + Number(form.jl4 || 0),

    risks: form.risks.trim()

  }

}



export const previewSections = (preview) => [

  {

    id: 'request',

    title: 'Request Information',

    items: [

      { label: 'Migration Request ID', value: preview.migrationRequestId },

      { label: 'Requested Date', value: preview.requestedDate },

      { label: 'Requestor', value: preview.requestor },

      { label: 'Status', value: preview.status }

    ]

  },

  {

    id: 'project',

    title: 'Project Details',

    items: [

      { label: 'Project name', value: preview.projectName },

      { label: 'Migration type', value: preview.migrationType },

      { label: 'Region', value: preview.region },

      { label: 'Area', value: preview.areas.join(', ') },

      { label: 'Country', value: preview.countries.join(', ') },

      {

        label: 'Area ↔ Country',

        value: preview.areaCountryPairs.length

          ? preview.areaCountryPairs.map((pair) => `${pair.area} → ${pair.country}`).join('; ')

          : '—'

      },

      {

        label: 'Location Strategy',

        value: preview.locationStrategyCustom

          ? preview.customLocationStrategies.join(', ')

          : preview.defaultLocationStrategies.join(', ')

      },

      {

        label: 'Location Strategy mode',

        value: preview.locationStrategyCustom ? 'Custom' : 'Default'

      },

      ...(preview.locationStrategyCustom

        ? [

            {

              label: 'Custom justification',

              value: preview.customLocationStrategyJustification || '—'

            },

            {

              label: 'Approval attachment',

              value: preview.customApprovalFile?.name ?? '—'

            }

          ]

        : [])

    ]

  },

  {

    id: 'scope',

    title: 'Scope & Function',

    items: [

      { label: 'Function', value: preview.function },

      { label: 'Product', value: preview.products.join(', ') },

      { label: 'Proposed scope', value: preview.proposedScope, multiline: true }

    ]

  },

  {

    id: 'workforce',

    title: 'Workforce and Language',

    items: [

      { label: 'Language dependency', value: preview.languageDependencies.join(', ') },

      { label: 'JL2', value: preview.jl2 },

      { label: 'JL3', value: preview.jl3 },

      { label: 'JL4', value: preview.jl4 },

      { label: 'FTE number', value: preview.fteNumber },

      {

        label: 'Job level total',

        value: String(preview.jobLevelTotal)

      }

    ]

  },

  {

    id: 'risk',

    title: 'Risk Assessment',

    items: [

      {

        label: 'Risks',

        value: preview.risks || '—',

        multiline: true

      }

    ]

  }

]

