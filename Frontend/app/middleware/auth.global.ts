import { useRoutePermissionMap } from '~/utils/auth/routes'

export default defineNuxtRouteMiddleware((to) => {
  const auth = useAuthStore()
  const path = to.path
  const routePermissionMap = useRoutePermissionMap()
  
  const isAllowed = (entry: any) => {
    const hasPerm = auth.hasPermission(entry.permission)
    const hasRole = !entry.roles || auth.hasRole(entry.roles)
    return hasPerm && hasRole
  }

  const firstAllowed = () => routePermissionMap.find(isAllowed)

  // Define public pages
  const isPublicPage = ['/login', '/otp'].includes(to.path)

  // Redirect if not logged in and trying to access a private page
  if (!auth.isLoggedIn && !isPublicPage) {
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
    if (first && first.home !== path) {
      return navigateTo(first.home)
    }
    // No permitted app route at all; send to login to avoid redirect loops.
    return navigateTo('/login')
  }
})
