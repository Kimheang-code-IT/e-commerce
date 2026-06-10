<script setup lang="ts">
import { useReward } from '~/composables/table/useReward'
import { formatDate } from '~/utils/format/date'

const {
  rowSelection,
  sorting,
  searchQuery,
  columnVisibility,
  columnFilters,
  pagination,
  isFormOpen,
  isConfirmOpen,
  totalRows,
  selectedEntry,
  filteredEntries,
  confirmConfig,
  isLoading,
  columns,
  getDropdownActions,
  handleSaveRequest,
  finalizeAction,
  handleAddNew,
  canCreate,
  formName,
  selectedProductIds,
  filteredProductOptions,
  isProductsLoading,
  productSearch,
  toggleProduct,
} = useReward()
</script>

<template>
  <LayoutAppHeader :title="$t('pages.reward.title')" show-datepicker>
    <template #right>
      <UButton
        v-if="canCreate"
        icon="i-lucide-circle-plus"
        color="primary"
        variant="solid"
        class="font-normal shadow-sm shrink-0"
        @click="handleAddNew"
      >
        <span class="hidden sm:inline">{{ $t('pages.reward.addBtn') }}</span>
      </UButton>
    </template>

    <div class="flex-1 min-h-0 overflow-hidden">
      <TableApptable
        :title="$t('pages.reward.tableTitle')"
        v-model:row-selection="rowSelection"
        v-model:sorting="sorting"
        v-model:column-visibility="columnVisibility"
        v-model:pagination="pagination"
        v-model:column-filters="columnFilters"
        v-model:global-filter="searchQuery"
        :data="filteredEntries"
        :columns="columns"
        :selectable="true"
        :total-rows="totalRows"
        :loading="isLoading"
        :get-row-actions="getDropdownActions"
      >
        <template #productNames-cell="{ row }">
          <span class="text-sm text-muted line-clamp-2">{{ row.original.productNames }}</span>
        </template>
        <template #createdAt-cell="{ row }">
          <span class="text-sm text-muted">{{ formatDate(row.original.createdAt) }}</span>
        </template>
      </TableApptable>
    </div>

    <CommonAppRewardSlideover
      v-model:open="isFormOpen"
      :entry="selectedEntry"
      :name="formName"
      :selected-product-ids="selectedProductIds"
      :products="filteredProductOptions"
      :products-loading="isProductsLoading"
      :product-search="productSearch"
      @update:name="formName = $event"
      @update:product-search="productSearch = $event"
      @toggle-product="toggleProduct"
      @submit="handleSaveRequest"
    />

    <CommonAppModalCURD v-model:open="isConfirmOpen" v-bind="confirmConfig" @submit="finalizeAction" />
  </LayoutAppHeader>
</template>
