<script setup lang="ts">
import { formatCurrency } from '~/utils/format/currency'
import { useSupplierTable } from '~/composables/table/usersupplier'
import type { Supplier } from '~/types'

const {
  rowSelection,
  sorting,
  columnFilters,
  columnVisibility,
  pagination,
  searchQuery,
  suppliers,
  totalRows,
  columns,
  supplierFormFields,
  productFormFields,
  confirmConfig,
  isFormOpen,
  isConfirmOpen,
  selectedSupplier,
  getDropdownActions,
  handleSaveRequest,
  finalizeAction,
  handleAddNew,
  isProductsDialogOpen,
  supplierForProducts,
  supplierProducts,
  supplierProductsLoading,
  supplierProductsTotal,
  supplierProductsDateRange,
  supplierProductsColumns,
  openProductsDialog,
  isProductEditOpen,
  productFormData,
  openProductEdit,
  saveProductEdit,
  canCreate,
  canUpdate,
  canView
} = useSupplierTable()

const isExportOpen = ref(false)

function onSubmitSupplier(data: Record<string, any>) {
  handleSaveRequest(data)
}

function onSubmitSupplierProduct(data: Record<string, any>) {
  saveProductEdit(data)
}
</script>

<template>
  <div class="flex flex-col h-full bg-background overflow-hidden text-foreground tracking-tight">
    <LayoutAppHeader :title="$t('pages.supplier.title')" show-datepicker>
      <template #right>
        <UButton v-if="canView" icon="i-lucide-download" color="neutral" variant="subtle"
          class="font-normal shadow-sm shrink-0" @click="isExportOpen = true">
          <span class="hidden sm:inline">{{ $t('common.export') }}</span>
        </UButton>
        <UButton v-if="canCreate" icon="i-lucide-circle-plus" color="primary" variant="solid"
          class="font-normal shadow-sm shrink-0" @click="handleAddNew">
          <span class="hidden sm:inline">{{ $t('pages.supplier.addBtn') }}</span>
        </UButton>
      </template>
    </LayoutAppHeader>

    <div class="flex-1 p-2 overflow-hidden">
      <TableApptable :title="$t('pages.supplier.tableTitle')" v-model:row-selection="rowSelection" v-model:sorting="sorting"
        v-model:column-visibility="columnVisibility" v-model:pagination="pagination"
        v-model:column-filters="columnFilters" v-model:global-filter="searchQuery" :data="suppliers" :columns="columns"
        :total-rows="totalRows" :selectable="true" :get-row-actions="getDropdownActions">
        <template #totalProduct-cell="{ row }">
          <UButton variant="ghost" color="primary" size="sm" class="px-2 underline"
            @click="openProductsDialog(row.original as Supplier)">
            {{ (row.original as Supplier).totalProduct }}
          </UButton>
        </template>

        <template #totalAmount-cell="{ row }">
          <span class="font-medium text-primary">
            {{ formatCurrency((row.original as Supplier).totalAmount, 'USD') }}
          </span>
        </template>
      </TableApptable>
    </div>

    <CommonAppSlideoverForm
      v-model:open="isFormOpen"
      :data="selectedSupplier || undefined"
      :fields="supplierFormFields"
      :title-key="selectedSupplier?.id ? 'pages.supplier.formTitleEdit' : 'pages.supplier.formTitleNew'"
      :submit-label-key="selectedSupplier?.id ? 'actions.save' : 'actions.add'"
      @submit="onSubmitSupplier"
    />

    <CommonAppModalCURD v-model:open="isConfirmOpen" v-bind="confirmConfig" @submit="finalizeAction" />

    <CommonAppSupplierProductsDialog v-model:open="isProductsDialogOpen" v-model:range="supplierProductsDateRange"
      :supplier-name="supplierForProducts?.name" :products="supplierProducts" :loading="supplierProductsLoading"
      :total-rows="supplierProductsTotal" :columns="supplierProductsColumns" />
    <CommonAppSlideoverForm
      v-model:open="isProductEditOpen"
      :data="productFormData"
      :fields="productFormFields"
      title-key="pages.supplier.formTitleEditProduct"
      submit-label-key="actions.save"
      @submit="onSubmitSupplierProduct"
    />
    <CommonAppExport v-model:open="isExportOpen" :data="suppliers" filename="suppliers" date-field="createdAt" />
  </div>
</template>