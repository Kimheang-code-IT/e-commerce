import type {
  AuditLog,
  Category,
  CommissionEntry,
  DeliveryEntry,
  FinanceEntry,
  Product,
  ReportRow,
  SystemRole,
  SystemUser
} from '~/types'
import { useAuthStore } from '~/stores/auth'

type ApiList<T> = { data: T[]; total?: number }
type AuthUser = { id?: number; name: string; email: string; avatar?: string; role?: string; pageAccess?: string[] }
type LoginResponseV3 = { success: boolean; message: string; data: { token: string; refreshToken: string; user: AuthUser } }
type LoginResponseV2 = { data: { tokens: { accessToken: string; refreshToken: string }; user: AuthUser } }
type RefreshResponseV2 = { data: { tokens: { accessToken: string; refreshToken: string } } }

export type ApiQueryParams = {
  page?: number
  limit?: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  search?: string
  dateFrom?: string
  dateTo?: string
  [key: string]: string | number | undefined
}

function makeCrudApi<T>(resource: string) {
  const api = useApi()
  return {
    list: (params?: ApiQueryParams, signal?: AbortSignal) =>
      api.get<ApiList<T>>(resource, { query: params, signal, dedupe: true }),
    create: (payload: Partial<T>) => api.post<T>(resource, payload),
    update: (id: string | number, payload: Partial<T>) => api.put<T>(`${resource}/${id}`, payload),
    remove: (id: string | number) => api.delete(`${resource}/${id}`)
  }
}

function makeViewListApi<T>(resource: string) {
  const api = useApi()
  return {
    list: (params?: ApiQueryParams, signal?: AbortSignal) =>
      api.get<ApiList<T>>(resource, { query: params, signal, dedupe: true })
  }
}

export function useAuthApi() {
  const api = useApi()
  const auth = useAuthStore()
  return {
    login: async (payload: { email: string; password: string }) => {
      const response = await api.post<LoginResponseV3 | LoginResponseV2 | { token: string; refreshToken?: string; user: AuthUser }>('/auth/login', payload)
      if ('success' in response && 'data' in response && response.data && 'token' in response.data) {
        return {
          tokens: {
            accessToken: response.data.token,
            refreshToken: response.data.refreshToken
          },
          user: response.data.user
        }
      }
      if ('data' in response && response.data && 'tokens' in response.data) {
        return {
          tokens: response.data.tokens,
          user: response.data.user
        }
      }
      const legacy = response as { token: string; refreshToken?: string; user: any }
      return {
        tokens: {
          accessToken: legacy.token,
          refreshToken: legacy.refreshToken || ''
        },
        user: legacy.user
      }
    },
    refresh: async () => {
      const response = await api.post<RefreshResponseV2>(
        '/auth/refresh',
        {},
        {
          skipAuthRefresh: true,
          headers: auth.refreshToken ? { refreshToken: auth.refreshToken } : {}
        }
      )
      return response.data
    },
    me: () => api.get<{ user?: any; data?: { user: any } }>('/auth/me'),
    logout: () => api.post('/auth/logout', {})
  }
}

export function useCategoryApi() {
  return makeCrudApi<Category>('/categories')
}

export function useProductApi() {
  const crud = makeCrudApi<Product>('/products')
  const api = useApi()
  return {
    ...crud,
    listStockAdditions: (id: number | string, params?: ApiQueryParams) =>
      api.get<ApiList<any>>(`/products/${id}/stock-additions`, { query: params }),
    listDamages: (id: number | string, params?: ApiQueryParams) =>
      api.get<ApiList<any>>(`/products/${id}/damages`, { query: params }),
  }
}

export function useRoleApi() {
  return makeCrudApi<SystemRole>('/roles')
}

export function useSystemRoleApi() {
  return useRoleApi()
}

export function useUserApi() {
  return makeCrudApi<SystemUser>('/users')
}

export function useSystemUserApi() {
  return useUserApi()
}

export function useHistoriesApi() {
  const api = useApi()
  return {
    list: (params?: ApiQueryParams, signal?: AbortSignal) =>
      api.get<ApiList<AuditLog>>('/histories', { query: params, signal, dedupe: true })
  }
}

export function useHistoryApi() {
  return useHistoriesApi()
}

export function useProductsViewApi() {
  return makeViewListApi<Product>('/products-view')
}

export function useReportsViewApi() {
  const api = useApi()
  return {
    list: (params?: ApiQueryParams, signal?: AbortSignal) =>
      api.get<ApiList<ReportRow>>('/reports-view', { query: params, signal, dedupe: true }),
    exportCsv: (params?: ApiQueryParams) =>
      api.get<{ url?: string; data?: ReportRow[] }>('/reports-view/export', { query: params })
  }
}

export function useDeliveriesViewApi() {
  return makeViewListApi<DeliveryEntry>('/deliveries-view')
}

export function useCommissionViewApi() {
  const api = useApi()
  return {
    list: (params?: ApiQueryParams, signal?: AbortSignal) =>
      api.get<ApiList<CommissionEntry>>('/commission-view', { query: params, signal, dedupe: true }),
    exportCsv: (params?: ApiQueryParams) =>
      api.get<{ url?: string; data?: CommissionEntry[] }>('/commission-view/export', { query: params })
  }
}

export function useFinanceViewApi() {
  const api = useApi()
  return {
    list: (params?: ApiQueryParams, signal?: AbortSignal) =>
      api.get<ApiList<FinanceEntry>>('/finance-view', { query: params, signal, dedupe: true }),
    update: (id: number, payload: { facebook: number; other: number }) =>
      api.put<{ data: FinanceEntry }>(`/finance-view/${id}`, payload),
    exportCsv: (params?: ApiQueryParams) =>
      api.get<{ url?: string; data?: FinanceEntry[] }>('/finance-view/export', { query: params })
  }
}

export function useFinanceApi() {
  return useFinanceViewApi()
}

export function useReportApi() {
  return useReportsViewApi()
}

export function useDeliveryApi() {
  return useDeliveriesViewApi()
}

export function useCommissionApi() {
  return useCommissionViewApi()
}

export function usePosApi() {
  const api = useApi()
  async function withLegacyFallback<T>(primary: () => Promise<T>, fallback: () => Promise<T>) {
    try {
      return await primary()
    } catch (error: any) {
      if (Number(error?.response?.status || error?.statusCode || 0) === 404) {
        return await fallback()
      }
      throw error
    }
  }
  return {
    createPreviewSession: (invoices: any[]) =>
      withLegacyFallback(
        () => api.post<{ previewKey: string }>('/pos/preview', { invoices }),
        () => api.post<{ previewKey: string }>('/invoices/preview-sessions', { invoices })
      ),
    getPreviewSession: (previewKey: string) =>
      withLegacyFallback(
        () => api.get<{ invoices: any[] }>(`/pos/preview/${previewKey}`),
        () => api.get<{ invoices: any[] }>(`/invoices/preview-sessions/${previewKey}`)
      ),
    getInvoicePreviewByNo: (invoiceNo: string) =>
      api.get<{ invoice?: any; lines?: any[]; invoices?: any[] }>(`/pos/invoice/${invoiceNo}`),
    calculateTotals: (payload: {
      discountPercent: number
      lines: Array<{ productId: number; qty: number }>
    }) =>
      withLegacyFallback(
        () => api.post<{ subtotal: number; discountAmount: number; total: number }>('/pos/calculate-totals', payload),
        () => api.post<{ subtotal: number; discountAmount: number; total: number }>('/invoices/calculate-totals', payload)
      ),
    checkout: (payload: {
      customerName: string
      customerPhone: string
      customerAddress: string
      source: string
      deliveryType: string
      deliveryPrice: number
      deliveryDate: string
      discountPercent: number
      sellerId?: number
      lines: Array<{ productId: number; qty: number }>
    }) =>
      withLegacyFallback(
        () =>
          api.post<{ data: { invoiceNo: string; subtotal: number; discountAmount: number; total: number; invoice: any } }>(
            '/pos/checkout',
            payload
          ),
        () =>
          api.post<{ data: { invoiceNo: string; subtotal: number; discountAmount: number; total: number; invoice: any } }>(
            '/invoices/checkout',
            payload
          )
      ),
  }
}

export function useDashboardApi() {
  const api = useApi()
  return {
    getSummary: (params?: ApiQueryParams) => api.get<{
      data: {
        totalProducts: number
        productsInStock: number
        productsOutOfStock: number
        soldProducts: number
        provincialDistribution: { name: string; value: number }[]
        topProducts: { name: string; value: number }[]
        userCommissions: { name: string; value: number }[]
      }
    }>('/dashboard/summary', { query: params })
  }
}
