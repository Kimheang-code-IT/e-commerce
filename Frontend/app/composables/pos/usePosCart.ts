import { computed, ref, watch } from 'vue'
import type { Product } from '~/types'
import { usePosApi } from '~/utils/api'
import { mapCartToApiLines, type PosCartItem } from '~/composables/pos/helpers'
import {
  discountUsdFromInput,
  type DiscountMode
} from '~/composables/pos/discountHelpers'

export function usePosCart() {
  const posApi = usePosApi()
  const cart = ref<PosCartItem[]>([])
  const discountMode = ref<DiscountMode>('usd')
  const discountInput = ref(0)
  const totals = ref({ subtotal: 0, discountAmount: 0, total: 0 })
  const isCalculatingTotals = ref(false)

  const localSubtotal = computed(() =>
    cart.value.reduce(
      (sum, entry) => sum + Number(entry.product.outPrice || 0) * Number(entry.qty || 0),
      0
    )
  )

  const discountUsd = computed(() =>
    discountUsdFromInput(discountMode.value, discountInput.value, localSubtotal.value)
  )

  async function refreshTotals() {
    if (!cart.value.length) {
      totals.value = { subtotal: 0, discountAmount: 0, total: 0 }
      return
    }
    isCalculatingTotals.value = true
    try {
      const result = await posApi.calculateTotals({
        discountAmount: discountUsd.value,
        lines: mapCartToApiLines(cart.value)
      })
      totals.value = result
    } finally {
      isCalculatingTotals.value = false
    }
  }

  function addItem(product: Product) {
    const existing = cart.value.find((entry) => entry.product.id === product.id)
    if (existing) existing.qty += 1
    else cart.value.push({ product, qty: 1 })
  }

  function removeItem(productId: number) {
    cart.value = cart.value.filter((entry) => entry.product.id !== productId)
  }

  function updateQty(productId: number, delta: number) {
    const item = cart.value.find((entry) => entry.product.id === productId)
    if (!item) return
    item.qty += delta
    if (item.qty <= 0) removeItem(productId)
  }

  function clearCart() {
    cart.value = []
    discountInput.value = 0
    discountMode.value = 'usd'
    totals.value = { subtotal: 0, discountAmount: 0, total: 0 }
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
    isInCart,
    getCartQty,
    refreshTotals
  }
}
