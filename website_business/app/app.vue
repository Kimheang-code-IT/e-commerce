<script setup lang="ts">
const { seo } = useAppConfig()
const { locale, t } = useI18n()

const siteName = computed(() => seo?.siteName || t('seo.siteName'))

useHead({
  meta: [
    { name: 'viewport', content: 'width=device-width, initial-scale=1' }
  ],
  link: [
    { rel: 'icon', type: 'image/png', href: '/image/logo.png' }
  ],
  htmlAttrs: {
    lang: locale
  }
})

useSeoMeta({
  title: siteName.value,
  titleTemplate: (titleChunk) => titleChunk || siteName.value,
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
