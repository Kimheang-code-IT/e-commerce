<script setup lang="ts">
import { usePos } from '~/composables/table/usePos'
import { useInvoicePrinter } from '~/composables/useInvoicePrinter'
import { formatCurrency } from '~/utils/format/currency'

const { t } = useI18n()
const {
    isLoadingProducts,
    filteredProducts,
    loadMoreProducts,
    selectedCategoryId,
    selectCategoryById,
    categoryTabs,
    searchQuery,
    viewMode,
    currentStep,
    isCheckoutConfirmOpen,
    isFinishDialogOpen,
    checkoutConfirmSummary,
    confirmCheckoutAndContinue,
    closeCheckoutConfirm,
    isFinishing,
    mobileStepperItems,
    items,
    mobilePanel,
    mobilePanelItems,
    customerType,
    customerName,
    customerPhone,
    customerAddress,
    deliveryType,
    deliveryPrice,
    deliveryDate,
    paymentMethod,
    deliveryStatus,
    sellerId,
    cart,
    itemCount,
    subtotal,
    discountMode,
    discountInput,
    discountUsd,
    discountAmount,
    total,
    selectedReportInvoice,
    selectedReportInvoiceLines,
    checkoutInvoiceNo,
    selectedReportInvoices,
    hasReportPreviewInvoices,
    isInvoicePreviewMode,
    displaySubtotal,
    displayDiscount,
    displayTotal,
    addToCart,
    updateQty,
    removeFromCart,
    setLineUnitPrice,
    resetLineUnitPrice,
    clearCart,
    requestFinish,
    finishWithoutPrint,
    finishWithPrint,
    isInCart,
    getCartQty,
    canCheckout
} = usePos()

const { invoicePrintRef, printInvoice } = useInvoicePrinter()

async function handleFinishWithPrint() {
    await finishWithPrint(printInvoice)
}


function buildCartFromLines(lines: any[]) {
    return lines.map((line: any, index: number) => {
        const unitPrice = Number(line.price || line.amount || 0)
        return {
            lineId: `preview-${index}-${line.productId || 0}-${unitPrice}`,
            product: {
                id: line.productId || -3000 - index,
                image: '',
                name: line.product,
                category: 'Report',
                categoryId: '',
                inPrice: 0,
                outPrice: unitPrice,
                salePrice: unitPrice,
                commission: 0,
                totalStock: 0,
                inStock: 0,
                sold: 0,
                added: 0,
                damaged: 0,
                status: 'active' as const,
                createdAt: line.date || new Date().toISOString()
            },
            qty: Number(line.qty || 1),
            unitPrice,
        }
    })
}

const groupedReportInvoices = computed(() => {
    const groups = new Map<string, any[]>()
    selectedReportInvoices.value.forEach(inv => {
        const key = String(inv?.invoiceNo || 'unknown')
        if (!groups.has(key)) {
            groups.set(key, [])
        }
        groups.get(key)!.push(inv)
    })
    return [...groups.entries()].map(([invoiceNo, lines]) => {
        const subtotal = lines.reduce((sum: number, l: any) => sum + Number((l.price || l.amount || 0) * (l.qty || 1)), 0)
        return {
            invoiceNo,
            lines,
            header: lines[0],
            subtotal
        }
    })
})

const posSearchExpanded = ref(false)

watch(currentStep, (step) => {
    if (step !== 0) posSearchExpanded.value = false
})

const previewCart = computed(() => {
    if (selectedReportInvoiceLines.value?.length > 0) {
        return selectedReportInvoiceLines.value.map((line: any, index: number) => ({
            lineId: `report-${index}-${line.productId || 0}-${line.price || 0}`,
            product: {
                id: line.productId || -2000 - index,
                image: '',
                name: line.product,
                category: 'Report',
                categoryId: '',
                inPrice: 0,
                outPrice: Number(line.price || 0),
                salePrice: Number(line.price || 0),
                commission: 0,
                totalStock: 0,
                inStock: 0,
                sold: 0,
                added: 0,
                damaged: 0,
                status: 'active' as const,
                createdAt: selectedReportInvoice.value?.date || new Date().toISOString()
            },
            qty: Number(line.qty || 0),
            unitPrice: Number(line.price || 0),
        }))
    }
    return cart.value
})
</script>

<template>
    <LayoutAppHeader hide-sidebar-toggle flush :title="t('pages.pos.title')">
        <template #leading>
            <UButton to="/" color="primary" variant="solid" size="sm" icon="i-lucide-layout-dashboard"
                :aria-label="t('navigation.dashboard')" class="shrink-0">
                {{ t('navigation.dashboard') }}
            </UButton>
        </template>
        <template #right>
            <div class="flex items-center gap-2">
                <template v-if="isInvoicePreviewMode">
                    <UButton icon="i-lucide-printer" color="primary" variant="solid" size="sm" class="shrink-0"
                        @click="printInvoice">
                        <span class="hidden sm:inline">{{ t('pages.pos.preview.print') }}</span>
                    </UButton>
                </template>
                <template v-else>
                    <UStepper v-model="currentStep" :items="mobileStepperItems" size="sm"
                        class="sm:hidden min-w-[140px]" />
                    <UStepper v-model="currentStep" :items="items" size="sm" class="hidden sm:flex min-w-[300px]" />
                </template>
            </div>
        </template>
        <div v-if="!isInvoicePreviewMode" class="lg:hidden shrink-0 border-b border-default">
            <UTabs v-model="mobilePanel" :items="mobilePanelItems" :content="false" color="primary" class="w-full" />
        </div>

        <!-- ── Body: Split Layout ── -->
        <div class="flex flex-col lg:flex-row flex-1 min-h-0 overflow-hidden">
            <div :class="[
                isInvoicePreviewMode ? 'flex' : (mobilePanel === 'left' ? 'flex' : 'hidden'),
                isInvoicePreviewMode ? 'lg:flex w-full' : 'lg:flex w-full lg:w-[65%]',
                'min-w-0 overflow-hidden',
                !isInvoicePreviewMode ? 'lg:border-r border-default' : '',
            ]">
                <!-- ══ LEFT: Content Panel ══ -->
                <div v-if="currentStep === 0" class="w-full flex flex-col min-w-0 overflow-hidden">

                    <!-- Toolbar -->
                    <div
                        class="flex flex-wrap items-center gap-2 px-3 py-3 border-b border-default shrink-0 bg-background/80 backdrop-blur-sm">
                        <!-- Category Pills -->
                        <div class="min-w-0 flex-1 overflow-x-auto">
                            <UTabs v-model="selectedCategoryId" :items="categoryTabs" size="xs" color="primary"
                                :content="false" class="w-max min-w-full" />
                        </div>

                        <div class="flex items-center gap-2 ml-auto shrink-0">
                            <UButton
                                v-if="!posSearchExpanded"
                                color="neutral"
                                variant="soft"
                                size="md"
                                icon="i-lucide-search"
                                :aria-label="t('common.search')"
                                @click="posSearchExpanded = true"
                            />
                            <div v-else class="flex items-center gap-1.5 min-w-0">
                                <CommonAppSearch
                                    v-model="searchQuery"
                                    :placeholder="t('common.search')"
                                    class="w-40 sm:w-52 min-w-0"
                                    autofocus
                                />
                                <UButton
                                    color="neutral"
                                    variant="ghost"
                                    size="sm"
                                    icon="i-lucide-search"
                                    :aria-label="t('common.search')"
                                    class="shrink-0"
                                    @click="posSearchExpanded = false"
                                />
                            </div>
                        </div>
                    </div>

                    <!-- Product Area — scrollable -->
                    <div class="flex-1 overflow-y-auto px-3 pt-2 pb-20 lg:p-3 relative">

                        <!-- Empty State -->
                        <div v-if="!isLoadingProducts && filteredProducts.length === 0"
                            class="flex flex-col items-center justify-center h-[50vh] gap-3 text-muted-foreground">
                            <UIcon name="i-lucide-package-search" class="size-12 opacity-30" />
                            <p class="text-sm">{{ t('pages.pos.noProducts') }}</p>
                        </div>

                        <!-- ── GRID View ── -->
                        <div
                            v-else-if="viewMode === 'grid'"
                            class="grid grid-cols-2 gap-3 sm:grid-cols-[repeat(auto-fill,minmax(200px,1fr))]"
                        >

                            <CommonAppPosProductCard v-for="product in filteredProducts" :key="product.id"
                                :product="product" :in-cart="isInCart(product.id)" :cart-qty="getCartQty(product.id)"
                                @add="addToCart(product)" @filter-category="selectCategoryById" />
                        </div>
                        <div class="mt-3 flex justify-center">
                            <UButton v-if="currentStep === 0 && filteredProducts.length >= 60" color="neutral"
                                variant="soft" size="sm" :loading="isLoadingProducts" @click="loadMoreProducts">
                                {{ t('pages.pos.loadMore') }}
                            </UButton>
                        </div>
                    </div>
                </div>

                <!-- ══ LEFT: Customer Info Panel ══ -->
                <CommonAppPosCustomerForm v-else-if="currentStep === 1" v-model:customer-type="customerType"
                    v-model:customer-name="customerName" v-model:customer-phone="customerPhone"
                    v-model:customer-address="customerAddress" v-model:delivery-type="deliveryType"
                    v-model:delivery-price="deliveryPrice" v-model:delivery-date="deliveryDate"
                    v-model:payment-method="paymentMethod" v-model:delivery-status="deliveryStatus"
                    v-model:seller-id="sellerId" />

                <!-- ══ LEFT: Invoice/Checkout Panel ══ -->
                <div v-else class="w-full min-h-0 flex flex-col bg-muted/30 px-6 py-1 overflow-y-auto">
                    <div ref="invoicePrintRef" class="invoice-print-target">
                        <!-- Bulk Preview (Multiple separate invoices) -->
                        <template v-if="groupedReportInvoices.length > 0 && selectedReportInvoiceLines.length === 0">
                            <div class="space-y-3">
                                <CommonAppPosInvoicePreview v-for="group in groupedReportInvoices"
                                    :key="group.invoiceNo" class="print-invoice-page"
                                    :cart="buildCartFromLines(group.lines)"
                                    :customer-name="group.header.customer || customerName"
                                    :customer-phone="group.header.phoneCustomer || customerPhone"
                                    :delivery-type="group.header.deliveryType || deliveryType"
                                    :delivery-price="group.header.deliveryPrice || 0"
                                    :selected-report-invoice="group.header" :display-subtotal="group.subtotal"
                                    :display-discount="group.header.discount || 0"
                                    :display-total="group.subtotal - (group.header.discount || 0)" />
                            </div>
                        </template>
                        <CommonAppPosInvoicePreview v-else class="print-invoice-page" :cart="previewCart"
                            :customer-name="selectedReportInvoice?.customer || customerName"
                            :customer-phone="selectedReportInvoice?.phoneCustomer || customerPhone"
                            :delivery-type="selectedReportInvoice?.deliveryType || deliveryType"
                            :delivery-price="selectedReportInvoice?.deliveryPrice || deliveryPrice"
                            :selected-report-invoice="selectedReportInvoice" :checkout-invoice-no="checkoutInvoiceNo"
                            :display-subtotal="displaySubtotal" :display-discount="displayDiscount"
                            :display-total="displayTotal" />
                    </div>
                </div>
            </div>

            <div v-if="!isInvoicePreviewMode"
                :class="[mobilePanel === 'right' ? 'flex' : 'hidden', 'lg:flex w-full lg:w-[35%] min-h-0 h-full flex-col']">
                <CommonAppPosCartPanel :cart="cart" :item-count="itemCount" :subtotal="subtotal"
                    v-model:discount-mode="discountMode" v-model:discount-input="discountInput"
                    :discount-amount="discountAmount" :total="total" :current-step="currentStep"
                    :total-steps="items.length" :allow-finish-without-cart="hasReportPreviewInvoices"
                    :can-checkout="canCheckout" @clear-cart="clearCart" @update-qty="updateQty"
                    @remove-item="removeFromCart" @set-line-price="setLineUnitPrice"
                    @reset-line-price="resetLineUnitPrice" @next="requestFinish" />
            </div>
        </div>

        <CommonAppModalCURD v-if="!isInvoicePreviewMode" v-model:open="isCheckoutConfirmOpen"
            :title="t('pages.pos.checkoutConfirm.title')" :description="t('pages.pos.checkoutConfirm.description')"
            :submit-label="t('pages.pos.checkoutConfirm.submit')" :cancel-label="t('components.cancel')" type="warning"
            @submit="confirmCheckoutAndContinue" @cancel="closeCheckoutConfirm">
            <div class="rounded-lg border border-default bg-muted/30 p-3 text-sm space-y-2">
                <div class="flex justify-between gap-2">
                    <span class="text-muted-foreground">{{ t('pages.pos.checkoutConfirm.customer') }}</span>
                    <span class="font-medium text-foreground text-right">{{ checkoutConfirmSummary.customerName
                        }}</span>
                </div>
                <div class="flex justify-between gap-2">
                    <span class="text-muted-foreground">{{ t('pages.pos.checkoutConfirm.phone') }}</span>
                    <span class="font-medium text-foreground">{{ checkoutConfirmSummary.customerPhone }}</span>
                </div>
                <div class="flex justify-between gap-2">
                    <span class="text-muted-foreground">{{ t('pages.pos.checkoutConfirm.address') }}</span>
                    <span class="font-medium text-foreground text-right">{{ checkoutConfirmSummary.customerAddress
                        }}</span>
                </div>
                <div class="flex justify-between gap-2">
                    <span class="text-muted-foreground">{{ t('pages.pos.checkoutConfirm.delivery') }}</span>
                    <span class="font-medium text-foreground">
                        {{ checkoutConfirmSummary.deliveryType }}
                        ({{ formatCurrency(checkoutConfirmSummary.deliveryPrice, 'USD') }})
                    </span>
                </div>
                <div class="flex justify-between gap-2">
                    <span class="text-muted-foreground">{{ t('pages.pos.checkoutConfirm.payment') }}</span>
                    <span class="font-medium text-foreground">{{ checkoutConfirmSummary.paymentMethod }}</span>
                </div>
                <div class="flex justify-between gap-2">
                    <span class="text-muted-foreground">{{ t('pages.pos.checkoutConfirm.items') }}</span>
                    <span class="font-medium text-foreground">{{ checkoutConfirmSummary.itemCount }}</span>
                </div>
                <USeparator />
                <div class="flex justify-between gap-2">
                    <span class="text-muted-foreground">{{ t('pages.pos.cart.subtotal') }}</span>
                    <span>{{ formatCurrency(checkoutConfirmSummary.subtotal, 'USD') }}</span>
                </div>
                <div class="flex justify-between gap-2">
                    <span class="text-muted-foreground">{{ t('pages.pos.cart.discount') }}</span>
                    <span>{{ formatCurrency(checkoutConfirmSummary.discount, 'USD') }}</span>
                </div>
                <div class="flex justify-between gap-2 text-base">
                    <span class="font-semibold text-foreground">{{ t('pages.pos.checkoutConfirm.total') }}</span>
                    <span class="font-bold text-primary">{{ formatCurrency(checkoutConfirmSummary.total, 'USD')
                        }}</span>
                </div>
            </div>
        </CommonAppModalCURD>

        <CommonAppModalCURD v-if="!isInvoicePreviewMode" v-model:open="isFinishDialogOpen"
            :title="t('pages.pos.printConfirm.title')" :description="t('pages.pos.printConfirm.description')"
            :submit-label="t('pages.pos.printConfirm.print')" :cancel-label="t('pages.pos.printConfirm.skip')"
            type="primary"             :loading="isFinishing" @submit="handleFinishWithPrint" @cancel="finishWithoutPrint" />
    </LayoutAppHeader>
</template>