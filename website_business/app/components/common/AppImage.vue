<script setup lang="ts">
const DEFAULT_FALLBACK = 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=640&q=80'

const props = withDefaults(defineProps<{
  src?: string
  alt?: string
  title?: string
  fallback?: string
  width?: number | string
  height?: number | string
  sizes?: string
  loading?: 'lazy' | 'eager'
  fetchpriority?: 'high' | 'low' | 'auto'
}>(), {
  alt: '',
  fallback: DEFAULT_FALLBACK,
  loading: 'lazy',
  fetchpriority: 'auto'
})

const hasError = ref(false)

const displaySrc = computed(() => {
  const primary = props.src?.trim()

  if (hasError.value || !primary) {
    return props.fallback
  }

  return primary
})

const isRemoteImage = computed(() => /^https?:\/\//.test(displaySrc.value))

const resolvedFetchPriority = computed(() => {
  if (props.fetchpriority !== 'auto') return props.fetchpriority
  return props.loading === 'eager' ? 'high' : 'auto'
})

watch(() => props.src, () => {
  hasError.value = false
})

function onError() {
  if (!hasError.value) {
    hasError.value = true
  }
}
</script>

<template>
  <img
    v-if="isRemoteImage"
    :src="displaySrc"
    :alt="alt"
    :title="title || alt"
    :width="width"
    :height="height"
    :sizes="sizes"
    :loading="loading"
    :fetchpriority="resolvedFetchPriority"
    decoding="async"
    v-bind="$attrs"
    @error="onError"
  >

  <NuxtImg
    v-else
    :src="displaySrc"
    :alt="alt"
    :title="title || alt"
    :width="width"
    :height="height"
    :sizes="sizes"
    :loading="loading"
    :fetchpriority="resolvedFetchPriority"
    decoding="async"
    v-bind="$attrs"
    @error="onError"
  />
</template>
