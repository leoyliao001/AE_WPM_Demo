/**
 * Persist Handsontable column widths in localStorage (per browser / per table).
 */

const STORAGE_PREFIX = 'ae-wpm-hot-col-widths:'

export function loadColumnWidths(tableId) {
  if (typeof localStorage === 'undefined' || !tableId) return {}
  try {
    const raw = localStorage.getItem(`${STORAGE_PREFIX}${tableId}`)
    if (!raw) return {}
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return {}
    return parsed
  } catch {
    return {}
  }
}

export function hasStoredColumnWidths(tableId) {
  return Object.keys(loadColumnWidths(tableId)).length > 0
}

export function resolveColumnWidth(defaultWidth, columnKey, storedWidths) {
  const value = storedWidths?.[columnKey]
  const parsed = Number(value)
  if (Number.isFinite(parsed) && parsed > 0) {
    return Math.round(parsed)
  }
  return defaultWidth
}

export function persistColumnWidths(hot, tableId, columnKeys) {
  if (!hot || hot.isDestroyed || !tableId || !Array.isArray(columnKeys)) return

  const widths = {}
  columnKeys.forEach((key) => {
    let colIndex
    try {
      colIndex = hot.propToCol(key)
    } catch {
      return
    }
    if (typeof colIndex !== 'number' || colIndex < 0) return
    const width = hot.getColWidth(colIndex)
    if (Number.isFinite(width) && width > 0) {
      widths[key] = Math.round(width)
    }
  })

  try {
    localStorage.setItem(`${STORAGE_PREFIX}${tableId}`, JSON.stringify(widths))
  } catch {
    // Ignore quota / private-mode failures
  }
}

/** Handsontable hook: save widths after the user finishes dragging a column edge. */
export function createAfterColumnResizeHandler(tableId, columnKeys) {
  return function afterColumnResize() {
    persistColumnWidths(this, tableId, columnKeys)
  }
}
