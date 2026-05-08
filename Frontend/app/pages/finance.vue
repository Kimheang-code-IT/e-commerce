<script setup lang="ts">
import { useFinance } from '~/composables/table/useFinance'
import { formatCurrency } from '~/utils/format/currency'

import { useFinanceApi } from '~/utils/api'

const { t } = useI18n()
const {
  data,
  columns,
  isLoading,
  sorting,
  searchQuery,
  columnFilters,
  pagination,
  totalRows,
  isSlideoverOpen,
  editingRow,
  editFields,
  openEdit,
  handleUpdate
} = useFinance()
const isExportOpen = ref(false)
const financeApi = useFinanceApi()

async function fetchFinanceExportData(args: { startDate?: string; endDate?: string }) {
  const res = await financeApi.exportCsv({
    ...((args.startDate || args.endDate) ? { dateFrom: args.startDate, dateTo: args.endDate } : {}),
    search: searchQuery.value || undefined
  })
  return res.data || data.value
}
</script>

<template>
  <div class="flex flex-col h-full bg-background overflow-hidden text-foreground tracking-tight">
    <LayoutAppHeader :title="t('pages.finance.title')" show-datepicker>
      <template #right>
        <UButton icon="i-lucide-download" color="neutral" variant="subtle" class="font-normal shadow-sm shrink-0"
          @click="isExportOpen = true">
          <span class="hidden sm:inline">{{ $t('common.export') }}</span>
        </UButton>
      </template>
    </LayoutAppHeader>

    <div class="flex-1 p-2 overflow-hidden">
      <TableApptable
        :title="t('pages.finance.tableTitle')"
        :data="data"
        :columns="columns"
        :loading="isLoading"
        v-model:sorting="sorting"
        v-model:column-filters="columnFilters"
        v-model:pagination="pagination"
        v-model:global-filter="searchQuery"
        :total-rows="totalRows"
        :selectable="false"
      >
        <template #actions-cell="{ row }">
          <div class="flex justify-end">
            <UButton
              icon="i-lucide-edit-3"
              variant="ghost"
              color="primary"
              size="sm"
              @click="openEdit(row.original)"
            />
          </div>
        </template>

        <template #printPrice-cell="{ row }">
          <span class="text-sm">{{ formatCurrency(Number(row.getValue('printPrice')), 'USD') }}</span>
        </template>

        <template #totalCommission-cell="{ row }">
          <span class="text-sm text-primary font-medium">
            {{ formatCurrency(Number(row.getValue('totalCommission')), 'USD') }}
          </span>
        </template>

        <template #facebook-cell="{ row }">
          <span class="text-sm">{{ formatCurrency(Number(row.getValue('facebook')), 'USD') }}</span>
        </template>

        <template #other-cell="{ row }">
          <span class="text-sm">{{ formatCurrency(Number(row.getValue('other')), 'USD') }}</span>
        </template>

        <template #inPriceForPos-cell="{ row }">
          <span class="text-sm font-medium">{{ formatCurrency(Number(row.getValue('inPriceForPos')), 'USD') }}</span>
        </template>

        <template #finalPrice-cell="{ row }">
          <span class="text-sm font-semibold text-primary">
            {{ formatCurrency(Number(row.getValue('finalPrice')), 'USD') }}
          </span>
        </template>
      </TableApptable>
      <CommonAppExport v-model:open="isExportOpen" :data="data" :fetch-export-data="fetchFinanceExportData"
        filename="finance" date-field="createdAt" />
    </div>

    <CommonAppSlideoverForm
      v-model:open="isSlideoverOpen"
      :title="t('pages.finance.editTitle')"
      :data="editingRow || undefined"
      :fields="editFields"
      @submit="handleUpdate"
    />
  </div>
</template>