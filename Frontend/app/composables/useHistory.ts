import { ref, computed, watch } from 'vue'
import type { DropdownMenuItem } from '@nuxt/ui'
import { useBaseTable } from "~/composables/table/useBaseTable";
import { useTableQuery } from "~/composables/table/useTableQuery";
import type { AuditLog } from '~/types'
import { useHistoryApi } from '~/utils/api'
import { useServerTableResource } from '~/composables/table/useServerTableResource'
import { useViewFilterOptions } from '~/composables/useViewFilterOptions'

export function useAuditHistory() {
    const useBackendApi = useBackendMode()
    const perms = useModulePermissions('history')
    const historyApi = useHistoryApi()
    const { formattedRange } = useGlobalFilter()
    const {
      rowSelection,
      columnVisibility,
      isDetailOpen,
    } = useBaseTable({});
  
    const {
      sorting,
      columnFilters,
      pagination,
      serverQuery,
    } = useTableQuery({ initialSorting: [{ id: 'id', desc: true }] });
    const searchQuery = ref('')

    const selectedLog = ref<AuditLog | null>(null)
    const selectedActions = ref<string[]>([]);

    const { itemsFor: filterItemsFor } = useViewFilterOptions(
      (query, signal) => historyApi.filterOptions(query, signal),
      ['actions']
    )
    const actionItems = filterItemsFor('actions')

    const logs = ref<AuditLog[]>([])
    const mergedServerQuery = computed(() => ({
        ...serverQuery.value,
        search: searchQuery.value.trim() || undefined,
        dateFrom: formattedRange.value.start || undefined,
        dateTo: formattedRange.value.end || undefined
    }))
    watch(searchQuery, () => {
        pagination.value.pageIndex = 0
    })
    watch(selectedActions, () => {
        pagination.value.pageIndex = 0
    })
    const resource = useServerTableResource<AuditLog, Record<string, unknown>>({
        resourceKey: 'histories',
        useBackendApi,
        serverQuery: mergedServerQuery,
        localData: logs,
        listFn: (query, signal) => historyApi.list({
            ...query,
            action: selectedActions.value.join(',') || undefined
        }, signal),
        debounceMs: 220
    })
    const effectiveLogs = computed(() => resource.rows.value)

    const filteredLogs = computed(() => effectiveLogs.value)

    function getDropdownActions(log: AuditLog): DropdownMenuItem[][] {
        return [[
            {
                label: 'View Details', icon: 'i-lucide-eye',
                onSelect: () => {
                   selectedLog.value = log
                   isDetailOpen.value = true
                }
            }
        ]]
    }

    return {
        rowSelection, sorting, searchQuery, columnVisibility, columnFilters,
        pagination, isDetailOpen,
        isLoading: resource.isLoading,
        totalRows: resource.totalRows,
        selectedLog, logs: effectiveLogs,
        actionItems, selectedActions,
        filteredLogs,
        getDropdownActions,
        canExport: perms.canExport,
    }
}

