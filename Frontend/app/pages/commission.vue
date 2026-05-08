<script setup lang="ts">
import { useCommission } from '~/composables/table/useCommission'
import { formatCurrency } from '~/utils/format/currency'
import { formatDate } from '~/utils/format/date'
import { useCommissionApi } from '~/utils/api'

const { data, columns, groupingOptions, grouping, isLoading, sorting, searchQuery, columnFilters, pagination, totalRows, productItems, selectedProducts } = useCommission()
const { t } = useI18n()
const isExportOpen = ref(false)
const commissionApi = useCommissionApi()

async function fetchCommissionExportData(args: { startDate?: string; endDate?: string }) {
  const res = await commissionApi.exportCsv({
    ...((args.startDate || args.endDate) ? { dateFrom: args.startDate, dateTo: args.endDate } : {}),
    search: searchQuery.value || undefined,
    product: selectedProducts.value.length ? selectedProducts.value.join(',') : undefined
  })
  return res.data || data.value
}
</script>

<template>
  <div class="flex flex-col h-full bg-background overflow-hidden text-foreground tracking-tight">
    <LayoutAppHeader :title="t('pages.commission.title')" show-datepicker>
      <template #right>
        <UButton icon="i-lucide-download" color="neutral" variant="subtle" class="font-normal shadow-sm shrink-0"
          @click="isExportOpen = true">
          <span class="hidden sm:inline">{{ $t('common.export') }}</span>
        </UButton>
      </template>
    </LayoutAppHeader>

    <div class="flex-1 p-2 overflow-hidden">
      <TableApptable
        :title="t('pages.commission.tableTitle')"
        :data="data"
        :columns="columns"
        :loading="isLoading"
        :total-rows="totalRows"
        v-model:sorting="sorting"
        v-model:column-filters="columnFilters"
        v-model:pagination="pagination"
        v-model:global-filter="searchQuery"
        v-model:filter-value="selectedProducts"
        :filter-items="productItems"
        :filter-placeholder="t('pages.commission.columns.product')"
        v-model:grouping="grouping"
        :grouping-options="groupingOptions"
        :selectable="false"
        :virtualize="true"
        :ui="{
          root: 'min-w-full',
          td: 'empty:p-2'
        }"
      >
        <template #seller-cell="{ row }">
          <div v-if="row.getIsGrouped()" class="flex items-center gap-2 py-1">
            <span class="inline-block" :style="{ width: `calc(${row.depth} * 1rem)` }" />
            <UButton
              color="neutral"
              variant="ghost"
              size="xs"
              :icon="row.getIsExpanded() ? 'i-lucide-chevron-down' : 'i-lucide-chevron-right'"
              @click="row.toggleExpanded()"
            />
            <span class="font-medium text-foreground">
              {{ String(row.groupingColumnId || '').replace('_key', '').toUpperCase() }}:
              {{ row.getValue(row.groupingColumnId || '') }}
              <span class="text-muted-foreground">({{ row.subRows?.length || 0 }} {{ t('common.items') }})</span>
            </span>
          </div>
          <span v-else class="font-medium">
            {{ row.getValue('seller') }}
          </span>
        </template>

        <template #date-cell="{ row }">
          <span class="text-sm text-muted-foreground">
            {{ formatDate(String(row.getValue('date') || '')) }}
          </span>
        </template>

        <template #source-cell="{ row }">
          <UBadge v-if="!row.getIsGrouped()" color="primary" variant="soft" class="font-normal">{{ row.getValue('source') }}</UBadge>
        </template>

        <template #amount-cell="{ row }">
          <span class="font-medium">{{ formatCurrency(Number(row.getValue('amount')), 'USD') }}</span>
        </template>

        <template #commission-cell="{ row }">
          <UBadge color="primary" variant="soft" class="font-normal">{{ formatCurrency(Number(row.getValue('commission')), 'USD') }}</UBadge>
        </template>
      </TableApptable>
      <CommonAppExport v-model:open="isExportOpen" :data="data" :fetch-export-data="fetchCommissionExportData"
        filename="commission" date-field="date" />
    </div>
  </div>
</template>

