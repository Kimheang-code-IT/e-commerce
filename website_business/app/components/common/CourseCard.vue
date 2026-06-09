<script lang="ts">
export interface CourseCardItem {
  id?: string
  category?: string
  image?: string
  model: string
  name: string
  discountPrice?: string | number
  totalPrice: string | number
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
const props = defineProps<{
  course: CourseCardItem
}>()

const { t } = useI18n()

function formatPrice(price: string | number) {
  if (typeof price === 'number') {
    return `$ ${price.toLocaleString()}`
  }
  return price.startsWith('$') ? price : `$ ${price}`
}

const formattedDiscountPrice = computed(() => {
  const price = props.course.discountPrice ?? props.course.totalPrice
  return formatPrice(price)
})

const formattedTotalPrice = computed(() => formatPrice(props.course.totalPrice))

const hasDiscount = computed(() => {
  const { discountPrice, totalPrice } = props.course
  if (discountPrice == null) return false
  return String(discountPrice) !== String(totalPrice)
})

const specRows = computed(() => [
  { key: 'size', label: t('product.spec.size'), value: props.course.size },
  { key: 'top', label: t('product.spec.top'), value: props.course.top },
  { key: 'backSide', label: t('product.spec.backSide'), value: props.course.backSide },
  { key: 'fretboard', label: t('product.spec.fretboard'), value: props.course.fretboard },
  { key: 'string', label: t('product.spec.string'), value: props.course.string },
  { key: 'finishing', label: t('product.spec.finishing'), value: props.course.finishing },
  { key: 'color', label: t('product.spec.color'), value: props.course.color }
])
</script>

<template>
  <article class="flex flex-col overflow-hidden rounded-sm border border-default bg-elevated shadow-sm">
    <div class="relative h-32 w-full overflow-hidden bg-gray-900 sm:h-44 md:h-52 lg:h-60">
      <AppImage
        :src="course.image"
        :alt="course.model"
        class="size-full object-cover"
        width="640"
        height="240"
      />
    </div>

    <div class="flex flex-1 flex-col bg-white px-2 py-3 text-black sm:px-3 sm:py-4">
      <div class="text-center">
        <h3 class="text-sm font-bold uppercase leading-snug text-red-600 sm:text-xs md:text-sm">
          {{ course.model }}
        </h3>
        <p class="mt-1 text-sm font-semibold uppercase leading-snug text-blue-800 sm:text-xs">
          {{ course.name }}
        </p>

        <div class="mt-1.5 flex flex-wrap items-baseline justify-center gap-x-2 gap-y-0.5">
          <p class="text-lg font-bold leading-none text-red-600 sm:text-xl">
            {{ formattedDiscountPrice }}
          </p>
          <p
            v-if="hasDiscount"
            class="text-xs font-semibold text-muted line-through sm:text-sm"
          >
            {{ formattedTotalPrice }}
          </p>
        </div>
      </div>

      <div class="my-2 border-t border-dashed border-black/50 sm:my-3" />

      <ul class="space-y-1 text-[10px] font-semibold leading-snug sm:text-sm">
        <li
          v-for="(row, index) in specRows"
          :key="row.key"
          :class="index % 2 === 0 ? 'text-red-600' : 'text-blue-800'"
        >
          - {{ row.label }} : {{ row.value }}
        </li>
      </ul>
    </div>
  </article>
</template>
