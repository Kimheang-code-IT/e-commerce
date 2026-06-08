import type { NavigationMenuItem } from '@nuxt/ui'
import { useLayoutSidebar } from '~/composables/layout/useLayoutSidebar'
import { getAllowedRouteHomeSet } from '~/utils/auth/access'

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
      icon: 'i-lucide-home',
      to: '/',
      class: 'text-md gap-2',
      onSelect: closeNav
    },
    {
      label: t('pages.category.title'),
      icon: 'i-lucide-swatch-book',
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
      icon: 'i-lucide-store',
      to: '/pos',
      class: 'my-2 text-md gap-2',
      onSelect: () => {
        collapseForPos()
        closeNav()
      },
    },
    {
      label: t('pages.report.title'),
      icon: 'i-lucide-file-bar-chart',
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
      icon: 'i-lucide-badge-percent',
      to: '/commission',
      class: 'my-2 text-md gap-2',
      onSelect: closeNav
    },
    {
      label: t('pages.finance.title'),
      icon: 'i-lucide-landmark',
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

  const allowedHomes = computed(() => getAllowedRouteHomeSet(auth))

  const links = computed(() => {
    const allowed = allowedHomes.value

    return rawLinks.value.map((group) =>
      group
        .map((item) => {
          if (!item.children) return item
          const filteredChildren = item.children.filter((child) => allowed.has(String(child.to)))
          return { ...item, children: filteredChildren }
        })
        .filter((item) => {
          if (!item.to) return false
          if (item.children) {
            return item.children.length > 0
          }
          return allowed.has(String(item.to))
        })
    )
  })

  return {
    open,
    links,
    allowedHomes,
  }
}
