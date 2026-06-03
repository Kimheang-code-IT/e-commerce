/** Shared dashboard sidebar open/collapsed state (Nuxt UI UDashboardSidebar). */

export function useLayoutSidebar() {
  const route = useRoute()
  const open = useState<boolean>('dashboard-sidebar-open', () => false)
  const collapsed = useState<boolean>('dashboard-sidebar-collapsed', () => false)

  const isPosRoute = computed(
    () => route.path === '/pos' || route.path.startsWith('/pos/'),
  )

  function applyRouteSidebarState(path: string) {
    const onPos = path === '/pos' || path.startsWith('/pos/')
    if (onPos) {
      open.value = false
      collapsed.value = true
      return
    }
    collapsed.value = false
  }

  function collapseForPos() {
    open.value = false
    collapsed.value = true
  }

  function closeSidebar() {
    open.value = false
  }

  watch(
    () => route.path,
    (path) => applyRouteSidebarState(path),
    { immediate: true },
  )

  return {
    open,
    collapsed,
    isPosRoute,
    collapseForPos,
    closeSidebar,
    applyRouteSidebarState,
  }
}
