import { computed, ref, watch } from 'vue'
import type { Product } from '~/types'
import { usePosApi } from '~/utils/api'
import {
  createCartLineId,
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
  const { t } = useI18n()
  const cart = ref<PosCartItem[]>([])
  const discountMode = ref<DiscountMode>('usd')
  const discountInput = ref(0)
  const totals = ref({ subtotal: 0, discountAmount: 0, total: 0 })
  const isCalculatingTotals = ref(false)
  const pendingRefresh = ref(false)
  const lastStockToastMessage = ref('')
  const lastStockToastAt = ref(0)
  const isSyncingFifo = ref(false)

  const localSubtotal = computed(() =>
    cart.value.reduce((sum, entry) => sum + getLineTotal(entry), 0),
  )

  const discountUsd = computed(() =>
    discountUsdFromInput(discountMode.value, discountInput.value, localSubtotal.value),
  )

  function linesForProduct(productId: number) {
    return cart.value.filter((entry) => entry.product.id === productId)
  }

  function totalQtyForProduct(productId: number) {
    return linesForProduct(productId).reduce((sum, entry) => sum + entry.qty, 0)
  }

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
      title: t('pages.pos.stock.notEnough'),
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

  async function syncFifoLinesForProduct(product: Product, targetQty: number) {
    const customLines = linesForProduct(product.id).filter((entry) => entry.manualPrice)
    const customQty = customLines.reduce((sum, entry) => sum + entry.qty, 0)
    const fifoQty = Math.max(0, targetQty - customQty)

    cart.value = cart.value.filter(
      (entry) => entry.product.id !== product.id || entry.manualPrice,
    )

    if (fifoQty <= 0) {
      await refreshTotals()
      return
    }

    isSyncingFifo.value = true
    try {
      const res = await posApi.expandFifoLines(product.id, fifoQty)
      const rows = Array.isArray(res?.data?.lines) ? res.data.lines : []
      const inStock = Number(res?.data?.inStock ?? product.inStock ?? 0)
      for (const row of rows) {
        const qty = Math.max(1, Number(row.qty || 0))
        const unitPrice = Number(row.unitPrice ?? 0)
        cart.value.push({
          lineId: createCartLineId(),
          product: { ...product, inStock },
          qty,
          unitPrice,
        })
      }
    } catch (error: any) {
      const message = String(error?.response?._data?.message || error?.data?.message || error?.message || '')
      notifyStockWarning(message || 'Could not load stock batches')
    } finally {
      isSyncingFifo.value = false
      await refreshTotals()
    }
  }

  async function addItem(product: Product) {
    const maxQty = Math.max(0, Number(product.inStock || 0))
    const current = totalQtyForProduct(product.id)
    if (current >= maxQty) {
      toast.add({
        title: t('pages.pos.stock.limitReached'),
        description: t('pages.pos.stock.limitReachedDesc', { name: product.name, qty: maxQty }),
        color: 'warning',
      })
      return
    }
    await syncFifoLinesForProduct(product, current + 1)
  }

  function setLineUnitPrice(lineId: string, price: number) {
    const item = cart.value.find((entry) => entry.lineId === lineId)
    if (!item) return
    item.unitPrice = Math.max(0, Number(price))
    item.manualPrice = true
    void refreshTotals()
  }

  async function resetLineUnitPrice(lineId: string) {
    const item = cart.value.find((entry) => entry.lineId === lineId)
    if (!item) return
    item.manualPrice = false
    const total = totalQtyForProduct(item.product.id)
    await syncFifoLinesForProduct(item.product, total)
  }

  function removeItem(lineId: string) {
    cart.value = cart.value.filter((entry) => entry.lineId !== lineId)
  }

  function updateQty(lineId: string, delta: number) {
    const item = cart.value.find((entry) => entry.lineId === lineId)
    if (!item) return
    if (delta > 0) {
      const maxQty = Math.max(0, Number(item.product.inStock || 0))
      const totalForProduct = totalQtyForProduct(item.product.id)
      if (totalForProduct >= maxQty) {
        toast.add({
          title: t('pages.pos.stock.limitReached'),
          description: t('pages.pos.stock.limitReachedDesc', { name: item.product.name, qty: maxQty }),
          color: 'warning',
        })
        return
      }
    }
    item.qty += delta
    if (item.qty <= 0) removeItem(lineId)
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
      const entry: PosCartItem = { lineId: createCartLineId(), product, qty }
      if (unitPrice != null) entry.unitPrice = unitPrice
      else entry.unitPrice = Number(line.price ?? getCatalogUnitPrice(product))
      cart.value.push(entry)
    })
    if (skipped > 0) {
      toast.add({
        title: t('pages.pos.stock.itemsSkipped'),
        description: t('pages.pos.stock.itemsSkippedDesc', { count: skipped }),
        color: 'warning',
      })
    }
    void refreshTotals()
  }

  const itemCount = computed(() => cart.value.reduce((sum, entry) => sum + entry.qty, 0))
  const cartProductIds = computed(() => new Set(cart.value.map((entry) => entry.product.id)))
  const isInCart = (productId: number) => cartProductIds.value.has(productId)
  const getCartQty = (productId: number) => totalQtyForProduct(productId)

  watch([cart, discountMode, discountInput], refreshTotals, { deep: true })

  return {
    cart,
    discountMode,
    discountInput,
    discountUsd,
    totals,
    isCalculatingTotals,
    isSyncingFifo,
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
