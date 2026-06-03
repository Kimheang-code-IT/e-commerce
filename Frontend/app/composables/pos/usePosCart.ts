import { computed, ref, watch } from 'vue'
import type { Product } from '~/types'
import { usePosApi } from '~/utils/api'
import {
  getCatalogUnitPrice,
  getLineTotal,
  getLineUnitPrice,
  mapCartToApiLines,
  productFromInvoiceLine,
  unitPriceFromLine,
  type InvoiceReopenLine,
  type PosCartItem,
} from '~/composables/pos/helpers'
import {
  discountUsdFromInput,
  type DiscountMode
} from '~/composables/pos/discountHelpers'

export function usePosCart() {
  const posApi = usePosApi()
  const toast = useToast()
  const cart = ref<PosCartItem[]>([])
  const discountMode = ref<DiscountMode>('usd')
  const discountInput = ref(0)
  const totals = ref({ subtotal: 0, discountAmount: 0, total: 0 })
  const isCalculatingTotals = ref(false)
  const pendingRefresh = ref(false)
  const lastStockToastMessage = ref('')
  const lastStockToastAt = ref(0)

  const localSubtotal = computed(() =>
    cart.value.reduce((sum, entry) => sum + getLineTotal(entry), 0),
  )

  const discountUsd = computed(() =>
    discountUsdFromInput(discountMode.value, discountInput.value, localSubtotal.value)
  )

  function resolveStockErrorItemName(message: string): string {
    const fifoMatch = message.match(/Not enough FIFO stock for (.+)$/i)
    if (fifoMatch?.[1]) return fifoMatch[1].trim()
    const stockMatch = message.match(/Not enough stock for (.+?) \(Available:/i)
    if (stockMatch?.[1]) return stockMatch[1].trim()
    return ''
  }

  function applyStockFallback(message: string) {
    const name = resolveStockErrorItemName(message)
    if (!name) return
    const idx = cart.value.findIndex((entry) => entry.product.name === name)
    if (idx < 0) return
    const entry = cart.value[idx]
    if (!entry) return
    if (entry.qty > 1) entry.qty -= 1
    else cart.value.splice(idx, 1)
  }

  function notifyStockWarning(message: string) {
    const text = message || 'One or more items exceed available FIFO stock.'
    const now = Date.now()
    if (lastStockToastMessage.value === text && now - lastStockToastAt.value < 1500) return
    lastStockToastMessage.value = text
    lastStockToastAt.value = now
    toast.add({
      title: 'Stock not enough',
      description: text,
      color: 'warning',
    })
  }

  async function refreshTotals() {
    if (isCalculatingTotals.value) {
      pendingRefresh.value = true
      return
    }
    if (!cart.value.length) {
      totals.value = { subtotal: 0, discountAmount: 0, total: 0 }
      return
    }
    do {
      pendingRefresh.value = false
      isCalculatingTotals.value = true
      try {
        const result = await posApi.calculateTotals({
          discountAmount: discountUsd.value,
          lines: mapCartToApiLines(cart.value)
        })
        totals.value = result
      } catch (error: any) {
        const message = String(error?.response?._data?.message || error?.data?.message || error?.message || '')
        const code = String(error?.response?._data?.code || error?.data?.code || '')
        if (code === 'NOT_ENOUGH_STOCK' || /Not enough (FIFO )?stock/i.test(message)) {
          applyStockFallback(message)
          notifyStockWarning(message)
        }
        totals.value = {
          subtotal: localSubtotal.value,
          discountAmount: discountUsd.value,
          total: Math.max(0, localSubtotal.value - discountUsd.value),
        }
      } finally {
        isCalculatingTotals.value = false
      }
    } while (pendingRefresh.value && cart.value.length)
  }

  function addItem(product: Product) {
    const existing = cart.value.find((entry) => entry.product.id === product.id)
    if (existing) {
      const maxQty = Math.max(0, Number(existing.product.inStock || 0))
      if (existing.qty >= maxQty) {
        toast.add({
          title: 'Stock limit reached',
          description: `${existing.product.name} has only ${maxQty} in stock.`,
          color: 'warning',
        })
        return
      }
      existing.qty += 1
    }
    else cart.value.push({ product, qty: 1 })
  }

  function setLineUnitPrice(productId: number, price: number) {
    const item = cart.value.find((entry) => entry.product.id === productId)
    if (!item) return
    item.unitPrice = Math.max(0, Number(price))
    void refreshTotals()
  }

  function resetLineUnitPrice(productId: number) {
    const item = cart.value.find((entry) => entry.product.id === productId)
    if (!item) return
    item.unitPrice = undefined
    void refreshTotals()
  }

  function removeItem(productId: number) {
    cart.value = cart.value.filter((entry) => entry.product.id !== productId)
  }

  function updateQty(productId: number, delta: number) {
    const item = cart.value.find((entry) => entry.product.id === productId)
    if (!item) return
    if (delta > 0) {
      const maxQty = Math.max(0, Number(item.product.inStock || 0))
      if (item.qty >= maxQty) {
        toast.add({
          title: 'Stock limit reached',
          description: `${item.product.name} has only ${maxQty} in stock.`,
          color: 'warning',
        })
        return
      }
    }
    item.qty += delta
    if (item.qty <= 0) removeItem(productId)
  }

  function clearCart() {
    cart.value = []
    discountInput.value = 0
    discountMode.value = 'usd'
    totals.value = { subtotal: 0, discountAmount: 0, total: 0 }
  }

  function loadFromLines(lines: InvoiceReopenLine[]) {
    cart.value = []
    let skipped = 0
    lines.forEach((line, index) => {
      const product = productFromInvoiceLine(line, index)
      if (!product) {
        skipped += 1
        return
      }
      const qty = Math.max(1, Number(line.qty || 1))
      const unitPrice = unitPriceFromLine(line, product)
      const entry: PosCartItem = { product, qty }
      if (unitPrice != null) entry.unitPrice = unitPrice
      cart.value.push(entry)
    })
    if (skipped > 0) {
      toast.add({
        title: 'Some items skipped',
        description: `${skipped} line(s) could not be loaded (missing product).`,
        color: 'warning',
      })
    }
    void refreshTotals()
  }

  const itemCount = computed(() => cart.value.reduce((sum, entry) => sum + entry.qty, 0))
  const cartProductIds = computed(() => new Set(cart.value.map((entry) => entry.product.id)))
  const isInCart = (productId: number) => cartProductIds.value.has(productId)
  const getCartQty = (productId: number) =>
    cart.value.find((entry) => entry.product.id === productId)?.qty || 0

  watch([cart, discountMode, discountInput], refreshTotals, { deep: true })

  return {
    cart,
    discountMode,
    discountInput,
    discountUsd,
    totals,
    isCalculatingTotals,
    itemCount,
    localSubtotal,
    addItem,
    removeItem,
    updateQty,
    clearCart,
    loadFromLines,
    isInCart,
    getCartQty,
    getLineUnitPrice,
    getCatalogUnitPrice,
    setLineUnitPrice,
    resetLineUnitPrice,
    refreshTotals,
  }
}
