<script setup lang="ts">
import { modalUiTable, dialogBody, dialogHeader } from '~/utils/ui/overlayUi'

const open = defineModel<boolean>('open', { default: false })

withDefaults(
  defineProps<{
    title?: string
    density?: 'default' | 'compact'
  }>(),
  {
    title: '',
    density: 'compact',
  },
)
</script>

<template>
  <UModal v-model:open="open" :dismissible="false" :ui="modalUiTable">
    <template #header>
      <div :class="dialogHeader">
        <div class="min-w-0 flex-1 space-y-1">
          <h3 v-if="title" class="font-semibold text-base sm:text-lg line-clamp-2">
            {{ title }}
          </h3>
          <slot name="header-meta" />
        </div>
        <div class="flex flex-wrap items-center gap-2 w-full sm:w-auto sm:shrink-0">
          <slot name="header-actions" />
          <UButton
            icon="i-lucide-x"
            color="neutral"
            variant="ghost"
            size="sm"
            class="shrink-0 ms-auto sm:ms-0"
            :aria-label="$t('components.cancel')"
            @click="open = false"
          />
        </div>
      </div>
    </template>

    <template #body>
      <div :class="dialogBody">
        <div class="overflow-x-auto overscroll-x-contain min-h-0 h-full flex flex-col">
          <slot :density="density" />
        </div>
      </div>
    </template>

    <template v-if="$slots.footer" #footer>
      <div class="overlay-safe-footer w-full">
        <slot name="footer" />
      </div>
    </template>
  </UModal>
</template>
