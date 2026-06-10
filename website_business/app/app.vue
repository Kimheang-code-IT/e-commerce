<script setup lang="ts">
const config = useRuntimeConfig()
const { seo } = useAppConfig()
const { locale, t } = useI18n()

const siteName = computed(() => seo?.siteName || t('seo.siteName'))
const siteUrl = computed(() => String(config.public.siteUrl || '').replace(/\/+$/, ''))

useHead({
  meta: [
    { name: 'viewport', content: 'width=device-width, initial-scale=1' },
    { name: 'theme-color', content: '#0a161c' },
    { name: 'format-detection', content: 'telephone=no' },
    { name: 'application-name', content: siteName.value },
    { name: 'apple-mobile-web-app-title', content: siteName.value },
    { name: 'apple-mobile-web-app-capable', content: 'yes' },
    { name: 'mobile-web-app-capable', content: 'yes' }
  ],
  link: [
    { rel: 'icon', type: 'image/png', href: '/image/logo.png' },
    { rel: 'apple-touch-icon', href: '/image/logoapp.png' },
    { rel: 'manifest', href: '/site.webmanifest' },
    ...(siteUrl.value ? [{ rel: 'sitemap', type: 'application/xml', href: `${siteUrl.value}/sitemap.xml` }] : [])
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
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>

    <FloatingTelegramButton />
  </UApp>
</template>
