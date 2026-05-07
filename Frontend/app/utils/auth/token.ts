import { AuthConstants } from '../constants/http'

/**
 * Enterprise token management wrapper orchestrating Nuxt SSR useCookie handlers.
 */
export const getToken = (): string | null => {
  const tokenCookie = useCookie(AuthConstants.TOKEN_KEY)
  return tokenCookie.value || null
}

export const setToken = (token: string, maxAgeSeconds: number = 86400): void => {
  const tokenCookie = useCookie(AuthConstants.TOKEN_KEY, { maxAge: maxAgeSeconds })
  tokenCookie.value = token
}

export const removeToken = (): void => {
  const tokenCookie = useCookie(AuthConstants.TOKEN_KEY)
  tokenCookie.value = null
}
