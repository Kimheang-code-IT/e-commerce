import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useCategoryApi, useDashboardApi, useProductApi } from '~/utils/api'

/** Home dashboard — fetches aggregated statistics from the optimized /dashboard/summary endpoint. */
export function useAnalyticsDashboard() {
  const { t } = useI18n()
  const useBackendApi = useBackendMode()
  const auth = useAuthStore()
  const dashboardApi = useDashboardApi()
  const categoryApi = useCategoryApi()
  const productApi = useProductApi()
  const { formattedRange } = useGlobalFilter()
  
  const pending = ref(false)
  const selectedCategoryId = ref<string | null>(null)
  const selectedProductId = ref<number | null>(null)
  const categories = ref<{ label: string; value: string }[]>([])
  const products = ref<{ label: string; value: number; categoryId: string }[]>([])

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
  const productOptions = computed(() => {
    const categoryId = selectedCategoryId.value
    if (!categoryId) return products.value
    return products.value.filter((p) => p.categoryId === categoryId)
  })

  watch(selectedCategoryId, () => {
    if (!selectedCategoryId.value) return
    const selectedProduct = products.value.find((p) => p.value === selectedProductId.value)
    if (selectedProduct && selectedProduct.categoryId !== selectedCategoryId.value) {
      selectedProductId.value = null
    }
  })

  async function refresh() {
    if (!useBackendApi.value) return
    if (!auth.hasPermission('dashboard:view')) {
      apiSummary.value = null
      return
    }
    pending.value = true
    try {
      const res = await dashboardApi.getSummary({
        dateFrom: formattedRange.value.start || undefined,
        dateTo: formattedRange.value.end || undefined,
        categoryId: selectedCategoryId.value || undefined,
        productId: selectedProductId.value || undefined
      })
      const data = res.data
      apiSummary.value = {
        stats: [
          {
            label: t('pages.dashboard.summary.totalProduct'),
            value: String(data?.totalProducts || 0),
            icon: 'i-lucide-folder-tree'
          },
          {
            label: t('pages.dashboard.summary.productInStock'),
            value: String(data?.productsInStock || 0),
            icon: 'i-lucide-package'
          },
          {
            label: t('pages.dashboard.summary.productOutOfStock'),
            value: String(data?.productsOutOfStock || 0),
            icon: 'i-lucide-file-text'
          },
          {
            label: t('pages.dashboard.summary.soldProducts'),
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
  watch([selectedCategoryId, selectedProductId], refresh)

  async function loadFilters() {
    if (!useBackendApi.value || !auth.hasPermission('dashboard:view')) return
    const [categoryRes, productRes] = await Promise.all([
      categoryApi.list({ page: 1, limit: 200 }),
      productApi.list({ page: 1, limit: 200 })
    ])
    categories.value = (categoryRes.data || []).map((item: any) => ({
      label: item.name,
      value: item.id
    }))
    products.value = (productRes.data || []).map((item: any) => ({
      label: item.name,
      value: Number(item.id),
      categoryId: item.categoryId
    }))
  }

  const topProducts = computed(() => apiSummary.value?.topProducts || [])
  const userCommissions = computed(() => apiSummary.value?.userCommissions || [])
  onMounted(async () => {
    await loadFilters()
    await refresh()
  })
  return {
    stats,
    currentAnalytics,
    topProducts,
    userCommissions,
    pending,
    refresh,
    categories,
    productOptions,
    selectedCategoryId,
    selectedProductId
  }
}
