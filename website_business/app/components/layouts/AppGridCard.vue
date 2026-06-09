<script setup lang="ts">
const props = withDefaults(defineProps<{
  showTabs?: boolean
}>(), {
  showTabs: true
})

const route = useRoute()
const router = useRouter()
const {
  allProducts,
  categories,
  isLoading,
  isProductsLoading,
  loadError,
  selectCategory,
  isKnownCategory
} = useCatalog()
const { t } = useI18n()
const localePath = useLocalePath()

const activeCategory = computed(() => (route.query.category as string | undefined) ?? '')

const tabs = computed(() => [
  { label: t('product.tabAll'), slug: '', count: null as number | null },
  ...categories.value.map(category => ({
    label: category.name,
    slug: category.id,
    count: category.productCount
  }))
])

const showCategoryTabs = computed(() =>
  props.showTabs && !isLoading.value && !loadError.value && categories.value.length > 0
)

const filteredProducts = computed(() => allProducts.value)

const productsSectionTitle = computed(() => {
  if (!activeCategory.value) return t('product.tabAll')
  const tab = tabs.value.find((item) => item.slug === activeCategory.value)
  return tab?.label || t('product.tabAll')
})

watch(
  () => route.query.category,
  async (value) => {
    const categoryId = typeof value === 'string' ? value : ''
    if (categoryId && !isKnownCategory(categoryId)) {
      await router.replace({ path: route.path, query: {} })
      return
    }
    await selectCategory(categoryId)
  },
  { immediate: true }
)

async function onSelectCategory(slug: string) {
  if (slug === activeCategory.value) return

  await router.replace({
    path: route.path,
    query: slug ? { category: slug } : {}
  })
}
</script>

<template>
  <section class="space-y-6" aria-labelledby="products-heading">
    <h2 id="products-heading" class="sr-only">
      {{ productsSectionTitle }}
    </h2>
    <div
      v-if="showCategoryTabs"
      class="sticky top-16 z-40 -mx-4 border-b border-primary-200 bg-default/95 px-4 pt-4 backdrop-blur-md supports-backdrop-filter:bg-default/90 dark:border-primary-900/50 sm:-mx-6 sm:px-6 lg:-mx-8 lg:px-8"
    >
      <div class="flex gap-6 overflow-x-auto [-ms-overflow-style:none] [scrollbar-none] [&::-webkit-scrollbar]:hidden">
        <button
          v-for="tab in tabs"
          :key="tab.slug || 'all'"
          type="button"
          class="relative shrink-0 whitespace-nowrap px-1 pb-3 text-sm transition-colors sm:text-base"
          :class="activeCategory === tab.slug
            ? 'font-bold text-highlighted'
            : 'font-normal text-muted hover:text-default'"
          :disabled="isProductsLoading"
          @click="onSelectCategory(tab.slug)"
        >
          <span class="inline-flex items-center gap-1.5">
            {{ tab.label }}
            <span
              v-if="tab.count != null"
              class="rounded-full bg-primary-100 px-1.5 py-0.5 text-[10px] font-semibold text-primary-700 dark:bg-primary-900/40 dark:text-primary-200"
            >
              {{ tab.count }}
            </span>
          </span>
          <span
            v-if="activeCategory === tab.slug"
            class="absolute inset-x-0 -bottom-px h-1 rounded-full bg-gold-500"
          />
        </button>
      </div>
    </div>

    <div
      v-if="isLoading || isProductsLoading"
      class="py-12 text-center"
    >
      <UIcon
        name="i-lucide-loader-circle"
        class="mx-auto mb-3 size-8 animate-spin text-muted"
      />
      <p class="text-sm text-muted">
        {{ t('product.loading') }}
      </p>
    </div>

    <div
      v-else-if="loadError"
      class="py-12 text-center"
    >
      <UIcon
        name="i-lucide-wifi-off"
        class="mx-auto mb-3 size-10 text-muted"
      />
      <p class="text-sm text-muted">
        {{ t('product.loadFailed') }}
      </p>
    </div>

    <div
      v-else-if="filteredProducts.length"
      class="grid grid-cols-2 gap-4 md:grid-cols-3 md:gap-6 lg:grid-cols-4"
    >
      <CourseCard
        v-for="product in filteredProducts"
        :key="product.id ?? product.model"
        :course="product"
      />
    </div>

    <div
      v-else
      class="py-12 text-center"
    >
      <UIcon
        name="i-lucide-package"
        class="mx-auto mb-3 size-10 text-muted"
      />
      <p class="text-sm text-muted">
        {{ t('product.emptyCategory') }}
      </p>
      <UButton
        :to="localePath('/')"
        :label="t('product.browseAll')"
        color="primary"
        variant="soft"
        class="mt-4"
        @click="onSelectCategory('')"
      />
    </div>
  </section>
</template>
