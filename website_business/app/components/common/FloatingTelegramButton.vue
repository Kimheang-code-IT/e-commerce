<script setup lang="ts">
const { floatingTelegram } = useAppConfig()

const telegramUrl = computed(() => floatingTelegram?.to ?? '')
</script>

<template>
  <a
    v-if="floatingTelegram?.enabled !== false && telegramUrl"
    :href="telegramUrl"
    target="_blank"
    rel="noopener noreferrer"
    aria-label="Telegram"
    class="fixed bottom-6 right-4 z-50 flex size-14 items-center justify-center rounded-full bg-[#26A5E4] text-white shadow-lg ring-1 ring-black/5 transition-transform hover:scale-105 hover:bg-[#1f95d0] active:scale-95"
  >
    <UIcon
      name="i-simple-icons-telegram"
      class="size-7"
    />
  </a>
</template>
