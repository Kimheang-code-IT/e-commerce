import { defineStore } from 'pinia'
import { computed } from 'vue'
import { hasPermission as hasPermissionByPolicy } from '~/utils/auth/policy'
import type { AuthUser } from '~/types'
import type { Permission } from '~/utils/auth/permissions'

export const useAuthStore = defineStore('auth', () => {
  const cookieOptions = {
    default: () => null,
    sameSite: 'strict' as const,
    secure: import.meta.env.PROD,
    path: '/',
    maxAge: 60 * 60 * 24 * 14
  }

  // Tokens are sent as Authorization headers, not ambient auth cookies.
  // sameSite/secure reduces CSRF exposure and accidental token leakage in production.
  const token = useCookie<string | null>('auth_token', cookieOptions)
  const refreshToken = useCookie<string | null>('refresh_token', cookieOptions)
  const user = useCookie<AuthUser | null>('auth_user', cookieOptions)

  const isLoggedIn = computed(() => !!token.value)
  const pageAccess = computed<string[]>(() => {
    const data = user.value
    if (data && Array.isArray(data.pageAccess)) {
      return data.pageAccess.map((x: unknown) => String(x).toLowerCase())
    }
    return []
  })

  function hasPermission(permission: Permission) {
    return hasPermissionByPolicy(pageAccess.value, permission)
  }

  function hasRole(roles: string[]) {
    const data = user.value
    if (!data?.role) return false
    return roles.includes(data.role.toLowerCase())
  }

  function setAccessToken(newToken: string | null) {
    token.value = newToken
  }

  function setRefreshToken(newToken: string | null) {
    refreshToken.value = newToken
  }

  function setAuth(newToken: string, userData: AuthUser, nextRefreshToken?: string | null) {
    token.value = newToken
    if (typeof nextRefreshToken === 'string') refreshToken.value = nextRefreshToken
    user.value = userData
  }

  function clearAuth() {
    token.value = null
    refreshToken.value = null
    user.value = null
  }

  function logout() {
    clearAuth()
    navigateTo('/login')
  }

  return { token, refreshToken, user, isLoggedIn, pageAccess, hasPermission, hasRole, setAccessToken, setRefreshToken, setAuth, clearAuth, logout }
})
