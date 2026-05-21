import { ref, computed, watch, onMounted, type Ref } from 'vue'
import { useGlobalFilter } from '~/composables/useGlobalFilter'

type DateQuery = { dateFrom?: string; dateTo?: string }

/**
 * Load list-page filter dropdown values from API (distinct DB values, not hardcoded presets).
 */
export function useViewFilterOptions<T extends Record<string, string[]>>(
  fetcher: (query: DateQuery, signal?: AbortSignal) => Promise<{ data?: T }>,
  keys: (keyof T & string)[]
) {
  const { formattedRange } = useGlobalFilter()
  const options = ref({}) as Ref<Partial<T>>
  const loading = ref(false)

  keys.forEach((key) => {
    ;(options.value as Record<string, string[]>)[key] = []
  })

  let abort: AbortController | null = null

  async function refresh() {
    abort?.abort()
    abort = new AbortController()
    loading.value = true
    try {
      const res = await fetcher(
        {
          dateFrom: formattedRange.value.start || undefined,
          dateTo: formattedRange.value.end || undefined
        },
        abort.signal
      )
      const data = (res.data || {}) as T
      keys.forEach((key) => {
        const list = Array.isArray(data[key]) ? data[key] : []
        ;(options.value as Record<string, string[]>)[key] = [...list]
      })
    } catch (e: unknown) {
      if ((e as { name?: string })?.name === 'AbortError') return
      keys.forEach((key) => {
        ;(options.value as Record<string, string[]>)[key] = []
      })
    } finally {
      loading.value = false
    }
  }

  watch(formattedRange, refresh, { deep: true })
  onMounted(refresh)

  function itemsFor(key: keyof T & string): Ref<string[]> {
    return computed(() => (options.value as Record<string, string[]>)[key] || [])
  }

  return { options, loading, refresh, itemsFor }
}
