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
  if (!import.meta.client) return

  try {
    const auth = useAuthStore()
    const path = to.path.replace(/\/+$/, '') || '/'
    const forbiddenToastState = useState<{ lastPath?: string }>('forbidden-toast', () => ({}))

    const firstAllowedHome = () => getFirstAllowedHome(auth)

    const isPublicPage = ['/login', '/setup'].includes(path)

    if (!auth.isLoggedIn && isPublicPage && path !== '/setup') {
      const needsSetup = await fetchNeedsSetup()
      if (needsSetup) {
        return navigateTo('/setup')
      }
    }

    if (!auth.isLoggedIn && !isPublicPage) {
      const needsSetup = await fetchNeedsSetup()
      if (needsSetup) {
        return navigateTo('/setup')
      }
      return navigateTo('/login')
    }

    if (auth.isLoggedIn && isPublicPage) {
      const home = firstAllowedHome()
      if (home) return navigateTo(home)
      return
    }

    if (!auth.isLoggedIn || isPublicPage) return

    if (!canAccessPath(path, auth)) {
      const home = firstAllowedHome()

      if (forbiddenToastState.value.lastPath !== path) {
        forbiddenToastState.value.lastPath = path
        showForbiddenToast()
      }

      if (home && home !== path) {
        return navigateTo(home)
      }
      return navigateTo('/login')
    }
  } catch {
    return navigateTo('/login')
  }
})
