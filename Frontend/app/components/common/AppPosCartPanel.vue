<script setup lang="ts">
import type { Product } from '~/types'
import { formatCurrency } from '~/utils/format/currency'

interface CartItem {
  product: Product
  qty: number
}

const discountPercent = defineModel<number>('discountPercent', { required: true })

const props = withDefaults(defineProps<{
  cart: CartItem[]
  itemCount: number
  subtotal: number
  discountAmount: number
  total: number
  currentStep: number
  totalSteps: number
  allowFinishWithoutCart?: boolean
}>(), {
  allowFinishWithoutCart: false
})

const emit = defineEmits<{
  (e: 'clear-cart'): void
  (e: 'update-qty', productId: number, delta: number): void
  (e: 'remove-item', productId: number): void
  (e: 'next'): void
}>()
</script>

<template>
  <div class="w-full flex flex-col bg-card overflow-hidden">
    <div class="flex items-center justify-between px-4 py-3.5 border-b border-default shrink-0">
      <div class="flex items-center gap-2">
        <UIcon name="i-lucide-shopping-cart" class="size-4 text-primary" />
        <span class="font-semibold text-base text-foreground">{{ $t('pages.pos.cart.title') }}</span>
      </div>
      <div class="flex items-center gap-1.5">
        <UButton
          v-if="cart.length > 0"
          size="xs"
          color="error"
          variant="outline"
          icon="i-lucide-trash-2"
          @click="emit('clear-cart')"
        >
          {{ $t('pages.pos.cart.clearAll') }}
        </UButton>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto min-h-0">
      <div
        v-if="cart.length === 0"
        class="flex flex-col items-center justify-center h-full gap-3 text-muted-foreground px-4"
      >
        <UIcon name="i-lucide-shopping-cart" class="size-10 opacity-20" />
        <p class="text-sm text-center">{{ $t('pages.pos.cart.empty') }}</p>
      </div>

      <div v-else class="flex flex-col">
        <div
          v-for="item in cart"
          :key="item.product.id"
          class="flex items-start gap-3 px-4 py-3 hover:bg-muted/30 transition-colors border-b border-default"
        >
          <div class="flex-1 min-w-32">
            <p class="text-xs font-medium text-foreground leading-tight line-clamp-1">
              {{ item.product.name }}
            </p>
            <UBadge color="primary" variant="soft">
              {{ formatCurrency(item.product.outPrice, 'USD') }}
            </UBadge>
          </div>

          <div class="flex items-center justify-between gap-4 shrink-0">
            <div class="flex items-center">
              <UButton
                size="xs"
                color="neutral"
                variant="outline"
                icon="i-lucide-minus"
                class="size-6 p-0 min-w-0 items-center justify-center"
                @click="emit('update-qty', item.product.id, -1)"
              />
              <span class="w-7 text-center text-sm font-medium tabular-nums">
                {{ item.qty }}
              </span>
              <UButton
                size="xs"
                color="neutral"
                variant="outline"
                icon="i-lucide-plus"
                class="size-6 p-0 min-w-0 items-center justify-center"
                :disabled="item.qty >= item.product.inStock"
                @click="emit('update-qty', item.product.id, 1)"
              />
            </div>
            <p class="text-sm font-semibold text-foreground">
              {{ formatCurrency(item.product.outPrice * item.qty, 'USD') }}
            </p>
            <UButton
              size="xs"
              color="error"
              variant="ghost"
              icon="i-lucide-trash-2"
              class="size-6 p-0 min-w-0 ml-1 items-center justify-center"
              @click="emit('remove-item', item.product.id)"
            />
          </div>
        </div>
      </div>
    </div>

    <div class="border-t border-default px-4 py-3 flex flex-col gap-2.5 bg-card shrink-0 mt-auto sticky bottom-0 z-10">
      <div class="flex justify-between text-sm text-muted-foreground">
        <span>{{ $t('pages.pos.cart.items') }}</span>
        <UBadge v-if="itemCount > 0" color="primary" variant="solid" size="sm">
          {{ itemCount }}
        </UBadge>
      </div>
      <div class="flex justify-between text-sm text-muted-foreground">
        <span>{{ $t('pages.pos.cart.subtotal') }}</span>
        <span class="font-medium text-foreground">{{ formatCurrency(subtotal, 'USD') }}</span>
      </div>

      <div class="flex items-center justify-between gap-2">
        <span class="text-sm text-muted-foreground shrink-0">{{ $t('pages.pos.cart.discount') }}</span>
        <div class="flex items-center gap-2">
          <UInput
            v-model.number="discountPercent"
            type="number"
            size="xs"
            min="0"
            max="100"
            class="w-16 text-center"
          />
          <span class="text-sm font-medium text-red-500 w-16 text-right shrink-0">
            -{{ formatCurrency(discountAmount, 'USD') }}
          </span>
        </div>
      </div>

      <USeparator />

      <div class="flex justify-between items-center">
        <span class="text-base font-bold text-foreground">{{ $t('pages.pos.cart.total') }}</span>
        <span class="text-lg font-bold text-primary">{{ formatCurrency(total, 'USD') }}</span>
      </div>

      <UButton
        block
        size="md"
        :icon="currentStep === totalSteps - 1 ? (cart.length === 0 && props.allowFinishWithoutCart ? 'i-lucide-printer' : 'i-lucide-check') : 'i-lucide-corner-down-right'"
        :color="currentStep === totalSteps - 1 ? 'primary' : 'primary'"
        variant="solid"
        :disabled="cart.length === 0 && !props.allowFinishWithoutCart"
        class="font-semibold"
        @click="emit('next')"
      >
        {{ currentStep === totalSteps - 1 ? (cart.length === 0 && props.allowFinishWithoutCart ? 'Print' : $t('pages.pos.cart.finish')) : $t('pages.pos.cart.next') }}
      </UButton>
    </div>
  </div>
</template>
