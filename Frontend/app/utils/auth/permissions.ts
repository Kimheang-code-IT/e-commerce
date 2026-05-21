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
  productExport: 'product:export',
  productAdjustStock: 'product:adjust-stock',
  productViewAdjustStock: 'product:view-adjust-stock',
  productAddDamage: 'product:add-damage',
  productViewAddDamage: 'product:view-add-damage',
  posView: 'pos:view',
  posCheckout: 'pos:checkout',
  financeView: 'finance:view',
  financeUpdate: 'finance:update',
  reportView: 'report:view',
  reportExport: 'report:export',
  commissionView: 'commission:view',
  commissionExport: 'commission:export',
  deliveryView: 'delivery:view',
  deliveryUpdate: 'delivery:update',
  deliveryExport: 'delivery:export',
  historyView: 'history:view',
  historyExport: 'history:export',
  userView: 'user:view',
  userCreate: 'user:create',
  userUpdate: 'user:update',
  userDelete: 'user:delete',
  roleView: 'role:view',
  roleCreate: 'role:create',
  roleUpdate: 'role:update',
  roleDelete: 'role:delete'
} as const

/** Any short permission key from RBAC or a literal stored token (e.g. settings:...:view). */
export type Permission = (typeof PERMISSIONS)[keyof typeof PERMISSIONS] | string

export const ADMIN_WILDCARD = 'admin:*'
export const ALL_PAGES = 'ALL_PAGES'
