<script setup lang="ts">
import { useProduct } from '~/composables/table/useProduct'
import { formatCurrency } from '~/utils/format/currency'
import { formatDate } from '~/utils/format/date'
import type { Product } from '~/types'

const { t } = useI18n()

const {
    rowSelection, sorting, searchQuery, columnVisibility, columnFilters,
    pagination, isFormOpen, isConfirmOpen, isStockAdjustOpen,
    totalRows,
    selectedEntry,
    categoryItems, selectedCategories,
    filteredEntries, confirmConfig,
    columns, entryFormFields,
    getDropdownActions, handleSaveRequest, finalizeAction, handleAddNew,
    canCreate, canExport, canAdjustStock, canViewAdjustStock, canAddDamage, canViewAddDamage,
    stockAdjustMode, stockAdjustQty, stockAdjustInPrice, stockAdjustOutPrice,
    stockAdjustNote, stockAdjustTarget, stockAdjustLotId, stockLotOptions, isStockLotsLoading,
    openStockAdjustDialog, applyStockAdjust,
    // History
    isHistoryOpen, historyType, historyEntries, isHistoryLoading, historyTotalRows,
    historyPagination, historyDateRange, openHistory, loadHistory, onHistorySaved,
} = useProduct()

const isExportOpen = ref(false)

function stockStatusLabel(tier: Product['stockStatus']) {
    const keyMap = {
        aLot: 'product.stockStatus.aLot',
        lower: 'product.stockStatus.lower',
        out: 'product.stockStatus.out',
    } as const
    return t(keyMap[tier ?? 'out'])
}

function stockStatusColor(tier: Product['stockStatus']) {
    if (tier === 'aLot') return 'success'
    if (tier === 'lower') return 'warning'
    return 'error'
}

function onSubmitProduct(data: Record<string, any>) {
    handleSaveRequest(data as any)
}

function onProductImageError(event: Event) {
    const img = event.target as HTMLImageElement | null
    if (!img) return
    img.src = '/logo.png'
}
</script>

<template>
    <div class="flex flex-col h-full bg-background overflow-hidden text-foreground tracking-tight">
        <LayoutAppHeader :title="$t('pages.product.title')" show-datepicker>
            <template #right>
                <UButton v-if="canExport" icon="i-lucide-download" color="neutral" variant="subtle"
                    class="font-normal shadow-sm shrink-0" @click="isExportOpen = true">
                    <span class="hidden sm:inline">{{ $t('common.export') }}</span>
                </UButton>
                <UButton v-if="canCreate" icon="i-lucide-circle-plus" color="primary" variant="solid"
                    class="font-normal shadow-sm shrink-0" @click="handleAddNew">
                    <span class="hidden sm:inline">{{ $t('pages.product.addBtn') }}</span>
                </UButton>
            </template>
        </LayoutAppHeader>

        <div class="flex-1 p-2 overflow-hidden">
            <TableApptable :title="$t('pages.product.tableTitle')" v-model:row-selection="rowSelection"
                v-model:sorting="sorting"
                v-model:column-visibility="columnVisibility" v-model:pagination="pagination"
                v-model:column-filters="columnFilters" v-model:filter-value="selectedCategories"
                v-model:global-filter="searchQuery"
                :filter-items="categoryItems" :filter-placeholder="$t('product.category')"
                :data="filteredEntries" :columns="columns" :selectable="true"
                :total-rows="totalRows"
                :get-row-actions="getDropdownActions">
                <!-- Image -->
                <template #image-cell="{ row }">
                    <img
                        :src="row.original.image"
                        :alt="row.original.name"
                        loading="lazy"
                        decoding="async"
                        @error="onProductImageError"
                        class="w-9 h-9 rounded-md object-cover border border-muted" />
                </template>

                <!-- Name -->
                <template #name-cell="{ row }">
                    <span class="font-medium text-foreground">{{ row.original.name }}</span>
                </template>

                <!-- Category -->
                <template #category-cell="{ row }">
                    <UBadge color="primary" variant="soft" class="font-normal">
                        {{ row.original.category }}
                    </UBadge>
                </template>

                <!-- Out Price -->
                <template #outPrice-cell="{ row }">
                    <span class="text-sm text-primary font-medium">
                        {{ formatCurrency(row.original.outPrice, 'USD') }}
                    </span>
                </template>

                <!-- Commission -->
                <template #commission-cell="{ row }">
                    <span class="text-sm text-primary font-medium">
                        {{ formatCurrency(row.original.commission, 'USD') }}
                    </span>
                </template>

                <!-- In Stock -->
                <template #inStock-cell="{ row }">
                    <span :class="[
                        'text-sm font-medium',
                        row.original.inStock === 0 ? 'text-red-500' :
                        row.original.inStock < 10 ? 'text-amber-500' : 'text-primary'
                    ]">
                        {{ row.original.inStock }}
                    </span>
                </template>

                <!-- Sold -->
                <template #sold-cell="{ row }">
                    <span class="text-sm text-foreground">{{ row.original.sold }}</span>
                </template>

                <!-- Added -->
                <template #added-cell="{ row }">
                    <UButton
                        v-if="canAdjustStock || canViewAdjustStock"
                        variant="ghost"
                        color="primary"
                        size="sm"
                        class="px-2 underline"
                        @click="canAdjustStock ? openStockAdjustDialog(row.original, 'added') : openHistory(row.original, 'added')"
                    >
                        {{ row.original.added }}
                    </UButton>
                </template>

                <!-- Damaged -->
                <template #damaged-cell="{ row }">
                    <UButton
                        v-if="canAddDamage || canViewAddDamage"
                        variant="ghost"
                        :color="row.original.damaged > 0 ? 'error' : 'neutral'"
                        size="sm"
                        class="px-2 underline"
                        @click="canAddDamage ? openStockAdjustDialog(row.original, 'damaged') : openHistory(row.original, 'damaged')"
                    >
                        {{ row.original.damaged }}
                    </UButton>
                </template>

                <!-- Status -->
                <template #status-cell="{ row }">
                    <UBadge variant="soft" :color="stockStatusColor(row.original.stockStatus)" size="md">
                        {{ stockStatusLabel(row.original.stockStatus) }}
                    </UBadge>
                </template>

                <!-- Created At -->
                <template #createdAt-cell="{ row }">
                    <span class="text-sm text-muted-foreground">
                        {{ formatDate(row.original.createdAt) }}
                    </span>
                </template>

            </TableApptable>
        </div>

        <CommonAppSlideoverForm
            v-model:open="isFormOpen"
            :data="selectedEntry || undefined"
            :fields="entryFormFields"
            :title-key="selectedEntry ? 'pages.product.formTitleEdit' : 'pages.product.formTitleNew'"
            :submit-label-key="selectedEntry ? 'actions.save' : 'actions.add'"
            @submit="onSubmitProduct"
        />
        <CommonAppModalCURD v-model:open="isConfirmOpen" v-bind="confirmConfig" @submit="finalizeAction" />
        <CommonAppStockAdjustModal
            v-model:open="isStockAdjustOpen"
            v-model:qty="stockAdjustQty"
            v-model:in-price="stockAdjustInPrice"
            v-model:out-price="stockAdjustOutPrice"
            v-model:note="stockAdjustNote"
            v-model:stock-lot-id="stockAdjustLotId"
            :mode="stockAdjustMode"
            :product-name="stockAdjustTarget?.name || ''"
            :default-in-price="stockAdjustTarget?.inPrice"
            :default-out-price="stockAdjustTarget?.salePrice ?? stockAdjustTarget?.outPrice"
            :stock-lot-options="stockLotOptions"
            :stock-lots-loading="isStockLotsLoading"
            @apply="applyStockAdjust"
        />
        
        <CommonAppStockHistoryModal
            v-model:open="isHistoryOpen"
            v-model:range="historyDateRange"
            v-model:pagination="historyPagination"
            :type="historyType"
            :product-id="selectedEntry?.id"
            :product-name="selectedEntry?.name"
            :data="historyEntries"
            :loading="isHistoryLoading"
            :total="historyTotalRows"
            :can-edit="canAdjustStock"
            @saved="onHistorySaved"
        />

        <CommonAppExport v-model:open="isExportOpen" :data="filteredEntries" filename="products" date-field="createdAt" />
    </div>
</template>
