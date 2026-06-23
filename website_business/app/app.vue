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
    { rel: 'icon', href: '/favicon.ico', sizes: '48x48' },
    { rel: 'icon', type: 'image/png', sizes: '48x48', href: '/image/favicon-48.png' },
    { rel: 'icon', type: 'image/png', sizes: '96x96', href: '/image/favicon-96.png' },
    { rel: 'icon', type: 'image/png', sizes: '192x192', href: '/image/favicon-192.png' },
    { rel: 'apple-touch-icon', sizes: '192x192', href: '/image/favicon-192.png' },
    { rel: 'manifest', href: '/site.webmanifest' },
    ...(siteUrl.value ? [{ rel: 'sitemap', type: 'application/xml', href: `${siteUrl.value}/sitemap.xml` }] : [])
  ],
  htmlAttrs: {
    lang: locale
  }
})

useSeoMeta({
  titleTemplate: (titleChunk) => {
    if (!titleChunk || titleChunk === siteName.value) return siteName.value
    return `${titleChunk} | ${siteName.value}`
  },
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
