import type { NavigationMenuItem } from '@nuxt/ui'
import { useLayoutSidebar } from '~/composables/layout/useLayoutSidebar'
import { useRoutePermissionMap } from '~/utils/auth/routes'
export const useMenu = () => {
  const { open, collapseForPos, closeSidebar } = useLayoutSidebar()
  const { t } = useI18n()
  const auth = useAuthStore()

  const closeNav = () => {
    closeSidebar()
  }

  const rawLinks = computed(() => [[
    {
      label: t('navigation.dashboard'),
      icon: 'i-lucide-home', // updated icon name
      to: '/',
      class: 'text-md gap-2',
      onSelect: closeNav
    },
    {
      label: t('pages.category.title'),
      icon: 'i-lucide-swatch-book', // updated icon name
      to: '/category',
      class: 'my-2 text-md gap-2',
      onSelect: closeNav
    },
    {
      label: t('pages.supplier.title'),
      icon: 'i-lucide-users',
      to: '/supplier',
      class: 'my-2 text-md gap-2',
      onSelect: closeNav
    },
    {
      label: t('pages.product.title'),
      icon: 'i-lucide-package-search',
      to: '/product',
      class: 'my-2 text-md gap-2',
      onSelect: closeNav
    },
    {
      label: t('pages.pos.title'),
      icon: 'i-lucide-store', // updated icon name
      to: '/pos',
      class: 'my-2 text-md gap-2',
      onSelect: () => {
        collapseForPos()
        closeNav()
      },
    },
    {
      label: t('pages.report.title'),
      icon: 'i-lucide-file-bar-chart', // updated icon name
      to: '/report',
      class: 'my-2 text-md gap-2',
      onSelect: closeNav
    },
    {
      label: t('pages.refund.title'),
      icon: 'i-lucide-arrow-left-right',
      to: '/refund',
      class: 'my-2 text-md gap-2',
      onSelect: closeNav
    },
    {
      label: t('pages.commission.title'),
      icon: 'i-lucide-badge-percent', // updated icon name
      to: '/commission',
      class: 'my-2 text-md gap-2',
      onSelect: closeNav
    },
    {
      label: t('pages.finance.title'),
      icon: 'i-lucide-landmark', // updated icon name
      to: '/finance',
      class: 'my-2 text-md gap-2',
      onSelect: closeNav
    },
    {
      label: t('pages.delivery.title'),
      icon: 'i-lucide-truck',
      to: '/delivery',
      class: 'my-2 text-md gap-2',
      onSelect: closeNav
    },
    {
      label: t('navigation.settings'),
      icon: 'i-lucide-settings',
      to: '/settings/user-management',
      defaultOpen: true,
      type: 'trigger',
      class: 'my-2 text-md gap-2',
      children: [
        {
          label: t('pages.userManagement.title'),
          to: '/settings/user-management',
          class: 'text-md gap-2',
          onSelect: closeNav
        },
        {
          label: t('pages.roleManagement.title'),
          to: '/settings/role-management',
          class: 'my-2 text-md gap-2',
          onSelect: closeNav
        }
      ],
      onSelect: closeNav
    }
  ], []] as NavigationMenuItem[][])

  const links = computed(() => {
    const routePermissionMap = useRoutePermissionMap()
    const allowed = new Set(
      routePermissionMap
        .filter((entry) => {
          const hasPerm = auth.hasPermission(entry.permission)
          const hasRole = !entry.roles || auth.hasRole(entry.roles)
          return hasPerm && hasRole
        })
        .map((entry) => entry.home)
    )

    return rawLinks.value.map((group) =>
      group
        .map((item) => {
          if (!item.children) return item
          const filteredChildren = item.children.filter((child) => allowed.has(String(child.to)))
          return { ...item, children: filteredChildren }
        })
        .filter((item) => {
          if (!item.to) return true
          const isHome = allowed.has(String(item.to))
          if (item.children && item.children.length === 0) return false
          return isHome
        })
    )
  })

  return {
    open,
    links
  }
}
