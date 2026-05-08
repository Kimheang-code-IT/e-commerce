import { ref, computed, watch } from 'vue'
import type { TableColumn, DropdownMenuItem } from '@nuxt/ui'
import { useBaseTable } from '~/composables/table/useBaseTable'
import { useTableQuery } from '~/composables/table/useTableQuery'
import type { SystemRole, FormField } from '~/types'
import { useSystemRoleApi } from '~/utils/api'
import type { ApiQueryParams } from '~/utils/api'
import { useServerTableResource } from '~/composables/table/useServerTableResource'
import { useMutation } from '~/composables/data/useMutation'

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
    const mergedServerQuery = computed(() => ({
        ...serverQuery.value,
        search: searchQuery.value.trim() || undefined,
        dateFrom: formattedRange.value.start || undefined,
        dateTo: formattedRange.value.end || undefined
    })
    )
    watch(searchQuery, () => {
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
    const roleFilterItems = computed(() => {
        const unique = new Set(effectiveRoles.value.map(r => r.name))
        return [...unique]
    })
    const selectedRoles = ref<string[]>([])

    const pageItems = [
        'dashboard',
        'category',
        'product',
        'pos',
        'delivery',
        'finance',
        'commission',
        'report',
        'history',
        'settings:user-management',
        'settings:role-management'
    ] as const

    const permissionItems = ['view', 'edit', 'update'] as const

    // --- Computed Logic ---
    const filteredRoles = computed(() => {
        if (selectedRoles.value.length === 0) return effectiveRoles.value
        return effectiveRoles.value.filter(r => {
            return selectedRoles.value.includes(r.name)
        })
    })

    const roleSummary = computed(() => ({
        count: filteredRoles.value.length
    }))

    const confirmConfig = computed(() => {
        if (confirmMode.value === 'delete') {
            return {
                title: t('actions.delete'),
                description: `Confirm permanent removal of the "${selectedRole.value?.name || ""}" role policy?`,
                type: 'error' as const,
                submitLabel: t('actions.delete'),
                icon: 'i-lucide-shield-off'
            }
        }
        if (confirmMode.value === 'edit') {
            return {
                title: t('actions.save'),
                description: `Confirm updating role policy for "${pendingRole.value?.name || ""}"?`,
                submitLabel: t('actions.save'),
                type: 'primary' as const,
                icon: 'i-lucide-save'
            }
        }
        return {
            title: t('pages.roleManagement.addBtn'),
            description: `Confirm creating new role policy "${pendingRole.value?.name || ""}"?`,
            submitLabel: t('actions.confirm'),
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
        { key: 'name', label: t('pages.roleManagement.columns.name'), type: 'input', icon: 'i-lucide-shield', required: true },
        {
            key: 'pageAccess',
            label: t('pages.roleManagement.columns.pageAccess'),
            type: 'permission-tree',
            items: [...pageItems],
            childItems: [...permissionItems],
            required: true
        }
    ])

    // --- Actions ---
    function getDropdownActions(role: SystemRole): DropdownMenuItem[][] {
        const actions: DropdownMenuItem[] = []
        if (auth.hasPermission('settings:role-management:edit')) {
            actions.push({
                label: t('actions.edit'), icon: 'i-lucide-edit',
                onSelect: () => {
                    selectedRole.value = { ...role, pageAccess: [...role.pageAccess] }
                    isFormOpen.value = true
                }
            })
        }
        if (auth.hasPermission('settings:role-management:update')) {
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

    function handleSaveRequest(data: any) {
        if (Array.isArray(data.pageAccess)) {
            data.pageAccess = data.pageAccess
                .map((s: any) => String(s).trim())
                .filter(Boolean)
                .map((s: string) => s.toLowerCase())
        } else {
            data.pageAccess = []
        }

        pendingRole.value = { ...data }
        confirmMode.value = (!data.id || data.id === 0) ? "add" : "edit";
        isConfirmOpen.value = true
    }

    async function finalizeAction() {
        if (confirmMode.value === 'delete' && selectedRole.value) {
            await mutation.run(() => systemRoleApi.remove(selectedRole.value!.id), 'roles')
            await resource.refresh()
            toast.add({ title: 'Role Purged', description: 'Role removed successfully.', color: 'error' })
        } else if (pendingRole.value) {
            if (confirmMode.value === 'add') {
                await mutation.run(() => systemRoleApi.create(pendingRole.value!), 'roles')
                await resource.refresh()
                toast.add({ title: 'Role Provisioned', description: 'New role policy is active.', color: 'primary' })
            } else if (confirmMode.value === 'edit') {
                const { id, ...updatePayload } = pendingRole.value!
                await mutation.run(() => systemRoleApi.update(id, updatePayload), 'roles')
                await resource.refresh()
                toast.add({ title: 'Role Synchronized', description: 'Policy updates synchronized.', color: 'primary' })
            }
        }
        isConfirmOpen.value = false
        isFormOpen.value = false
        selectedRole.value = null
        pendingRole.value = null
    }

    function handleAddNew() {
        if (!auth.hasPermission('settings:role-management:update')) return
        selectedRole.value = null
        isFormOpen.value = true
    }

    return {
        // Table States
        rowSelection, sorting, searchQuery, columnVisibility, columnFilters, pagination,
        // Overlay States
        isFormOpen, isConfirmOpen,
        selectedRole, roles: effectiveRoles, roleFilterItems, selectedRoles, isLoading: resource.isLoading,
        totalRows: resource.totalRows,
        // Computed
        filteredRoles, confirmConfig,
        // Config
        columns, roleFormFields,
        // Actions
        getDropdownActions, handleSaveRequest, finalizeAction, handleAddNew,
    }
}
