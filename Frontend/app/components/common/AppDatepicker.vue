<script setup lang="ts">
import { breakpointsTailwind, useBreakpoints } from '@vueuse/core'

const { t } = useI18n()
const { dateRange: globalRange, resetRange: globalReset } = useGlobalFilter()

const props = withDefaults(
  defineProps<{
    range?: { start: any; end: any }
    /** Calendar trigger: icon + chevrons on mobile only. */
    iconOnlyOnMobile?: boolean
  }>(),
  {
    iconOnlyOnMobile: false,
  },
)

const emit = defineEmits<{
  (e: 'update:range', val: { start: any; end: any }): void
}>()

const isMobile = useBreakpoints(breakpointsTailwind).smaller('sm')
const isIconOnly = computed(() => props.iconOnlyOnMobile && isMobile.value)

const dateRange = computed({
  get: () => (props.range !== undefined ? props.range : globalRange.value),
  set: (val) => {
    if (props.range !== undefined) emit('update:range', val)
    else globalRange.value = val
  },
})

const resetRange = () => {
  if (props.range !== undefined) emit('update:range', { start: undefined, end: undefined })
  else globalReset()
}

function formatRangeDate(value: { toString: () => string } | undefined) {
  if (!value) return ''
  return new Date(value.toString()).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  })
}
</script>

<template>
  <UPopover :content="{ align: 'end' }">
    <UButton
      color="neutral"
      variant="subtle"
      icon="i-lucide-calendar"
      :trailing-icon="isIconOnly ? 'i-lucide-chevrons-up-down' : 'i-lucide-chevron-down'"
      :square="isIconOnly"
      :size="isIconOnly ? 'sm' : 'md'"
      class="shrink-0 font-normal"
      :class="isIconOnly ? 'w-9 px-0' : ''"
      :aria-label="t('components.pickDate')"
    >
      <span v-if="!isIconOnly" class="hidden sm:inline-flex items-center gap-1 ml-1.5">
        <template v-if="dateRange.start">
          <template v-if="dateRange.end">
            <span class="text-xs opacity-70">{{ formatRangeDate(dateRange.start) }}</span>
            <span class="mx-1 text-primary">→</span>
            <span class="text-xs font-bold">{{ formatRangeDate(dateRange.end) }}</span>
          </template>
          <template v-else>
            {{ formatRangeDate(dateRange.start) }}
          </template>
        </template>
        <template v-else>
          {{ t('components.pickDate') }}
        </template>
      </span>
    </UButton>

    <template #content>
      <div class="flex flex-col bg-background rounded-lg overflow-hidden min-w-[200px]">
        <UCalendar
          v-model="dateRange"
          class="p-2"
          :number-of-months="1"
          range
        />
        <div class="p-4 bg-muted/20 border-t flex flex-col gap-2 justify-end">
          <UButton
            :label="t('components.reset')"
            size="xs"
            variant="ghost"
            color="neutral"
            icon="i-lucide-rotate-ccw"
            @click="resetRange"
          />
        </div>
      </div>
    </template>
  </UPopover>
</template>
