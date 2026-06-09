/** UI labels for role `page_access` tokens (stored as settings:*-management:action). */

export const ROLE_PAGE_SETTINGS_KEYS = [
  'settings:dashboard-management',
  'settings:category-management',
  'settings:supplier-management',
  'settings:product-management',
  'settings:pos-management',
  'settings:finance-management',
  'settings:report-management',
  'settings:refund-management',
  'settings:delivery-management',
  'settings:history-management',
  'settings:commission-management',
  'settings:role-management',
  'settings:user-management',
] as const

const PAGE_I18N_KEY: Record<string, string> = {
  'settings:dashboard-management': 'pages.roleManagement.pages.dashboard',
  'settings:category-management': 'pages.roleManagement.pages.category',
  'settings:supplier-management': 'pages.roleManagement.pages.supplier',
  'settings:product-management': 'pages.roleManagement.pages.product',
  'settings:pos-management': 'pages.roleManagement.pages.pos',
  'settings:finance-management': 'pages.roleManagement.pages.finance',
  'settings:report-management': 'pages.roleManagement.pages.report',
  'settings:refund-management': 'pages.roleManagement.pages.refund',
  'settings:delivery-management': 'pages.roleManagement.pages.delivery',
  'settings:history-management': 'pages.roleManagement.pages.history',
  'settings:commission-management': 'pages.roleManagement.pages.commission',
  'settings:role-management': 'pages.roleManagement.pages.role',
  'settings:user-management': 'pages.roleManagement.pages.user',
}

const ACTION_I18N_KEY: Record<string, string> = {
  view: 'pages.roleManagement.actions.view',
  create: 'pages.roleManagement.actions.create',
  update: 'pages.roleManagement.actions.update',
  delete: 'pages.roleManagement.actions.delete',
  export: 'pages.roleManagement.actions.export',
  checkout: 'pages.roleManagement.actions.checkout',
  'adjust-stock': 'pages.roleManagement.actions.adjustStock',
  'view-adjust-stock': 'pages.roleManagement.actions.viewAdjustStock',
  'add-damage': 'pages.roleManagement.actions.addDamage',
  'view-add-damage': 'pages.roleManagement.actions.viewAddDamage',
  refund: 'pages.roleManagement.actions.refund',
}

export function parseRolePermissionToken(token: string): { page: string; action: string } | null {
  const normalized = String(token || '').trim().toLowerCase()
  if (!normalized.startsWith('settings:')) return null
  const lastColon = normalized.lastIndexOf(':')
  if (lastColon <= 'settings:'.length) return null
  return {
    page: normalized.slice(0, lastColon),
    action: normalized.slice(lastColon + 1),
  }
}

export function rolePageLabel(pageKey: string, t: (key: string) => string): string {
  const key = PAGE_I18N_KEY[pageKey]
  return key ? t(key) : pageKey
}

export function roleActionLabel(action: string, t: (key: string) => string): string {
  const key = ACTION_I18N_KEY[action]
  return key ? t(key) : action.replaceAll('-', ' ')
}

/** Single page name for tree headers and badges. */
export function formatRolePageToken(token: string, t: (key: string) => string): string | null {
  if (token === 'ALL_PAGES' || token === 'admin:*') return t('pages.roleManagement.allPages')
  const parsed = parseRolePermissionToken(token)
  if (!parsed) return null
  return rolePageLabel(parsed.page, t)
}

/** Page · action (optional detail). */
export function formatRolePermissionToken(token: string, t: (key: string) => string): string {
  const all = formatRolePageToken(token, t)
  if (all && (token === 'ALL_PAGES' || token === 'admin:*')) return all
  const parsed = parseRolePermissionToken(token)
  if (!parsed) return token
  return `${rolePageLabel(parsed.page, t)} · ${roleActionLabel(parsed.action, t)}`
}

export function uniqueRolePageLabels(tokens: string[], t: (key: string) => string): string[] {
  const names = new Set<string>()
  for (const token of tokens) {
    const label = formatRolePageToken(token, t)
    if (label) names.add(label)
  }
  return [...names]
}
