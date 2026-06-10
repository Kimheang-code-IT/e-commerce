<script setup lang="ts">
import type { Reward } from '~/types'

const props = defineProps<{
  reward: Reward
}>()

const emit = defineEmits<{
  (e: 'add'): void
}>()

const { t } = useI18n()

const productSummary = computed(() =>
  (props.reward.products || [])
    .map((p) => p.name)
    .filter(Boolean)
    .join(', '),
)
</script>

<template>
  <UCard class="shadow-sm border border-default hover:border-primary/40 transition-colors">
    <div class="flex flex-col gap-3 p-1">
      <div class="flex items-start justify-between gap-2">
        <div class="min-w-0">
          <h3 class="font-semibold text-sm truncate">{{ reward.name }}</h3>
          <p class="text-xs text-muted mt-1 line-clamp-2">{{ productSummary }}</p>
        </div>
        <UBadge color="success" variant="subtle" size="xs">{{ t('pages.pos.rewards.free') }}</UBadge>
      </div>
      <UButton color="primary" variant="soft" block size="sm" icon="i-lucide-gift" @click="emit('add')">
        {{ t('pages.pos.rewards.addToCart') }}
      </UButton>
    </div>
  </UCard>
</template>
