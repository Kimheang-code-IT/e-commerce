<script setup lang="ts">
const { footer } = useAppConfig()
const { t } = useI18n()

const currentYear = new Date().getFullYear()

const navLinks = computed(() => footer?.nav ?? [])
const socialLinks = computed(() => footer?.social ?? [])
</script>

<template>
  <footer class="overflow-x-clip bg-[#0a161c] px-3 py-6 text-white sm:px-6 sm:py-10 lg:px-8">
    <UContainer class="max-w-full space-y-5 sm:space-y-8">
      <nav
        v-if="navLinks.length"
        class="footer-scroll flex items-center justify-start gap-x-1.5 overflow-x-auto text-[10px] font-medium uppercase tracking-wide whitespace-nowrap text-white/90 sm:justify-center sm:gap-x-2 sm:text-xs md:text-sm"
        :aria-label="t('a11y.footerNav')"
      >
        <template v-for="(link, index) in navLinks" :key="`${link.slug}-${index}`">
          <span v-if="index > 0" class="shrink-0 text-white/40" aria-hidden="true">|</span>
          <span class="shrink-0">
            {{ t(`footer.nav.${link.slug}`) }}
          </span>
        </template>
      </nav>

      <div class="flex items-center justify-center gap-4 overflow-x-auto whitespace-nowrap sm:justify-center sm:gap-6 lg:gap-8">
        <div v-if="socialLinks.length" class="flex shrink-0 items-center gap-3 sm:gap-4">
          <NuxtLink
            v-for="(link, index) in socialLinks"
            :key="`${link.label}-${index}`"
            :to="link.to"
            target="_blank"
            rel="noopener noreferrer"
            :aria-label="link.label"
            class="shrink-0 text-white/80 transition-colors hover:text-white"
          >
            <UIcon :name="link.icon" class="size-4 sm:size-5" />
          </NuxtLink>
        </div>
      </div>

      <p class="text-center text-[11px] leading-snug text-white/80 sm:text-sm sm:leading-relaxed">
        {{ t('footer.description') }}
      </p>

      <p class="text-center text-[10px] whitespace-nowrap text-white/70 sm:text-sm">
        {{ t('footer.copyright', { year: currentYear }) }}
      </p>
    </UContainer>
  </footer>
</template>

<style scoped>
.footer-scroll {
  scrollbar-width: none;
  -ms-overflow-style: none;
  -webkit-overflow-scrolling: touch;
}

.footer-scroll::-webkit-scrollbar {
  display: none;
}
</style>
