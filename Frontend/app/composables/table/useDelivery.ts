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
  const extraQuery = computed(() => ({
    address: selectedAddresses.value.join(',') || undefined,
    deliveryType: selectedDeliveryTypes.value.join(',') || undefined
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

  const filteredDeliveryRows = computed<DeliveryEntry[]>(() => {
    return effectiveRows.value.filter((row) => {
      const matchAddress = selectedAddresses.value.length === 0 || selectedAddresses.value.includes(row.address)
      const matchType = selectedDeliveryTypes.value.length === 0 || selectedDeliveryTypes.value.includes(row.deliveryType)
      return matchAddress && matchType
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
    { accessorKey: 'date', header: t('pages.delivery.columns.date') }
  ])

  return {
    rowSelection,
    sorting,
    searchQuery,
    columnVisibility,
    columnFilters,
    pagination,
    addressItems,
    deliveryTypeItems,
    selectedAddresses,
    selectedDeliveryTypes,
    isLoading: resource.isLoading,
    totalRows: resource.totalRows,
    deliveryRows: resource.rows,
    filteredDeliveryRows,
    columns
  }
}
