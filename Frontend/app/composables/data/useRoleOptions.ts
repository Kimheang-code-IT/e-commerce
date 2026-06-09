import { onMounted, ref } from 'vue'
import { useSystemRoleApi } from '~/utils/api'
import { useQueryClient } from '~/composables/data/useQueryClient'
import { MAX_TABLE_PAGE_SIZE } from '~/utils/table/pagination'

const ROLE_OPTIONS_KEY = 'reference:roles'
const ROLE_OPTIONS_TTL = 60_000

export function useRoleOptions() {
  const auth = useAuthStore()
  const systemRoleApi = useSystemRoleApi()
  const queryClient = useQueryClient()
  const roleNames = ref<string[]>([])
  const isLoading = ref(false)

  async function load() {
    if (!auth.hasPermission('role:view')) {
      roleNames.value = []
      return
    }
    isLoading.value = true
    try {
      const res = await queryClient.getOrFetch(
        ROLE_OPTIONS_KEY,
        () => systemRoleApi.list(
          { page: 1, limit: MAX_TABLE_PAGE_SIZE, sortBy: 'name', sortOrder: 'asc' },
          undefined,
          { suppressErrorToast: true },
        ),
        ROLE_OPTIONS_TTL,
      )
      roleNames.value = (res.data || [])
        .map((role: { name?: string }) => String(role?.name || '').trim())
        .filter(Boolean)
    } catch {
      roleNames.value = []
    } finally {
      isLoading.value = false
    }
  }

  function invalidate() {
    queryClient.invalidate(ROLE_OPTIONS_KEY)
  }

  onMounted(load)

  return { roleNames, isLoading, load, invalidate }
}
