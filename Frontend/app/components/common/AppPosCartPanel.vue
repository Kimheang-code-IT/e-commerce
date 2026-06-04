<script setup lang="ts">
import type { Product } from '~/types'
import { formatCurrency } from '~/utils/format/currency'
import {
  getCatalogUnitPrice,
  getLineTotal,
  getLineUnitPrice,
  isLinePriceCustom,
  type PosCartItem,
} from '~/composables/pos/helpers'
import {
  validateDiscountInput,
  type DiscountMode,
} from '~/composables/pos/discountHelpers'

const discountMode = defineModel<DiscountMode>('discountMode', { default: 'usd' })
const discountInput = defineModel<number>('discountInput', { required: true })

const props = withDefaults(
  defineProps<{
    cart: PosCartItem[]
    itemCount: number
    subtotal: number
    discountAmount: number
    total: number
    currentStep: number
    totalSteps: number
    allowFinishWithoutCart?: boolean
    canCheckout?: boolean
  }>(),
  {
    allowFinishWithoutCart: false,
    canCheckout: true,
  },
)

const emit = defineEmits<{
  (e: 'clear-cart'): void
  (e: 'update-qty', lineId: string, delta: number): void
  (e: 'remove-item', lineId: string): void
  (e: 'set-line-price', lineId: string, price: number): void
  (e: 'reset-line-price', lineId: string): void
  (e: 'next'): void
}>()

const { t } = useI18n()

const editingLineId = ref<string | null>(null)
const priceDraft = ref(0)

const isCartStep = computed(() => props.currentStep === 0)
const isSummaryStep = computed(() => props.currentStep > 0)
const isLastStep = computed(() => props.currentStep === props.totalSteps - 1)

const discountValidationKey = computed(() =>
  validateDiscountInput(discountMode.value, discountInput.value, props.subtotal),
)

const discountErrorMessage = computed(() => {
  const key = discountValidationKey.value
  if (!key) return ''
  if (key === 'percentMax') return t('pages.pos.validation.discountPercentMax')
  if (key === 'usdMax') return t('pages.pos.validation.discountUsdMax')
  return t('pages.pos.validation.numberRequired')
})

const discountInputMax = computed(() =>
  discountMode.value === 'percent' ? 100 : props.subtotal,
)

const cartNextDisabled = computed(
  () => props.cart.length === 0 && !props.allowFinishWithoutCart,
)

const needsCheckoutPermission = computed(
  () => isLastStep.value || props.currentStep === props.totalSteps - 2,
)

const summaryNextDisabled = computed(
  () =>
    cartNextDisabled.value ||
    !!discountValidationKey.value ||
    (needsCheckoutPermission.value && props.canCheckout === false),
)

watch(discountMode, () => {
  if (discountInput.value < 0) discountInput.value = 0
})

function isEditingItem(item: PosCartItem) {
  return editingLineId.value === item.lineId
}

function openPriceEdit(item: PosCartItem) {
  editingLineId.value = item.lineId
  priceDraft.value = getLineUnitPrice(item)
}

function commitPriceEdit(item: PosCartItem) {
  if (!isEditingItem(item)) return
  const price = Number(priceDraft.value)
  if (Number.isFinite(price) && price >= 0) {
    emit('set-line-price', item.lineId, price)
  }
  editingLineId.value = null
}

function cancelPriceEdit() {
  editingLineId.value = null
}

function resetInlinePrice(item: PosCartItem) {
  emit('reset-line-price', item.lineId)
  editingLineId.value = null
}

function hasDuplicateProductName(item: PosCartItem) {
  return props.cart.filter((row) => row.product.name === item.product.name).length > 1
}

function getCartQtyForProduct(item: PosCartItem) {
  return props.cart
    .filter((row) => row.product.id === item.product.id)
    .reduce((sum, row) => sum + row.qty, 0)
}

function catalogPrice(product: Product) {
  return getCatalogUnitPrice(product)
}
</script>

<template>
  <div class="w-full h-full min-h-0 flex flex-col bg-card overflow-hidden">
    <div class="flex items-center justify-between px-4 py-3.5 border-b border-default shrink-0">
      <div class="flex items-center gap-2">
        <UIcon name="i-lucide-shopping-cart" class="size-4 text-primary" />
        <span class="font-semibold text-base text-foreground">{{ $t('pages.pos.cart.title') }}</span>
        <UBadge
          v-if="isCartStep && itemCount > 0"
          color="primary"
          variant="soft"
          size="sm"
        >
          {{ itemCount }}
        </UBadge>
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

    <div class="flex-1 min-h-0 overflow-y-auto">
      <div
        v-if="cart.length === 0"
        class="flex flex-col items-center justify-center min-h-48 gap-3 text-muted-foreground px-4 py-8"
      >
        <UIcon name="i-lucide-shopping-cart" class="size-10 opacity-20" />
        <p class="text-sm text-center">{{ $t('pages.pos.cart.empty') }}</p>
      </div>

      <div v-else class="flex flex-col">
        <div
          v-for="item in cart"
          :key="item.lineId"
          class="px-4 py-3 border-b border-default transition-colors"
          :class="[
            isEditingItem(item) ? 'bg-primary/5 ring-1 ring-inset ring-primary/20 py-3.5' : 'hover:bg-muted/30',
          ]"
        >
          <div class="flex items-start gap-3">
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-foreground leading-tight line-clamp-2">
                {{ item.product.name }}
                <span
                  v-if="hasDuplicateProductName(item)"
                  class="text-primary font-semibold"
                >
                  @ {{ formatCurrency(getLineUnitPrice(item), 'USD') }}
                </span>
              </p>
              <p
                v-if="!isEditingItem(item)"
                class="text-xs text-muted-foreground mt-0.5 tabular-nums"
              >
                {{ formatCurrency(getLineUnitPrice(item), 'USD') }} × {{ item.qty }}
              </p>
            </div>

            <div class="flex flex-col items-end gap-2 shrink-0 min-w-0">
              <!-- Row A: qty + line total + actions (always visible) -->
              <div class="flex items-center gap-1">
                <div class="flex items-center">
                  <UButton
                    size="xs"
                    color="neutral"
                    variant="outline"
                    icon="i-lucide-minus"
                    class="size-6 p-0 min-w-0 items-center justify-center"
                    @click="emit('update-qty', item.lineId, -1)"
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
                    :disabled="getCartQtyForProduct(item) >= item.product.inStock"
                    @click="emit('update-qty', item.lineId, 1)"
                  />
                </div>

                <p
                  v-if="!(isCartStep && isEditingItem(item))"
                  class="text-sm font-semibold text-foreground tabular-nums min-w-18 text-right"
                >
                  {{ formatCurrency(getLineTotal(item), 'USD') }}
                </p>
                <UInput
                  v-else
                  v-model.number="priceDraft"
                  type="number"
                  min="0"
                  step="0.01"
                  size="xs"
                  class="w-24 min-w-18"
                  autofocus
                  @keyup.enter="commitPriceEdit(item)"
                  @keyup.escape="cancelPriceEdit"
                />

                <template v-if="isCartStep && isEditingItem(item)">
                  <UButton
                    size="xs"
                    color="primary"
                    variant="soft"
                    icon="i-lucide-check"
                    class="size-6 p-0 min-w-0 items-center justify-center"
                    @mousedown.prevent
                    @click="commitPriceEdit(item)"
                  />
                  <UButton
                    v-if="isLinePriceCustom(item) || priceDraft !== catalogPrice(item.product)"
                    size="xs"
                    color="neutral"
                    variant="ghost"
                    icon="i-lucide-rotate-ccw"
                    class="size-6 p-0 min-w-0 items-center justify-center"
                    :aria-label="$t('pages.pos.cart.resetPrice')"
                    @mousedown.prevent
                    @click="resetInlinePrice(item)"
                  />
                </template>
                <template v-else>
                  <UButton
                    v-if="isCartStep"
                    size="xs"
                    color="neutral"
                    variant="ghost"
                    icon="i-lucide-pencil"
                    class="size-6 p-0 min-w-0 items-center justify-center"
                    :aria-label="$t('pages.pos.cart.editLinePrice')"
                    @click.stop="openPriceEdit(item)"
                  />
                  <UButton
                    size="xs"
                    color="error"
                    variant="ghost"
                    icon="i-lucide-trash-2"
                    class="size-6 p-0 min-w-0 items-center justify-center"
                    @click="emit('remove-item', item.lineId)"
                  />
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Step 0: Next only -->
    <div
      v-if="isCartStep"
      class="border-t border-default px-4 py-3 bg-card shrink-0"
    >
      <UButton
        block
        size="md"
        icon="i-lucide-corner-down-right"
        color="primary"
        variant="solid"
        :disabled="cartNextDisabled"
        class="font-semibold"
        @click="emit('next')"
      >
        {{ $t('pages.pos.cart.next') }}
      </UButton>
    </div>

    <!-- Steps 1–2: full summary + Next / Finish -->
    <div
      v-else-if="isSummaryStep"
      class="border-t border-default px-4 py-3 flex flex-col gap-2.5 bg-card shrink-0"
    >
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

      <div class="flex flex-col gap-1 min-w-0">
        <div class="flex flex-row items-center gap-2 w-full min-w-0">
          <span class="text-sm text-muted-foreground shrink-0">
            {{ $t('pages.pos.cart.discount') }}
          </span>
          <CommonAppMoneyModeInput
            v-model:mode="discountMode"
            v-model:input-value="discountInput"
            class="flex-1 min-w-0"
            size="sm"
            :max-usd="discountInputMax"
          />
          <span class="text-sm font-medium text-red-500 shrink-0 tabular-nums whitespace-nowrap">
            -{{ formatCurrency(discountAmount, 'USD') }}
          </span>
        </div>
        <p v-if="discountErrorMessage" class="text-xs text-error text-right">
          {{ discountErrorMessage }}
        </p>
      </div>

      <USeparator />

      <div class="flex justify-between items-center">
        <span class="text-base font-bold text-foreground">{{ $t('pages.pos.cart.total') }}</span>
        <span class="text-lg font-bold text-primary">{{ formatCurrency(total, 'USD') }}</span>
      </div>

      <UButton
        block
        size="md"
        :icon="isLastStep ? (cart.length === 0 && props.allowFinishWithoutCart ? 'i-lucide-printer' : 'i-lucide-check') : 'i-lucide-corner-down-right'"
        color="primary"
        variant="solid"
        :disabled="summaryNextDisabled"
        class="font-semibold"
        @click="emit('next')"
      >
        {{
          isLastStep
            ? cart.length === 0 && props.allowFinishWithoutCart
              ? 'Print'
              : $t('pages.pos.cart.finish')
            : $t('pages.pos.cart.next')
        }}
      </UButton>
    </div>
  </div>
</template>
