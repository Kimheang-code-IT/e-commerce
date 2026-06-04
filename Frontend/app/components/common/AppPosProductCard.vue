<script setup lang="ts">
import type { Product } from '~/types'
import { formatCurrency } from '~/utils/format/currency'

const props = defineProps<{
  product: Product
  inCart?: boolean
  cartQty?: number
}>()

const emit = defineEmits<{
  (e: 'add', product: Product): void
  (e: 'filter-category', categoryId: string): void
}>()

const { t } = useI18n()

const stockColor = computed<'primary' | 'warning' | 'error'>(() => {
  if (props.product.inStock > 10) return 'primary'
  if (props.product.inStock > 0) return 'warning'
  return 'error'
})

const addLabel = computed(() =>
  props.inCart ? t('pages.pos.productCard.addMore') : t('pages.pos.productCard.addToCart'),
)

const cannotAdd = computed(
  () =>
    (props.product.inStock || 0) === 0 ||
    (props.cartQty || 0) >= (props.product.inStock || 0),
)
</script>

<template>
  <UCard
    :ui="{ body: 'p-0 sm:p-0 flex flex-col h-full', root: 'rounded-sm overflow-hidden transition-all duration-200 hover:shadow-md hover:-translate-y-0.5 bg-card group h-full' }"
    :class="inCart ? 'border-primary/60 ring-1 ring-primary/30' : 'border-default'"
  >
    <div class="relative flex-1 min-h-32 max-h-44 sm:min-h-44 sm:max-h-50 bg-muted overflow-hidden">
      <img
        :src="product.image"
        :alt="product.name"
        class="w-full h-full min-h-32 max-h-44 sm:min-h-44 sm:max-h-50 object-contain object-center transition-transform duration-300 group-hover:scale-[1.02]"
        loading="lazy"
      />
      <div class="absolute top-2 right-2 z-10">
        <UBadge :color="stockColor" variant="solid" size="sm" class="max-sm:text-[10px]">
          {{ product.inStock }} {{ $t('pages.pos.productCard.inStock') }}
        </UBadge>
      </div>
      <div
        class="absolute inset-x-0 bottom-0 z-10 bg-linear-to-t from-black/80 via-black/50 to-transparent pt-10 pb-2 px-2.5 pointer-events-none"
      >
        <p class="text-sm sm:text-md font-semibold text-white leading-snug line-clamp-2 drop-shadow-sm">
          {{ product.name }}
        </p>
      </div>
    </div>
    <div class="flex flex-col gap-1 px-2 pt-2 pb-1 sm:gap-1.5 sm:px-3 sm:pt-2.5 shrink-0">
      <p class="text-sm sm:text-base font-bold text-primary">
        {{ formatCurrency(product.outPrice, 'USD') }}
      </p>
    </div>

    <div class="px-2 pb-2 pt-1 sm:px-3 sm:pb-3 shrink-0">
      <UButton
        block
        size="sm"
        icon="i-lucide-plus"
        color="primary"
        class="max-sm:text-xs max-sm:py-2 sm:hidden"
        :variant="inCart ? 'outline' : 'solid'"
        :disabled="cannotAdd"
        @click="emit('add', product)"
      >
        {{ addLabel }}
      </UButton>
      <UButton
        block
        size="md"
        icon="i-lucide-plus"
        color="primary"
        class="hidden sm:flex"
        :variant="inCart ? 'outline' : 'solid'"
        :disabled="cannotAdd"
        @click="emit('add', product)"
      >
        {{ addLabel }}
      </UButton>
    </div>
  </UCard>
</template>
