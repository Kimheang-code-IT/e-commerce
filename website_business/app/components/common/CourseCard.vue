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

            {{ formattedSalePrice }}

          </p>

          <p

            v-if="hasDiscount"

            class="text-xs font-semibold text-muted line-through sm:text-sm"

          >

            {{ formattedListPrice }}

          </p>

        </div>

      </div>



      <div class="my-2 border-t border-dashed border-black/50 sm:my-3" />



      <ul class="space-y-1 text-xs font-semibold leading-snug sm:text-md">

        <li

          v-for="(row, index) in [

            { key: 'size', label: t('product.spec.size'), value: course.size },

            { key: 'top', label: t('product.spec.top'), value: course.top },

            { key: 'backSide', label: t('product.spec.backSide'), value: course.backSide },

            { key: 'fretboard', label: t('product.spec.fretboard'), value: course.fretboard },

            { key: 'string', label: t('product.spec.string'), value: course.string },

            { key: 'finishing', label: t('product.spec.finishing'), value: course.finishing },

            { key: 'color', label: t('product.spec.color'), value: course.color },

          ]"

          :key="row.key"

          :class="index % 2 === 0 ? 'text-red-600' : 'text-blue-800'"

        >

          - {{ row.label }} : {{ row.value }}

        </li>

      </ul>

    </div>

  </article>

</template>

