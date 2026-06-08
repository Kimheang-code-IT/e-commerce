import type { RoutePermissionEntry } from '~/utils/auth/routes'
import { routePermissionMap } from '~/utils/auth/routes'
import type { Permission } from '~/utils/auth/permissions'

type AuthAccess = {
  hasPermission: (permission: Permission) => boolean
  hasRole: (roles: string[]) => boolean
  pageAccess?: string[]
}

export function isRouteEntryAllowed(entry: RoutePermissionEntry, auth: AuthAccess): boolean {
  const hasPerm = auth.hasPermission(entry.permission)
  const hasRole = !entry.roles || auth.hasRole(entry.roles)
  return hasPerm && hasRole
}

export function getAllowedRouteEntries(auth: AuthAccess): RoutePermissionEntry[] {
  return routePermissionMap.filter((entry) => isRouteEntryAllowed(entry, auth))
}

export function getAllowedRouteHomes(auth: AuthAccess): string[] {
  return getAllowedRouteEntries(auth).map((entry) => entry.home)
}

export function getAllowedRouteHomeSet(auth: AuthAccess): Set<string> {
  return new Set(getAllowedRouteHomes(auth))
}

export function getFirstAllowedHome(auth: AuthAccess): string | null {
  const entry = routePermissionMap.find((item) => isRouteEntryAllowed(item, auth))
  return entry?.home ?? null
}

export function canAccessPath(path: string, auth: AuthAccess): boolean {
  const entry = routePermissionMap.find((item) => item.match(path))
  if (!entry) return true
  return isRouteEntryAllowed(entry, auth)
}
