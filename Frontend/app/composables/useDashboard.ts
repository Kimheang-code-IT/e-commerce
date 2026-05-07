import { ref, computed, onMounted, watch } from 'vue'
import { useDashboardApi } from '~/utils/api'

/** Home dashboard — fetches aggregated statistics from the optimized /dashboard/summary endpoint. */
export function useAnalyticsDashboard() {
  const useBackendApi = useBackendMode()
  const dashboardApi = useDashboardApi()
  const { formattedRange } = useGlobalFilter()
  
  const pending = ref(false)
  const apiSummary = ref<{ 
    stats?: { label: string; value: string; icon: string }[]; 
    chartData?: { name: string; value: number }[];
    topProducts?: { name: string; value: number }[];
    userCommissions?: { name: string; value: number }[];
  } | null>(null)

  const stats = computed(() => apiSummary.value?.stats || [])
  const currentAnalytics = computed(() => ({
    chartData: apiSummary.value?.chartData || []
  }))

  async function refresh() {
    if (!useBackendApi.value) return
    pending.value = true
    try {
      const res = await dashboardApi.getSummary({
        dateFrom: formattedRange.value.start || undefined,
        dateTo: formattedRange.value.end || undefined
      })
      const data = res.data
      apiSummary.value = {
        stats: [
          {
            label: 'Total Product',
            value: String(data?.totalProducts || 0),
            icon: 'i-lucide-folder-tree'
          },
          {
            label: 'Product in Stock',
            value: String(data?.productsInStock || 0),
            icon: 'i-lucide-package'
          },
          {
            label: 'Product Out of Stock',
            value: String(data?.productsOutOfStock || 0),
            icon: 'i-lucide-file-text'
          },
          {
            label: 'Sold Products',
            value: String(data?.soldProducts || 0),
            icon: 'i-lucide-users'
          }
        ],
        chartData: data?.provincialDistribution || [],
        topProducts: data?.topProducts || [],
        userCommissions: data?.userCommissions || []
      }
    } finally {
      pending.value = false
    }
  }

  // Refresh when date range changes
  watch(formattedRange, refresh)

  const topProducts = computed(() => apiSummary.value?.topProducts || [])
  const userCommissions = computed(() => apiSummary.value?.userCommissions || [])
  onMounted(refresh)
  return { stats, currentAnalytics, topProducts, userCommissions, pending, refresh }
}
