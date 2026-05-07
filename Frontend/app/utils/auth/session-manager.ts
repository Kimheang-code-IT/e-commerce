import type { AuthTokenPair, AuthUser } from '~/types'
import { useAuthApi } from '~/utils/api'

export function useAuthSessionManager() {
  const auth = useAuthStore()
  const accessToken = useState<string | null>('auth.accessToken', () => auth.token || null)
  const refreshing = useState<boolean>('auth.refreshing', () => false)
  const refreshPromise = useState<Promise<boolean> | null>('auth.refreshPromise', () => null)

  if (!accessToken.value && auth.token) {
    accessToken.value = auth.token
  }

  function setSession(tokens: AuthTokenPair, user: AuthUser) {
    accessToken.value = tokens.accessToken
    auth.setAuth(tokens.accessToken, user, tokens.refreshToken)
  }

  function clearSession() {
    accessToken.value = null
    auth.clearAuth()
  }

  async function refreshAccessToken(): Promise<boolean> {
    if (refreshPromise.value) return refreshPromise.value
    refreshing.value = true
    const api = useAuthApi()
    const task = (async () => {
      try {
        const result = await api.refresh()
        accessToken.value = result.tokens.accessToken
        auth.setAccessToken(result.tokens.accessToken)
        auth.setRefreshToken(result.tokens.refreshToken)
        return true
      } catch {
        clearSession()
        return false
      } finally {
        refreshing.value = false
        refreshPromise.value = null
      }
    })()
    refreshPromise.value = task
    return task
  }

  return {
    accessToken,
    refreshing,
    setSession,
    clearSession,
    refreshAccessToken
  }
}
