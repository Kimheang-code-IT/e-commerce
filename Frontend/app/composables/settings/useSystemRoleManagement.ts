import { ref, computed, watch } from 'vue'
import type { TableColumn, DropdownMenuItem } from '@nuxt/ui'
import { useBaseTable } from '~/composables/table/useBaseTable'
import { useTableQuery } from '~/composables/table/useTableQuery'
import type { SystemRole, FormField } from '~/types'
import { useSystemRoleApi } from '~/utils/api'
import type { ApiQueryParams } from '~/utils/api'
import { useServerTableResource } from '~/composables/table/useServerTableResource'
import { useMutation } from '~/composables/data/useMutation'
import { useRoleOptions } from '~/composables/data/useRoleOptions'
import { PAGE_PERMISSION_MAP, ROLE_PAGE_KEYS } from '~/utils/auth/permissionRegistry'
import { uniqueRolePageLabels } from '~/utils/auth/rolePages'

export function useSystemRoleManagement() {
    const useBackendApi = useBackendMode()
    const systemRoleApi = useSystemRoleApi()
    const { formattedRange } = useGlobalFilter()
    const {
        t, toast, rowSelection,
        columnVisibility,
        isFormOpen,
        isConfirmOpen,
    } = useBaseTable({ });

    const {
        sorting,
        columnFilters,
        pagination,
        serverQuery,
    } = useTableQuery({ initialSorting: [{ id: 'id', desc: false }] });
    const searchQuery = ref('')

    // --- Context States ---
    const selectedRole = ref<SystemRole | null>(null)
    const pendingRole = ref<SystemRole | null>(null)
    const confirmMode = ref<'add' | 'edit' | 'delete'>('add')


    // --- Mock Data ---
    const roles = ref<SystemRole[]>([])
    const mutation = useMutation()
    const auth = useAuthStore()
    const selectedRoles = ref<string[]>([])
    const mergedServerQuery = computed(() => ({
        ...serverQuery.value,
        search: searchQuery.value.trim() || undefined,
        dateFrom: formattedRange.value.start || undefined,
        dateTo: formattedRange.value.end || undefined,
        name: selectedRoles.value.join(',') || undefined,
    }))
    watch(searchQuery, () => {
        pagination.value.pageIndex = 0
    })
    watch(selectedRoles, () => {
        pagination.value.pageIndex = 0
    })
    const resource = useServerTableResource<SystemRole, ApiQueryParams>({
        resourceKey: 'roles',
        useBackendApi,
        serverQuery: mergedServerQuery,
        localData: roles,
        listFn: (query, signal) => systemRoleApi.list(query, signal),
        debounceMs: 220
    })
    const effectiveRoles = computed(() => resource.rows.value)

    // --- Filter States ---
    const { roleNames: roleFilterItems } = useRoleOptions()

    const pagePermissionMap = PAGE_PERMISSION_MAP
    const pageItems = [...ROLE_PAGE_KEYS]
    const permissionItems = [
        'view',
        'create',
        'update',
        'delete',
        'export',
        'checkout',
        'adjust-stock',
        'view-adjust-stock',
        'add-damage',
        'view-add-damage',
        'refund',
    ] as const

    const roleSummary = computed(() => ({
        count: resource.totalRows.value
    }))

    const confirmConfig = computed(() => {
        if (confirmMode.value === 'delete') {
            return {
                titleKey: 'pages.roleManagement.confirmDeleteTitle',
                description: t('pages.roleManagement.confirmDeleteDesc', {
                    name: selectedRole.value?.name || '',
                }),
                type: 'error' as const,
                submitLabelKey: 'actions.delete',
                icon: 'i-lucide-shield-off'
            }
        }
        if (confirmMode.value === 'edit') {
            return {
                titleKey: 'pages.roleManagement.confirmEditTitle',
                description: t('pages.roleManagement.confirmEditDesc', {
                    name: pendingRole.value?.name || '',
                }),
                submitLabelKey: 'actions.save',
                type: 'primary' as const,
                icon: 'i-lucide-save'
            }
        }
        return {
            titleKey: 'pages.roleManagement.confirmAddTitle',
            description: t('pages.roleManagement.confirmAddDesc', {
                name: pendingRole.value?.name || '',
            }),
            submitLabelKey: 'actions.confirm',
            type: 'primary' as const,
            icon: 'i-lucide-shield-plus'
        }
    })

    // --- Table Columns ---
    const columns = computed<TableColumn<SystemRole>[]>(() => [
        { accessorKey: 'id', header: t('common.rank') },
        {
            accessorKey: 'name',
            header: t('pages.roleManagement.columns.name'),
            footer: `Count: ${roleSummary.value.count}`
        },
        { accessorKey: 'pageAccess', header: t('pages.roleManagement.columns.pageAccess') },
        { id: 'action', header: t('common.actions') }
    ])

    // --- Form Fields ---
    const roleFormFields = computed<FormField[]>(() => [
        { key: 'name', label: t('pages.roleManagement.columns.name'), type: 'input', icon: 'i-lucide-shield', required: true, textRule: 'text' },
        {
            key: 'pageAccess',
            label: t('pages.roleManagement.columns.pageAccess'),
            type: 'permission-tree',
            items: [...pageItems],
            childItems: [...permissionItems],
            actionsByPage: pagePermissionMap,
            required: true
        }
    ])

    // --- Actions ---
    function getDropdownActions(role: SystemRole): DropdownMenuItem[][] {
        const actions: DropdownMenuItem[] = []
        if (auth.hasPermission('role:update')) {
            actions.push({
                label: t('actions.edit'), icon: 'i-lucide-edit',
                onSelect: () => {
                    selectedRole.value = { ...role, pageAccess: [...(role.pageAccess ?? [])] }
                    isFormOpen.value = true
                }
            })
        }
        if (auth.hasPermission('role:delete')) {
            actions.push({
                label: t('actions.delete'),
                icon: 'i-lucide-trash',
                color: 'error' as const,
                onSelect: () => {
                    selectedRole.value = role
                    confirmMode.value = 'delete'
                    isConfirmOpen.value = true
                }
            })
        }
        return actions.length ? [actions] : []
    }

    function normalizeRoleName(name: string) {
        return String(name || '').trim().toLowerCase()
    }

    function isDuplicateRoleName(name: string, excludeId?: number | null) {
        const normalized = normalizeRoleName(name)
        if (!normalized) return false
        return effectiveRoles.value.some(
            (role) => normalizeRoleName(role.name) === normalized && role.id !== excludeId
        )
    }

    function handleSaveRequest(data: any) {
        if (Array.isArray(data.pageAccess)) {
            data.pageAccess = data.pageAccess
                .map((s: any) => String(s).trim())
                .filter(Boolean)
                .map((s: string) => {
                    if (s === 'ALL_PAGES' || s === 'admin:*') return s
                    return s.toLowerCase()
                })
        } else {
            data.pageAccess = []
        }

        const isAdd = !data.id || data.id === 0
        const roleName = String(data.name || '').trim()
        if (isDuplicateRoleName(roleName, isAdd ? undefined : data.id)) {
            toast.add({
                title: t('pages.roleManagement.toastDuplicateName'),
                description: t('pages.roleManagement.toastDuplicateNameDesc'),
                color: 'error',
            })
            return
        }

        pendingRole.value = { ...data, name: roleName }
        confirmMode.value = isAdd ? 'add' : 'edit'
        isConfirmOpen.value = true
    }

    async function finalizeAction() {
        if (mutation.isMutating.value) return

        try {
            if (confirmMode.value === 'delete' && selectedRole.value) {
                await mutation.run(() => systemRoleApi.remove(selectedRole.value!.id), 'roles')
                await resource.load()
                toast.add({
                    title: t('pages.roleManagement.toastDeleted'),
                    description: t('pages.roleManagement.toastDeletedDesc'),
                    color: 'error',
                })
            } else if (pendingRole.value) {
                if (confirmMode.value === 'add') {
                    await mutation.run(() => systemRoleApi.create(pendingRole.value!), 'roles')
                    await resource.load()
                    toast.add({
                        title: t('pages.roleManagement.toastAdded'),
                        description: t('pages.roleManagement.toastAddedDesc'),
                        color: 'primary',
                    })
                } else if (confirmMode.value === 'edit') {
                    const { id, ...updatePayload } = pendingRole.value!
                    await mutation.run(() => systemRoleApi.update(id, updatePayload), 'roles')
                    await resource.load()
                    toast.add({
                        title: t('pages.roleManagement.toastUpdated'),
                        description: t('pages.roleManagement.toastUpdatedDesc'),
                        color: 'primary',
                    })
                }
            }

            isConfirmOpen.value = false
            isFormOpen.value = false
            selectedRole.value = null
            pendingRole.value = null
        } catch {
            // useApi already shows the API error toast; keep dialogs open for retry.
        }
    }

    function handleAddNew() {
        if (!auth.hasPermission('role:create')) return
        selectedRole.value = null
        isFormOpen.value = true
    }

    function formatPageAccessForDisplay(tokens: string[]) {
        return uniqueRolePageLabels(tokens, t)
    }

    return {
        // Table States
        rowSelection, sorting, searchQuery, columnVisibility, columnFilters, pagination,
        // Overlay States
        isFormOpen, isConfirmOpen,
        selectedRole, roles: effectiveRoles, roleFilterItems, selectedRoles, isLoading: resource.isLoading,
        totalRows: resource.totalRows,
        // Computed
        confirmConfig,
        // Config
        columns, roleFormFields,
        // Actions
        getDropdownActions, handleSaveRequest, finalizeAction, handleAddNew,
        formatPageAccessForDisplay,
        isMutating: mutation.isMutating,
    }
}
