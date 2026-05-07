import { defineStore } from 'pinia'
import { computed } from 'vue'
import { hasPermission as hasPermissionByPolicy } from '~/utils/auth/policy'
import type { AuthUser } from '~/types'
import type { Permission } from '~/utils/auth/permissions'

export const useAuthStore = defineStore('auth', () => {
  // Use cookies for both token and user data to ensure SSR compatibility
  const token = useCookie<string | null>('auth_token', { default: () => null })
  const refreshToken = useCookie<string | null>('refresh_token', { default: () => null })
  const user = useCookie<AuthUser | null>('auth_user', { default: () => null })

  const isLoggedIn = computed(() => !!token.value)
  const pageAccess = computed<string[]>(() => {
    const data = user.value
    if (data && Array.isArray(data.pageAccess)) {
      return data.pageAccess.map((x: unknown) => String(x))
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
