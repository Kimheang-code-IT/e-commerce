<script setup lang="ts">
import logo from '~/assets/images/logo.png'
import { useMenu } from '~/composables/layout/useMenu'
import { useLayoutSidebar } from '~/composables/layout/useLayoutSidebar'

const { links } = useMenu()
const { open, collapsed } = useLayoutSidebar()
</script>

<template>
  <UDashboardSidebar
    id="default"
    v-model:open="open"
    v-model:collapsed="collapsed"
    collapsible
    :collapsed-size="4"
    class="bg-white dark:bg-gray-900"
    :ui="{
      header: collapsed
        ? 'h-auto flex-col items-center gap-2 px-2 py-3 shrink-0 bg-white dark:bg-gray-900'
        : 'h-auto flex-col items-stretch gap-3 px-4 py-2 shrink-0 bg-white dark:bg-gray-900',
      footer: collapsed
        ? 'lg:border-t lg:border-default px-2 py-2 bg-white dark:bg-gray-900'
        : 'lg:border-t lg:border-default px-4 py-2 bg-white dark:bg-gray-900',
    }"
  >
    <template #header="{ collapsed: isCollapsed }">
      <div
        class="flex w-full items-center gap-2"
        :class="isCollapsed ? 'flex-col justify-center' : 'justify-between'"
      >
        <NuxtLink
          to="/"
          class="flex min-w-0 items-center"
          :class="isCollapsed ? 'justify-center' : 'gap-3 py-1'"
          :title="isCollapsed ? 'PDME-Revenue' : undefined"
        >
          <img
            :src="logo"
            alt="PDME-Revenue logo"
            class="shrink-0 rounded-full object-contain transition-[width,height]"
            :class="isCollapsed ? 'h-10 w-10' : 'h-16 w-60'"
          >
        </NuxtLink>
        <UDashboardSidebarCollapse
          :class="isCollapsed ? 'mx-auto' : 'shrink-0'"
          :ui="{ base: isCollapsed ? 'size-8' : undefined }"
        />
      </div>

      <UDashboardSearchButton
        v-if="!isCollapsed"
        :collapsed="false"
        class="mb-1 bg-transparent ring-default"
      />
    </template>

    <template #default="{ collapsed }">
      <UNavigationMenu
        :collapsed="collapsed"
        :items="links[0]"
        orientation="vertical"
        tooltip
        popover
      />

      <UNavigationMenu
        :collapsed="collapsed"
        :items="links[1]"
        orientation="vertical"
        tooltip
      />
    </template>

    <template #footer="{ collapsed }">
      <LayoutUserMenu :collapsed="collapsed" />
    </template>
  </UDashboardSidebar>
</template>
