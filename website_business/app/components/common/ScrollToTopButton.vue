<script setup lang="ts">
import { useWindowScroll } from '@vueuse/core'

const { t } = useI18n()
const { y } = useWindowScroll()

const isVisible = computed(() => y.value > 320)

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>

<template>
  <Transition
    enter-active-class="transition duration-200 ease-out"
    enter-from-class="translate-y-2 opacity-0"
    enter-to-class="translate-y-0 opacity-100"
    leave-active-class="transition duration-150 ease-in"
    leave-from-class="translate-y-0 opacity-100"
    leave-to-class="translate-y-2 opacity-0"
  >
    <button
      v-show="isVisible"
      type="button"
      class="fixed bottom-24 right-4 z-50 flex size-12 items-center justify-center rounded-full border border-default bg-default text-default shadow-lg ring-1 ring-black/5 transition-transform hover:scale-105 active:scale-95 dark:bg-elevated"
      :aria-label="t('a11y.scrollToTop')"
      @click="scrollToTop"
    >
      <UIcon name="i-lucide-arrow-up" class="size-5" />
    </button>
  </Transition>
</template>
