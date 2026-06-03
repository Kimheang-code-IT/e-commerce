<script setup lang="ts">
import { useRefund } from '~/composables/table/useRefund'
import { formatCurrency } from '~/utils/format/currency'
import { formatDate } from '~/utils/format/date'

const {
  rowSelection,
  sorting,
  searchQuery,
  columnVisibility,
  columnFilters,
  pagination,
  totalRows,
  isLoading,
  selectedProducts,
  selectedSources,
  selectedAddresses,
  productItems,
  sourceItems,
  addressItems,
  refundRecords,
  refundColumns,
  removeRefundRecord,
  canDelete,
  canView
} = useRefund()

const isExportOpen = ref(false)
</script>

<template>
  <div class="flex flex-col h-full bg-background overflow-hidden text-foreground tracking-tight">
    <LayoutAppHeader :title="$t('pages.refund.title')" show-datepicker>
      <template #right>
        <UButton
          v-if="canView"
          icon="i-lucide-download"
          color="neutral"
          variant="subtle"
          class="font-normal shadow-sm shrink-0"
          @click="isExportOpen = true"
        >
          <span class="hidden sm:inline">{{ $t('common.export') }}</span>
        </UButton>
      </template>
    </LayoutAppHeader>

    <div class="flex-1 p-2 overflow-hidden flex flex-col gap-2">
      <div class="flex-1 min-h-0">
        <TableApptable
          :title="$t('pages.refund.recordsTitle')"
          v-model:row-selection="rowSelection"
          v-model:sorting="sorting"
          v-model:column-visibility="columnVisibility"
          v-model:pagination="pagination"
          v-model:column-filters="columnFilters"
          v-model:filter-value="selectedProducts"
          v-model:filter-value-secondary="selectedSources"
          v-model:filter-value-third="selectedAddresses"
          v-model:global-filter="searchQuery"
          :filter-items="productItems"
          :filter-items-secondary="sourceItems"
          :filter-items-third="addressItems"
          filter-placeholder="Product"
          filter-placeholder-secondary="Source"
          filter-placeholder-third="Province"
          :data="refundRecords"
          :columns="refundColumns"
          :loading="isLoading"
          :total-rows="totalRows"
          :selectable="false"
        >
          <template #amount-cell="{ row }">
            <span class="font-medium text-primary">
              {{ formatCurrency(row.original.amount, 'USD') }}
            </span>
          </template>
          <template #refundedAt-cell="{ row }">
            {{ formatDate(row.original.refundedAt) }}
          </template>
          <template #refundReason-cell="{ row }">
            <span class="line-clamp-2">{{ row.original.refundReason || 'N/A' }}</span>
          </template>
          <template #action-cell="{ row }">
            <UButton
              v-if="canDelete"
              icon="i-lucide-trash"
              color="error"
              variant="ghost"
              size="xs"
              @click="removeRefundRecord(row.original.id)"
            />
          </template>
        </TableApptable>
      </div>
    </div>

    <CommonAppExport
      v-model:open="isExportOpen"
      :data="refundRecords"
      filename="refunds"
      date-field="refundedAt"
    />
  </div>
</template>
