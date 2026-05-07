import { ref, computed } from 'vue'
import type { TableColumn } from '@nuxt/ui'
import type { FinanceEntry } from '~/types'
import { useFinanceApi } from '~/utils/api'
import { useServerListTable } from '~/features/shared/useServerListTable'

export function useFinance() {
  const { t } = useI18n()
  const financeApi = useFinanceApi()
  const data = ref<FinanceEntry[]>([])
  const { sorting, columnFilters, pagination, searchQuery, resource } = useServerListTable<FinanceEntry>({
    resourceKey: 'finance-view',
    initialSorting: [{ id: 'productName', desc: false }],
    localData: data,
    listFn: (query, signal) => financeApi.list(query, signal)
  })
  const groupingOptions = ref({})
  const grouping = ref<string[]>([])
  const effectiveRows = computed(() => resource.rows.value)

  const financeSummary = computed(() => {
    const rows = effectiveRows.value
    const sumBy = (selector: (row: FinanceEntry) => number) =>
      rows.reduce((total, row) => total + Number(selector(row) || 0), 0)

    const printPriceSum = sumBy((row: FinanceEntry) => row.printPrice)
    const totalCommissionSum = sumBy((row: FinanceEntry) => row.totalCommission)
    const facebookSum = sumBy((row: FinanceEntry) => row.facebook)
    const otherSum = sumBy((row: FinanceEntry) => row.other)
    const posSum = sumBy((row: FinanceEntry) => row.inPriceForPos)
    const grossRevenueSum = sumBy((row: FinanceEntry) => row.grossRevenue)
    const soldQtySum = sumBy((row: FinanceEntry) => row.soldQty)
    const totalPriceSum = sumBy((row: FinanceEntry) => row.finalPrice)

    return {
      count: rows.length,
      printPriceSum,
      totalCommissionSum,
      facebookSum,
      otherSum,
      posSum,
      grossRevenueSum,
      soldQtySum,
      totalPriceSum
    }
  })

  const isSlideoverOpen = ref(false)
  const editingRow = ref<FinanceEntry | null>(null)

  const editFields = computed(() => [
    { key: 'productName', label: t('pages.finance.columns.productName'), type: 'input', readonly: true },
    { key: 'facebook', label: t('pages.finance.columns.facebook'), type: 'number' },
    { key: 'other', label: t('pages.finance.columns.other'), type: 'number' },
    { key: 'totalCommission', label: t('pages.finance.columns.totalCommission'), type: 'number', readonly: true },
    { key: 'inPriceForPos', label: t('pages.finance.columns.inPriceForPos'), type: 'number', readonly: true },
  ])

  function openEdit(row: FinanceEntry) {
    editingRow.value = { ...row }
    isSlideoverOpen.value = true
  }

  async function handleUpdate(updatedData: any) {
    if (!editingRow.value?.id) return
    try {
      await financeApi.update(Number(editingRow.value?.id || 0), {
        facebook: Number(updatedData.facebook || 0),
        other: Number(updatedData.other || 0)
      })
      resource.refresh()
      isSlideoverOpen.value = false
      editingRow.value = null
    } catch (err) {
      console.error('Update failed:', err)
    }
  }

  const columns = computed<TableColumn<FinanceEntry>[]>(() => [
    {
      accessorKey: 'productName',
      header: t('pages.finance.columns.productName'),
      footer: `Count: ${financeSummary.value.count}`
    },
    {
      accessorKey: 'printPrice',
      header: t('product.inPrice'),
      footer: formatCurrency(financeSummary.value.printPriceSum, 'USD')
    },
    {
      accessorKey: 'soldQty',
      header: t('pages.report.columns.sold'),
      footer: `Total: ${financeSummary.value.soldQtySum}`
    },

    {
      accessorKey: 'inPriceForPos',
      header: t('pages.finance.columns.inPriceForPos'),
      footer: formatCurrency(financeSummary.value.posSum, 'USD')
    },
    {
      accessorKey: 'totalCommission',
      header: t('pages.finance.columns.totalCommission'),
      footer: formatCurrency(financeSummary.value.totalCommissionSum, 'USD')
    },
    {
      accessorKey: 'facebook',
      header: t('pages.finance.columns.facebook'),
      footer: formatCurrency(financeSummary.value.facebookSum, 'USD')
    },
    {
      accessorKey: 'other',
      header: t('pages.finance.columns.other'),
      footer: formatCurrency(financeSummary.value.otherSum, 'USD')
    },
    {
      accessorKey: 'grossRevenue',
      header: t('common.amount'),
      cell: ({ row }) => formatCurrency(row.original.grossRevenue, 'USD'),
      footer: formatCurrency(financeSummary.value.grossRevenueSum, 'USD')
    },
    {
      id: 'finalPrice',
      header: t('pages.finance.columns.finalPrice'),
      accessorFn: (row: FinanceEntry) => Number(row.finalPrice),
      footer: formatCurrency(financeSummary.value.totalPriceSum, 'USD'),
      meta: {
        class: {
          th: '',
          td: ' font-medium'
        }
      }
    },
    {
      id: 'actions',
      header: '',
      meta: {
        class: {
          th: 'w-10',
          td: 'text-right'
        }
      }
    }
  ])

  return {
    data: effectiveRows,
    isLoading: resource.isLoading,
    sorting,
    searchQuery,
    columnFilters,
    pagination,
    totalRows: resource.totalRows,
    columns,
    groupingOptions,
    grouping,
    isSlideoverOpen,
    editingRow,
    editFields,
    openEdit,
    handleUpdate
  }
}



