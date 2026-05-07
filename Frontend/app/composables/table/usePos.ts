import { computed, onMounted, ref, watch } from 'vue'
import type { StepperItem } from '@nuxt/ui'
import { usePosProducts } from '~/composables/pos/usePosProducts'
import { usePosCart } from '~/composables/pos/usePosCart'
import { usePosCustomer } from '~/composables/pos/usePosCustomer'
import { usePosCheckout } from '~/composables/pos/usePosCheckout'
import { usePosInvoicePreview } from '~/composables/pos/usePosInvoicePreview'
import { usePosPrint } from '~/composables/pos/usePosPrint'

export function usePos() {
  const { t } = useI18n()
  const toast = useToast()

  const products = usePosProducts()
  const cartState = usePosCart()
  const customer = usePosCustomer()
  const checkout = usePosCheckout()
  const preview = usePosInvoicePreview()
  const printing = usePosPrint()

  const items = ref<StepperItem[]>([
    { title: t('pages.pos.steps.addToCart'), icon: 'i-lucide-house' },
    { title: t('pages.pos.steps.customerInfo'), icon: 'i-lucide-user' },
    { title: t('pages.pos.steps.checkout'), icon: 'i-lucide-check' }
  ])
  const mobileStepperItems = [{ icon: 'i-lucide-house' }, { icon: 'i-lucide-user' }, { icon: 'i-lucide-check' }]
  const currentStep = ref(0)
  const mobilePanel = ref<'left' | 'right'>('left')
  const viewMode = ref<'grid' | 'list'>('grid')

  const hasReportPreviewInvoices = preview.hasReportPreviewInvoices
  const displaySubtotal = computed(() => {
    if (preview.selectedReportInvoiceLines.value.length > 0) {
      return preview.selectedReportInvoiceLines.value.reduce((sum, line) => sum + Number(line.price || 0) * Number(line.qty || 1), 0)
    }
    if (preview.selectedReportInvoice.value) return Number(preview.selectedReportInvoice.value.subtotal || preview.selectedReportInvoice.value.amount || 0)
    return cartState.totals.value.subtotal
  })
  const displayDiscount = computed(() => {
    if (preview.selectedReportInvoice.value) return Number(preview.selectedReportInvoice.value.discount || 0)
    return cartState.totals.value.discountAmount
  })
  const displayTotal = computed(() => {
    if (preview.selectedReportInvoiceLines.value.length > 0) {
      const sub = preview.selectedReportInvoiceLines.value.reduce((sum, line) => sum + Number(line.price || 0) * Number(line.qty || 1), 0)
      const disc = Number(preview.selectedReportInvoice.value?.discount || 0)
      return sub - disc
    }
    if (preview.selectedReportInvoice.value) return Number(preview.selectedReportInvoice.value.amount || 0)
    return cartState.totals.value.total
  })

  function requestFinish() {
    if (currentStep.value === 0) {
      if (cartState.cart.value.length === 0 && !hasReportPreviewInvoices.value) {
        toast.add({ title: t('common.error'), description: 'Cart is empty', color: 'error' })
        return
      }
      currentStep.value += 1
      return
    }

    if (currentStep.value === 1) {
      // Validate customer form
      if (!customer.customerName.value) {
        toast.add({ title: t('common.error'), description: 'Customer name is required', color: 'error' })
        return
      }
      if (!customer.customerPhone.value) {
        toast.add({ title: t('common.error'), description: 'Customer phone is required', color: 'error' })
        return
      }
      if (!customer.customerAddress.value) {
        toast.add({ title: t('common.error'), description: 'Customer address is required', color: 'error' })
        return
      }
      if (!customer.deliveryDate.value) {
        toast.add({ title: t('common.error'), description: 'Delivery date is required', color: 'error' })
        return
      }
      
      currentStep.value += 1
      return
    }

    if (cartState.cart.value.length === 0 && !hasReportPreviewInvoices.value) return
    printing.openPrintDialog()
  }

  function completeCheckoutUiReset() {
    cartState.clearCart()
    customer.reset()
    currentStep.value = 0
    printing.closePrintDialog()
    products.loadProducts()
  }

  async function finishWithoutPrint() {
    try {
      if (cartState.cart.value.length > 0) {
        await checkout.checkout({
          cart: cartState.cart.value,
          discountPercent: cartState.discountPercent.value,
          customer: {
            customerName: customer.customerName.value,
            customerPhone: customer.customerPhone.value,
            customerAddress: customer.customerAddress.value,
            source: customer.source.value,
            deliveryType: customer.deliveryType.value,
            deliveryPrice: customer.deliveryPrice.value,
            deliveryDate: customer.deliveryDate.value,
            paymentMethod: customer.paymentMethod.value,
            deliveryStatus: customer.deliveryStatus.value,
            sellerId: customer.sellerId.value
          }
        })
      }
      completeCheckoutUiReset()
    } catch (error: any) {
      toast.add({ title: t('common.error') || 'Error', description: String(error?.message || 'Checkout failed'), color: 'error' })
    }
  }

  async function finishWithPrint(onPrint: () => Promise<void> | void) {
    try {
      if (cartState.cart.value.length > 0) {
        await checkout.checkout({
          cart: cartState.cart.value,
          discountPercent: cartState.discountPercent.value,
          customer: {
            customerName: customer.customerName.value,
            customerPhone: customer.customerPhone.value,
            customerAddress: customer.customerAddress.value,
            source: customer.source.value,
            deliveryType: customer.deliveryType.value,
            deliveryPrice: customer.deliveryPrice.value,
            deliveryDate: customer.deliveryDate.value,
            paymentMethod: customer.paymentMethod.value,
            deliveryStatus: customer.deliveryStatus.value,
            sellerId: customer.sellerId.value
          }
        })
      }
      await onPrint()
      completeCheckoutUiReset()
    } catch (error: any) {
      toast.add({ title: t('common.error') || 'Error', description: String(error?.message || 'Checkout failed'), color: 'error' })
    }
  }

  onMounted(() => {
    if (preview.shouldAutoOpenPrintDialog.value && hasReportPreviewInvoices.value) {
      printing.openPrintDialog()
      currentStep.value = 2
    } else if (hasReportPreviewInvoices.value) {
      currentStep.value = 2
    }
  })

  watch(
    () => preview.selectedReportInvoices.value,
    (invoices) => {
      if (invoices.length > 0) {
        currentStep.value = 2
        checkout.checkoutInvoiceNo.value = ''
        checkout.lastInvoiceData.value = null
      }
    },
    { immediate: true }
  )

  watch(
    () => preview.selectedReportInvoice.value,
    (invoice) => {
      if (invoice) {
        currentStep.value = 2
        customer.customerName.value = String(invoice.customer || '')
        customer.customerPhone.value = String(invoice.phoneCustomer || '')
        customer.customerAddress.value = String(invoice.address || '')
        customer.source.value = String(invoice.source || 'other')
        checkout.checkoutInvoiceNo.value = ''
        checkout.lastInvoiceData.value = null
      }
    },
    { immediate: true }
  )

  const mobilePanelItems = computed(() => [
    { label: items.value[currentStep.value]?.title || 'Panel', value: 'left' },
    { label: t('pages.pos.cart.title'), value: 'right' }
  ])

  return {
    ...products,
    viewMode,
    currentStep,
    mobilePanel,
    items,
    mobileStepperItems,
    mobilePanelItems,
    customerType: customer.customerType,
    customerName: customer.customerName,
    customerPhone: customer.customerPhone,
    customerAddress: customer.customerAddress,
    deliveryType: customer.deliveryType,
    deliveryPrice: customer.deliveryPrice,
    deliveryDate: customer.deliveryDate,
    paymentMethod: customer.paymentMethod,
    deliveryStatus: customer.deliveryStatus,
    source: customer.source,
    sellerId: customer.sellerId,
    cart: cartState.cart,
    itemCount: cartState.itemCount,
    subtotal: computed(() => cartState.totals.value.subtotal),
    discountPercent: cartState.discountPercent,
    discountAmount: computed(() => cartState.totals.value.discountAmount),
    total: computed(() => cartState.totals.value.total),
    selectedReportInvoice: preview.selectedReportInvoice,
    selectedReportInvoiceLines: preview.selectedReportInvoiceLines,
    selectedReportInvoices: preview.selectedReportInvoices,
    hasReportPreviewInvoices,
    checkoutInvoiceNo: checkout.checkoutInvoiceNo,
    displaySubtotal,
    displayDiscount,
    displayTotal,
    isFinishDialogOpen: printing.isFinishDialogOpen,
    isFinishing: checkout.isFinishing,
    addToCart: cartState.addItem,
    updateQty: cartState.updateQty,
    removeFromCart: cartState.removeItem,
    clearCart: cartState.clearCart,
    requestFinish,
    finishWithoutPrint,
    finishWithPrint,
    isInCart: cartState.isInCart,
    getCartQty: cartState.getCartQty,
    loadProducts: products.loadProducts
  }
}
