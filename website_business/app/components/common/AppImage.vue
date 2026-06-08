<script setup lang="ts">
const DEFAULT_FALLBACK = 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=640&q=80'

const props = withDefaults(defineProps<{
  src?: string
  alt?: string
  fallback?: string
  width?: number | string
  height?: number | string
  loading?: 'lazy' | 'eager'
}>(), {
  alt: '',
  fallback: DEFAULT_FALLBACK,
  loading: 'lazy'
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
    :width="width"
    :height="height"
    :loading="loading"
    decoding="async"
    v-bind="$attrs"
    @error="onError"
  >

  <NuxtImg
    v-else
    :src="displaySrc"
    :alt="alt"
    :width="width"
    :height="height"
    :loading="loading"
    decoding="async"
    v-bind="$attrs"
    @error="onError"
  />
</template>
