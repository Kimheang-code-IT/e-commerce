import { computed, onMounted, ref } from 'vue'
import { useRoute } from '#imports'
import { usePosApi } from '~/utils/api'

export function usePosInvoicePreview() {
  const route = useRoute()
  const posApi = usePosApi()
  const selectedReportInvoices = ref<any[]>([])
  const selectedReportInvoice = ref<any | null>(null)
  const selectedReportInvoiceLines = ref<any[]>([])
  const isLoadingPreview = ref(false)
  const shouldAutoOpenPrintDialog = computed(() => String(route.query.autoPrint || '') === '1')

  async function loadPreviewFromRoute() {
    const previewKey = String(route.query.previewKey || '')
    const invoiceNo = String(route.query.invoiceNo || '')
    if (!previewKey && !invoiceNo) return
    isLoadingPreview.value = true
    try {
      if (previewKey) {
        const preview = await posApi.getPreviewSession(previewKey)
        const invoices = preview?.invoices || []
        selectedReportInvoices.value = invoices

        // If all items belong to the same invoice number, treat as single invoice
        const uniqueNos = new Set(invoices.map((inv: any) => inv.invoiceNo).filter(Boolean))
        if (uniqueNos.size === 1) {
          selectedReportInvoice.value = invoices[0]
          selectedReportInvoiceLines.value = invoices
        } else {
          selectedReportInvoice.value = invoices.length === 1 ? invoices[0] : null
          selectedReportInvoiceLines.value = []
        }
        return
      }

      if (invoiceNo) {
        const preview = await posApi.getInvoicePreviewByNo(invoiceNo)
        if (preview?.invoices) {
          const invoices = preview.invoices
          selectedReportInvoices.value = invoices

          const uniqueNos = new Set(invoices.map((inv: any) => inv.invoiceNo).filter(Boolean))
          if (uniqueNos.size === 1) {
            selectedReportInvoice.value = invoices[0]
            selectedReportInvoiceLines.value = invoices
          } else {
            selectedReportInvoice.value = null
            selectedReportInvoiceLines.value = []
          }
        } else {
          selectedReportInvoice.value = preview?.invoice || null
          selectedReportInvoiceLines.value = preview?.lines || []
          selectedReportInvoices.value = selectedReportInvoice.value ? [selectedReportInvoice.value] : []
        }
      }
    } finally {
      isLoadingPreview.value = false
    }
  }

  const hasReportPreviewInvoices = computed(
    () => selectedReportInvoices.value.length > 0 || Boolean(selectedReportInvoice.value)
  )

  onMounted(loadPreviewFromRoute)

  return {
    selectedReportInvoices,
    selectedReportInvoice,
    selectedReportInvoiceLines,
    hasReportPreviewInvoices,
    isLoadingPreview,
    shouldAutoOpenPrintDialog,
    loadPreviewFromRoute
  }
}
