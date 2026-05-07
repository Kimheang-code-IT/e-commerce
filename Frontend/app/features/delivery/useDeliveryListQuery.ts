import { computed, type Ref } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { useDeliveryApi, type ApiQueryParams } from '~/utils/api'
import type { DeliveryEntry } from '~/types'

export function useDeliveryListQuery(params: Ref<ApiQueryParams>) {
  const api = useDeliveryApi()
  return useQuery<{ data?: DeliveryEntry[]; total?: number }>({
    queryKey: computed(() => ['delivery-list', params.value]),
    queryFn: ({ signal }) => api.list(params.value, signal),
    staleTime: 15_000
  })
}
