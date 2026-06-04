<script setup lang="ts">
interface Props {
  title: string
  showDatepicker?: boolean
  /** Hide menu toggle (e.g. POS fullscreen uses Dashboard link instead). */
  hideSidebarToggle?: boolean
}

withDefaults(defineProps<Props>(), {
  showDatepicker: false,
  hideSidebarToggle: false,
})
</script>

<template>
  <ClientOnly>
    <UDashboardNavbar :title="title">
      <template #leading>
        <slot name="leading">
          <UDashboardSidebarCollapse v-if="!hideSidebarToggle" />
        </slot>
      </template>

      <div class="flex-1" />

      <template #right>
        <div class="flex flex-nowrap items-center justify-end gap-1 max-sm:px-1.5 px-2">
          <slot name="right" />
          <CommonAppDatepicker v-if="showDatepicker" icon-only-on-mobile class="shrink-0" />
        </div>
      </template>
    </UDashboardNavbar>
  </ClientOnly>
</template>
