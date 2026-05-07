import { computed, ref, watch } from 'vue'
import type { TableColumn } from '@nuxt/ui'
import { useBaseTable } from '~/composables/table/useBaseTable'
import { useReportApi } from '~/utils/api'
import { formatCurrency } from '~/utils/format/currency'
import type { ReportRow } from '~/types'
import { useServerListTable } from '~/features/shared/useServerListTable'

export function useReport() {
  const { t } = useI18n()
  const reportApi = useReportApi()
  const { rowSelection, columnVisibility } = useBaseTable({})
  const reportRows = ref<ReportRow[]>([])
  const selectedProducts = ref<string[]>([])
  const selectedProductsQuery = computed(() => ({
    product: selectedProducts.value.join(',') || undefined
  }))
  const { sorting, columnFilters, pagination, searchQuery, resource } = useServerListTable<ReportRow>({
    resourceKey: 'reports-view',
    initialSorting: [{ id: 'date', desc: true }],
    localData: reportRows,
    extraQuery: selectedProductsQuery,
    listFn: (query, signal) => reportApi.list(query, signal),
  })
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
  const productItems = computed<string[]>(() => {
    const allProducts = new Set<string>()
    effectiveRows.value.forEach((row) => {
      if (row.product) {
        row.product.split(',').forEach((p) => {
          const trimmed = p.trim()
          if (trimmed) allProducts.add(trimmed)
        })
      }
    })
    return [...allProducts].sort()
  })

  const filteredReportRows = computed<ReportRow[]>(() => {
    if (!selectedProducts.value.length) return effectiveRows.value
    return effectiveRows.value.filter((row) => selectedProducts.value.includes(row.product))
  })

  const reportSummary = computed(() => {
    const rows = filteredReportRows.value
    const invoiceCount = new Set(rows.map((row) => row.invoiceNo)).size
    const productCount = rows.length
    const amountSum = rows.reduce((sum, row) => sum + Number(row.amount || 0), 0)

    return {
      invoiceCount,
      productCount,
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
    { accessorKey: 'amount', header: t('pages.report.columns.amount'), footer: formatCurrency(reportSummary.value.amountSum, 'USD') }
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
    selectedProducts,
    selectedReportRows,
    allFilteredSelected,
    someFilteredSelected,
    toggleSelectAllFiltered,
    columns,
    totalRows: resource.totalRows
  }
}


