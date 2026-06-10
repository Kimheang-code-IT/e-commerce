<script setup lang="ts">
import { useRefund } from '~/composables/table/useRefund'
import { formatCurrency } from '~/utils/format/currency'
import { formatDate } from '~/utils/format/date'
import type { RefundRecord } from '~/types'

const router = useRouter()
const { t } = useI18n()

function goToPreview(row: RefundRecord) {
  router.push({
    path: '/pos',
    query: { invoiceNo: row.invoiceNo },
  })
}

function goToReport(row: RefundRecord) {
  router.push({
    path: '/report',
    query: { search: row.invoiceNo },
  })
}

function goToSelectedInvoices() {
  if (!selectedRefundRows.value.length) return
  const invoiceNos = [...new Set(selectedRefundRows.value.map((r) => r.invoiceNo))]
  router.push({
    path: '/pos',
    query: { invoiceNo: invoiceNos.join(',') },
  })
}

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
  selectedAddresses,
  productItems,
  addressItems,
  filteredRefundRows,
  selectedRefundRows,
  allFilteredSelected,
  someFilteredSelected,
  toggleSelectAllFiltered,
  refundColumns,
  getDropdownActions,
  isConfirmOpen,
  confirmConfig,
  requestDeleteRefund,
  finalizeDeleteRefund,
  canView,
} = useRefund({ onPreview: goToPreview, onGoToReport: goToReport })

const { canView: canViewPos, canCheckout: canCheckoutPos } = useModulePermissions('pos')

const isExportOpen = ref(false)
</script>

<template>
  <LayoutAppHeader :title="$t('pages.refund.title')" show-datepicker>
    <template #right>
      <UButton v-if="canViewPos || canCheckoutPos" icon="i-lucide-receipt-text" color="primary" variant="solid"
        class="font-normal shadow-sm shrink-0" :disabled="selectedRefundRows.length === 0"
        @click="goToSelectedInvoices">
        <span class="hidden sm:inline">{{ $t('pages.refund.previewSelected') }}</span>
      </UButton>
      <UButton v-if="canView" icon="i-lucide-download" color="neutral" variant="subtle"
        class="font-normal shadow-sm shrink-0" @click="isExportOpen = true">
        <span class="hidden sm:inline">{{ $t('common.export') }}</span>
      </UButton>
    </template>

    <div class="flex-1 min-h-0 overflow-hidden flex flex-col">
      <div class="flex-1 min-h-0">
        <TableApptable :title="$t('pages.refund.recordsTitle')" v-model:row-selection="rowSelection"
          v-model:sorting="sorting" v-model:column-visibility="columnVisibility" v-model:pagination="pagination"
          v-model:column-filters="columnFilters" v-model:filter-value="selectedProducts"
          v-model:filter-value-secondary="selectedAddresses" v-model:global-filter="searchQuery"
          :filter-items="productItems" :filter-items-secondary="addressItems" :filter-placeholder="$t('product.name')"
          :filter-placeholder-secondary="$t('pages.report.filterProvince')" :data="filteredRefundRows"
          :columns="refundColumns" :loading="isLoading" :total-rows="totalRows" :selectable="true"
          :get-row-actions="getDropdownActions">
          <template #no-header>
            <div class="flex items-center gap-2">
              <UCheckbox :model-value="allFilteredSelected" :indeterminate="someFilteredSelected"
                @update:model-value="toggleSelectAllFiltered(!!$event)" />
              <UButton v-if="selectedRefundRows.length > 0 && (canViewPos || canCheckoutPos)"
                icon="i-lucide-receipt-text" color="primary" variant="ghost" size="xs" @click="goToSelectedInvoices" />
            </div>
          </template>
          <template #no-cell="{ row }">
            <div class="flex items-center gap-2">
              <UCheckbox :model-value="row.getIsSelected()" @update:model-value="row.toggleSelected(!!$event)" />
            </div>
          </template>

          <template #amount-cell="{ row }">
            <span class="font-medium text-primary">
              {{ formatCurrency(row.original.amount, 'USD') }}
            </span>
          </template>
          <template #seller-cell="{ row }">
            <UBadge color="primary" variant="soft" class="font-normal">
              {{ row.original.seller }}
            </UBadge>
          </template>
          <template #product-cell="{ row }">
            <UBadge color="neutral" variant="soft" class="font-normal">
              {{ row.original.product }}
            </UBadge>
          </template>
          <template #address-cell="{ row }">
            <UBadge color="primary" variant="soft" class="font-normal">
              {{ row.original.address }}
            </UBadge>
          </template>
          <template #invoiceNo-cell="{ row }">
            <span class="text-sm font-medium">{{ row.original.invoiceNo }}</span>
          </template>
          <template #refundedAt-cell="{ row }">
            {{ formatDate(row.original.refundedAt) }}
          </template>
          <template #refundReason-cell="{ row }">
            <span class="line-clamp-2">{{ row.original.refundReason || 'N/A' }}</span>
          </template>
        </TableApptable>
      </div>
    </div>

    <CommonAppModalCURD
      v-model:open="isConfirmOpen"
      v-bind="confirmConfig"
      @submit="finalizeDeleteRefund"
    />

    <CommonAppExport v-model:open="isExportOpen" :data="filteredRefundRows" filename="refunds"
      date-field="refundedAt" />
  </LayoutAppHeader>
</template>
