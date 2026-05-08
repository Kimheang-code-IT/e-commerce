import { computed, ref } from 'vue'
import type { TableColumn } from '@nuxt/ui'
import { useBaseTable } from '~/composables/table/useBaseTable'
import type { DeliveryEntry } from '~/types'
import { formatCurrency } from '~/utils/format/currency'
import { useDeliveryApi } from '~/utils/api'
import { useServerListTable } from '~/features/shared/useServerListTable'

export function useDelivery() {
  const { t } = useI18n()
  const deliveryApi = useDeliveryApi()
  const { rowSelection, columnVisibility } = useBaseTable({})
  const deliveryRows = ref<DeliveryEntry[]>([])
  const selectedAddresses = ref<string[]>([])
  const selectedDeliveryTypes = ref<string[]>([])
  const selectedStatuses = ref<string[]>([])
  const extraQuery = computed(() => ({
    address: selectedAddresses.value.join(',') || undefined,
    deliveryType: selectedDeliveryTypes.value.join(',') || undefined,
    deliveryStatus: selectedStatuses.value.join(',') || undefined
  }))
  const { sorting, columnFilters, pagination, searchQuery, resource } = useServerListTable<DeliveryEntry>({
    resourceKey: 'deliveries-view',
    initialSorting: [{ id: 'date', desc: true }],
    localData: deliveryRows,
    extraQuery,
    listFn: (query, signal) => deliveryApi.list(query, signal),
  })
  const effectiveRows = computed(() => resource.rows.value)

  const addressItems = computed<string[]>(() => {
    const unique = new Set(effectiveRows.value.map((row) => row.address))
    return [...unique]
  })

  const deliveryTypeItems = computed<string[]>(() => {
    const unique = new Set(effectiveRows.value.map((row) => row.deliveryType))
    return [...unique]
  })
  
  const statusItems = computed<string[]>(() => {
    const unique = new Set(effectiveRows.value.map((row) => row.deliveryStatus))
    return [...unique]
  })

  const filteredDeliveryRows = computed<DeliveryEntry[]>(() => {
    return effectiveRows.value.filter((row) => {
      const matchAddress = selectedAddresses.value.length === 0 || selectedAddresses.value.includes(row.address)
      const matchType = selectedDeliveryTypes.value.length === 0 || selectedDeliveryTypes.value.includes(row.deliveryType)
      const matchStatus = selectedStatuses.value.length === 0 || selectedStatuses.value.includes(row.deliveryStatus)
      return matchAddress && matchType && matchStatus
    })
  })

  const deliverySummary = computed(() => {
    const rows = filteredDeliveryRows.value
    const invoiceCount = rows.length
    const deliveryPriceSum = rows.reduce((sum, row) => sum + Number(row.deliveryPrice || 0), 0)

    return {
      invoiceCount,
      deliveryPriceSum
    }
  })

  const columns = computed<TableColumn<DeliveryEntry>[]>(() => [
    { accessorKey: 'no', header: t('pages.delivery.columns.no') },
    {
      accessorKey: 'invoiceId',
      header: t('pages.delivery.columns.invoiceId'),
      footer: `Count: ${deliverySummary.value.invoiceCount}`
    },
    { accessorKey: 'address', header: t('pages.delivery.columns.address') },
    { accessorKey: 'deliveryType', header: t('pages.delivery.columns.deliveryType') },
    {
      accessorKey: 'deliveryPrice',
      header: t('pages.delivery.columns.deliveryPrice'),
      footer: formatCurrency(deliverySummary.value.deliveryPriceSum, 'USD')
    },
    { accessorKey: 'deliveryStatus', header: t('pages.delivery.columns.deliveryStatus') },
    { accessorKey: 'date', header: t('pages.delivery.columns.date') }
  ])

  const toast = useToast()
  async function updateStatus(invoiceId: string, status: string) {
    try {
      await deliveryApi.updateStatus(invoiceId, status)
      toast.add({ title: t('common.success') || 'Success', color: 'success' })
      resource.refresh()
    } catch (error: any) {
      toast.add({ title: t('common.error') || 'Error', description: error.message, color: 'error' })
    }
  }

  async function updateAllPendingToDelivered() {
    const pendingRows = effectiveRows.value.filter(r => r.deliveryStatus === 'pending')
    if (pendingRows.length === 0) return
    
    try {
      await Promise.all(pendingRows.map(r => deliveryApi.updateStatus(r.invoiceId, 'delivered')))
      toast.add({ title: t('common.success') || 'Success', description: `Updated ${pendingRows.length} items`, color: 'success' })
      resource.refresh()
    } catch (error: any) {
      toast.add({ title: t('common.error') || 'Error', description: error.message, color: 'error' })
    }
  }

  return {
    rowSelection,
    sorting,
    searchQuery,
    columnVisibility,
    columnFilters,
    pagination,
    addressItems,
    deliveryTypeItems,
    statusItems,
    selectedAddresses,
    selectedDeliveryTypes,
    selectedStatuses,
    isLoading: resource.isLoading,
    totalRows: resource.totalRows,
    deliveryRows: resource.rows,
    filteredDeliveryRows,
    columns,
    updateStatus,
    updateAllPendingToDelivered,
    refresh: resource.refresh
  }
}
