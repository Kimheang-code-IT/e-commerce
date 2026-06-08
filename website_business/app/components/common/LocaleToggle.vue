<script setup lang="ts">
withDefaults(defineProps<{
  variant?: 'dark' | 'default'
}>(), {
  variant: 'default'
})

const { locale, setLocale, t } = useI18n()

const languages = [
  { code: 'en' as const, labelKey: 'a11y.localeEn' },
  { code: 'km' as const, labelKey: 'a11y.localeKm' }
]

async function switchTo(code: 'en' | 'km') {
  if (locale.value !== code) {
    await setLocale(code)
  }
}
</script>

<template>
  <div
    class="flex shrink-0 items-center rounded-md p-0.5"
    :class="variant === 'dark' ? 'bg-white/10' : 'bg-muted'"
    role="group"
    :aria-label="t('a11y.changeLanguage')"
  >
    <button
      v-for="lang in languages"
      :key="lang.code"
      type="button"
      class="rounded px-2 py-1 text-[11px] font-semibold transition-colors sm:text-xs"
      :class="locale === lang.code
        ? variant === 'dark'
          ? 'bg-white/25 text-white'
          : 'bg-elevated text-highlighted shadow-sm'
        : variant === 'dark'
          ? 'text-white/70 hover:text-white'
          : 'text-muted hover:text-default'"
      :aria-pressed="locale === lang.code"
      @click="switchTo(lang.code)"
    >
      {{ t(lang.labelKey) }}
    </button>
  </div>
</template>
