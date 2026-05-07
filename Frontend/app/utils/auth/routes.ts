import { PERMISSIONS, type Permission } from '~/utils/auth/permissions'

export type RoutePermissionEntry = {
  home: string
  match: (path: string) => boolean
  permission: Permission
  roles?: string[]
}

export const routePermissionMap: RoutePermissionEntry[] = [
  { home: '/', match: (path) => path === '/', permission: PERMISSIONS.dashboardView },
  { home: '/category', match: (path) => path.startsWith('/category'), permission: PERMISSIONS.categoryView },
  { home: '/product', match: (path) => path.startsWith('/product'), permission: PERMISSIONS.productView },
  { home: '/pos', match: (path) => path.startsWith('/pos'), permission: PERMISSIONS.posView },
  { home: '/report', match: (path) => path.startsWith('/report'), permission: PERMISSIONS.reportView },
  { home: '/commission', match: (path) => path.startsWith('/commission'), permission: PERMISSIONS.commissionView },
  { home: '/finance', match: (path) => path.startsWith('/finance'), permission: PERMISSIONS.financeView },
  { home: '/delivery', match: (path) => path.startsWith('/delivery'), permission: PERMISSIONS.deliveryView },
  { home: '/history', match: (path) => path.startsWith('/history'), permission: PERMISSIONS.historyView },
  { home: '/settings/user-management', match: (path) => path.startsWith('/settings/user-management'), permission: PERMISSIONS.settingsUserView, roles: ['admin']},
  { home: '/settings/role-management', match: (path) => path.startsWith('/settings/role-management'), permission: PERMISSIONS.settingsRoleView, roles: ['admin']},
]

export function useRoutePermissionMap() {
  return routePermissionMap
}
