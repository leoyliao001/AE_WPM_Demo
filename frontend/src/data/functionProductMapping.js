/** Function → Product mapping from Function Product Mapping.xlsx */
export const functionProductMapping = {
  APMT: ['APMT'],
  'ATR (Accounting to Reporting)': [
    'General L&S',
    'General Ocean',
    'General Warehouse & Distribution'
  ],
  'Business Controlling': ['General L&S', 'General Ocean'],
  'Customer Delivery': [
    'Booking Services',
    'FCL',
    'First Mile',
    'Freight Audit & Payment',
    'General Air',
    'General Cold Chain',
    'General Customs',
    'General E-Commerce',
    'General INLAND',
    'General LCL',
    'General Ocean',
    'General Warehouse & Distribution',
    'Intermodal - Multicarrier',
    'Last Mile',
    'Maersk Flow',
    'Maersk NeoNav',
    'Maersk Project Logistics',
    'Middle Mile',
    'Ocean LCL',
    'SCM',
    'Supply Chain Orchestrator'
  ],
  'Customer Experience': ['General Ocean'],
  'Customer Program Management': ['General Lead Logistics'],
  'OCL - Ocean Fulfilment': ['General Ocean'],
  'OTC (Order to Cash)': ['General L&S', 'General Ocean'],
  'PTP (Procure to Pay)': ['General L&S', 'General Ocean'],
  'Sales Operations & Enablement': ['General Lead Logistics', 'General Ocean']
}

export const functions = Object.keys(functionProductMapping)

export const getProductsForFunction = (fn) => functionProductMapping[fn] ?? []
