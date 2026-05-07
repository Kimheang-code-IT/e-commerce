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
    stockAdjustMode, stockAdjustQty, stockAdjustNote, stockAdjustTarget,
    openStockAdjustDialog, applyStockAdjust,
    // History
    isHistoryOpen, historyType, historyEntries, isHistoryLoading, historyTotalRows,
    historyPagination, historyDateRange, openHistory, loadHistory,
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
        <LayoutAppHeader :title="$t('pages.dataEntry.title')" show-datepicker>
            <template #right>
                <UButton icon="i-lucide-download" color="neutral" variant="subtle"
                    class="font-normal shadow-sm shrink-0" @click="isExportOpen = true">
                    <span class="hidden sm:inline">{{ $t('common.export') }}</span>
                </UButton>
                <UButton icon="i-lucide-circle-plus" color="primary" variant="solid"
                    class="font-normal shadow-sm shrink-0" @click="handleAddNew">
                    <span class="hidden sm:inline">{{ $t('pages.dataEntry.addBtn') }}</span>
                </UButton>
            </template>
        </LayoutAppHeader>

        <div class="flex-1 p-2 overflow-hidden">
            <TableApptable :title="$t('pages.dataEntry.tableTitle')" v-model:row-selection="rowSelection"
                v-model:sorting="sorting"
                v-model:column-visibility="columnVisibility" v-model:pagination="pagination"
                v-model:column-filters="columnFilters" v-model:filter-value="selectedCategories"
                :filter-items="categoryItems" :filter-placeholder="$t('product.category')"
                :data="filteredEntries" :columns="columns" :selectable="true"
                :total-rows="totalRows"
                :get-row-actions="getDropdownActions">
                <template #header>
                    <div class="w-full max-w-[280px]">
                        <CommonAppSearch v-model="searchQuery" />
                    </div>
                </template>

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
                        variant="ghost"
                        color="primary"
                        size="sm"
                        class="px-2 underline"
                        @click="openStockAdjustDialog(row.original, 'added')"
                    >
                        {{ row.original.added }}
                    </UButton>
                </template>

                <!-- Damaged -->
                <template #damaged-cell="{ row }">
                    <UButton
                        variant="ghost"
                        :color="row.original.damaged > 0 ? 'error' : 'neutral'"
                        size="sm"
                        class="px-2 underline"
                        @click="openStockAdjustDialog(row.original, 'damaged')"
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

        <CommonAppSlideoverForm v-model:open="isFormOpen" :data="selectedEntry || undefined" :fields="entryFormFields"
            :title="selectedEntry ? $t('pages.dataEntry.formTitleEdit') : $t('pages.dataEntry.formTitleNew')"
            :submit-label="selectedEntry ? $t('actions.save') : $t('actions.add')" @submit="onSubmitProduct" />
        <CommonAppModalCURD v-model:open="isConfirmOpen" v-bind="confirmConfig" @submit="finalizeAction" />
        <CommonAppStockAdjustModal
            v-model:open="isStockAdjustOpen"
            v-model:qty="stockAdjustQty"
            v-model:note="stockAdjustNote"
            :mode="stockAdjustMode"
            :product-name="stockAdjustTarget?.name || ''"
            @apply="applyStockAdjust"
        />
        
        <CommonAppStockHistoryModal
            v-model:open="isHistoryOpen"
            v-model:range="historyDateRange"
            v-model:pagination="historyPagination"
            :type="historyType"
            :product-name="selectedEntry?.name"
            :data="historyEntries"
            :loading="isHistoryLoading"
            :total="historyTotalRows"
        />

        <CommonAppExport v-model:open="isExportOpen" :data="filteredEntries" filename="products" date-field="createdAt" />
    </div>
</template>
