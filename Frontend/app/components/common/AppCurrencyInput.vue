<script setup lang="ts">
const model = defineModel<number>({ required: true })

const props = withDefaults(
  defineProps<{
    min?: number
    max?: number
    step?: number
    size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
    disabled?: boolean
    /** i18n key or plain message shown when invalid */
    errorMessage?: string
  }>(),
  {
    min: 0,
    step: 0.01,
    size: 'lg'
  }
)

const { t } = useI18n()

const numericValue = computed(() => Number(model.value ?? 0))

const validationError = computed(() => {
  if (props.errorMessage) return props.errorMessage
  const v = numericValue.value
  if (!Number.isFinite(v)) return t('pages.pos.validation.numberRequired')
  if (v < (props.min ?? 0)) return t('pages.pos.validation.minUsd', { min: props.min ?? 0 })
  if (props.max != null && v > props.max) {
    return t('pages.pos.validation.maxUsd', { max: props.max })
  }
  return ''
})

const inputColor = computed(() => (validationError.value ? 'error' : undefined))
</script>

<template>
  <div class="w-full space-y-1">
    <UInput
      v-model.number="model"
      type="number"
      :size="size"
      :min="min"
      :max="max"
      :step="step"
      :disabled="disabled"
      :color="inputColor"
      class="w-full tabular-nums"
      :ui="{ trailing: 'pe-2' }"
    >
      <template #trailing>
        <span class="text-xs font-semibold text-muted-foreground select-none">USD</span>
      </template>
    </UInput>
    <p v-if="validationError" class="text-xs text-error">
      {{ validationError }}
    </p>
  </div>
</template>
