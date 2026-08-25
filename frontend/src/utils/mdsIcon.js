/**
 * MDS mc-icon expects the icon name WITHOUT the `mi-` prefix.
 * The component resolves icons as `mi-${icon}.js`.
 */
const ICON_ALIASES = {
  // Not all MDS icon names exist in the package; map app aliases to real files.
  list: 'list-bullets',
  'mi-list': 'list-bullets'
}

export const normalizeMdsIconName = (icon) => {
  if (!icon || icon === 'empty') return icon
  const aliased = ICON_ALIASES[icon] || icon
  return aliased.startsWith('mi-') ? aliased.slice(3) : aliased
}

export const patchMcIconComponent = (McIcon) => {
  if (!McIcon?.prototype?.renderIcon || McIcon.prototype.renderIcon.__mdsIconPatched) {
    return
  }

  const originalRenderIcon = McIcon.prototype.renderIcon

  const normalizeIconSize = (size) => {
    const value = Number(size)
    if (!Number.isFinite(value)) {
      return 20
    }
    // Installed icon package only ships 20px and 24px sets.
    return value <= 20 ? 20 : 24
  }

  McIcon.prototype.renderIcon = async function patchedRenderIcon(size) {
    const normalized = normalizeMdsIconName(this.icon)
    if (normalized !== this.icon) {
      this.icon = normalized
    }
    return originalRenderIcon.call(this, normalizeIconSize(size ?? this.size))
  }

  McIcon.prototype.renderIcon.__mdsIconPatched = true
}
