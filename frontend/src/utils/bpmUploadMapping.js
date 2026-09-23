/**
 * Shared Excel header mapping for the BPM ROFO / BPM Actual importers.
 *
 * Both pages take their column list from the API response, so a backend field
 * change flows through to the download template, the upload parser and the
 * admin mapping dialog without a frontend edit.
 */

export function normalizeHeader(value) {
  return String(value ?? '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
}

/**
 * Header spellings accepted for one column, most preferred first: the field key,
 * then the template label, then any legacy aliases. The key comes first so that
 * a file exported straight from the API wins over a look-alike label column.
 */
export function candidateHeaders(column, aliases = {}) {
  const headers = []
  const push = (value) => {
    const norm = normalizeHeader(value)
    if (norm && !headers.includes(norm)) headers.push(norm)
  }
  push(column.key)
  push(column.label)
  ;(aliases[column.key] || []).forEach(push)
  return headers
}

/** Flatten one sheet row into { normalizedHeader: value }. */
export function normalizeRow(row) {
  const out = {}
  Object.entries(row || {}).forEach(([header, value]) => {
    out[normalizeHeader(header)] = value
  })
  return out
}

/**
 * Returns pick(key) -> the first non-empty value among that column's accepted
 * headers, or '' when the row carries none of them.
 */
export function createRowPicker(row, columns, aliases = {}) {
  const normalized = normalizeRow(row)
  const headersByKey = new Map(columns.map((col) => [col.key, candidateHeaders(col, aliases)]))
  return (key) => {
    const headers = headersByKey.get(key) || [normalizeHeader(key)]
    for (const header of headers) {
      const value = normalized[header]
      if (value !== undefined && value !== null && String(value) !== '') return value
    }
    return ''
  }
}

/**
 * Rows for the admin "Field Mapping" dialog.
 *
 * `computedKeys` are filled by page-specific logic rather than a plain header
 * match; `gridKeys` are the columns the page actually renders, so a field the
 * backend added but the grid does not know about shows up as drift.
 */
export function describeMapping(columns, { aliases = {}, computedKeys = [], gridKeys = [] } = {}) {
  const inGrid = new Set(gridKeys)
  return columns.map((col) => ({
    label: col.label,
    key: col.key,
    alsoAccepted: candidateHeaders(col, aliases).filter((h) => h !== normalizeHeader(col.label)),
    computed: computedKeys.includes(col.key),
    inGrid: inGrid.has(col.key)
  }))
}
