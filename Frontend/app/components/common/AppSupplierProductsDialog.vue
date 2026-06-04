<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import type { SupplierProductItem } from '~/types'
import { formatCurrency } from '~/utils/format/currency'
import { formatDate } from '~/utils/format/date'

const open = defineModel<boolean>('open', { default: false })
const dateRange = defineModel<{ start: any; end: any }>('range', {
  default: () => ({ start: undefined, end: undefined }),
})

const props = withDefaults(
  defineProps<{
    supplierName?: string
    title?: string
    products?: SupplierProductItem[]
    loading?: boolean
    totalRows?: number
    columns?: TableColumn<SupplierProductItem>[]
  }>(),
  {
    supplierName: '',
    title: '',
    products: () => [],
    loading: false,
    totalRows: 0,
  },
)

const defaultColumns: TableColumn<SupplierProductItem>[] = [
  { accessorKey: 'id', header: 'No' },
  { accessorKey: 'productName', header: 'Product Name' },
  { accessorKey: 'qty', header: 'Qty' },
  { accessorKey: 'unitPrice', header: 'Unit Price' },
  { accessorKey: 'amount', header: 'Amount' },
  { accessorKey: 'createdAt', header: 'Created At' },
]

const tableColumns = computed(() => (props.columns?.length ? props.columns : defaultColumns))

const dialogTitle = computed(
  () => props.title || `Products by ${props.supplierName || ''}`.trim(),
)
</script>

<template>
  <CommonAppDataTableModal v-model:open="open" :title="dialogTitle">
    <template #header-actions>
      <CommonAppDatepicker v-model:range="dateRange" icon-only-on-mobile class="shrink-0" />
    </template>

    <TableApptable
      density="compact"
      :columns="tableColumns"
      :data="products"
      :loading="loading"
      :selectable="false"
      :total-rows="totalRows"
      class="h-full min-h-[200px]"
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
  </CommonAppDataTableModal>
</template>
