import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from '#imports'
import type { StepperItem } from '@nuxt/ui'
import { usePosProducts } from '~/composables/pos/usePosProducts'
import { usePosCart } from '~/composables/pos/usePosCart'
import { usePosCustomer } from '~/composables/pos/usePosCustomer'
import { usePosCheckout } from '~/composables/pos/usePosCheckout'
import { usePosInvoicePreview } from '~/composables/pos/usePosInvoicePreview'
import { usePosPrint } from '~/composables/pos/usePosPrint'
import { usePosReopen } from '~/composables/pos/usePosReopen'
import { usePosRewards } from '~/composables/pos/usePosRewards'

export function usePos() {
  const { t } = useI18n()
  const toast = useToast()
  const route = useRoute()
  const router = useRouter()
  const posPerms = useModulePermissions('pos')

  const products = usePosProducts()
  const rewards = usePosRewards()
  const cartState = usePosCart()
  const customer = usePosCustomer()
  const checkout = usePosCheckout()
  const preview = usePosInvoicePreview()
  const printing = usePosPrint()
  const reopen = usePosReopen()
  const reopenHandled = ref(false)

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
  const isInvoicePreviewMode = computed(
    () => hasReportPreviewInvoices.value && !reopenHandled.value,
  )
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
    if (isInvoicePreviewMode.value) return
    if (currentStep.value === 0) {
      if (cartState.cart.value.length === 0 && !hasReportPreviewInvoices.value) {
        toast.add({ title: t('common.error'), description: t('pages.pos.validation.cartEmpty'), color: 'error' })
        return
      }
      currentStep.value += 1
      return
    }

    if (currentStep.value === 1) {
      if (!posPerms.canCheckout.value) {
        toast.add({ title: t('common.error'), description: t('pages.pos.validation.noCheckoutPermission'), color: 'error' })
        return
      }
      // Validate customer form
      if (!customer.customerName.value) {
        toast.add({ title: t('common.error'), description: t('pages.pos.validation.customerNameRequired'), color: 'error' })
        return
      }
      if (!customer.customerPhone.value) {
        toast.add({ title: t('common.error'), description: t('pages.pos.validation.customerPhoneRequired'), color: 'error' })
        return
      }
      if (!customer.customerAddress.value) {
        toast.add({ title: t('common.error'), description: t('pages.pos.validation.customerAddressRequired'), color: 'error' })
        return
      }
      if (!customer.deliveryDate.value) {
        toast.add({ title: t('common.error'), description: t('pages.pos.validation.deliveryDateRequired'), color: 'error' })
        return
      }
      
      currentStep.value += 1
      return
    }

    if (cartState.cart.value.length === 0 && !hasReportPreviewInvoices.value) return
    if (!posPerms.canCheckout.value) {
      toast.add({ title: t('common.error'), description: t('pages.pos.validation.noCheckoutPermission'), color: 'error' })
      return
    }
    printing.openCheckoutConfirm()
  }

  const checkoutConfirmSummary = computed(() => ({
    customerName: customer.customerName.value,
    customerPhone: customer.customerPhone.value,
    customerAddress: customer.customerAddress.value,
    deliveryType: customer.deliveryType.value,
    deliveryPrice: Number(customer.deliveryPrice.value || 0),
    paymentMethod: customer.paymentMethod.value,
    itemCount: cartState.itemCount.value,
    subtotal: displaySubtotal.value,
    discount: displayDiscount.value,
    total: displayTotal.value
  }))

  function completeCheckoutUiReset() {
    cartState.clearCart()
    customer.reset()
    currentStep.value = 0
    printing.closePrintDialog()
    products.loadProducts()
    rewards.loadRewards()
  }

  async function finishWithoutPrint() {
    if (!posPerms.canCheckout.value) return
    try {
      if (cartState.cart.value.length > 0) {
        await checkout.checkout({
          cart: cartState.cart.value,
          discountAmount: cartState.discountUsd.value,
          customer: {
            customerName: customer.customerName.value,
            customerPhone: customer.customerPhone.value,
            customerAddress: customer.customerAddress.value,
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
      toast.add({ title: t('common.error'), description: String(error?.message || t('pages.pos.validation.checkoutFailed')), color: 'error' })
    }
  }

  async function finishWithPrint(onPrint: () => Promise<void> | void) {
    if (!posPerms.canCheckout.value) return
    try {
      if (cartState.cart.value.length > 0) {
        await checkout.checkout({
          cart: cartState.cart.value,
          discountAmount: cartState.discountUsd.value,
          customer: {
            customerName: customer.customerName.value,
            customerPhone: customer.customerPhone.value,
            customerAddress: customer.customerAddress.value,
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
      toast.add({ title: t('common.error'), description: String(error?.message || t('pages.pos.validation.checkoutFailed')), color: 'error' })
    }
  }

  onMounted(async () => {
    const isReopen = String(route.query.reopen || '') === '1'
    const invoiceNo = String(route.query.invoiceNo || '').trim()

    if (isReopen && invoiceNo) {
      preview.clearPreview()
      const ok = await reopen.loadInvoiceForReopen(invoiceNo, { cart: cartState, customer })
      if (ok) {
        reopenHandled.value = true
        currentStep.value = 0
        mobilePanel.value = 'right'
        await products.loadProducts()
        const { reopen: _reopen, ...rest } = route.query
        await router.replace({ path: route.path, query: rest })
      }
      return
    }

    await preview.loadPreviewFromRoute()

    if (reopenHandled.value) return
    if (hasReportPreviewInvoices.value) {
      currentStep.value = 2
    }
  })

  watch(
    () => preview.selectedReportInvoices.value,
    (invoices) => {
      if (reopenHandled.value) return
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
      if (reopenHandled.value) return
      if (invoice) {
        currentStep.value = 2
        customer.applyInvoiceHeader(invoice as Record<string, unknown>)
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
    addressNote: customer.addressNote,
    deliveryType: customer.deliveryType,
    deliveryPrice: customer.deliveryPrice,
    deliveryDate: customer.deliveryDate,
    paymentMethod: customer.paymentMethod,
    deliveryStatus: customer.deliveryStatus,
    sellerId: customer.sellerId,
    cart: cartState.cart,
    itemCount: cartState.itemCount,
    subtotal: computed(() => cartState.totals.value.subtotal),
    discountMode: cartState.discountMode,
    discountInput: cartState.discountInput,
    discountUsd: cartState.discountUsd,
    discountAmount: computed(() => cartState.totals.value.discountAmount),
    total: computed(() => cartState.totals.value.total),
    selectedReportInvoice: preview.selectedReportInvoice,
    selectedReportInvoiceLines: preview.selectedReportInvoiceLines,
    selectedReportInvoices: preview.selectedReportInvoices,
    hasReportPreviewInvoices,
    isInvoicePreviewMode,
    checkoutInvoiceNo: checkout.checkoutInvoiceNo,
    displaySubtotal,
    displayDiscount,
    displayTotal,
    isCheckoutConfirmOpen: printing.isCheckoutConfirmOpen,
    isFinishDialogOpen: printing.isFinishDialogOpen,
    checkoutConfirmSummary,
    confirmCheckoutAndContinue: printing.confirmCheckoutAndContinue,
    closeCheckoutConfirm: printing.closeCheckoutConfirm,
    isFinishing: checkout.isFinishing,
    addToCart: cartState.addItem,
    addRewardBundle: cartState.addRewardBundle,
    posRewards: rewards.rewards,
    isLoadingRewards: rewards.isLoadingRewards,
    updateQty: cartState.updateQty,
    removeFromCart: cartState.removeItem,
    clearCart: cartState.clearCart,
    requestFinish,
    finishWithoutPrint,
    finishWithPrint,
    canCheckout: posPerms.canCheckout,
    isInCart: cartState.isInCart,
    getCartQty: cartState.getCartQty,
    setLineUnitPrice: cartState.setLineUnitPrice,
    resetLineUnitPrice: cartState.resetLineUnitPrice,
    loadProducts: products.loadProducts,
  }
}
