<script setup lang="ts">
const { seo } = useAppConfig()
const { locale, t } = useI18n()

const siteName = computed(() => seo?.siteName || t('seo.siteName'))

useHead({
  meta: [
    { name: 'viewport', content: 'width=device-width, initial-scale=1' }
  ],
  link: [
    { rel: 'icon', href: '/favicon.ico' }
  ],
  htmlAttrs: {
    lang: locale
  }
})

useSeoMeta({
  titleTemplate: `%s - ${siteName.value}`,
  ogSiteName: siteName.value,
  twitterCard: 'summary_large_image',
  robots: 'index, follow, max-image-preview:large'
})
</script>

<template>
  <UApp class="w-full max-w-full overflow-x-clip">
    <NuxtLoadingIndicator />

    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>

    <FloatingTelegramButton />
  </UApp>
</template>
