<script setup lang="ts">
const { t } = useI18n()
const { loadCatalog, categories } = useCatalog()
const { siteName, applyPageSeo } = useSiteSeo()

const route = useRoute()
const initialCategory = typeof route.query.category === 'string' ? route.query.category : ''
await loadCatalog(initialCategory)

const pageTitle = computed(() => {
  const categoryId = typeof route.query.category === 'string' ? route.query.category : ''
  if (!categoryId) return siteName.value
  const category = categories.value.find((item) => item.id === categoryId)
  return category?.name ? `${category.name} | ${siteName.value}` : siteName.value
})

applyPageSeo({
  title: pageTitle.value,
  description: t('home.seoDescription'),
  keywords: t('seo.keywords')
})

watch(pageTitle, (title) => {
  applyPageSeo({
    title,
    description: t('home.seoDescription'),
    keywords: t('seo.keywords')
  })
})
</script>

<template>
  <BookGridBackground>
    <AppHero />

    <UContainer id="products" class="space-y-4">
      <AppGridCard />
    </UContainer>
  </BookGridBackground>
</template>
