import { computed, type Ref } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { useFinanceApi, type ApiQueryParams } from '~/utils/api'
import type { FinanceEntry } from '~/types'

export function useFinanceListQuery(params: Ref<ApiQueryParams>) {
  const api = useFinanceApi()
  return useQuery<{ data?: FinanceEntry[]; total?: number }>({
    queryKey: computed(() => ['finance-list', params.value]),
    queryFn: ({ signal }) => api.list(params.value, signal),
    staleTime: 15_000
  })
}
