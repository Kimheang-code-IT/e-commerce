<script setup lang="ts">
import { useDelivery } from '~/composables/table/useDelivery'
import { formatCurrency } from '~/utils/format/currency'
import { formatDate } from '~/utils/format/date'
const { t } = useI18n()
const router = useRouter()

const {
  rowSelection,
  sorting,
  searchQuery,
  columnVisibility,
  columnFilters,
  pagination,
  isLoading,
  totalRows,
  addressItems,
  deliveryTypeItems,
  selectedAddresses,
  selectedDeliveryTypes,
  filteredDeliveryRows,
  columns
} = useDelivery()

function goToInvoice(row: any) {
  router.push({
    path: '/pos',
    query: {
      invoiceNo: row.invoiceId
    }
  })
}
</script>

<template>
  <div class="flex flex-col h-full bg-background overflow-hidden text-foreground tracking-tight">
    <LayoutAppHeader :title="t('pages.delivery.title')" show-datepicker />

    <div class="flex-1 p-2 overflow-hidden">
      <TableApptable
        :title="t('pages.delivery.tableTitle')"
        v-model:row-selection="rowSelection"
        v-model:sorting="sorting"
        v-model:column-visibility="columnVisibility"
        v-model:pagination="pagination"
        v-model:column-filters="columnFilters"
        v-model:filter-value="selectedAddresses"
        v-model:filter-value-secondary="selectedDeliveryTypes"
        :filter-items="addressItems"
        :filter-items-secondary="deliveryTypeItems"
        :filter-placeholder="t('pages.delivery.columns.address')"
        :filter-placeholder-secondary="t('pages.delivery.columns.deliveryType')"
        :data="filteredDeliveryRows"
        :loading="isLoading"
        :total-rows="totalRows"
        :columns="columns"
        :selectable="false"
      >
        <template #header>
          <div class="w-full max-w-[280px]">
            <CommonAppSearch v-model="searchQuery" />
          </div>
        </template>
        <template #no-cell="{ row }">
          <span class="text-sm text-muted-foreground">{{ row.index + 1 }}</span>
        </template>

        <template #invoiceId-cell="{ row }">
          <div class="flex items-center gap-2">
            <span class="font-medium text-foreground">{{ row.original.invoiceId }}</span>
            <UButton
              icon="i-lucide-receipt-text"
              color="primary"
              variant="ghost"
              size="xs"
              @click="goToInvoice(row.original)"
            />
          </div>
        </template>

        <template #address-cell="{ row }">
          <span class="text-sm text-foreground">{{ row.original.address }}</span>
        </template>

        <template #deliveryType-cell="{ row }">
          <UBadge variant="soft" color="primary" class="font-normal">
            {{ row.original.deliveryType }}
          </UBadge>
        </template>

        <template #deliveryPrice-cell="{ row }">
          <span class="text-sm font-medium text-primary">
            {{ formatCurrency(row.original.deliveryPrice, 'USD') }}
          </span>
        </template>

        <template #date-cell="{ row }">
          <span class="text-sm text-muted-foreground">{{ formatDate(row.original.date) }}</span>
        </template>
      </TableApptable>
    </div>
  </div>
</template>