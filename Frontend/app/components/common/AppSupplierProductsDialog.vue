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
  }
)

const defaultColumns: TableColumn<SupplierProductItem>[] = [
  { accessorKey: 'id', header: 'No' },
  { accessorKey: 'productName', header: 'Product Name' },
  { accessorKey: 'qty', header: 'Qty' },
  { accessorKey: 'unitPrice', header: 'Unit Price' },
  { accessorKey: 'amount', header: 'Amount' },
  { accessorKey: 'createdAt', header: 'Created At' },
]

const tableColumns = computed(() => props.columns?.length ? props.columns : defaultColumns)

const dialogTitle = computed(
  () => props.title || `Products by ${props.supplierName || ''}`.trim()
)
</script>

<template>
  <UModal v-model:open="open" :dismissible="false" :ui="{ content: 'sm:max-w-5xl h-[80vh] flex flex-col' }">
    <template #header>
      <div class="flex items-center justify-between w-full">
        <h3 class="font-semibold">{{ dialogTitle }}</h3>
        <div class="flex items-center gap-2">
          <CommonAppDatepicker v-model:range="dateRange" class="shrink-0" />
          <UButton icon="i-lucide-x" color="neutral" variant="ghost" size="sm" @click="open = false" />
        </div>
      </div>
    </template>

    <template #body>
      <TableApptable :columns="tableColumns" :data="products" :loading="loading" :selectable="false"
        :total-rows="totalRows">
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
</template>
