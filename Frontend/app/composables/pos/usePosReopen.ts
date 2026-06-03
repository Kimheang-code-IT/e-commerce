import { usePosApi } from '~/utils/api'
import { handleApiError } from '~/composables/pos/helpers'
import type { usePosCart } from '~/composables/pos/usePosCart'
import type { usePosCustomer } from '~/composables/pos/usePosCustomer'

type CartState = ReturnType<typeof usePosCart>
type CustomerState = ReturnType<typeof usePosCustomer>

function normalizePreview(payload: {
  invoice?: Record<string, unknown>
  lines?: unknown[]
  invoices?: unknown[]
}) {
  if (payload.invoice && Array.isArray(payload.lines)) {
    return { invoice: payload.invoice, lines: payload.lines }
  }
  const invoices = Array.isArray(payload.invoices) ? payload.invoices : []
  if (!invoices.length) return null
  const first = invoices[0] as Record<string, unknown>
  const invoiceNo = String(first.invoiceNo || '')
  const lines = invoices.filter(
    (row: unknown) => String((row as Record<string, unknown>).invoiceNo || '') === invoiceNo || !invoiceNo,
  )
  const header = { ...first }
  return { invoice: header, lines }
}

export function usePosReopen() {
  const posApi = usePosApi()
  const toast = useToast()
  const { t } = useI18n()

  async function loadInvoiceForReopen(
    invoiceNo: string,
    deps: { cart: CartState; customer: CustomerState },
  ): Promise<boolean> {
    const trimmed = String(invoiceNo || '').trim()
    if (!trimmed) return false
    try {
      const preview = await posApi.getInvoicePreviewByNo(trimmed)
      const normalized = normalizePreview(preview || {})
      if (!normalized?.invoice || !Array.isArray(normalized.lines) || normalized.lines.length === 0) {
        toast.add({
          title: t('common.error'),
          description: 'Invoice not found or has no lines.',
          color: 'error',
        })
        return false
      }
      deps.cart.loadFromLines(normalized.lines as Parameters<CartState['loadFromLines']>[0])
      if (deps.cart.cart.value.length === 0) {
        toast.add({
          title: t('common.error'),
          description: 'No cart items could be loaded from this invoice.',
          color: 'error',
        })
        return false
      }
      deps.customer.applyInvoiceHeader(normalized.invoice)
      deps.cart.discountMode.value = 'usd'
      deps.cart.discountInput.value = Number(normalized.invoice.discount || 0)
      toast.add({
        title: 'Invoice loaded',
        description: `${trimmed} — edit cart and continue checkout.`,
        color: 'success',
      })
      return true
    } catch (error: unknown) {
      toast.add({
        title: t('common.error'),
        description: handleApiError(error, 'Failed to load invoice'),
        color: 'error',
      })
      return false
    }
  }

  return { loadInvoiceForReopen }
}
