import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { Product } from '~/types'
import { useCategoryApi, useProductsViewApi } from '~/utils/api'

export function usePosProducts() {
  const productsViewApi = useProductsViewApi()
  const categoryApi = useCategoryApi()
  const isLoadingProducts = ref(false)
  const products = ref<Product[]>([])
  const categories = ref<{ label: string; value: string }[]>([{ label: 'All', value: 'All' }])
  const selectedCategoryId = ref('All')
  const searchQuery = ref('')
  const debouncedSearchQuery = ref('')
  const visibleCount = ref(60)
  const selectedCategory = computed(() => selectedCategoryId.value)
  const categoryTabs = computed(() => categories.value)
  let searchDebounceTimer: ReturnType<typeof setTimeout> | null = null

  async function loadCategories() {
    const res = await categoryApi.list({ limit: 100 })
    const cats = (res.data || []).map((item: any) => ({
      label: String(item.name || ''),
      value: String(item.id || '')
    }))
    categories.value = [{ label: 'All', value: 'All' }, ...cats]
  }

  async function loadProducts() {
    isLoadingProducts.value = true
    try {
      const query: any = {
        limit: visibleCount.value,
        search: debouncedSearchQuery.value || undefined,
        category: selectedCategory.value === 'All' ? undefined : selectedCategory.value
      }
      const res = await productsViewApi.list(query)
      products.value = res?.data || []
    } finally {
      isLoadingProducts.value = false
    }
  }

  function loadMoreProducts() {
    visibleCount.value += 60
  }

  function selectCategoryById(categoryId: string) {
    selectedCategoryId.value = categoryId
  }

  const filteredProducts = computed(() => products.value.filter((item) => item.status !== 'out_of_stock'))

  watch(searchQuery, (value) => {
    if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
    searchDebounceTimer = setTimeout(() => {
      debouncedSearchQuery.value = value.trim().toLowerCase()
    }, 300)
  }, { immediate: true })

  watch([debouncedSearchQuery, selectedCategoryId], async () => {
    visibleCount.value = 60
    await loadProducts()
  })

  watch(visibleCount, loadProducts)

  onMounted(async () => {
    await loadCategories()
    await loadProducts()
  })

  onBeforeUnmount(() => {
    if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  })

  return {
    isLoadingProducts,
    filteredProducts,
    categoryTabs,
    selectedCategoryId,
    searchQuery,
    loadProducts,
    loadMoreProducts,
    selectCategoryById
  }
}
