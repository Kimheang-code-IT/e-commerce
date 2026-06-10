import { ref, computed, watch } from 'vue'
import type { TableColumn } from '@nuxt/ui'
import type { DeliveryEntry } from '~/types'
import { useDeliveryApi } from '~/utils/api'
import { useBaseTable } from '~/composables/table/useBaseTable'
import { useServerListTable } from '~/features/shared/useServerListTable'
import { useViewFilterOptions } from '~/composables/useViewFilterOptions'
import { useAuthStore } from '~/stores/auth'
import { formatCurrency } from '~/utils/format/currency'

export function useDelivery() {
  const { t } = useI18n()
  const auth = useAuthStore()
  const perms = useModulePermissions('delivery')
  const isAdmin = computed(() => auth.hasRole(['admin']))
  const deliveryApi = useDeliveryApi()
  const { rowSelection, columnVisibility } = useBaseTable({})
  const localRows = ref<DeliveryEntry[]>([])
  const selectedAddresses = ref<string[]>([])
  const selectedDeliveryTypes = ref<string[]>([])
  const selectedStatuses = ref<string[]>([])
  const extraQuery = computed(() => ({
    address: selectedAddresses.value.join(',') || undefined,
    deliveryType: selectedDeliveryTypes.value.join(',') || undefined,
    deliveryStatus: selectedStatuses.value.join(',') || undefined,
  }))
  const { sorting, columnFilters, pagination, searchQuery, resource } = useServerListTable<DeliveryEntry>({
    resourceKey: 'deliveries-view',
    initialSorting: [{ id: 'date', desc: true }],
    localData: localRows,
    extraQuery,
    listFn: (query, signal) => deliveryApi.list(query, signal),
  })

  const { itemsFor } = useViewFilterOptions(
    (query, signal) => deliveryApi.filterOptions(query, signal),
    ['addresses', 'deliveryTypes', 'statuses']
  )
  const addressItems = itemsFor('addresses')
  const deliveryTypeItems = itemsFor('deliveryTypes')
  const statusItems = itemsFor('statuses')

  const effectiveRows = computed(() => resource.rows.value)
  const filteredDeliveryRows = computed<DeliveryEntry[]>(() => effectiveRows.value)
  const deliverySummary = computed(() => {
    const rows = filteredDeliveryRows.value
    return {
      count: rows.length,
      deliveryPriceSum: rows.reduce((sum, row) => sum + Number(row.deliveryPrice || 0), 0),
      totalSum: rows.reduce((sum, row) => sum + Number(row.total || 0), 0),
    }
  })

  watch([selectedAddresses, selectedDeliveryTypes, selectedStatuses], () => {
    pagination.value.pageIndex = 0
  })

  const columns = computed<TableColumn<DeliveryEntry>[]>(() => {
    const base: TableColumn<DeliveryEntry>[] = [
    { accessorKey: 'invoiceNo', header: t('pages.delivery.columns.invoiceNo'), footer: `Count: ${deliverySummary.value.count}` },
    ...(isAdmin.value
      ? [{ accessorKey: 'seller', header: t('pages.delivery.columns.seller') } satisfies TableColumn<DeliveryEntry>]
      : []),
    { accessorKey: 'customer', header: t('pages.delivery.columns.customer') },
    { accessorKey: 'address', header: t('pages.delivery.columns.address') },
    { accessorKey: 'deliveryType', header: t('pages.delivery.columns.deliveryType') },
    { accessorKey: 'deliveryStatus', header: t('pages.delivery.columns.deliveryStatus') },
    { accessorKey: 'deliveryPrice', header: t('pages.delivery.columns.deliveryPrice'), footer: formatCurrency(deliverySummary.value.deliveryPriceSum, 'USD') },
    { accessorKey: 'total', header: t('pages.delivery.columns.total'), footer: formatCurrency(deliverySummary.value.totalSum, 'USD') },
    { accessorKey: 'date', header: t('pages.delivery.columns.date') },
    { id: 'actions', header: '' },
    ]
    return base
  })

  async function updateStatus(invoiceId: string, status: string) {
    await deliveryApi.updateStatus(invoiceId, status)
    await resource.refresh()
  }

  async function updateAllPendingToDelivered() {
    const pendingRows = effectiveRows.value.filter((r) => r.deliveryStatus === 'pending')
    for (const row of pendingRows) {
      const id = row.invoiceId || row.invoiceNo
      if (id) await deliveryApi.updateStatus(id, 'delivered')
    }
    await resource.refresh()
  }

  return {
    rowSelection,
    sorting,
    columnFilters,
    pagination,
    searchQuery,
    columnVisibility,
    isLoading: resource.isLoading,
    totalRows: resource.totalRows,
    addressItems,
    deliveryTypeItems,
    statusItems,
    selectedAddresses,
    selectedDeliveryTypes,
    selectedStatuses,
    filteredDeliveryRows,
    columns,
    updateStatus,
    updateAllPendingToDelivered,
    canUpdate: perms.canUpdate,
    canExport: perms.canExport,
    isAdmin,
  }
}
