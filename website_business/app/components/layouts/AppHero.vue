<script setup lang="ts">
import heroLight from '~/assets/image/herolight.png'
import heroDark from '~/assets/image/herodark.png'

const { t } = useI18n()
const localePath = useLocalePath()
const { allProducts } = useCatalog()

const heroCtaTo = computed(() => localePath({ path: '/', hash: '#products' }))
const productCount = computed(() => {
  const count = allProducts.value.length
  return count > 0 ? `${count}+` : '0'
})
</script>

<template>
  <section class="relative w-full overflow-x-clip text-slate-800 dark:text-white">
    <div
      class="pointer-events-none absolute inset-0 bg-linear-to-b from-white from-20% via-white/90 to-transparent dark:from-[#0f172a] dark:via-[#0f172a]/90 dark:to-transparent"
      aria-hidden="true"
    />

    <UContainer class="relative py-6 sm:py-8 lg:py-12">
      <div class="flex flex-col gap-4 sm:gap-6 lg:grid lg:grid-cols-2 lg:items-center lg:gap-10">
        <div class="order-1 space-y-2 text-center lg:hidden">
          <span
            class="inline-flex rounded-full bg-primary-100 px-3 py-1 text-sm font-medium text-primary-800 dark:bg-white/15 dark:text-white sm:px-4 sm:py-1.5 sm:text-base"
          >
            {{ productCount }} {{ t('hero.productCountSuffix') }}
          </span>

          <h1 class="text-3xl font-bold leading-tight sm:text-4xl md:text-5xl">
            {{ t('hero.title') }}
          </h1>
        </div>

        <div class="order-2 flex justify-center lg:order-2 lg:justify-end">
          <img
            :src="heroLight"
            :alt="t('hero.imageAlt')"
            width="800"
            height="600"
            loading="eager"
            decoding="async"
            class="h-44 w-full max-w-xl object-contain object-center sm:h-64 lg:h-80 dark:hidden"
          >
          <img
            :src="heroDark"
            :alt="t('hero.imageAlt')"
            width="800"
            height="600"
            loading="eager"
            decoding="async"
            class="hidden h-44 w-full max-w-xl object-contain object-center sm:h-64 lg:h-80 dark:block"
          >
        </div>

        <div class="order-3 space-y-4 text-center lg:order-1 lg:text-left">
          <span
            class="hidden rounded-full bg-primary-100 px-3 py-1 text-sm font-medium text-primary-800 lg:inline-flex dark:bg-white/15 dark:text-white sm:px-4 sm:py-1.5 sm:text-base"
          >
            {{ productCount }} {{ t('hero.productCountSuffix') }}
          </span>

          <div class="space-y-3">
            <h1 class="hidden text-3xl font-bold leading-tight lg:block sm:text-4xl lg:text-5xl xl:text-6xl">
              {{ t('hero.title') }}
            </h1>
            <p class="mx-auto max-w-xl text-base leading-relaxed text-slate-600 dark:text-white/90 sm:text-lg lg:mx-0 lg:text-xl">
              {{ t('hero.subtitle') }}
            </p>
          </div>

          <UButton
            :to="heroCtaTo"
            :label="t('hero.cta')"
            size="xl"
            color="primary"
            class="rounded-full px-6 font-semibold sm:px-8"
          />
        </div>
      </div>
    </UContainer>
  </section>
</template>
