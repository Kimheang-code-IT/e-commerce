import { onMounted, ref } from 'vue'
import { useCategoryApi } from '~/utils/api'
import { useQueryClient } from '~/composables/data/useQueryClient'
import { MAX_TABLE_PAGE_SIZE } from '~/utils/table/pagination'

const CATEGORY_OPTIONS_KEY = 'reference:categories'
const CATEGORY_OPTIONS_TTL = 60_000

export type CategoryOption = { label: string; value: string }

export function useCategoryOptions() {
  const categoryApi = useCategoryApi()
  const queryClient = useQueryClient()
  const items = ref<CategoryOption[]>([])
  const isLoading = ref(false)

  async function load() {
    isLoading.value = true
    try {
      const res = await queryClient.getOrFetch(
        CATEGORY_OPTIONS_KEY,
        () => categoryApi.list({ page: 1, limit: MAX_TABLE_PAGE_SIZE, sortBy: 'name', sortOrder: 'asc' }),
        CATEGORY_OPTIONS_TTL,
      )
      items.value = (res.data || [])
        .map((item: { id?: string | number; name?: string }) => ({
          id: String(item?.id || '').trim(),
          name: String(item?.name || '').trim(),
        }))
        .filter((item: { id: string; name: string }) => Boolean(item.id && item.name))
        .map((item: { id: string; name: string }) => ({
          label: item.name,
          value: item.id,
        }))
    } catch {
      items.value = []
    } finally {
      isLoading.value = false
    }
  }

  function invalidate() {
    queryClient.invalidate(CATEGORY_OPTIONS_KEY)
  }

  onMounted(load)

  return { items, isLoading, load, invalidate }
}
