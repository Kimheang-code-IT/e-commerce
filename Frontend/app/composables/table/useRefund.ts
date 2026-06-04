import { computed, ref, watch } from 'vue'
import type { DropdownMenuItem, TableColumn } from '@nuxt/ui'
import type { ReportRow, RefundRecord } from '~/types'
import { useRefundApi } from '~/utils/api'
import { formatCurrency } from '~/utils/format/currency'
import { useBaseTable } from '~/composables/table/useBaseTable'
import { useServerListTable } from '~/features/shared/useServerListTable'
import { useAuthStore } from '~/stores/auth'

export type RefundRowActionHandlers = {
  onPreview?: (row: RefundRecord) => void
}

export function useRefund(handlers?: RefundRowActionHandlers) {
  const { t } = useI18n()
  const toast = useToast()
  const auth = useAuthStore()
  const perms = useModulePermissions('refund')
  const refundApi = useRefundApi()
  const { rowSelection, columnVisibility } = useBaseTable({})

  const refundRows = ref<RefundRecord[]>([])
  const selectedProducts = ref<string[]>([])
  const selectedSources = ref<string[]>([])
  const selectedAddresses = ref<string[]>([])

  const filterExtraQuery = computed(() => ({
    product: selectedProducts.value.join(',') || undefined,
    source: selectedSources.value.join(',') || undefined,
    province: selectedAddresses.value.join(',') || undefined,
  }))

  const { sorting, columnFilters, pagination, searchQuery, resource } = useServerListTable<RefundRecord>({
    resourceKey: 'refunds-view',
    initialSorting: [{ id: 'refundedAt', desc: true }],
    localData: refundRows,
    extraQuery: filterExtraQuery,
    listFn: (query, signal) => refundApi.list(query, signal),
  })

  const isRefundDialogOpen = ref(false)
  const refundTargetRow = ref<ReportRow | null>(null)
  const refundReason = ref('')
  const submittingRefund = ref(false)

  const filteredRefundRows = computed<RefundRecord[]>(() => resource.rows.value)

  const productItems = computed(() =>
    [...new Set(filteredRefundRows.value.map((row) => String(row.product || '').trim()).filter(Boolean))]
  )
  const sourceItems = computed(() =>
    [...new Set(filteredRefundRows.value.map((row) => String(row.source || '').trim()).filter(Boolean))]
  )
  const addressItems = computed(() =>
    [...new Set(filteredRefundRows.value.map((row) => String(row.address || '').trim()).filter(Boolean))]
  )

  const selectedRefundRows = computed<RefundRecord[]>(() => {
    const selectedIndexes = Object.keys(rowSelection.value || {})
      .filter((key) => (rowSelection.value as Record<string, boolean>)[key])
      .map((key) => Number(key))
      .filter((value) => Number.isInteger(value) && value >= 0)

    return selectedIndexes
      .map((index) => filteredRefundRows.value[index])
      .filter((row): row is RefundRecord => Boolean(row))
  })

  const allFilteredSelected = computed(() => {
    const rows = filteredRefundRows.value
    if (!rows.length) return false
    const selected = rowSelection.value as Record<string, boolean>
    return rows.every((_, index) => Boolean(selected[String(index)]))
  })

  const someFilteredSelected = computed(() => {
    const rows = filteredRefundRows.value
    if (!rows.length) return false
    const selected = rowSelection.value as Record<string, boolean>
    const selectedCount = rows.reduce(
      (count, _row, index) => (selected[String(index)] ? count + 1 : count),
      0
    )
    return selectedCount > 0 && selectedCount < rows.length
  })

  const refundSummary = computed(() => {
    const rows = filteredRefundRows.value
    return {
      invoiceCount: rows.length,
      amountSum: rows.reduce((sum, row) => sum + Number(row.amount || 0), 0),
    }
  })

  async function loadRefunds() {
    try {
      await resource.refresh()
    } catch {
      refundRows.value = []
      toast.add({ title: 'Load failed', description: 'Could not load refund records.', color: 'error' })
    }
  }

  watch([selectedProducts, selectedSources, selectedAddresses], () => {
    pagination.value.pageIndex = 0
  })

  watch(filteredRefundRows, (rows) => {
    const current = rowSelection.value as Record<string, boolean>
    const next: Record<string, boolean> = {}
    rows.forEach((_row, index) => {
      const key = String(index)
      if (current[key]) next[key] = true
    })
    rowSelection.value = next
  })

  function toggleSelectAllFiltered(checked: boolean) {
    const rows = filteredRefundRows.value
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

  const refundColumns = computed<TableColumn<RefundRecord>[]>(() => [
    { accessorKey: 'no', header: t('pages.report.columns.no') },
    {
      accessorKey: 'invoiceNo',
      header: t('pages.report.columns.invoiceNo'),
      footer: `Count: ${refundSummary.value.invoiceCount}`,
    },
    { accessorKey: 'customer', header: t('pages.report.columns.customer') },
    { accessorKey: 'product', header: t('pages.report.columns.product') },
    { accessorKey: 'seller', header: t('pages.report.columns.seller') },
    { accessorKey: 'source', header: t('pages.report.columns.source') },
    { accessorKey: 'address', header: t('pages.report.columns.address') },
    {
      accessorKey: 'amount',
      header: t('pages.report.columns.amount'),
      footer: formatCurrency(refundSummary.value.amountSum, 'USD'),
    },
    { accessorKey: 'refundedAt', header: t('pages.refund.columns.refundedAt') },
    { accessorKey: 'refundReason', header: t('pages.refund.columns.reason') },
    { id: 'action', header: t('common.actions') },
  ])

  function getDropdownActions(row: RefundRecord): DropdownMenuItem[][] {
    if (!handlers?.onPreview) return []
    if (!auth.hasPermission('pos:view') && !auth.hasPermission('pos:checkout')) return []
    return [
      [
        {
          label: t('pages.report.actions.preview'),
          icon: 'i-lucide-eye',
          onSelect: () => handlers.onPreview!(row),
        },
      ],
    ]
  }

  function openRefundDialog(row: ReportRow) {
    refundTargetRow.value = row
    refundReason.value = ''
    isRefundDialogOpen.value = true
  }

  async function removeRefundInvoice(row: RefundRecord) {
    if (!row.invoiceNo) return
    try {
      await refundApi.removeByInvoice(row.invoiceNo)
      await loadRefunds()
      toast.add({ title: t('common.success'), description: t('pages.refund.deleteSuccess'), color: 'primary' })
    } catch {
      toast.add({ title: 'Delete failed', color: 'error' })
    }
  }

  function buildRefundPayload(row: ReportRow, reason: string) {
    const invoiceKey = Number(row.invoiceId ?? row.id ?? 0)
    const payload: ReportRow & { refundReason: string; invoiceId?: number; id?: number } = {
      invoiceNo: row.invoiceNo,
      date: row.date || '',
      product: row.product || '',
      productId: Number(row.productId ?? 0) || 0,
      qty: Number(row.qty ?? 0) || 0,
      price: Number(row.price ?? 0) || 0,
      customer: row.customer || '',
      phoneCustomer: row.phoneCustomer || '',
      phoneSaler: row.phoneSaler || '',
      seller: row.seller || '',
      source: row.source || '',
      address: row.address || '',
      deliveryPrice: Number(row.deliveryPrice ?? 0) || 0,
      discount: Number(row.discount ?? 0) || 0,
      amount: Number(row.amount ?? 0) || 0,
      refundReason: reason,
    }
    if (invoiceKey >= 1) {
      payload.id = invoiceKey
      payload.invoiceId = invoiceKey
    }
    return payload
  }

  function formatRefundError(err: unknown): string {
    const data = (err as { response?: { _data?: { message?: string; errors?: Record<string, string[]> } } })
      ?.response?._data
    if (data?.errors) {
      const parts = Object.entries(data.errors).flatMap(([field, msgs]) =>
        (msgs || []).map((m) => `${field}: ${m}`)
      )
      if (parts.length) return parts.join('; ')
    }
    return data?.message || 'Could not save refund.'
  }

  async function confirmRefund(onSuccess?: () => void | Promise<void>) {
    const row = refundTargetRow.value
    const reason = refundReason.value.trim()

    if (!row) {
      toast.add({ title: t('common.error'), description: 'No invoice line selected.', color: 'error' })
      return
    }
    if (!reason) {
      toast.add({
        title: t('common.error'),
        description: t('pages.report.refundDialog.reasonRequired'),
        color: 'error',
      })
      return
    }

    submittingRefund.value = true

    try {
      const created = await refundApi.createMany([buildRefundPayload(row, reason)])
      const createdCount = Array.isArray(created?.data) ? created.data.length : 0

      if (!createdCount) {
        toast.add({
          title: 'Refund not saved',
          description: 'This item may already be refunded.',
          color: 'warning',
        })
        return
      }

      await loadRefunds()
      await onSuccess?.()

      toast.add({
        title: t('pages.report.refundDialog.successTitle'),
        description: t('pages.report.refundDialog.successDescription'),
        color: 'primary',
      })

      isRefundDialogOpen.value = false
      refundTargetRow.value = null
      refundReason.value = ''
    } catch (err: unknown) {
      toast.add({
        title: 'Refund failed',
        description: formatRefundError(err),
        color: 'error',
      })
    } finally {
      submittingRefund.value = false
    }
  }

  return {
    rowSelection,
    sorting,
    searchQuery,
    columnVisibility,
    columnFilters,
    pagination,
    totalRows: resource.totalRows,
    isLoading: resource.isLoading,
    selectedProducts,
    selectedSources,
    selectedAddresses,
    productItems,
    sourceItems,
    addressItems,
    selectedRefundRows,
    allFilteredSelected,
    someFilteredSelected,
    toggleSelectAllFiltered,
    filteredRefundRows,
    isRefundDialogOpen,
    refundTargetRow,
    refundReason,
    submittingRefund,
    openRefundDialog,
    confirmRefund,
    refundColumns,
    getDropdownActions,
    removeRefundInvoice,
    loadRefunds,
    canDelete: perms.canDelete,
    canView: perms.canView,
  }
}
