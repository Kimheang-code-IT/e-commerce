import { computed, type Ref } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { useReportApi, type ApiQueryParams } from '~/utils/api'
import type { ReportRow } from '~/types'

export function useReportListQuery(params: Ref<ApiQueryParams>) {
  const api = useReportApi()
  return useQuery<{ data?: ReportRow[]; total?: number }>({
    queryKey: computed(() => ['report-list', params.value]),
    queryFn: ({ signal }) => api.list(params.value, signal),
    staleTime: 15_000
  })
}
