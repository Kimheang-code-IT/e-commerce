<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { breakpointsTailwind, onClickOutside, useBreakpoints } from '@vueuse/core'

const modelValue = defineModel<string>()
const expanded = defineModel<boolean>('expanded', { default: false })

const props = withDefaults(
  defineProps<{
    placeholder?: string
    /** Icon-only on mobile; tap to expand full-width search. */
    expandableOnMobile?: boolean
    desktopWidthClass?: string
  }>(),
  {
    expandableOnMobile: true,
    desktopWidthClass: 'w-52',
  },
)

const { t } = useI18n()
const breakpoints = useBreakpoints(breakpointsTailwind)
const isMobile = breakpoints.smaller('sm')
const rootRef = ref<HTMLElement | null>(null)

const useExpandableMobile = computed(
  () => props.expandableOnMobile && isMobile.value,
)

function openSearch() {
  expanded.value = true
  nextTick(() => {
    rootRef.value?.querySelector('input')?.focus()
  })
}

function closeSearch() {
  expanded.value = false
}

onClickOutside(rootRef, () => {
  if (useExpandableMobile.value && expanded.value) {
    closeSearch()
  }
})

watch(modelValue, (value) => {
  if (useExpandableMobile.value && String(value || '').trim()) {
    expanded.value = true
  }
})

watch(isMobile, (mobile) => {
  if (!mobile) {
    expanded.value = false
  }
})
</script>

<template>
  <div
    ref="rootRef"
    class="flex items-center shrink-0 min-w-0"
    :class="[
      useExpandableMobile && expanded ? 'w-full' : '',
      !useExpandableMobile ? desktopWidthClass : '',
    ]"
  >
    <ClientOnly>
      <template v-if="!useExpandableMobile">
        <UInput
          v-model="modelValue"
          :placeholder="placeholder || $t('common.search')"
          icon="i-lucide-search"
          class="w-full font-medium text-highlighted"
          size="md"
          v-bind="$attrs"
          :ui="{ trailing: 'pe-1' }"
        >
          <template v-if="modelValue?.length" #trailing>
            <UButton
              color="neutral"
              variant="link"
              size="sm"
              icon="i-lucide-circle-x"
              :aria-label="$t('components.clear')"
              @click="modelValue = ''"
            />
          </template>
        </UInput>
      </template>
      <template v-else-if="!expanded">
        <UButton
          icon="i-lucide-search"
          color="neutral"
          variant="soft"
          size="md"
          square
          :aria-label="placeholder || $t('common.search')"
          @click="openSearch"
        />
      </template>
      <template v-else>
        <div class="flex items-center gap-1.5 w-full min-w-0">
          <UInput
            v-model="modelValue"
            :placeholder="placeholder || $t('common.search')"
            icon="i-lucide-search"
            class="flex-1 min-w-0 font-medium text-highlighted"
            size="md"
            v-bind="$attrs"
            :ui="{ trailing: 'pe-1' }"
          >
            <template v-if="modelValue?.length" #trailing>
              <UButton
                color="neutral"
                variant="link"
                size="sm"
                icon="i-lucide-circle-x"
                :aria-label="$t('components.clear')"
                @click="modelValue = ''"
              />
            </template>
          </UInput>
          <UButton
            icon="i-lucide-x"
            color="neutral"
            variant="ghost"
            size="sm"
            square
            :aria-label="$t('components.cancel')"
            @click="closeSearch"
          />
        </div>
      </template>
    </ClientOnly>
  </div>
</template>
