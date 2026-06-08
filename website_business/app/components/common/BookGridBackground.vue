<template>
  <div class="relative isolate min-h-full w-full max-w-full overflow-x-clip">
    <div
      class="pointer-events-none absolute inset-0 -z-20 bg-white dark:bg-[#0f172a]"
      aria-hidden="true"
    />

    <div
      class="book-bg-grid pointer-events-none absolute inset-0 -z-20"
      aria-hidden="true"
    />

    <div class="relative z-10">
      <slot />
    </div>
  </div>
</template>
