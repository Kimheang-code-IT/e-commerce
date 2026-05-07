export const PERMISSIONS = {
  dashboardView: 'dashboard:view',
  categoryView: 'category:view',
  categoryCreate: 'category:create',
  categoryUpdate: 'category:update',
  categoryDelete: 'category:delete',
  productView: 'product:view',
  productCreate: 'product:create',
  productUpdate: 'product:update',
  productDelete: 'product:delete',
  posView: 'pos:view',
  posCreate: 'pos:create',
  reportView: 'report:view',
  commissionView: 'commission:view',
  financeView: 'finance:view',
  financeUpdate: 'finance:update',
  deliveryView: 'delivery:view',
  historyView: 'history:view',
  settingsUserView: 'settings:user-management:view',
  settingsUserEdit: 'settings:user-management:edit',
  settingsUserUpdate: 'settings:user-management:update',
  settingsRoleView: 'settings:role-management:view',
  settingsRoleEdit: 'settings:role-management:edit',
  settingsRoleUpdate: 'settings:role-management:update'
} as const

export type Permission = (typeof PERMISSIONS)[keyof typeof PERMISSIONS]

export const ADMIN_WILDCARD = 'admin:*'
export const ALL_PAGES = 'ALL_PAGES'
