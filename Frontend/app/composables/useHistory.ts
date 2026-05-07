import { ref, computed, watch } from 'vue'
import type { DropdownMenuItem } from '@nuxt/ui'
import { useBaseTable } from "~/composables/table/useBaseTable";
import { useTableQuery } from "~/composables/table/useTableQuery";
import type { AuditLog } from '~/types'
import { useHistoryApi } from '~/utils/api'
import { useServerTableResource } from '~/composables/table/useServerTableResource'

export function useAuditHistory() {
    const useBackendApi = useBackendMode()
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

    // --- Context States ---
    const selectedLog = ref<AuditLog | null>(null)

    // --- Filter States ---
    const actionItems = ['Login', 'Logout', 'Create', 'Update', 'Delete', 'Export'];
    const selectedActions = ref<string[]>([]);

    // --- Refactor: Use Standalone Data ---
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

    // --- Computed Logic ---
    const filteredLogs = computed(() => {
        if (!selectedActions.value.length) return effectiveLogs.value;
        return effectiveLogs.value.filter(l => selectedActions.value.includes(l.typeAction));
    })

    // --- Actions ---
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
        // States
        rowSelection, sorting, searchQuery, columnVisibility, columnFilters,
        pagination, isDetailOpen,
        isLoading: resource.isLoading,
        totalRows: resource.totalRows,
        selectedLog, logs: effectiveLogs,
        actionItems, selectedActions,
        // Computed
        filteredLogs,
        // Actions
        getDropdownActions,
    }
}

