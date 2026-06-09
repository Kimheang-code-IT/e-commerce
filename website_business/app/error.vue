<script setup lang="ts">
import type { NuxtError } from '#app'

defineProps<{
  error: NuxtError
}>()

const { locale, t } = useI18n()

useHead({
  htmlAttrs: {
    lang: locale
  }
})

useSeoMeta({
  title: () => t('error.title'),
  description: () => t('error.description'),
  robots: 'noindex, nofollow'
})
</script>

<template>
  <UApp class="bg-default text-default">
    <AppHeader />
    <UError :error="error" />
    <AppFooter />
  </UApp>
</template>
