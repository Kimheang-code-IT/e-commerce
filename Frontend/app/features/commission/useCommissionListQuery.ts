import { computed, type Ref } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { useCommissionApi, type ApiQueryParams } from '~/utils/api'
import type { CommissionEntry } from '~/types'

export function useCommissionListQuery(params: Ref<ApiQueryParams>) {
  const api = useCommissionApi()
  return useQuery<{ data?: CommissionEntry[]; total?: number }>({
    queryKey: computed(() => ['commission-list', params.value]),
    queryFn: ({ signal }) => api.list(params.value, signal),
    staleTime: 15_000
  })
}
