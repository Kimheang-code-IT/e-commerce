<script setup lang="ts">
import { useIntervalFn } from '@vueuse/core'

const { banner } = useAppConfig()
const { locale, t } = useI18n()

const socialLinks = computed(() => banner?.social ?? [])
const currentIndex = ref(0)

const notifications = computed(() => {
  const items = banner?.notifications ?? []

  return items.map(item => ({
    icon: item.icon,
    message: t(`banner.notifications.${item.key}`)
  }))
})

const currentNotification = computed(() => {
  const items = notifications.value

  if (!items.length) {
    return null
  }

  return items[currentIndex.value % items.length]
})

watch(locale, () => {
  currentIndex.value = 0
})

useIntervalFn(() => {
  if (notifications.value.length > 1) {
    currentIndex.value = (currentIndex.value + 1) % notifications.value.length
  }
}, () => banner?.interval ?? 5000)
</script>

<template>
  <div
    class="overflow-x-clip border-b border-white/10 bg-[#1d1e22] text-white"
    :aria-label="t('a11y.siteBanner')"
  >
    <UContainer class="py-0">
      <div
        class="banner-scroll flex h-10 items-center gap-3 overflow-x-auto sm:justify-between sm:gap-4 sm:overflow-visible"
      >
        <div class="relative flex shrink-0 items-center sm:min-w-0 sm:flex-1 sm:overflow-hidden">
          <Transition
            name="banner-notification"
            mode="out-in"
          >
            <div
              v-if="currentNotification"
              :key="`${locale}-${currentIndex}`"
              class="flex items-center gap-2 text-xs sm:min-w-0 sm:text-sm"
            >
              <UIcon
                :name="currentNotification.icon"
                class="size-4 shrink-0 text-green-400"
              />
              <p class="whitespace-nowrap font-medium sm:truncate">
                {{ currentNotification.message }}
              </p>
            </div>
          </Transition>
        </div>

        <div class="flex shrink-0 items-center gap-2">  
          <UColorModeButton
            v-if="banner?.colorMode"
            color="neutral"
            variant="soft"
            size="sm"
            square
            class="shrink-0 bg-white/30 text-white hover:bg-white/20"
          />

          <NuxtLink
            v-for="(link, index) in socialLinks"
            :key="`${link.label}-${index}`"
            :to="link.to"
            target="_blank"
            rel="noopener noreferrer"
            :aria-label="link.label"
            :class="[
              'flex size-6 shrink-0 items-center justify-center rounded-md text-white transition-colors sm:size-7',
              link.class
            ]"
          >
            <UIcon
              :name="link.icon"
              class="size-3.5 sm:size-4"
            />
          </NuxtLink>
        </div>
      </div>
    </UContainer>
  </div>
</template>

<style scoped>
.banner-notification-enter-active,
.banner-notification-leave-active {
  transition: opacity 0.35s ease, transform 0.35s ease;
}

.banner-notification-enter-from {
  opacity: 0;
  transform: translateY(0.5rem);
}

.banner-notification-leave-to {
  opacity: 0;
  transform: translateY(-0.5rem);
}

@media (prefers-reduced-motion: reduce) {
  .banner-notification-enter-active,
  .banner-notification-leave-active {
    transition: opacity 0.2s ease;
  }

  .banner-notification-enter-from,
  .banner-notification-leave-to {
    transform: none;
  }
}

.banner-scroll {
  scrollbar-width: none;
  -ms-overflow-style: none;
  -webkit-overflow-scrolling: touch;
}

.banner-scroll::-webkit-scrollbar {
  display: none;
}
</style>
