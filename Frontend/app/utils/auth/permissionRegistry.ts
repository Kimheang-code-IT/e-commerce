/**
 * Single catalog for RBAC. Keep in sync with:
 * - Backend/app/security/rbac.py ALIASES
 * - Frontend/app/utils/auth/rbacAliases.ts
 * - Role editor uses PAGE_PERMISSION_MAP
 */
import { ROLE_PAGE_SETTINGS_KEYS } from '~/utils/auth/rolePages'

/** Actions available per settings page key (stored as settings:page:action). */
export const PAGE_PERMISSION_MAP: Record<string, string[]> = {
  'settings:dashboard-management': ['view'],
  'settings:category-management': ['view', 'create', 'update', 'delete'],
  'settings:supplier-management': ['view', 'create', 'update', 'delete'],
  'settings:product-management': [
    'view',
    'create',
    'update',
    'delete',
    'export',
    'adjust-stock',
    'view-adjust-stock',
    'add-damage',
    'view-add-damage',
  ],
  'settings:pos-management': ['view', 'checkout'],
  'settings:finance-management': ['view', 'update'],
  'settings:report-management': ['view', 'export'],
  'settings:refund-management': ['view', 'create', 'delete'],
  'settings:delivery-management': ['view', 'update', 'export'],
  'settings:history-management': ['view', 'export'],
  'settings:commission-management': ['view', 'export'],
  'settings:role-management': ['view', 'create', 'update', 'delete'],
  'settings:user-management': ['view', 'create', 'update', 'delete'],
}

export const ROLE_PAGE_KEYS = ROLE_PAGE_SETTINGS_KEYS

/** Short API module names used in require_permission and hasPermission. */
export const APP_MODULES = [
  'dashboard',
  'category',
  'supplier',
  'product',
  'pos',
  'finance',
  'report',
  'refund',
  'delivery',
  'history',
  'commission',
  'role',
  'user',
] as const

export type AppModule = (typeof APP_MODULES)[number]

/** Standard CRUD + export actions per module (short permission suffix). */
export const MODULE_STANDARD_ACTIONS = ['view', 'create', 'update', 'delete', 'export'] as const

export type ModuleAction = (typeof MODULE_STANDARD_ACTIONS)[number] | string

export function modulePermission(module: string, action: string): string {
  return `${module}:${action}`
}
