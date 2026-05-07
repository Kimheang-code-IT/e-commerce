import { useAuthStore } from '~/stores/auth'
import { useAuthSessionManager } from '~/utils/auth/session-manager'

/**
 * Standard API Fetching Composable
 * ───────────────────────────────────────
 * Use this for all backend requests. It automatically:
 * 1. Attaches the Bearer token (if user is logged in)
 * 2. Handles global error notifications
 * 3. Supports standard REST methods
 */
export function useApi() {
    const toast = useToast()
    const config = useRuntimeConfig()
    
    // Base URL from nuxt.config (fallback to localhost for dev)
    const baseURL = config.public.apiBase || 'http://localhost:8000/api/v1'

    type ApiErrorPayload = {
        message?: string
        code?: string
        traceId?: string
        errors?: Record<string, string[]>
    }

    const mapApiErrorMessage = (status: number, payload: ApiErrorPayload | null | undefined) => {
        if (payload?.message) return payload.message
        if (status >= 500) return 'Server error. Please try again later.'
        if (status === 401) return 'Unauthorized access.'
        if (status === 403) return 'You do not have permission for this action.'
        if (status === 404) return 'Requested resource was not found.'
        return 'Something went wrong'
    }

    const inFlight = useState<Map<string, Promise<unknown>>>('api-in-flight', () => new Map())
    const toRequestKey = (method: string, url: string, query?: unknown) => `${method}:${url}:${JSON.stringify(query || {})}`

    const fetch = async <T>(url: string, options: Record<string, unknown> = {}) => {
        // Retrieve real global app state via Pinia
        const authStore = useAuthStore()
        const session = useAuthSessionManager()
        const bearerToken = session.accessToken.value || authStore.token || null
        if (!session.accessToken.value && authStore.token) {
          session.accessToken.value = authStore.token
        }

        const method = String(options.method || 'GET').toUpperCase()
        const key = toRequestKey(method, url, options.query)
        const dedupe = Boolean(options.dedupe)
        const skipAuthRefresh = Boolean(options.skipAuthRefresh)
        if (dedupe && inFlight.value.has(key)) {
            return (await inFlight.value.get(key)) as T
        }
        const requestOptions = {
          baseURL,
          ...options,
          headers: {
            ...(bearerToken ? { Authorization: `Bearer ${bearerToken}` } : {}),
            ...((options.headers as Record<string, string> | undefined) || {})
          }
        }
        delete (requestOptions as Record<string, unknown>).skipAuthRefresh

        const execute = () => $fetch<T>(url, requestOptions)
        const request = execute()
        if (dedupe) inFlight.value.set(key, request as unknown as Promise<unknown>)

        try {
            return await request
        } catch (err: unknown) {
            const fetchErr = err as { name?: string; response?: { status?: number; _data?: ApiErrorPayload } }
            if (fetchErr?.response?.status === 401 && !skipAuthRefresh) {
              const refreshed = await session.refreshAccessToken()
              if (refreshed) {
                return await execute()
              }
              authStore.logout()
              throw err
            }
            if (fetchErr?.name === 'FetchError') {
              const statusCode = fetchErr.response?.status
              if (statusCode) {
                toast.add({
                  title: `API Error: ${statusCode}`,
                  description: mapApiErrorMessage(statusCode, fetchErr.response?._data),
                  color: 'error'
                })
              } else {
                toast.add({ title: 'Connection Error', description: 'Could not reach the server', color: 'error' })
              }
            }
            throw err
        } finally {
            if (dedupe) inFlight.value.delete(key)
        }
    }

    return {
        get: <T>(url: string, opt?: Record<string, unknown>) => fetch<T>(url, { method: 'GET', ...opt }),
        post: <T>(url: string, body: unknown, opt?: Record<string, unknown>) => fetch<T>(url, { method: 'POST', body, ...opt }),
        put: <T>(url: string, body: unknown, opt?: Record<string, unknown>) => fetch<T>(url, { method: 'PUT', body, ...opt }),
        delete: <T>(url: string, opt?: Record<string, unknown>) => fetch<T>(url, { method: 'DELETE', ...opt }),
    }
}
