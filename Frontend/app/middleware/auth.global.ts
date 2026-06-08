import { canAccessPath, getFirstAllowedHome } from '~/utils/auth/access'
import { routePermissionMap } from '~/utils/auth/routes'
import { fetchNeedsSetup } from '~/utils/auth/setup'

function showForbiddenToast() {
  // useToast() must run on client only — calling it during SSR causes a 500 error.
  if (!import.meta.client) return
  const { t } = useI18n()
  useToast().add({
    title: t('pages.error.forbiddenTitle'),
    description: t('pages.error.forbiddenMessage'),
    color: 'error',
  })
}

export default defineNuxtRouteMiddleware(async (to) => {
  const auth = useAuthStore()
  const path = to.path
  const forbiddenToastState = useState<{ lastPath?: string }>('forbidden-toast', () => ({}))

  const firstAllowedHome = () => getFirstAllowedHome(auth)

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
    const home = firstAllowedHome()
    if (home) return navigateTo(home)
    // Logged-in user has no permissions payload yet; allow staying on login.
    return
  }

  if (!auth.isLoggedIn || isPublicPage) return

  if (!canAccessPath(path, auth)) {
    const home = firstAllowedHome()

    // Show a one-time toast when user hits an unauthorized page.
    // This prevents spamming toasts during navigation/back-forward.
    if (forbiddenToastState.value.lastPath !== path) {
      forbiddenToastState.value.lastPath = path
      showForbiddenToast()
    }

    if (home && home !== path) {
      return navigateTo(home)
    }
    // No permitted app route at all; send to login to avoid redirect loops.
    return navigateTo('/login')
  }
})
