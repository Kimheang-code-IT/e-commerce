import { useAuthApi } from '~/utils/api'

export default defineNuxtPlugin(async () => {
  const auth = useAuthStore()
  if (!auth.isLoggedIn || !auth.token) return

  try {
    const res = await useAuthApi().me()
    const user = (res as { user?: Record<string, unknown> })?.user
      ?? (res as { data?: { user?: Record<string, unknown> } })?.data?.user

    if (!user || !auth.user) return

    auth.setAuth(auth.token, {
      ...auth.user,
      id: Number(user.id ?? auth.user.id ?? 0) || auth.user.id,
      name: String(user.name ?? auth.user.name ?? ''),
      email: String(user.email ?? auth.user.email ?? ''),
      avatar: String(user.avatar ?? auth.user.avatar ?? ''),
      role: String(user.role ?? auth.user.role ?? ''),
      pageAccess: Array.isArray(user.pageAccess)
        ? user.pageAccess.map((item) => String(item))
        : auth.user.pageAccess ?? [],
    }, auth.refreshToken)
  } catch {
    // Keep cached session; API client handles expired tokens.
  }
})
