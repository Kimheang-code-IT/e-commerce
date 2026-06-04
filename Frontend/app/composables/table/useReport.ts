import { computed, ref, watch } from 'vue'
import type { DropdownMenuItem, TableColumn } from '@nuxt/ui'
import { useBaseTable } from '~/composables/table/useBaseTable'
import { useReportApi } from '~/utils/api'
import { formatCurrency } from '~/utils/format/currency'
import type { ReportRow } from '~/types'
import { useServerListTable } from '~/features/shared/useServerListTable'
import { useViewFilterOptions } from '~/composables/useViewFilterOptions'
import { useAuthStore } from '~/stores/auth'

export type ReportRowActionHandlers = {
  onRefund: (row: ReportRow) => void
  onCheckout: (row: ReportRow) => void
  onPreview?: (row: ReportRow) => void
}

export function useReport(handlers?: ReportRowActionHandlers) {
  const { t } = useI18n()
  const auth = useAuthStore()
  const reportApi = useReportApi()
  const { rowSelection, columnVisibility } = useBaseTable({})
  const reportRows = ref<ReportRow[]>([])
  const selectedProducts = ref<string[]>([])
  const selectedSources = ref<string[]>([])
  const selectedProvinces = ref<string[]>([])
  const filterExtraQuery = computed(() => ({
    product: selectedProducts.value.join(',') || undefined,
    source: selectedSources.value.join(',') || undefined,
    province: selectedProvinces.value.join(',') || undefined
  }))
  const { sorting, columnFilters, pagination, searchQuery, resource } = useServerListTable<ReportRow>({
    resourceKey: 'reports-view',
    initialSorting: [{ id: 'date', desc: true }],
    localData: reportRows,
    extraQuery: filterExtraQuery,
    listFn: (query, signal) => reportApi.list(query, signal),
  })

  const { itemsFor } = useViewFilterOptions(
    (query, signal) => reportApi.filterOptions(query, signal),
    ['products', 'sources', 'provinces']
  )
  const productItems = itemsFor('products')
  const sourceItems = itemsFor('sources')
  const provinceItems = itemsFor('provinces')

  const selectedReportRows = computed<ReportRow[]>(() => {
    const selectedIndexes = Object.keys(rowSelection.value || {})
      .filter((key) => (rowSelection.value as Record<string, boolean>)[key])
      .map((key) => Number(key))
      .filter((value) => Number.isInteger(value) && value >= 0)

    return selectedIndexes
      .map((index) => filteredReportRows.value[index])
      .filter((row): row is ReportRow => Boolean(row))
  })
  const allFilteredSelected = computed(() => {
    const rows = filteredReportRows.value
    if (!rows.length) return false
    const selected = rowSelection.value as Record<string, boolean>
    return rows.every((_, index) => Boolean(selected[String(index)]))
  })
  const someFilteredSelected = computed(() => {
    const rows = filteredReportRows.value
    if (!rows.length) return false
    const selected = rowSelection.value as Record<string, boolean>
    const selectedCount = rows.reduce(
      (count, _row, index) => (selected[String(index)] ? count + 1 : count),
      0
    )
    return selectedCount > 0 && selectedCount < rows.length
  })

  const effectiveRows = computed(() => resource.rows.value)
  const filteredReportRows = computed<ReportRow[]>(() => effectiveRows.value)

  watch([selectedProducts, selectedSources, selectedProvinces], () => {
    pagination.value.pageIndex = 0
  })

  const reportSummary = computed(() => {
    const rows = filteredReportRows.value
    const invoiceCount = rows.length
    const amountSum = rows.reduce((sum, row) => sum + Number(row.amount || 0), 0)

    return {
      invoiceCount,
      productCount: invoiceCount,
      amountSum
    }
  })

  const columns = computed<TableColumn<ReportRow>[]>(() => [
    { accessorKey: 'no', header: t('pages.report.columns.no') },
    { accessorKey: 'invoiceNo', header: t('pages.report.columns.invoiceNo'), footer: `Count: ${reportSummary.value.invoiceCount}` },
    { accessorKey: 'customer', header: t('pages.report.columns.customer') },
    { accessorKey: 'product', header: t('pages.report.columns.product') },
    { accessorKey: 'phoneCustomer', header: t('pages.report.columns.phoneCustomer') },
    { accessorKey: 'seller', header: t('pages.report.columns.seller') },
    { accessorKey: 'source', header: t('pages.report.columns.source') },
    { accessorKey: 'address', header: t('pages.report.columns.address') },
    { accessorKey: 'amount', header: t('pages.report.columns.amount'), footer: formatCurrency(reportSummary.value.amountSum, 'USD') },
    { id: 'action', header: t('common.actions') }
  ])

  function toggleSelectAllFiltered(checked: boolean) {
    const rows = filteredReportRows.value
    if (!rows.length) {
      rowSelection.value = {}
      return
    }
    if (checked) {
      const next: Record<string, boolean> = {}
      rows.forEach((_row, index) => {
        next[String(index)] = true
      })
      rowSelection.value = next
      return
    }
    rowSelection.value = {}
  }

  watch(filteredReportRows, (rows) => {
    const current = rowSelection.value as Record<string, boolean>
    const next: Record<string, boolean> = {}
    rows.forEach((_row, index) => {
      const key = String(index)
      if (current[key]) next[key] = true
    })
    rowSelection.value = next
  })

  function getDropdownActions(row: ReportRow): DropdownMenuItem[][] {
    if (!handlers) return []
    const items: DropdownMenuItem[] = []
    if (auth.hasPermission('refund:create')) {
      items.push({
        label: t('pages.report.actions.refund'),
        icon: 'i-lucide-rotate-ccw',
        color: 'warning',
        onSelect: () => handlers.onRefund(row)
      })
    }
    if (handlers.onPreview && (auth.hasPermission('pos:view') || auth.hasPermission('pos:checkout'))) {
      items.push({
        label: t('pages.report.actions.preview'),
        icon: 'i-lucide-eye',
        onSelect: () => handlers.onPreview!(row),
      })
    }
    if (auth.hasPermission('pos:checkout')) {
      items.push({
        label: t('pages.report.actions.checkout'),
        icon: 'i-lucide-shopping-cart',
        onSelect: () => handlers.onCheckout(row),
      })
    }
    return items.length ? [items] : []
  }

  return {
    rowSelection,
    sorting,
    searchQuery,
    columnVisibility,
    columnFilters,
    pagination,
    isLoading: resource.isLoading,
    reportRows: resource.rows,
    filteredReportRows,
    productItems,
    sourceItems,
    provinceItems,
    selectedProducts,
    selectedSources,
    selectedProvinces,
    selectedReportRows,
    allFilteredSelected,
    someFilteredSelected,
    toggleSelectAllFiltered,
    columns,
    getDropdownActions,
    totalRows: resource.totalRows,
    refresh: () => resource.refresh()
  }
}
