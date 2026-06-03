import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from '#imports'
import type { TableColumn } from '@nuxt/ui'
import type { ReportRow, RefundRecord } from '~/types'
import { useRefundApi } from '~/utils/api'
import { formatCurrency } from '~/utils/format/currency'
import { useBaseTable } from '~/composables/table/useBaseTable'
import { useServerListTable } from '~/features/shared/useServerListTable'

export function useRefund() {
  const { t } = useI18n()
  const toast = useToast()
  const route = useRoute()
  const router = useRouter()
  const refundApi = useRefundApi()
  const { rowSelection, columnVisibility } = useBaseTable({})

  const refundRows = ref<RefundRecord[]>([])
  const selectedProducts = ref<string[]>([])
  const selectedSources = ref<string[]>([])
  const selectedAddresses = ref<string[]>([])

  const { sorting, columnFilters, pagination, searchQuery, resource } = useServerListTable<RefundRecord>({
    resourceKey: 'refunds-view',
    initialSorting: [{ id: 'refundedAt', desc: true }],
    localData: refundRows,
    listFn: (query, signal) => refundApi.list(query, signal),
  })

  const pendingInvoiceNo = ref('')
  const pendingRows = ref<ReportRow[]>([])
  const pendingItemId = ref<number | null>(null)
  const pendingLoading = ref(false)
  const refundReason = ref('')
  const submittingRefund = ref(false)
  const selectedPendingIds = ref<Set<number>>(new Set())

  const effectiveRows = computed(() => resource.rows.value)
  const hasPendingRefund = computed(() => Boolean(pendingInvoiceNo.value && pendingRows.value.length))

  const refundRecords = computed<RefundRecord[]>(() => {
    const products = selectedProducts.value
    const sources = selectedSources.value
    const addresses = selectedAddresses.value
    const hideInvoice = pendingInvoiceNo.value.trim()
    return effectiveRows.value.filter((row) => {
      if (hideInvoice && String(row.invoiceNo || '') === hideInvoice) return false
      const okProduct = !products.length || products.includes(String(row.product || ''))
      const okSource = !sources.length || sources.includes(String(row.source || ''))
      const okAddress = !addresses.length || addresses.includes(String(row.address || ''))
      return okProduct && okSource && okAddress
    })
  })

  const selectedPendingRows = computed(() =>
    pendingRows.value.filter((row) => row.id != null && selectedPendingIds.value.has(Number(row.id))),
  )

  const productItems = computed(() =>
    [...new Set(effectiveRows.value.map((row) => String(row.product || '').trim()).filter(Boolean))]
  )
  const sourceItems = computed(() =>
    [...new Set(effectiveRows.value.map((row) => String(row.source || '').trim()).filter(Boolean))]
  )
  const addressItems = computed(() =>
    [...new Set(effectiveRows.value.map((row) => String(row.address || '').trim()).filter(Boolean))]
  )

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

  const refundColumns = computed<TableColumn<RefundRecord>[]>(() => [
    { accessorKey: 'invoiceNo', header: t('pages.report.columns.invoiceNo'), footer: `Count: ${refundRecords.value.length}` },
    { accessorKey: 'customer', header: t('pages.report.columns.customer') },
    { accessorKey: 'product', header: t('pages.report.columns.product') },
    { accessorKey: 'seller', header: t('pages.report.columns.seller') },
    { accessorKey: 'source', header: t('pages.report.columns.source') },
    { accessorKey: 'address', header: t('pages.report.columns.address') },
    { accessorKey: 'amount', header: t('pages.report.columns.amount'), footer: formatCurrency(refundRecords.value.reduce((s, r) => s + Number(r.amount || 0), 0), 'USD') },
    { accessorKey: 'refundedAt', header: 'Refunded At' },
    { accessorKey: 'refundReason', header: 'Reason' },
  ])

  function clearPendingRefund() {
    pendingInvoiceNo.value = ''
    pendingRows.value = []
    pendingItemId.value = null
    selectedPendingIds.value = new Set()
    refundReason.value = ''
    const { invoiceNo: _i, itemId: _id, ...rest } = route.query
    void router.replace({ path: route.path, query: rest })
  }

  async function loadPendingFromRoute() {
    const invoiceNo = String(route.query.invoiceNo || '').trim()
    const itemIdRaw = String(route.query.itemId || '').trim()
    const itemId = itemIdRaw ? Number(itemIdRaw) : null

    if (!invoiceNo) {
      if (pendingInvoiceNo.value) clearPendingRefund()
      return
    }

    pendingLoading.value = true
    pendingInvoiceNo.value = invoiceNo
    pendingItemId.value = Number.isFinite(itemId) && itemId! > 0 ? itemId : null
    refundReason.value = ''
    try {
      const res = await refundApi.searchInvoices(invoiceNo, undefined, true)
      let rows = res.data || []
      if (pendingItemId.value) {
        rows = rows.filter((row) => Number(row.id) === pendingItemId.value)
      }
      pendingRows.value = rows
      selectedPendingIds.value = new Set(
        rows.map((row) => Number(row.id)).filter((id) => Number.isFinite(id) && id > 0),
      )
      if (!rows.length) {
        toast.add({
          title: t('common.error'),
          description: pendingItemId.value
            ? 'This line is already refunded or not found.'
            : 'No refundable items for this invoice.',
          color: 'warning',
        })
        clearPendingRefund()
      }
    } catch (err: unknown) {
      const message = (err as { response?: { _data?: { message?: string } } })?.response?._data?.message
      const code = (err as { response?: { _data?: { code?: string } } })?.response?._data?.code
      toast.add({
        title: t('common.error'),
        description: message || (code === 'ALL_REFUNDED' ? 'All items for this invoice are already refunded.' : 'Could not load invoice.'),
        color: 'error',
      })
      clearPendingRefund()
    } finally {
      pendingLoading.value = false
    }
  }

  function togglePendingRow(id: number, checked: boolean) {
    const next = new Set(selectedPendingIds.value)
    if (checked) next.add(id)
    else next.delete(id)
    selectedPendingIds.value = next
  }

  function openRefundFromReport(row: ReportRow) {
    void router.push({
      path: '/refund',
      query: {
        invoiceNo: row.invoiceNo,
        ...(row.id != null ? { itemId: String(row.id) } : {}),
      },
    })
  }

  function removeRefundRecord(id: number | string) {
    const numericId = Number(id)
    refundApi.remove(numericId).then(async () => {
      await loadRefunds()
    }).catch(() => {
      toast.add({ title: 'Delete failed', color: 'error' })
    })
  }

  async function confirmPendingRefund() {
    const rows = selectedPendingRows.value
    if (!rows.length || !refundReason.value.trim()) return
    submittingRefund.value = true
    try {
      const reason = refundReason.value.trim()
      const created = await refundApi.createMany(
        rows.map((row) => ({ ...row, refundReason: reason })),
      )
      const createdCount = created.data?.length || 0
      if (!createdCount) {
        toast.add({
          title: 'Refund not saved',
          description: 'Selected item(s) may already be refunded.',
          color: 'warning',
        })
        return
      }
      await loadRefunds()
      toast.add({
        title: t('pages.report.refundDialog.successTitle'),
        description: t('pages.report.refundDialog.successDescription'),
        color: 'primary',
      })
      clearPendingRefund()
    } catch (err: unknown) {
      const message = (err as { response?: { _data?: { message?: string } } })?.response?._data?.message
      toast.add({
        title: 'Refund failed',
        description: message || 'Could not save refund.',
        color: 'error',
      })
    } finally {
      submittingRefund.value = false
    }
  }

  watch(
    () => [route.query.invoiceNo, route.query.itemId],
    () => {
      void loadPendingFromRoute()
    },
  )

  onMounted(() => {
    void loadPendingFromRoute()
  })

  return {
    rowSelection,
    sorting,
    searchQuery,
    columnVisibility,
    columnFilters,
    pagination,
    totalRows: computed(() => refundRecords.value.length),
    isLoading: resource.isLoading,
    selectedProducts,
    selectedSources,
    selectedAddresses,
    productItems,
    sourceItems,
    addressItems,
    pendingInvoiceNo,
    pendingRows,
    pendingLoading,
    hasPendingRefund,
    selectedPendingIds,
    selectedPendingRows,
    refundReason,
    submittingRefund,
    openRefundFromReport,
    confirmPendingRefund,
    clearPendingRefund,
    togglePendingRow,
    refundRecords,
    refundColumns,
    removeRefundRecord,
  }
}
