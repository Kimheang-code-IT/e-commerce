<script setup lang="ts">
import { buildCatalogJsonLd } from '~/utils/seo/structured-data'

const { t, locale } = useI18n()
const { loadCatalog, categories, allProducts } = useCatalog()
const { siteName, siteUrl, apiBase, applyPageSeo, resolvePageImage } = useSiteSeo()

const route = useRoute()
const initialCategory = typeof route.query.category === 'string' ? route.query.category : ''
await loadCatalog(initialCategory)

const activeCategoryId = computed(() =>
  typeof route.query.category === 'string' ? route.query.category : ''
)

const activeCategory = computed(() =>
  categories.value.find((item) => item.id === activeCategoryId.value)
)

const pageTitle = computed(() => {
  if (!activeCategory.value?.name) return siteName.value
  return `${activeCategory.value.name} | ${siteName.value}`
})

const pageDescription = computed(() => {
  if (activeCategory.value?.name) {
    return t('seo.categoryDescription', { category: activeCategory.value.name })
  }
  return t('home.seoDescription')
})

const pageKeywords = computed(() => {
  if (activeCategory.value?.name) {
    return `${t('seo.keywords')}, ${activeCategory.value.name}`
  }
  return t('seo.keywords')
})

const pageImage = computed(() => {
  if (activeCategory.value) {
    const firstWithImage = allProducts.value.find((item) => String(item.image || '').trim())
    if (firstWithImage?.image) return resolvePageImage(firstWithImage.image)
  }
  return resolvePageImage('/image/favicon-192.png')
})

const pageJsonLd = computed(() =>
  buildCatalogJsonLd({
    siteUrl: siteUrl.value || 'https://anyamusicschool.com',
    siteName: siteName.value,
    description: pageDescription.value,
    products: allProducts.value,
    apiBase: apiBase.value,
    categoryName: activeCategory.value?.name,
    sameAs: (useAppConfig().social || []).map((link: { to: string }) => link.to).filter(Boolean)
  })
)

function syncPageSeo() {
  applyPageSeo({
    title: pageTitle.value,
    description: pageDescription.value,
    keywords: pageKeywords.value,
    image: pageImage.value,
    imageAlt: activeCategory.value?.name
      ? t('seo.categoryOgImageAlt', { category: activeCategory.value.name })
      : t('seo.defaultOgImageAlt'),
    jsonLd: pageJsonLd.value
  })
}

syncPageSeo()

watch([pageTitle, pageDescription, pageKeywords, pageImage, pageJsonLd, locale], syncPageSeo)
</script>

<template>
  <BookGridBackground>
    <AppHero />

    <UContainer id="products" class="space-y-4">
      <AppGridCard />
    </UContainer>
  </BookGridBackground>
</template>
