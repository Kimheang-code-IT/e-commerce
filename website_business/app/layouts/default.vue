<template>
  <div class="flex min-h-dvh w-full max-w-full flex-col overflow-x-clip bg-default text-default">
    <AppBanner class="relative z-50" />

    <div class="sticky top-0 z-50 overflow-x-clip border-b border-default bg-default">
      <AppHeader />
    </div>

    <UMain class="flex-1 max-w-full overflow-x-clip bg-default mb-10">
      <slot />
    </UMain>

    <AppFooter />
  </div>
</template>
