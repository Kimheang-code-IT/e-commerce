<script setup lang="ts">
/**
 * Stock addition / damage history with per-row edit (adjust totals).
 */
import { useProductApi } from '~/utils/api'
import { modalUiConfirm, dialogFooterActions, dialogBody } from '~/utils/ui/overlayUi'

const open = defineModel<boolean>('open', { default: false })
const range = defineModel<any>('range')
const pagination = defineModel<any>('pagination', {
  default: () => ({ pageIndex: 0, pageSize: 50 }),
})

const props = withDefaults(
  defineProps<{
    type: 'added' | 'damaged'
    productId?: number
    productName?: string
    data: any[]
    loading?: boolean
    total: number
    canEdit?: boolean
  }>(),
  {
    productId: undefined,
    productName: '',
    loading: false,
    canEdit: false,
  },
)

const emit = defineEmits<{
  (e: 'saved'): void
}>()

const { t } = useI18n()
const toast = useToast()
const productApi = useProductApi()

const isEditOpen = ref(false)
const editRow = ref<Record<string, unknown> | null>(null)
const editQty = ref(0)
const editInPrice = ref(0)
const editOutPrice = ref(0)
const editNote = ref('')
const isSaving = ref(false)

const pageQtyTotal = computed(() =>
  (props.data || []).reduce((sum, row) => sum + Number(row.qty || 0), 0),
)

const columns = computed(() => {
  const base: { accessorKey: string; header: string }[] = [
    { accessorKey: 'id', header: t('product.id') },
    { accessorKey: 'qty', header: t('product.qty') },
  ]
  if (props.type === 'added') {
    base.push(
      { accessorKey: 'inPrice', header: t('product.inPrice') },
      { accessorKey: 'outPrice', header: t('product.outPrice') },
      { accessorKey: 'qtyRemaining', header: t('product.qtyRemaining') },
    )
  }
  base.push(
    { accessorKey: 'note', header: t('product.note') },
    { accessorKey: 'createdAt', header: t('product.createdAt') },
  )
  if (props.canEdit) {
    base.push({ accessorKey: 'actions', header: t('common.actions') })
  }
  return base
})

const canSaveEdit = computed(() => {
  const q = Number(editQty.value)
  return Number.isFinite(q) && q > 0
})

function openEdit(row: Record<string, unknown>) {
  editRow.value = row
  editQty.value = Number(row.qty || 0)
  editInPrice.value = Number(row.inPrice || 0)
  editOutPrice.value = Number(row.outPrice || 0)
  editNote.value = String(row.note || '')
  isEditOpen.value = true
}

async function saveEdit() {
  if (!props.productId || !editRow.value?.id || !canSaveEdit.value) return
  isSaving.value = true
  try {
    if (props.type === 'added') {
      await productApi.updateStockAddition(props.productId, editRow.value.id as number, {
        qty: Number(editQty.value),
        inPrice: Number(editInPrice.value),
        outPrice: Number(editOutPrice.value),
        note: editNote.value || undefined,
      })
    } else {
      await productApi.updateDamage(props.productId, editRow.value.id as number, {
        qty: Number(editQty.value),
        note: editNote.value || undefined,
      })
    }
    toast.add({
      title: t('product.historyUpdateSuccess'),
      color: 'primary',
    })
    isEditOpen.value = false
    emit('saved')
  } catch (err: unknown) {
    const fetchErr = err as { response?: { _data?: { message?: string } } }
    const detail = fetchErr?.response?._data?.message
    toast.add({
      title: t('product.historyUpdateFailed'),
      description: detail || undefined,
      color: 'error',
    })
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <CommonAppDataTableModal v-model:open="open" :title="productName">
    <template #header-meta>
      <div class="flex flex-wrap items-center gap-2">
        <UBadge :color="type === 'added' ? 'primary' : 'error'" variant="soft" size="sm">
          {{ type === 'added' ? $t('product.historyTitleAdded') : $t('product.historyTitleDamaged') }}
        </UBadge>
        <UBadge color="neutral" variant="outline" size="sm">
          {{ $t('product.historyPageQtyTotal') }}: {{ pageQtyTotal }}
        </UBadge>
        <span class="text-xs text-muted-foreground">
          {{ $t('product.historyRecordsTotal', { count: total }) }}
        </span>
      </div>
    </template>

    <template #header-actions>
      <CommonAppDatepicker v-model:range="range" icon-only-on-mobile class="shrink-0" />
    </template>

    <TableApptable
      density="compact"
      :columns="columns"
      :data="data"
      :loading="loading"
      :total-rows="total"
      v-model:pagination="pagination"
      :selectable="false"
      class="h-full min-h-[200px]"
    >
        <template #id-cell="{ row }">
          <span class="text-xs text-muted-foreground">#{{ row.original.id }}</span>
        </template>
        <template #qty-cell="{ row }">
          <UBadge :color="type === 'added' ? 'primary' : 'error'" variant="soft">
            {{ type === 'added' ? '+' : '-' }}{{ row.original.qty }}
          </UBadge>
        </template>
        <template v-if="type === 'added'" #inPrice-cell="{ row }">
          {{ formatCurrency(row.original.inPrice, 'USD') }}
        </template>
        <template v-if="type === 'added'" #outPrice-cell="{ row }">
          {{ formatCurrency(row.original.outPrice, 'USD') }}
        </template>
        <template v-if="type === 'added'" #qtyRemaining-cell="{ row }">
          {{ row.original.qtyRemaining ?? row.original.qty }}
        </template>
        <template #note-cell="{ row }">
          <span class="text-sm line-clamp-2">{{ row.original.note || '—' }}</span>
        </template>
        <template #createdAt-cell="{ row }">
          <span class="text-sm text-muted-foreground">
            {{ formatDate(row.original.createdAt) }}
          </span>
        </template>
        <template v-if="canEdit" #actions-cell="{ row }">
          <UButton
            icon="i-lucide-pencil"
            size="xs"
            color="primary"
            variant="soft"
            :aria-label="$t('actions.edit')"
            @click="openEdit(row.original)"
          />
        </template>
    </TableApptable>
  </CommonAppDataTableModal>

  <UModal v-model:open="isEditOpen" :dismissible="false" :ui="modalUiConfirm">
    <template #header>
      <div class="flex items-center justify-between w-full">
        <h3 class="font-semibold">
          {{ type === 'added' ? $t('product.historyEditBatch') : $t('product.historyEditDamage') }}
          <span class="text-muted font-normal">#{{ editRow?.id }}</span>
        </h3>
        <UButton icon="i-lucide-x" color="neutral" variant="ghost" size="sm" @click="isEditOpen = false" />
      </div>
    </template>
    <template #body>
      <div :class="[dialogBody, 'space-y-3']">
        <UFormField :label="$t('product.qty')">
          <UInput v-model.number="editQty" type="number" min="1" step="1" class="w-full" />
        </UFormField>
        <template v-if="type === 'added'">
          <UFormField :label="$t('product.inPrice')">
            <UInput v-model.number="editInPrice" type="number" min="0" step="0.01" class="w-full" />
          </UFormField>
          <UFormField :label="$t('product.outPrice')">
            <UInput v-model.number="editOutPrice" type="number" min="0" step="0.01" class="w-full" />
          </UFormField>
        </template>
        <UFormField :label="$t('product.note')">
          <UTextarea v-model="editNote" :rows="3" class="w-full" />
        </UFormField>
      </div>
    </template>
    <template #footer>
      <div :class="dialogFooterActions">
        <UButton color="neutral" variant="soft" @click="isEditOpen = false">
          {{ $t('actions.cancel') }}
        </UButton>
        <UButton color="primary" :loading="isSaving" :disabled="!canSaveEdit" @click="saveEdit">
          {{ $t('actions.save') }}
        </UButton>
      </div>
    </template>
  </UModal>
</template>
