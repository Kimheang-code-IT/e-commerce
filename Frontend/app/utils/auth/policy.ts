import { ADMIN_WILDCARD, ALL_PAGES } from '~/utils/auth/permissions'
import { RBAC_ALIASES } from '~/utils/auth/rbacAliases'

/** Same logic as `user_has_permission` in `Backend/app/security/rbac.py`. */
export function hasPermission(permissions: string[] | undefined, permission: string): boolean {
  const tokens = new Set(permissions || [])
  if (tokens.has(ADMIN_WILDCARD) || tokens.has(ALL_PAGES)) return true
  if (tokens.has(permission)) return true
  const aliases = RBAC_ALIASES[permission]
  if (aliases?.some((a) => tokens.has(a))) return true
  return false
}
