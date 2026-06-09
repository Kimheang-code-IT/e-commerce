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

const route = useRoute()
const panelId = computed(() => {
  const slug = route.path.replace(/^\//, '').replace(/\//g, '-') || 'home'
  return `page-${slug}`
})
</script>

<template>
  <UDashboardPanel :id="panelId" class="flex flex-1 flex-col min-w-0 h-full"
    :ui="{ body: 'flex flex-1 flex-col min-h-0 overflow-hidden p-0 m-0 gap-0' }">
    <template #header>
      <UDashboardNavbar :title="title" :toggle="!hideSidebarToggle">
        <template #left>
          <slot name="leading">
            <UDashboardSidebarCollapse v-if="!hideSidebarToggle" />
          </slot>
        </template>

        <template #right>
          <div class="flex flex-nowrap items-center justify-end gap-2">
            <slot name="right" />
            <CommonAppDatepicker v-if="showDatepicker" class="shrink-0" />
          </div>
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div
        class="flex flex-1 flex-col min-h-0 m-2 md:-m-4 overflow-hidden bg-background text-foreground tracking-tight">
        <slot />
      </div>
    </template>
  </UDashboardPanel>
</template>
