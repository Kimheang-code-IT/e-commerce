<script setup lang="ts">
/**
 * Amount input with USD / % toggle in a flex row (toggle left, input right — not inside the input).
 */
export type MoneyInputMode = 'usd' | 'percent'

const mode = defineModel<MoneyInputMode>('mode', { default: 'usd' })
const inputValue = defineModel<number>('inputValue', { required: true })

const props = withDefaults(
  defineProps<{
    min?: number
    maxUsd?: number
    maxPercent?: number
    stepUsd?: number
    stepPercent?: number
    size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
    disabled?: boolean
    errorMessage?: string
    usdPreview?: number
    showUsdPreview?: boolean
    placeholder?: string
  }>(),
  {
    min: 0,
    maxPercent: 100,
    stepUsd: 0.01,
    stepPercent: 1,
    size: 'lg',
    showUsdPreview: false
  }
)

const emit = defineEmits<{
  (e: 'mode-change', value: MoneyInputMode): void
  (e: 'input'): void
}>()

const { t } = useI18n()

const effectiveMax = computed(() =>
  mode.value === 'percent' ? props.maxPercent : props.maxUsd
)

const effectiveStep = computed(() =>
  mode.value === 'percent' ? props.stepPercent : props.stepUsd
)

const inputColor = computed(() => (props.errorMessage ? 'error' : undefined))

const groupRingClass = computed(() =>
  props.errorMessage
    ? 'ring-2 ring-error/40 border-error/60'
    : 'ring-0 border-default focus-within:ring-2 focus-within:ring-primary/30'
)

function selectMode(next: MoneyInputMode) {
  if (props.disabled || mode.value === next) return
  mode.value = next
  emit('mode-change', next)
}

function onInput() {
  emit('input')
}
</script>

<template>
  <div class="w-full space-y-1">
    <div
      class="flex flex-row items-stretch w-full rounded-md border overflow-hidden "
      :class="groupRingClass"
    >
      <!-- Mode toggle (sibling, not inside UInput) -->
      <div
        class="flex shrink-0 flex-row divide-x divide-default border-r border-default bg-muted/40"
        role="group"
        :aria-label="t('pages.pos.cart.discount')"
      >
        <button
          type="button"
          class="px-3 min-w-11 text-xs font-semibold transition-colors disabled:opacity-50 flex items-center justify-center"
          :class="
            mode === 'usd'
              ? 'bg-primary text-inverted'
              : 'text-muted-foreground hover:bg-muted'
          "
          :disabled="disabled"
          @click="selectMode('usd')"
        >
          {{ t('pages.pos.cart.discountUsd') }}
        </button>
        <button
          type="button"
          class="px-3 min-w-9 text-xs font-semibold transition-colors disabled:opacity-50 flex items-center justify-center"
          :class="
            mode === 'percent'
              ? 'bg-primary text-inverted'
              : 'text-muted-foreground hover:bg-muted'
          "
          :disabled="disabled"
          @click="selectMode('percent')"
        >
          {{ t('pages.pos.cart.discountPercent') }}
        </button>
      </div>

      <!-- Number input -->
      <UInput
        v-model.number="inputValue"
        type="number"
        inputmode="decimal"
        :size="size"
        :min="min"
        :max="effectiveMax"
        :step="effectiveStep"
        :disabled="disabled"
        :placeholder="placeholder"
        :color="inputColor"
        class="flex-1 min-w-0 tabular-nums"
        :ui="{
          root: 'w-full',
          base: 'rounded-none border-0 shadow-none ring-0 focus-visible:ring-0'
        }"
        @input="onInput"
      />
    </div>

    <p v-if="errorMessage" class="text-xs text-error">
      {{ errorMessage }}
    </p>
    <p
      v-else-if="showUsdPreview"
      class="text-xs text-muted-foreground text-right tabular-nums"
    >
      = {{ Number(usdPreview ?? 0).toFixed(2) }} USD
    </p>
  </div>
</template>
