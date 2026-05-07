import { ADMIN_WILDCARD, ALL_PAGES, type Permission } from '~/utils/auth/permissions'

export function hasPermission(permissions: string[] | undefined, permission: Permission): boolean {
  const tokens = Array.isArray(permissions) ? permissions : []
  if (tokens.includes(ADMIN_WILDCARD) || tokens.includes(ALL_PAGES)) return true
  return tokens.includes(permission)
}
