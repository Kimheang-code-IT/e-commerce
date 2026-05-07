import { useAuthStore } from '~/stores/auth'
import type { AuthTokenPair, AuthUser } from '~/types'
import { useAuthSessionManager } from '~/utils/auth/session-manager'

/**
 * The standard authentication provider coordinating cookie + localstorage destruction.
 * Now backed by Pinia for global real app state.
 */
export const useAuthSession = () => {
  const store = useAuthStore()
  const manager = useAuthSessionManager()

  const login = (tokens: AuthTokenPair, user: AuthUser) => {
    manager.setSession(tokens, user)
  }

  const logout = async () => {
    manager.clearSession()
    await store.logout()
  }

  const getUser = () => {
    return store.user
  }

  return { login, logout, getUser }
}
