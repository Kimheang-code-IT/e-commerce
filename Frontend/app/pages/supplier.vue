<script setup lang="ts">
import { formatCurrency } from '~/utils/format/currency'
import { formatDate } from '~/utils/format/date'
import { useSupplierTable } from '~/composables/table/usersupplier'
import type { Supplier, SupplierProductItem } from '~/types'

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
    <LayoutAppHeader title="Supplier Management" show-datepicker>
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
        <UButton
          v-if="canCreate"
          icon="i-lucide-circle-plus"
          color="primary"
          variant="solid"
          class="font-normal shadow-sm shrink-0"
          @click="handleAddNew"
        >
          Add Supplier
        </UButton>
      </template>
    </LayoutAppHeader>

    <div class="flex-1 p-2 overflow-hidden">
      <TableApptable
        title="Supplier Table"
        v-model:row-selection="rowSelection"
        v-model:sorting="sorting"
        v-model:column-visibility="columnVisibility"
        v-model:pagination="pagination"
        v-model:column-filters="columnFilters"
        v-model:global-filter="searchQuery"
        :data="suppliers"
        :columns="columns"
        :total-rows="totalRows"
        :selectable="true"
        :get-row-actions="getDropdownActions"
      >
        <template #totalProduct-cell="{ row }">
          <UButton
            variant="ghost"
            color="primary"
            size="sm"
            class="px-2 underline"
            @click="openProductsDialog(row.original as Supplier)"
          >
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
      :title="selectedSupplier?.id ? 'Edit Supplier' : 'Add Supplier'"
      :submit-label="selectedSupplier?.id ? 'Save' : 'Add'"
      @submit="onSubmitSupplier"
    />

    <CommonAppModalCURD
      v-model:open="isConfirmOpen"
      v-bind="confirmConfig"
      @submit="finalizeAction"
    />

    <!-- Supplier Products Dialog -->
    <UModal
      v-model:open="isProductsDialogOpen"
      :dismissible="false"
      :ui="{ content: 'sm:max-w-5xl h-[80vh] flex flex-col' }"
    >
      <template #header>
        <div class="flex items-center justify-between w-full">
          <h3 class="font-semibold">
            Products by {{ supplierForProducts?.name || '' }}
          </h3>
          <div class="flex items-center gap-2">
            <CommonAppDatepicker v-model:range="supplierProductsDateRange" class="shrink-0" />
            <UButton
              icon="i-lucide-x"
              color="neutral"
              variant="ghost"
              size="sm"
              @click="isProductsDialogOpen = false"
            />
          </div>
        </div>
      </template>

      <template #body>
        <TableApptable
          :columns="supplierProductsColumns"
          :data="supplierProducts"
          :loading="supplierProductsLoading"
          :selectable="false"
          :total-rows="supplierProductsTotal"
        >
          <template #unitPrice-cell="{ row }">
            {{ formatCurrency((row.original as SupplierProductItem).unitPrice, 'USD') }}
          </template>
          <template #amount-cell="{ row }">
            {{ formatCurrency((row.original as SupplierProductItem).amount, 'USD') }}
          </template>
          <template #createdAt-cell="{ row }">
            {{ formatDate((row.original as SupplierProductItem).createdAt) }}
          </template>
        </TableApptable>
      </template>
    </UModal>

    <CommonAppSlideoverForm
      v-model:open="isProductEditOpen"
      :data="productFormData"
      :fields="productFormFields"
      title="Edit Supplier Product"
      submit-label="Save"
      @submit="onSubmitSupplierProduct"
    />
    <CommonAppExport
      v-model:open="isExportOpen"
      :data="suppliers"
      filename="suppliers"
      date-field="createdAt"
    />
  </div>
</template>