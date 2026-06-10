<script lang="ts">
export interface CourseCardItem {
  id?: string
  category?: string
  image?: string
  model: string
  name: string
  /** Public list price (from admin out price). */
  outPrice?: string | number
  discountPrice?: string | number
  totalPrice?: string | number
  size: string
  top: string
  backSide: string
  fretboard: string
  string: string
  finishing: string
  color: string
}
</script>

<script setup lang="ts">
import { useSocialLinks } from '~/composables/useSocialLinks'

const props = defineProps<{
  course: CourseCardItem
}>()

const { t } = useI18n()
const socialLinks = useSocialLinks()

function formatPrice(price: string | number) {
  if (typeof price === 'number') {
    return `$ ${price.toLocaleString()}`
  }
  return price.startsWith('$') ? price : `$ ${price}`
}

const listPrice = computed(() => {
  const out = props.course.outPrice
  if (out != null && String(out).trim() !== '') return Number(out)
  return Number(props.course.totalPrice ?? 0)
})

const salePrice = computed(() => {
  const list = listPrice.value
  const sale = Number(props.course.discountPrice ?? 0)
  if (sale > 0 && sale < list) return sale
  return list
})

const formattedSalePrice = computed(() => formatPrice(salePrice.value))
const formattedListPrice = computed(() => formatPrice(listPrice.value))
const hasDiscount = computed(() => salePrice.value < listPrice.value)

const imageAlt = computed(() =>
  t('seo.productImageAlt', {
    model: props.course.model,
    name: props.course.name
  })
)

const specRows = computed(() => [
  { key: 'size', label: t('product.spec.size'), value: props.course.size },
  { key: 'top', label: t('product.spec.top'), value: props.course.top },
  { key: 'backSide', label: t('product.spec.backSide'), value: props.course.backSide },
  { key: 'fretboard', label: t('product.spec.fretboard'), value: props.course.fretboard },
  { key: 'string', label: t('product.spec.string'), value: props.course.string },
  { key: 'finishing', label: t('product.spec.finishing'), value: props.course.finishing },
  { key: 'color', label: t('product.spec.color'), value: props.course.color },
])
</script>

<template>
  <article
    class="flex w-full flex-col overflow-hidden rounded-sm border border-default bg-elevated shadow-sm"
    :aria-label="`${course.model} ${course.name}`"
  >
    <div
      class="relative flex w-full aspect-[3/4] items-center justify-center overflow-hidden bg-gray-900 sm:aspect-[4/5] md:aspect-[3/4] lg:aspect-[4/5]"
    >
      <AppImage
        :src="course.image"
        :alt="imageAlt"
        :title="imageAlt"
        class="size-full object-contain object-center"
        width="640"
        height="800"
        sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"
      />
    </div>

    <div class="flex flex-1 flex-col bg-white px-3 py-4 text-black sm:px-4 sm:py-5">
      <div class="text-center">
        <h3 class="text-base font-bold uppercase leading-snug text-red-600 sm:text-lg md:text-xl">
          {{ course.model }}
        </h3>
        <p class="mt-1.5 text-sm font-semibold uppercase leading-snug text-blue-800 sm:text-base md:text-lg">
          {{ course.name }}
        </p>

        <div
          class="mt-2 flex flex-wrap items-baseline justify-center gap-x-2 gap-y-1 sm:mt-2.5"
          :aria-label="hasDiscount
            ? t('seo.priceWithDiscount', { sale: formattedSalePrice, list: formattedListPrice })
            : t('seo.priceLabel', { price: formattedSalePrice })"
        >
          <p class="text-xl font-bold leading-none text-red-600 sm:text-2xl md:text-3xl" aria-hidden="true">
            {{ formattedSalePrice }}
          </p>
          <p
            v-if="hasDiscount"
            class="text-sm font-semibold text-muted line-through sm:text-base md:text-lg"
            aria-hidden="true"
          >
            {{ formattedListPrice }}
          </p>
        </div>
      </div>

      <div class="my-3 border-t border-dashed border-black/50 sm:my-4" />

      <ul class="space-y-1 text-sm font-semibold leading-relaxed sm:text-base md:text-lg">
        <li
          v-for="(row, index) in specRows"
          :key="row.key"
          :class="index % 2 === 0 ? 'text-red-600' : 'text-blue-800'"
        >
          - {{ row.label }} : {{ row.value }}
        </li>
      </ul>

      <div
        v-if="socialLinks.length"
        class="mt-4 flex flex-wrap items-center justify-center gap-2 border-t border-dashed border-black/30 pt-3"
      >
        <a
          v-for="link in socialLinks"
          :key="link.label"
          :href="link.to"
          target="_blank"
          rel="noopener noreferrer"
          :aria-label="link.label"
          :title="link.label"
          :class="[
            'flex size-8 items-center justify-center rounded-md text-white transition-colors',
            link.class
          ]"
        >
          <UIcon :name="link.icon" class="size-4" />
        </a>
      </div>
    </div>
  </article>
</template>
