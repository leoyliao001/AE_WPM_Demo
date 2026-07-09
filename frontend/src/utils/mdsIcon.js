/**
 * MDS mc-icon expects the icon name WITHOUT the `mi-` prefix.
 * The component resolves icons as `mi-${icon}.js`.
 */
export const normalizeMdsIconName = (icon) => {
  if (!icon || icon === 'empty') return icon
  return icon.startsWith('mi-') ? icon.slice(3) : icon
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
    return originalRenderIcon.call(this, size)
  }

  McIcon.prototype.renderIcon.__mdsIconPatched = true
}
