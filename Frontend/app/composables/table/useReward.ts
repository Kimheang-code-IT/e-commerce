import { computed, ref, watch } from 'vue'
import type { TableColumn, DropdownMenuItem } from '@nuxt/ui'
import { useBaseTable } from '~/composables/table/useBaseTable'
import { useTableQuery } from '~/composables/table/useTableQuery'
import type { Product, Reward } from '~/types'
import { useProductApi, useRewardApi } from '~/utils/api'
import type { ApiQueryParams } from '~/utils/api'
import { useServerTableResource } from '~/composables/table/useServerTableResource'

type RewardFormPayload = {
  id?: number
  name: string
  productIds: number[]
}

export function useReward() {
  const useBackendApi = computed(() => true)
  const rewardApi = useRewardApi()
  const productApi = useProductApi()
  const { formattedRange } = useGlobalFilter()
  const { t, toast, rowSelection, columnVisibility, isConfirmOpen } = useBaseTable({})
  const perms = useModulePermissions('product')

  const { sorting, columnFilters, pagination, serverQuery } = useTableQuery({
    initialSorting: [{ id: 'id', desc: true }],
  })
  const searchQuery = ref('')
  const isFormOpen = ref(false)
  const selectedEntry = ref<Reward | null>(null)
  const formName = ref('')
  const selectedProductIds = ref<number[]>([])
  const allProducts = ref<Product[]>([])
  const isProductsLoading = ref(false)
  const productSearch = ref('')

  const confirmMode = ref<'add' | 'edit' | 'delete'>('add')
  const pendingPayload = ref<RewardFormPayload | null>(null)
  const pendingDeleteId = ref<number | null>(null)

  const mergedServerQuery = computed(() => ({
    ...serverQuery.value,
    search: searchQuery.value.trim() || undefined,
    dateFrom: formattedRange.value.start || undefined,
    dateTo: formattedRange.value.end || undefined,
  }))

  watch(searchQuery, () => {
    pagination.value.pageIndex = 0
  })

  const resource = useServerTableResource<Reward, ApiQueryParams>({
    resourceKey: 'rewards',
    useBackendApi,
    serverQuery: mergedServerQuery,
    localData: ref([]),
    listFn: (query, signal) => rewardApi.list(query, signal),
    debounceMs: 250,
  })

  const filteredEntries = computed(() => resource.rows.value)
  const totalRows = computed(() => resource.totalRows.value)
  const isLoading = computed(() => resource.isLoading.value)

  const filteredProductOptions = computed(() => {
    const q = productSearch.value.trim().toLowerCase()
    if (!q) return allProducts.value
    return allProducts.value.filter((p) => p.name.toLowerCase().includes(q))
  })

  const columns = computed<TableColumn<Reward>[]>(() => [
    { accessorKey: 'id', header: t('reward.no') },
    { accessorKey: 'name', header: t('reward.name') },
    { accessorKey: 'productNames', header: t('reward.products') },
    { accessorKey: 'createdAt', header: t('reward.createdAt') },
    { id: 'action', header: t('common.actions') },
  ])

  async function loadProducts() {
    isProductsLoading.value = true
    try {
      const res = await productApi.list({ page: 1, limit: 500, sortBy: 'name', sortOrder: 'asc' })
      allProducts.value = (res?.data || []).filter((p) => p.status !== 'inactive')
    } finally {
      isProductsLoading.value = false
    }
  }

  function resetForm() {
    formName.value = ''
    selectedProductIds.value = []
    productSearch.value = ''
    selectedEntry.value = null
  }

  function handleAddNew() {
    resetForm()
    selectedEntry.value = null
    isFormOpen.value = true
    void loadProducts()
  }

  function openEdit(entry: Reward) {
    selectedEntry.value = entry
    formName.value = entry.name
    selectedProductIds.value = [...(entry.productIds || [])]
    productSearch.value = ''
    isFormOpen.value = true
    void loadProducts()
  }

  function toggleProduct(productId: number, checked: boolean) {
    if (checked) {
      if (!selectedProductIds.value.includes(productId)) {
        selectedProductIds.value = [...selectedProductIds.value, productId]
      }
      return
    }
    selectedProductIds.value = selectedProductIds.value.filter((id) => id !== productId)
  }

  function getDropdownActions(entry: Reward): DropdownMenuItem[][] {
    const items: DropdownMenuItem[] = []
    if (perms.canUpdate.value) {
      items.push({
        label: t('actions.edit'),
        icon: 'i-lucide-edit',
        onSelect: () => openEdit(entry),
      })
    }
    if (perms.canDelete.value) {
      items.push({
        label: t('actions.delete'),
        icon: 'i-lucide-trash',
        color: 'error' as const,
        onSelect: () => {
          pendingDeleteId.value = entry.id
          confirmMode.value = 'delete'
          isConfirmOpen.value = true
        },
      })
    }
    return items.length ? [items] : []
  }

  function handleSaveRequest() {
    const name = formName.value.trim()
    if (!name) return
    if (!selectedProductIds.value.length) {
      toast.add({ title: t('common.error'), description: t('reward.selectProductsError'), color: 'error' })
      return
    }
    const isEdit = selectedEntry.value != null
    if (isEdit && !perms.canUpdate.value) return
    if (!isEdit && !perms.canCreate.value) return

    pendingPayload.value = {
      id: selectedEntry.value?.id,
      name,
      productIds: [...selectedProductIds.value],
    }
    confirmMode.value = isEdit ? 'edit' : 'add'
    isConfirmOpen.value = true
  }

  const confirmConfig = computed(() => {
    if (confirmMode.value === 'delete') {
      return {
        title: t('pages.reward.confirmDeleteTitle'),
        description: t('pages.reward.confirmDeleteDesc'),
        type: 'error' as const,
        submitLabel: t('actions.delete'),
      }
    }
    const name = pendingPayload.value?.name || ''
    if (confirmMode.value === 'edit') {
      return {
        title: t('pages.reward.confirmEditTitle'),
        description: t('pages.reward.confirmEditDesc', { name }),
        type: 'primary' as const,
        submitLabel: t('actions.save'),
      }
    }
    return {
      title: t('pages.reward.confirmAddTitle'),
      description: t('pages.reward.confirmAddDesc', { name }),
      type: 'primary' as const,
      submitLabel: t('actions.confirm'),
    }
  })

  async function finalizeAction() {
    try {
      if (confirmMode.value === 'delete' && pendingDeleteId.value != null) {
        await rewardApi.remove(pendingDeleteId.value)
        toast.add({ title: t('pages.reward.toastDeleted'), color: 'error' })
        pendingDeleteId.value = null
      } else {
        const payload = pendingPayload.value
        if (!payload) return
        const body = {
          name: payload.name,
          products: payload.productIds.map((productId) => ({ productId, qty: 1 })),
        }
        if (confirmMode.value === 'edit' && payload.id) {
          await rewardApi.update(payload.id, body)
          toast.add({ title: t('pages.reward.toastUpdated'), color: 'primary' })
        } else {
          await rewardApi.create(body)
          toast.add({ title: t('pages.reward.toastAdded'), color: 'primary' })
        }
        pendingPayload.value = null
        isFormOpen.value = false
        resetForm()
      }
      await resource.refresh()
      isConfirmOpen.value = false
    } catch (err: any) {
      const msg = err?.data?.message || err?.message || t('common.toast.tryAgain')
      toast.add({
        title: t('common.toast.requestFailed'),
        description: msg,
        color: 'error',
      })
    }
  }

  return {
    rowSelection,
    sorting,
    searchQuery,
    columnVisibility,
    columnFilters,
    pagination,
    isFormOpen,
    isConfirmOpen,
    totalRows,
    selectedEntry,
    filteredEntries,
    confirmConfig,
    isLoading,
    columns,
    getDropdownActions,
    handleSaveRequest,
    finalizeAction,
    handleAddNew,
    canCreate: perms.canCreate,
    canUpdate: perms.canUpdate,
    canDelete: perms.canDelete,
    formName,
    selectedProductIds,
    allProducts,
    filteredProductOptions,
    isProductsLoading,
    productSearch,
    toggleProduct,
    resetForm,
  }
}
