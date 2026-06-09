import { computed, ref, watch } from 'vue'
import type { DropdownMenuItem } from '@nuxt/ui'
import { useBaseTable } from '~/composables/table/useBaseTable'
import type { AuditLog } from '~/types'
import { useHistoryApi } from '~/utils/api'
import { useServerListTable } from '~/features/shared/useServerListTable'
import { useViewFilterOptions } from '~/composables/useViewFilterOptions'

export function useAuditHistory() {
  const historyApi = useHistoryApi()
  const perms = useModulePermissions('history')
  const {
    rowSelection,
    columnVisibility,
    isDetailOpen,
  } = useBaseTable({})

  const selectedLog = ref<AuditLog | null>(null)
  const selectedActions = ref<string[]>([])
  const logs = ref<AuditLog[]>([])

  const extraQuery = computed(() => ({
    action: selectedActions.value.join(',') || undefined,
  }))

  const {
    sorting,
    columnFilters,
    pagination,
    searchQuery,
    resource,
  } = useServerListTable<AuditLog>({
    resourceKey: 'histories',
    initialSorting: [{ id: 'id', desc: true }],
    localData: logs,
    extraQuery,
    listFn: (query, signal) => historyApi.list(query, signal),
  })

  watch(selectedActions, () => {
    pagination.value.pageIndex = 0
  })

  const { itemsFor: filterItemsFor } = useViewFilterOptions(
    (query, signal) => historyApi.filterOptions(query, signal),
    ['actions'],
  )
  const actionItems = filterItemsFor('actions')

  const effectiveLogs = computed(() => resource.rows.value)

  function getDropdownActions(log: AuditLog): DropdownMenuItem[][] {
    return [[
      {
        label: 'View Details',
        icon: 'i-lucide-eye',
        onSelect: () => {
          selectedLog.value = log
          isDetailOpen.value = true
        },
      },
    ]]
  }

  return {
    rowSelection,
    sorting,
    searchQuery,
    columnVisibility,
    columnFilters,
    pagination,
    isDetailOpen,
    isLoading: resource.isLoading,
    totalRows: resource.totalRows,
    selectedLog,
    logs: effectiveLogs,
    actionItems,
    selectedActions,
    getDropdownActions,
    canExport: perms.canExport,
  }
}
