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

const stockColor = computed<'primary' | 'warning' | 'error'>(() => {
  if (props.product.inStock > 10) return 'primary'
  if (props.product.inStock > 0) return 'warning'
  return 'error'
})

const sku = computed(() => {
  return `${props.product.category.substring(0, 3).toUpperCase()}-${String(props.product.id).padStart(4, '0')}`
})
</script>

<template>
  <UCard
    :ui="{ body: 'p-0 sm:p-0', root: 'rounded-none overflow-hidden transition-all duration-200 hover:shadow-md hover:-translate-y-0.5 bg-card group' }"
    :class="inCart ? 'border-primary/60 ring-1 ring-primary/30' : 'border-default'">
    <div class="relative h-36 bg-muted overflow-hidden">
      <img :src="product.image" :alt="product.name"
        class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105" loading="lazy" />
      <div class="absolute top-2 right-2">
        <UBadge :color="stockColor" variant="solid" size="xs">
          {{ product.inStock }} {{ $t('pages.pos.productCard.inStock') }}
        </UBadge>
      </div>
    </div>

    <div class="flex flex-col gap-1 px-3 pt-2 pb-1">
      <p class="text-xs font-semibold text-foreground leading-tight line-clamp-2">
        {{ product.name }}
      </p>
      <p class="text-[10px] text-muted-foreground flex items-center gap-1">
        <span>{{ $t('product.category') }}:</span>
        <button type="button" class="hover:text-primary hover:underline transition-colors"
          @click.stop="emit('filter-category', product.categoryId)">
          {{ product.category }}
        </button>
      </p>
      <p class="text-sm font-bold text-primary mt-1">
        {{ formatCurrency(product.outPrice, 'USD') }}
      </p>
    </div>

    <div class="px-3 pb-3 pt-1">
      <UButton block size="sm" icon="i-lucide-plus" color="primary" :variant="inCart ? 'outline' : 'solid'"
        :disabled="(product.inStock || 0) === 0 || (cartQty || 0) >= (product.inStock || 0)"
        @click="emit('add', product)">
        {{ inCart ? $t('pages.pos.productCard.addMore') : $t('pages.pos.productCard.addToCart') }}
      </UButton>
    </div>
  </UCard>
</template>
