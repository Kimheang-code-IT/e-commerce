import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { Product } from '~/types'
import { useProductsViewApi } from '~/utils/api'
import { useCategoryOptions } from '~/composables/data/useCategoryOptions'

export function usePosProducts() {
  const productsViewApi = useProductsViewApi()
  const { items: categoryOptions } = useCategoryOptions()
  const isLoadingProducts = ref(false)
  const products = ref<Product[]>([])
  const categories = computed(() => [{ label: 'All', value: 'All' }, ...categoryOptions.value]))
  const selectedCategoryId = ref('All')
  const searchQuery = ref('')
  const debouncedSearchQuery = ref('')
  const visibleCount = ref(60)
  const selectedCategory = computed(() => selectedCategoryId.value)
  const categoryTabs = computed(() => categories.value)
  let searchDebounceTimer: ReturnType<typeof setTimeout> | null = null

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

  watch([debouncedSearchQuery, selectedCategoryId], () => {
    if (visibleCount.value !== 60) {
      visibleCount.value = 60
      return
    }
    loadProducts()
  })

  watch(visibleCount, (count, previous) => {
    if (count === previous) return
    loadProducts()
  })

  onMounted(() => {
    loadProducts()
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
