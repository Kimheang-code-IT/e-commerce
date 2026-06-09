<script setup lang="ts">
import type { CourseCardItem } from '~/components/common/CourseCard.vue'
import { onClickOutside } from '@vueuse/core'

const props = withDefaults(defineProps<{
  placeholder?: string
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
}>(), {
  size: 'xl'
})

const route = useRoute()
const { t } = useI18n()

const searchPlaceholder = computed(() =>
  props.placeholder ?? t('header.searchPlaceholder')
)

const searchQuery = ref('')
const showSearchResults = ref(false)
const resultsTop = ref(0)

const searchRef = useTemplateRef<HTMLElement>('searchRef')
const resultsRef = useTemplateRef<HTMLElement>('resultsRef')

const { allProducts } = useCatalog()

const searchableProducts = computed<CourseCardItem[]>(() => allProducts.value)

const filteredCourses = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return []

  return searchableProducts.value.filter((item) => {
    const haystack = [
      item.model,
      item.name,
      String(item.outPrice ?? ''),
      String(item.discountPrice ?? ''),
      String(item.totalPrice ?? ''),
      item.size,
      item.top,
      item.backSide,
      item.fretboard,
      item.string,
      item.finishing,
      item.color
    ].filter(Boolean).join(' ').toLowerCase()

    return haystack.includes(query)
  }).slice(0, 6)
})

const isResultsVisible = computed(() => showSearchResults.value && !!searchQuery.value.trim())

function updateResultsTop() {
  const el = searchRef.value
  if (!el) return
  resultsTop.value = el.getBoundingClientRect().bottom + 8
}

function openSearchResults() {
  if (searchQuery.value.trim()) {
    showSearchResults.value = true
  }
}

function closeSearchResults() {
  showSearchResults.value = false
}

function selectCourse(course: CourseCardItem) {
  closeSearchResults()
  searchQuery.value = ''

  if (course.category) {
    navigateTo({ path: route.path, query: { category: course.category } })
  }
}

let stopClickOutside: (() => void) | undefined

watch(isResultsVisible, async (visible) => {
  stopClickOutside?.()
  stopClickOutside = undefined
  if (!visible) return

  await nextTick()
  updateResultsTop()
  stopClickOutside = onClickOutside(resultsRef, closeSearchResults, {
    ignore: [searchRef]
  })
})

watch(searchQuery, (value) => {
  showSearchResults.value = !!value.trim()
})

watch(() => route.path, closeSearchResults)

onMounted(() => {
  window.addEventListener('resize', updateResultsTop)
  window.addEventListener('scroll', updateResultsTop, true)
})

onUnmounted(() => {
  stopClickOutside?.()
  window.removeEventListener('resize', updateResultsTop)
  window.removeEventListener('scroll', updateResultsTop, true)
})
</script>

<template>
  <div
    ref="searchRef"
    class="relative min-w-0 flex-1"
  >
    <UInput
      v-model="searchQuery"
      :placeholder="searchPlaceholder"
      :size="size"
      class="w-full"
      :ui="{
        root: 'w-full',
        base: 'rounded-lg border-default bg-elevated pe-10 text-sm placeholder:text-muted'
      }"
      @focus="openSearchResults"
    >
      <template #trailing>
        <UIcon
          name="i-lucide-search"
          class="size-4 text-muted"
        />
      </template>
    </UInput>

    <Teleport to="body">
      <div
        v-if="isResultsVisible"
        ref="resultsRef"
        class="fixed inset-x-0 z-50 border-t border-default bg-default shadow-lg"
        :style="{ top: `${resultsTop}px` }"
      >
        <UContainer class="py-1 sm:py-2">
          <div class="mx-auto w-full max-w-2xl">
            <template v-if="filteredCourses.length">
              <button
                v-for="course in filteredCourses"
                :key="course.id ?? course.model"
                type="button"
                class="flex w-full flex-col gap-0.5 border-b border-default px-4 py-3 text-left transition-colors last:border-b-0 hover:bg-elevated"
                @click="selectCourse(course)"
              >
                <span class="text-sm font-semibold text-highlighted">
                  {{ course.model }}
                </span>
                <span class="text-xs text-muted">
                  {{ course.name }} · {{ course.size }} · {{ course.color }}
                </span>
              </button>
            </template>

            <p
              v-else
              class="px-4 py-3 text-sm text-muted"
            >
              {{ t('search.noResults', { query: searchQuery }) }}
            </p>
          </div>
        </UContainer>
      </div>
    </Teleport>
  </div>
</template>
