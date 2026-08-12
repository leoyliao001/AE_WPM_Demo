/**
 * MDS mc-icon expects the icon name WITHOUT the `mi-` prefix.
 * The component resolves icons as `mi-${icon}.js`.
 *
 * The @maersk-global/icons package only ships 20px/24px folders.
 * Remap requested sizes to the nearest available folder.
 */
const ICON_ALIASES = {
  // Not all MDS icon names exist in the package; map app aliases to real files.
  list: 'list-bullets',
  'mi-list': 'list-bullets',
  layers: 'stack',
  'mi-layers': 'stack'
}

const AVAILABLE_ICON_SIZES = [20, 24]

export const normalizeMdsIconName = (icon) => {
  if (!icon || icon === 'empty') return icon
  const aliased = ICON_ALIASES[icon] || icon
  return aliased.startsWith('mi-') ? aliased.slice(3) : aliased
}

export const nearestMdsIconSize = (size) => {
  const n = Number(size)
  if (!Number.isFinite(n)) return 24
  let best = AVAILABLE_ICON_SIZES[0]
  let bestDist = Math.abs(n - best)
  for (const candidate of AVAILABLE_ICON_SIZES) {
    const dist = Math.abs(n - candidate)
    if (dist < bestDist) {
      best = candidate
      bestDist = dist
    }
  }
  return best
}

export const patchMcIconComponent = (McIcon) => {
  if (!McIcon?.prototype?.renderIcon || McIcon.prototype.renderIcon.__mdsIconPatched) {
    return
  }

  const originalRenderIcon = McIcon.prototype.renderIcon

  McIcon.prototype.renderIcon = async function patchedRenderIcon(size) {
    const normalized = normalizeMdsIconName(this.icon)
    if (normalized !== this.icon) {
      this.icon = normalized
    }
    return originalRenderIcon.call(this, nearestMdsIconSize(size))
  }

  McIcon.prototype.renderIcon.__mdsIconPatched = true
}
