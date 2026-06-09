<script setup lang="ts">
import logo from '~/assets/image/logo.png'

const props = withDefaults(defineProps<{
  alt?: string
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'xxl'
  height?: string | number
  maxWidth?: string | number
}>(), {
  alt: '',
  size: 'md'
})

const { seo, header } = useAppConfig()
const { t } = useI18n()

const logoAlt = computed(() => {
  return props.alt || header?.title || seo?.siteName || t('seo.siteName')
})

const sizeClasses: Record<'sm' | 'md' | 'lg' | 'xl' | 'xxl', string> = {
  sm: 'h-8 max-w-[140px]',
  md: 'h-10 max-w-[180px] sm:h-12',
  lg: 'h-14 max-w-[220px] sm:h-16',
  xl: 'h-16 max-w-[240px] sm:h-20',
  xxl: 'h-20 max-w-[280px] sm:h-32'
}

const imageClass = computed(() => {
  if (props.height || props.maxWidth) {
    return 'block w-auto object-contain'
  }

  return `block w-auto object-contain ${sizeClasses[props.size]}`
})

const imageStyle = computed(() => {
  const style: Record<string, string> = {}

  if (props.height !== undefined) {
    style.height = typeof props.height === 'number' ? `${props.height}px` : props.height
  }

  if (props.maxWidth !== undefined) {
    style.maxWidth = typeof props.maxWidth === 'number' ? `${props.maxWidth}px` : props.maxWidth
  }

  return Object.keys(style).length ? style : undefined
})
</script>

<template>
  <span class="inline-flex shrink-0 items-center overflow-hidden rounded-md">
    <img
      :src="logo"
      :alt="logoAlt"
      width="180"
      height="56"
      loading="eager"
      decoding="async"
      :class="imageClass"
      :style="imageStyle"
    >
  </span>
</template>
