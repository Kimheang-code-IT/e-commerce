<script setup lang="ts">
import { useSystemRoleManagement } from '~/composables/settings/useSystemRoleManagement'
const {
    rowSelection, sorting, searchQuery, columnVisibility, columnFilters,
    pagination, isFormOpen, isConfirmOpen,
    totalRows,
    selectedRole, filteredRoles, confirmConfig,
    roleFormFields, columns, roleFilterItems, selectedRoles,
    getDropdownActions, handleSaveRequest, finalizeAction, handleAddNew,
    formatPageAccessForDisplay,
} = useSystemRoleManagement()
const auth = useAuthStore()
/** Backend maps role:create/update/delete to the same stored token; any grants management UI. */
const canUpdateRole = computed(
    () =>
        auth.hasPermission('role:create') ||
        auth.hasPermission('role:update') ||
        auth.hasPermission('role:delete')
)

function onSubmitRole(data: Record<string, any>) {
    if (!canUpdateRole.value) return
    handleSaveRequest(data as any)
}
</script>

<template>
    <div class="flex flex-col h-full bg-background overflow-hidden text-foreground tracking-tight">
        <LayoutAppHeader :title="$t('pages.roleManagement.title')">
            <template #right>
                <UButton v-if="auth.hasPermission('role:create')" icon="i-lucide-shield-plus" color="primary" variant="solid"
                    class="font-normal shadow-sm shrink-0" @click="handleAddNew">
                    <span class="hidden sm:inline">{{ $t('pages.roleManagement.addBtn') }}</span>
                </UButton>
            </template>
        </LayoutAppHeader>

        <div class="flex-1 p-2 overflow-hidden">
            <TableApptable :title="$t('pages.roleManagement.tableTitle')" v-model:row-selection="rowSelection"
                v-model:sorting="sorting"
                v-model:column-visibility="columnVisibility" v-model:pagination="pagination"
                v-model:column-filters="columnFilters" v-model:filter-value="selectedRoles"
                v-model:global-filter="searchQuery"
                :filter-items="roleFilterItems" :data="filteredRoles" :columns="columns" :selectable="true"
                :total-rows="totalRows"
                :get-row-actions="getDropdownActions">
                <template #name-cell="{ row }">
                    <div class="flex items-center gap-2">
                        <span>{{ row.original.name }}</span>
                    </div>
                </template>
                <template #pageAccess-cell="{ row }">
                    <div class="flex flex-wrap gap-1 max-w-md">
                        <template v-if="row.original.pageAccess.includes('ALL_PAGES') || row.original.pageAccess.includes('admin:*')">
                            <UBadge variant="solid" color="primary" size="md">
                                {{ $t('pages.roleManagement.allPages') }}
                            </UBadge>
                        </template>
                        <template v-else>
                            <UBadge
                                v-for="label in formatPageAccessForDisplay(row.original.pageAccess)"
                                :key="label"
                                variant="soft"
                                color="neutral"
                                size="md"
                            >
                                {{ label }}
                            </UBadge>
                        </template>
                    </div>
                </template>
            </TableApptable>
        </div>
        <CommonAppSlideoverForm
            v-model:open="isFormOpen"
            :data="selectedRole || undefined"
            :fields="roleFormFields"
            :title-key="selectedRole ? 'pages.roleManagement.formTitleEdit' : 'pages.roleManagement.formTitleNew'"
            :submit-label-key="selectedRole ? 'actions.save' : 'actions.confirm'"
            @submit="onSubmitRole"
        />
        <CommonAppModalCURD v-model:open="isConfirmOpen" v-bind="confirmConfig" @submit="finalizeAction" />
    </div>
</template>
