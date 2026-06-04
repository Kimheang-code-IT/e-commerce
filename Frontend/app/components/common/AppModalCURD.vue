<script setup lang="ts">
import { computed } from 'vue'

const { t } = useI18n()
const open = defineModel<boolean>('open')

interface Props {
  title?: string
  titleKey?: string
  description?: string
  descriptionKey?: string
  descriptionParams?: Record<string, string | number>
  submitLabel?: string
  submitLabelKey?: string
  cancelLabel?: string
  cancelLabelKey?: string
  type?: 'primary' | 'error' | 'warning' | 'neutral'
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  type: 'primary',
  loading: false
})

const emit = defineEmits<{
  (e: 'submit'): void
  (e: 'cancel'): void
}>()

const typeConfig = computed(() => {
  switch (props.type) {
    case 'error':
      return {
        color: 'error' as const
      }
    case 'warning':
      return {
        color: 'warning' as const
      }
    case 'primary':
      return {
        color: 'primary' as const
      }
    default:
      return {
        color: 'neutral' as const
      }
  }
})

const modalUi = {
  content: 'max-w-md w-[95vw] sm:w-full',
  description: 'whitespace-pre-line'
} as const

const resolvedTitle = computed(() => {
  if (props.titleKey) return t(props.titleKey)
  return props.title || t('components.confirmAction')
})
const resolvedDescription = computed(() => {
  if (props.descriptionKey) {
    return t(props.descriptionKey, props.descriptionParams ?? {})
  }
  return props.description || t('components.confirmDesc')
})
const resolvedCancelLabel = computed(() => {
  if (props.cancelLabelKey) return t(props.cancelLabelKey)
  return props.cancelLabel || t('components.cancel')
})
const resolvedSubmitLabel = computed(() => {
  if (props.submitLabelKey) return t(props.submitLabelKey)
  return props.submitLabel || t('components.proceed')
})

function onCancel() {
  if (props.loading) return
  open.value = false
  emit('cancel')
}

function onSubmit() {
  if (props.loading) return
  emit('submit')
}
</script>

<template>
  <UModal
    v-model:open="open"
    :title="resolvedTitle"
    :description="resolvedDescription"
    :dismissible="false"
    :ui="modalUi"
    @close:prevent="onCancel"
  >
    <template #close>
      <UButton
        icon="i-lucide-x"
        color="neutral"
        variant="ghost"
        size="md"
        :disabled="loading"
        @click="onCancel"
      />
    </template>

    <template v-if="$slots.default" #body>
      <slot />
    </template>

    <template #footer>
      <div class="flex items-center justify-end gap-3 w-full">
        <UButton
          :label="resolvedCancelLabel"
          color="neutral"
          variant="soft"
          size="lg"
          class="font-semibold"
          :disabled="loading"
          @click="onCancel"
        />
        <UButton
          :label="resolvedSubmitLabel"
          :color="typeConfig.color"
          variant="solid"
          size="lg"
          class="font-semibold"
          :loading="loading"
          @click="onSubmit"
        />
      </div>
    </template>
  </UModal>
</template>
