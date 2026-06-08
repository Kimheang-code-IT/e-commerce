import { useRoutePermissionMap } from '~/utils/auth/routes'
import { fetchNeedsSetup } from '~/utils/auth/setup'

export default defineNuxtRouteMiddleware(async (to) => {
  const toast = useToast()
  const { t } = useI18n()
  const auth = useAuthStore()
  const path = to.path
  const routePermissionMap = useRoutePermissionMap()
  const forbiddenToastState = useState<{ lastPath?: string }>('forbidden-toast', () => ({}))
  
  const isAllowed = (entry: any) => {
    const hasPerm = auth.hasPermission(entry.permission)
    const hasRole = !entry.roles || auth.hasRole(entry.roles)
    return hasPerm && hasRole
  }

  const firstAllowed = () => routePermissionMap.find(isAllowed)

  // Define public pages
  const isPublicPage = ['/login', '/otp', '/setup'].includes(to.path)

  if (!auth.isLoggedIn && isPublicPage && to.path !== '/setup') {
    const needsSetup = await fetchNeedsSetup()
    if (needsSetup) {
      return navigateTo('/setup')
    }
  }

  // Redirect if not logged in and trying to access a private page
  if (!auth.isLoggedIn && !isPublicPage) {
    const needsSetup = await fetchNeedsSetup()
    if (needsSetup) {
      return navigateTo('/setup')
    }
    return navigateTo('/login')
  }

  // Redirect if logged in and trying to access login page
  if (auth.isLoggedIn && isPublicPage) {
    const first = firstAllowed()
    if (first) return navigateTo(first.home)
    // Logged-in user has no permissions payload yet; allow staying on login.
    return
  }

  if (!auth.isLoggedIn || isPublicPage) return

  const matched = routePermissionMap.find((entry) => entry.match(path))
  if (!matched) return
  if (!isAllowed(matched)) {
    const first = firstAllowed()

    // Show a one-time toast when user hits an unauthorized page.
    // This prevents spamming toasts during navigation/back-forward.
    if (forbiddenToastState.value.lastPath !== path) {
      forbiddenToastState.value.lastPath = path
      toast.add({
        title: t('pages.error.forbiddenTitle'),
        description: t('pages.error.forbiddenMessage'),
        color: 'error',
      })
    }

    if (first && first.home !== path) {
      return navigateTo(first.home)
    }
    // No permitted app route at all; send to login to avoid redirect loops.
    return navigateTo('/login')
  }
})
