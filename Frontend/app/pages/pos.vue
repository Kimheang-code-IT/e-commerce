<script setup lang="ts">
import { usePos } from '~/composables/table/usePos'
import { useInvoicePrinter } from '~/composables/useInvoicePrinter'
import { formatDate } from '~/utils/format/date'

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
    isFinishDialogOpen,
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
    source,
    sellerId,
    cart,
    itemCount,
    subtotal,
    discountPercent,
    discountAmount,
    total,
    selectedReportInvoice,
    selectedReportInvoiceLines,
    checkoutInvoiceNo,
    selectedReportInvoices,
    hasReportPreviewInvoices,
    displaySubtotal,
    displayDiscount,
    displayTotal,
    addToCart,
    updateQty,
    removeFromCart,
    clearCart,
    requestFinish,
    finishWithoutPrint,
    finishWithPrint,
    isInCart,
    getCartQty
} = usePos()

const { invoicePrintRef, printInvoice } = useInvoicePrinter()

async function handleFinishWithPrint() {
    await finishWithPrint(printInvoice)
}


function buildCartFromLines(lines: any[]) {
    return lines.map((line: any, index: number) => ({
        product: {
            id: line.productId || -3000 - index,
            image: '',
            name: line.product,
            category: 'Report',
            categoryId: '',
            inPrice: 0,
            outPrice: Number(line.price || line.amount || 0),
            commission: 0,
            totalStock: 0,
            inStock: 0,
            sold: 0,
            added: 0,
            damaged: 0,
            status: 'active' as const,
            createdAt: line.date || new Date().toISOString()
        },
        qty: Number(line.qty || 1)
    }))
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

const previewCart = computed(() => {
    if (selectedReportInvoiceLines.value?.length > 0) {
        return selectedReportInvoiceLines.value.map((line: any, index: number) => ({
            product: {
                id: line.productId || -2000 - index,
                image: '',
                name: line.product,
                category: 'Report',
                categoryId: '',
                inPrice: 0,
                outPrice: Number(line.price || 0),
                commission: 0,
                totalStock: 0,
                inStock: 0,
                sold: 0,
                added: 0,
                damaged: 0,
                status: 'active' as const,
                createdAt: selectedReportInvoice.value?.date || new Date().toISOString()
            },
            qty: Number(line.qty || 0)
        }))
    }
    return cart.value
})
</script>

<template>
    <div class="flex flex-col h-full bg-background text-foreground overflow-hidden tracking-tight">

        <!-- ── Header ── -->
        <LayoutAppHeader :title="selectedReportInvoice?.invoiceNo ? `${t('pages.pos.invoice.fields.invoiceNo')}: ${selectedReportInvoice.invoiceNo}` : (groupedReportInvoices.length > 0 ? `${t('pages.pos.invoice.title')} (${groupedReportInvoices.length})` : (checkoutInvoiceNo ? `${t('pages.pos.invoice.fields.invoiceNo')}: ${checkoutInvoiceNo}` : 'Point of Sale'))">
            <template #right>
                <div class="flex items-center">
                    <UStepper v-model="currentStep" :items="mobileStepperItems" size="sm"
                        class="sm:hidden min-w-[140px]" />
                    <UStepper v-model="currentStep" :items="items" size="sm" class="hidden sm:flex min-w-[300px]" />
                </div>
            </template>
        </LayoutAppHeader>
        <div class="lg:hidden px-2 pt-2">
            <UTabs v-model="mobilePanel" :items="mobilePanelItems" :content="false" color="primary" class="w-full" />
        </div>

        <!-- ── Body: Split Layout ── -->
        <div class="flex flex-col lg:flex-row flex-1 overflow-hidden min-h-0">
            <div
                :class="[mobilePanel === 'left' ? 'flex' : 'hidden', 'lg:flex w-full lg:w-[65%] min-w-0 lg:border-r border-default overflow-hidden']">
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

                        <div class="flex items-center gap-2 ml-auto">
                            <!-- Search -->
                            <CommonAppSearch v-model="searchQuery" :placeholder="t('common.search')" class="w-52" />
                        </div>
                    </div>

                    <!-- Product Area — scrollable -->
                    <div class="flex-1 overflow-y-auto p-3 relative">

                        <!-- Empty State -->
                        <div v-if="!isLoadingProducts && filteredProducts.length === 0"
                            class="flex flex-col items-center justify-center h-[50vh] gap-3 text-muted-foreground">
                            <UIcon name="i-lucide-package-search" class="size-12 opacity-30" />
                            <p class="text-sm">No products found</p>
                        </div>

                        <!-- ── GRID View ── -->
                        <div v-else-if="viewMode === 'grid'" class="grid gap-3"
                            style="grid-template-columns: repeat(auto-fill, minmax(200px, 1fr))">

                            <CommonAppPosProductCard v-for="product in filteredProducts" :key="product.id"
                                :product="product" :in-cart="isInCart(product.id)" :cart-qty="getCartQty(product.id)"
                                @add="addToCart(product)" @filter-category="selectCategoryById" />
                        </div>
                        <div class="mt-3 flex justify-center">
                            <UButton v-if="currentStep === 0 && filteredProducts.length >= 60" color="neutral"
                                variant="soft" size="sm" :loading="isLoadingProducts" @click="loadMoreProducts">
                                Load more
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
                    v-model:source="source" v-model:seller-id="sellerId" />

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
                                    :delivery-type="group.header.source || deliveryType"
                                    :delivery-price="group.header.deliveryPrice || 0"
                                    :selected-report-invoice="group.header" :display-subtotal="group.subtotal"
                                    :display-discount="group.header.discount || 0"
                                    :display-total="group.subtotal - (group.header.discount || 0)" />
                            </div>
                        </template>
                        <CommonAppPosInvoicePreview v-else class="print-invoice-page" :cart="previewCart"
                            :customer-name="selectedReportInvoice?.customer || customerName"
                            :customer-phone="selectedReportInvoice?.phoneCustomer || customerPhone"
                            :delivery-type="selectedReportInvoice?.source || deliveryType"
                            :delivery-price="selectedReportInvoice?.deliveryPrice || deliveryPrice" :selected-report-invoice="selectedReportInvoice"
                            :checkout-invoice-no="checkoutInvoiceNo" :display-subtotal="displaySubtotal"
                            :display-discount="displayDiscount" :display-total="displayTotal" />
                    </div>
                </div>
            </div>

            <div :class="[mobilePanel === 'right' ? 'flex' : 'hidden', 'lg:flex w-full lg:w-[35%]']">
                <CommonAppPosCartPanel :cart="cart" :item-count="itemCount" :subtotal="subtotal"
                    v-model:discount-percent="discountPercent" :discount-amount="discountAmount" :total="total"
                    :current-step="currentStep" :total-steps="items.length"
                    :allow-finish-without-cart="hasReportPreviewInvoices" @clear-cart="clearCart"
                    @update-qty="updateQty" @remove-item="removeFromCart" @next="requestFinish" />
            </div>
        </div>

        <CommonAppModalCURD v-model:open="isFinishDialogOpen" title="Finish Checkout"
            description="Do you want to print the invoice now?" submit-label="Print Invoice" cancel-label="No"
            type="primary" :loading="isFinishing" @submit="handleFinishWithPrint" @cancel="finishWithoutPrint" />
    </div>
</template>