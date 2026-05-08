<script setup lang="ts">
import { useReport } from '~/composables/table/useReport'
import { formatCurrency } from '~/utils/format/currency'
import { usePosApi, useReportApi } from '~/utils/api'

const {
  rowSelection,
  sorting,
  searchQuery,
  columnVisibility,
  columnFilters,
  pagination,
  totalRows,
  filteredReportRows,
  selectedReportRows,
  allFilteredSelected,
  someFilteredSelected,
  toggleSelectAllFiltered,
  productItems,
  selectedProducts,
  columns
} = useReport()
const { t } = useI18n()
const router = useRouter()
const isExportOpen = ref(false)
const posApi = usePosApi()
const reportApi = useReportApi()


function goToInvoice(row: any) {
  router.push({
    path: '/pos',
    query: { invoiceNo: row.invoiceNo }
  })
}

async function goToSelectedInvoices() {
  if (!selectedReportRows.value.length) return
  const invoiceNos = [...new Set(selectedReportRows.value.map((r) => r.invoiceNo))]
  router.push({
    path: '/pos',
    query: { invoiceNo: invoiceNos.join(',') }
  })
}

async function fetchReportExportData(args: { startDate?: string; endDate?: string }) {
  const res = await reportApi.exportCsv({
    ...((args.startDate || args.endDate) ? { dateFrom: args.startDate, dateTo: args.endDate } : {}),
    search: searchQuery.value || undefined,
    product: selectedProducts.value.length ? selectedProducts.value.join(',') : undefined
  })
  return res.data || filteredReportRows.value
}
</script>

<template>
  <div class="flex flex-col h-full bg-background overflow-hidden text-foreground tracking-tight">
    <LayoutAppHeader :title="t('pages.report.title')" show-datepicker>
      <template #right>
        <UButton icon="i-lucide-receipt-text" color="primary" variant="solid" class="font-normal shadow-sm shrink-0"
          :disabled="selectedReportRows.length === 0" @click="goToSelectedInvoices">
          <span class="hidden sm:inline">Preview Selected</span>
        </UButton>
        <UButton icon="i-lucide-download" color="neutral" variant="subtle" class="font-normal shadow-sm shrink-0"
          @click="isExportOpen = true">
          <span class="hidden sm:inline">{{ $t('common.export') }}</span>
        </UButton>
      </template>
    </LayoutAppHeader>
    <div class="flex-1 p-2 overflow-hidden">
      <TableApptable :title="t('pages.report.tableTitle')" v-model:row-selection="rowSelection"
        v-model:sorting="sorting" v-model:column-visibility="columnVisibility" v-model:pagination="pagination"
        v-model:column-filters="columnFilters" v-model:filter-value="selectedProducts" v-model:global-filter="searchQuery" :filter-items="productItems"
        :filter-placeholder="$t('product.name')" :data="filteredReportRows" :total-rows="totalRows" :columns="columns"
        :selectable="true">
        <template #no-header>
          <div class="flex items-center gap-2">
            <UCheckbox :model-value="allFilteredSelected" :indeterminate="someFilteredSelected"
              @update:model-value="toggleSelectAllFiltered(!!$event)" />
            <UButton v-if="selectedReportRows.length > 0" icon="i-lucide-receipt-text" color="primary" variant="ghost"
              size="xs" @click="goToSelectedInvoices" />
          </div>
        </template>
        <template #no-cell="{ row }">
          <div class="flex items-center gap-2">
            <UCheckbox :model-value="row.getIsSelected()" @update:model-value="row.toggleSelected(!!$event)" />
            <span class="text-sm text-muted-foreground">{{ row.index + 1 }}</span>
          </div>
        </template>

        <template #amount-cell="{ row }">
          <span class="text-sm font-medium">{{ formatCurrency(row.original.amount, 'USD') }}</span>
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
        <template #source-cell="{ row }">
          <UBadge color="primary" variant="soft" class="font-normal">
            {{ row.original.source }}
          </UBadge>
        </template>
        <template #address-cell="{ row }">
          <UBadge color="primary" variant="soft" class="font-normal">
            {{ row.original.address }}
          </UBadge>
        </template>
        <template #invoiceNo-cell="{ row }">
          <div class="flex items-center gap-2">
            <span class="text-sm font-medium">{{ row.original.invoiceNo }}</span>
            <UButton icon="i-lucide-receipt-text" color="primary" variant="ghost" size="xs"
              @click="goToInvoice(row.original)" />
          </div>
        </template>
      </TableApptable>
      <CommonAppExport v-model:open="isExportOpen" :data="filteredReportRows" :fetch-export-data="fetchReportExportData"
        filename="report" date-field="date" />
    </div>
  </div>
</template>
