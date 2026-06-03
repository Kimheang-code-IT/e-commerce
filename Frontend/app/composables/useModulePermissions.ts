import { computed } from 'vue'
import type { Permission } from '~/utils/auth/permissions'
import { modulePermission, type AppModule } from '~/utils/auth/permissionRegistry'

export function useModulePermissions(module: AppModule | string) {
  const auth = useAuthStore()

  function can(action: string) {
    return computed(() => auth.hasPermission(modulePermission(module, action) as Permission))
  }

  return {
    can,
    canView: can('view'),
    canCreate: can('create'),
    canUpdate: can('update'),
    canDelete: can('delete'),
    canExport: can('export'),
    canCheckout: can('checkout'),
    canAdjustStock: can('adjust-stock'),
    canViewAdjustStock: can('view-adjust-stock'),
    canAddDamage: can('add-damage'),
    canViewAddDamage: can('view-add-damage'),
  }
}
