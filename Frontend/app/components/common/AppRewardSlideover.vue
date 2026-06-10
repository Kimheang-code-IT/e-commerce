<script setup lang="ts">
import type { Product, Reward } from '~/types'

const open = defineModel<boolean>('open', { default: false })

const props = defineProps<{
  entry?: Reward | null
  name: string
  selectedProductIds: number[]
  products: Product[]
  productsLoading?: boolean
  productSearch: string
}>()

const emit = defineEmits<{
  (e: 'update:name', value: string): void
  (e: 'update:productSearch', value: string): void
  (e: 'toggle-product', productId: number, checked: boolean): void
  (e: 'submit'): void
}>()

const { t } = useI18n()

const title = computed(() =>
  props.entry ? t('pages.reward.formTitleEdit') : t('pages.reward.formTitleNew'),
)
</script>

<template>
  <USlideover v-model:open="open" :title="title" :ui="{ content: 'max-w-md' }">
    <template #body>
      <div class="flex flex-col gap-4 p-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-sm font-medium">{{ t('reward.name') }}</label>
          <UInput
            :model-value="name"
            :placeholder="t('reward.namePlaceholder')"
            @update:model-value="emit('update:name', String($event || ''))"
          />
        </div>

        <div class="flex flex-col gap-2">
          <div class="flex items-center justify-between gap-2">
            <label class="text-sm font-medium">{{ t('reward.selectProducts') }}</label>
            <span class="text-xs text-muted">{{ selectedProductIds.length }} {{ t('common.items') }}</span>
          </div>
          <UInput
            :model-value="productSearch"
            icon="i-lucide-search"
            :placeholder="t('common.search')"
            @update:model-value="emit('update:productSearch', String($event || ''))"
          />
          <div class="border border-default rounded-lg max-h-[50vh] overflow-y-auto divide-y divide-default">
            <div v-if="productsLoading" class="p-4 text-sm text-muted">{{ t('common.loading') }}</div>
            <label
              v-for="product in products"
              :key="product.id"
              class="flex items-center gap-3 px-3 py-2.5 hover:bg-muted/40 cursor-pointer"
            >
              <UCheckbox
                :model-value="selectedProductIds.includes(product.id)"
                @update:model-value="emit('toggle-product', product.id, Boolean($event))"
              />
              <span class="text-sm truncate">{{ product.name }}</span>
            </label>
            <div v-if="!productsLoading && !products.length" class="p-4 text-sm text-muted">
              {{ t('common.noData') }}
            </div>
          </div>
        </div>
      </div>
    </template>
    <template #footer>
      <div class="flex justify-end gap-2 p-4">
        <UButton color="neutral" variant="ghost" @click="open = false">{{ t('actions.cancel') }}</UButton>
        <UButton color="primary" @click="emit('submit')">{{ t('actions.save') }}</UButton>
      </div>
    </template>
  </USlideover>
</template>
