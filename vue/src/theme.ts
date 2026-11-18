import type { BootConfig } from './types'

export function contrastText(hex?: string) {
  const value = String(hex || '').replace('#', '')
  if (!/^[0-9a-f]{6}$/i.test(value)) return '#0b2342'
  const r = parseInt(value.slice(0, 2), 16)
  const g = parseInt(value.slice(2, 4), 16)
  const b = parseInt(value.slice(4, 6), 16)
  const luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
  return luminance > 0.62 ? '#0b2342' : '#ffffff'
}

export function applyTheme(config?: BootConfig | null) {
  if (!config) return
  const root = document.documentElement
  const set = (name: string, value?: string) => {
    if (value && /^#[0-9a-f]{6}$/i.test(value)) root.style.setProperty(name, value)
  }
  set('--primary', config.themeColor)
  set('--page-bg', config.pageBackground)
  set('--card-bg', config.cardBackground)
  set('--header-bg', config.headerBackground)
  set('--ink', config.textColor)
  set('--muted', config.mutedColor)
  set('--line', config.borderColor)
  set('--icon', config.iconColor)
  root.style.setProperty(
    '--btn-text',
    config.buttonTextAuto === false ? config.buttonTextColor || '#fff' : contrastText(config.themeColor),
  )
  document.body.dataset.template = config.template || '1'
}