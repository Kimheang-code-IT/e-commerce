<script setup lang="ts">
import {
  modalUiTable,
  dialogBody,
  dialogHeaderRow,
  dialogHeaderMeta,
  dialogFooter,
} from '~/utils/ui/overlayUi'

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
      <div class="w-full">
        <div :class="dialogHeaderRow">
          <h3
            v-if="title"
            class="flex-1 min-w-0 text-sm sm:text-base font-semibold truncate"
          >
            {{ title }}
          </h3>
          <div class="flex items-center gap-1 shrink-0">
            <slot name="header-actions" />
            <UButton
              icon="i-lucide-x"
              color="neutral"
              variant="ghost"
              size="sm"
              square
              :aria-label="$t('components.cancel')"
              @click="open = false"
            />
          </div>
        </div>
        <div v-if="$slots['header-meta']" :class="dialogHeaderMeta">
          <slot name="header-meta" />
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
      <div :class="dialogFooter">
        <slot name="footer" />
      </div>
    </template>
  </UModal>
</template>
