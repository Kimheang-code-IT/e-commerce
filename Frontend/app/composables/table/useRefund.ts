import { computed, ref, watch } from 'vue'

import type { TableColumn } from '@nuxt/ui'

import type { ReportRow, RefundRecord } from '~/types'

import { useRefundApi } from '~/utils/api'

import { formatCurrency } from '~/utils/format/currency'

import { useBaseTable } from '~/composables/table/useBaseTable'

import { useServerListTable } from '~/features/shared/useServerListTable'



export function useRefund() {

  const { t } = useI18n()

  const toast = useToast()

  const perms = useModulePermissions('refund')

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



  const isRefundDialogOpen = ref(false)

  const refundTargetRow = ref<ReportRow | null>(null)

  const refundReason = ref('')

  const submittingRefund = ref(false)



  const effectiveRows = computed(() => resource.rows.value)

  const refundRecords = computed<RefundRecord[]>(() => {

    const products = selectedProducts.value

    const sources = selectedSources.value

    const addresses = selectedAddresses.value

    return effectiveRows.value.filter((row) => {

      const okProduct = !products.length || products.includes(String(row.product || ''))

      const okSource = !sources.length || sources.includes(String(row.source || ''))

      const okAddress = !addresses.length || addresses.includes(String(row.address || ''))

      return okProduct && okSource && okAddress

    })

  })



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



  function openRefundDialog(row: ReportRow) {

    refundTargetRow.value = row

    refundReason.value = ''

    isRefundDialogOpen.value = true

  }



  function removeRefundRecord(id: number | string) {

    const numericId = Number(id)

    refundApi.remove(numericId).then(async () => {

      await loadRefunds()

    }).catch(() => {

      toast.add({ title: 'Delete failed', color: 'error' })

    })

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

          color: 'warning'

        })

        return

      }

      await loadRefunds()

      await onSuccess?.()



      toast.add({

        title: t('pages.report.refundDialog.successTitle'),

        description: t('pages.report.refundDialog.successDescription'),

        color: 'primary'

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

    totalRows: computed(() => refundRecords.value.length),

    isLoading: resource.isLoading,

    selectedProducts,

    selectedSources,

    selectedAddresses,

    productItems,

    sourceItems,

    addressItems,

    isRefundDialogOpen,

    refundTargetRow,

    refundReason,

    submittingRefund,

    openRefundDialog,

    confirmRefund,

    refundRecords,

    refundColumns,

    removeRefundRecord,
    canDelete: perms.canDelete,
    canView: perms.canView,

  }

}


