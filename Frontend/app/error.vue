<script setup lang="ts">
import * as locales from '@nuxt/ui/locale'
import type { NuxtError } from '#app'

const props = defineProps<{
  error: NuxtError
}>()

const { t, locale } = useI18n()

const currentLocale = computed(() => locales[locale.value as keyof typeof locales])
const lang = computed(() => locales[locale.value as keyof typeof locales]?.code || locale.value)
const dir = computed(() => locales[locale.value as keyof typeof locales]?.dir || 'ltr')

const statusCode = computed(() => Number(props.error?.statusCode) || 500)
const isNotFound = computed(() => statusCode.value === 404)

const seoTitle = computed(() =>
  isNotFound.value ? t('pages.error.seoTitle404') : t('pages.error.seoTitleGeneric')
)
const seoDescription = computed(() =>
  isNotFound.value ? t('pages.error.seoDescription404') : t('pages.error.seoDescriptionGeneric')
)

useSeoMeta({
  title: seoTitle,
  description: seoDescription
})

useHead({
  htmlAttrs: {
    lang,
    dir
  }
})

const displayError = computed(() => {
  const code = statusCode.value

  if (code === 404) {
    return {
      statusCode: code,
      statusMessage: t('pages.error.notFoundTitle'),
      message: t('pages.error.notFoundMessage')
    }
  }

  if (code === 403) {
    return {
      statusCode: code,
      statusMessage: t('pages.error.forbiddenTitle'),
      message: t('pages.error.forbiddenMessage')
    }
  }

  if (code >= 500) {
    return {
      statusCode: code,
      statusMessage: t('pages.error.serverErrorTitle'),
      message: t('pages.error.serverErrorMessage')
    }
  }

  return {
    statusCode: code,
    statusMessage: t('pages.error.genericTitle'),
    message: props.error?.message || t('pages.error.genericMessage')
  }
})

const clearButton = computed(() => ({
  label: t('pages.error.backHome')
}))
</script>

<template>
  <UApp :locale="currentLocale">
    <UError :error="displayError" :clear="clearButton" />
  </UApp>
</template>
