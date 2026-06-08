import type { CourseCardItem } from '~/components/common/CourseCard.vue'

export type CatalogCategory = {
  id: string
  name: string
  productCount: number
}

type CatalogListResponse<T> = {
  data?: T[]
  total?: number
}

function resolveCatalogImage(image: string | undefined, apiBase: string) {
  const value = String(image || '').trim()
  if (!value) return ''
  if (value.startsWith('http://') || value.startsWith('https://')) return value
  const origin = apiBase.replace(/\/api\/v1\/?$/, '')
  return value.startsWith('/') ? `${origin}${value}` : `${origin}/${value}`
}

function mapCatalogProduct(item: Record<string, unknown>, apiBase: string): CourseCardItem {
  return {
    id: String(item.id ?? ''),
    category: String(item.category ?? ''),
    image: resolveCatalogImage(String(item.image ?? ''), apiBase),
    model: String(item.model ?? ''),
    name: String(item.name ?? ''),
    discountPrice: item.discountPrice as string | number | undefined,
    totalPrice: (item.totalPrice ?? 0) as string | number,
    size: String(item.size ?? ''),
    top: String(item.top ?? ''),
    backSide: String(item.backSide ?? ''),
    fretboard: String(item.fretboard ?? ''),
    string: String(item.string ?? ''),
    finishing: String(item.finishing ?? ''),
    color: String(item.color ?? '')
  }
}

export function useCatalog() {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase as string

  const categories = useState<CatalogCategory[]>('catalog-categories', () => [])
  const allProducts = useState<CourseCardItem[]>('catalog-products', () => [])
  const isLoading = useState('catalog-loading', () => false)
  const isProductsLoading = useState('catalog-products-loading', () => false)
  const loadError = useState<string | null>('catalog-error', () => null)
  const activeCategoryId = useState<string>('catalog-active-category', () => '')

  async function loadCategories() {
    const categoryRes = await $fetch<CatalogListResponse<Record<string, unknown>>>(
      `${apiBase}/catalog/categories`,
      { query: { page: 1, limit: 200 } }
    )

    categories.value = (categoryRes.data || [])
      .map((item) => ({
        id: String(item.id || '').trim(),
        name: String(item.name || '').trim(),
        productCount: Number(item.productCount ?? 0)
      }))
      .filter((item) => item.id && item.name && item.productCount > 0)
  }

  async function loadProducts(categoryId = '') {
    isProductsLoading.value = true
    try {
      const productRes = await $fetch<CatalogListResponse<Record<string, unknown>>>(
        `${apiBase}/catalog/products`,
        {
          query: {
            page: 1,
            limit: 500,
            category: categoryId || undefined
          }
        }
      )

      allProducts.value = (productRes.data || []).map((item) =>
        mapCatalogProduct(item, apiBase)
      )
      activeCategoryId.value = categoryId
    } finally {
      isProductsLoading.value = false
    }
  }

  async function loadCatalog(categoryId = '') {
    if (isLoading.value) return
    isLoading.value = true
    loadError.value = null

    try {
      await loadCategories()
      await loadProducts(categoryId)
    } catch (error) {
      categories.value = []
      allProducts.value = []
      loadError.value = error instanceof Error ? error.message : 'Failed to load catalog'
    } finally {
      isLoading.value = false
    }
  }

  async function selectCategory(categoryId: string) {
    if (categoryId === activeCategoryId.value) return
    loadError.value = null
    try {
      await loadProducts(categoryId)
    } catch (error) {
      loadError.value = error instanceof Error ? error.message : 'Failed to load products'
    }
  }

  function isKnownCategory(categoryId: string) {
    if (!categoryId) return true
    return categories.value.some((item) => item.id === categoryId)
  }

  return {
    categories,
    allProducts,
    isLoading,
    isProductsLoading,
    loadError,
    activeCategoryId,
    loadCatalog,
    loadProducts,
    selectCategory,
    isKnownCategory
  }
}
