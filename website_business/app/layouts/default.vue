<script setup lang="ts">
const { t } = useI18n()
</script>

<template>
  <div class="flex min-h-dvh w-full max-w-full flex-col overflow-x-clip bg-default text-default">
    <a
      href="#products"
      class="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-100 focus:rounded-md focus:bg-primary-600 focus:px-4 focus:py-2 focus:text-white focus:outline-none"
    >
      {{ t('a11y.skipToProducts') }}
    </a>

    <AppBanner class="relative z-50" />

    <div class="sticky top-0 z-50 overflow-x-clip border-b border-default bg-default">
      <AppHeader />
    </div>

    <UMain class="flex-1 max-w-full overflow-x-clip bg-default mb-10">
      <slot />
    </UMain>

    <AppFooter />
  </div>
</template>
