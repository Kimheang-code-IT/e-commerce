import { computed, ref, watch, type Ref } from 'vue'
import type { ApiQueryParams } from '~/utils/api'
import { useTableQuery } from '~/composables/table/useTableQuery'
import { useServerTableResource } from '~/composables/table/useServerTableResource'

type UseServerListTableOptions<T> = {
  resourceKey: string
  initialSorting?: Array<{ id: string; desc: boolean }>
  extraQuery?: Ref<Record<string, string | number | undefined>>
  localData?: Ref<T[]> | Ref<any[]>
  listFn: (query: ApiQueryParams, signal?: AbortSignal) => Promise<{ data?: T[]; total?: number; aggregates?: Record<string, number> }>
}

export function useServerListTable<T>(options: UseServerListTableOptions<T>) {
  const useBackendApi = useBackendMode()
  const { formattedRange } = useGlobalFilter()
  const fallbackData = (options.localData ?? ref<T[]>([])) as Ref<T[]>
  const { sorting, columnFilters, pagination, serverQuery } = useTableQuery({
    initialSorting: options.initialSorting ?? []
  })
  const searchQuery = ref('')
  const mergedServerQuery = computed<ApiQueryParams>(() => ({
    ...serverQuery.value,
    search: searchQuery.value.trim() || undefined,
    dateFrom: formattedRange.value.start || undefined,
    dateTo: formattedRange.value.end || undefined,
    ...(options.extraQuery?.value || {})
  }))

  watch(searchQuery, () => {
    pagination.value.pageIndex = 0
  })

  const resource = useServerTableResource<T, ApiQueryParams>({
    resourceKey: options.resourceKey,
    useBackendApi,
    serverQuery: mergedServerQuery,
    localData: fallbackData,
    listFn: options.listFn,
    debounceMs: 220
  })

  return {
    sorting,
    columnFilters,
    pagination,
    searchQuery,
    mergedServerQuery,
    resource
  }
}
