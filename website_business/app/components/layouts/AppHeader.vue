<script setup lang="ts">
const { header, seo } = useAppConfig()
const { t } = useI18n()
const localePath = useLocalePath()

const siteTitle = computed(() => header?.title || seo?.siteName || t('seo.siteName'))
</script>

<template>
  <header class="relative overflow-visible bg-default">
    <UContainer class="flex h-16 items-center gap-1 overflow-visible sm:gap-4">
      <NuxtLink
        :to="localePath(header?.to || '/')"
        :aria-label="siteTitle"
      >
        <AppLogo />
      </NuxtLink>

      <div class="flex min-w-0 flex-1 justify-center overflow-visible pr-1 sm:px-2 lg:px-6">
        <HeaderSearch class="min-w-0 flex-1 max-w-2xl" />
      </div>

      <div class="ml-auto flex shrink-0 items-center gap-1 sm:gap-2">
        <LocaleToggle />
      </div>
    </UContainer>
  </header>
</template>
