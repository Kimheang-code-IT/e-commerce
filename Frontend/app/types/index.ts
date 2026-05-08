export interface AuditLog {
  id: number
  typeAction: 'Login' | 'Logout' | 'Create' | 'Update' | 'Delete' | 'Export'
  username: string
  date: string
  description: string
  metadata?: any
}

export interface Category {
  id: string
  name: string
  description: string
  total: number
  createdAt: string
}

export interface Statistic {
  label: string
  value: string
  icon: string
}

export interface ChartDataPoint {
  name: string
  value: number
}

export interface FormField {
  key: string
  label: string
  type?: 'input' | 'number' | 'select' | 'permission-tree' | 'textarea' | 'password' | 'date' | 'file' | string
  icon?: string
  placeholder?: string
  items?: any[]
  childItems?: any[]
  multiple?: boolean
  readonly?: boolean
  required?: boolean
  class?: string
}

/** Derived on the server from `inStock`; same keys as `product.stockStatus.*` i18n. */
export type ProductStockStatusTier = 'aLot' | 'lower' | 'out'

export interface Product {
  id: number
  image: string
  name: string
  /** Display name of the category (from joined category row). */
  category: string
  /** Public category id from the API (`Cat_00001`). */
  categoryId: string
  inPrice: number
  outPrice: number
  commission: number
  totalStock: number
  inStock: number
  sold: number
  added: number
  damaged: number
  status: 'active' | 'inactive' | 'out_of_stock'
  /** Stock level band from backend (`GET /products` and `/products/stock-status`). */
  stockStatus?: ProductStockStatusTier
  stockNote?: string
  createdAt: string
}

export interface FinanceEntry {
  id: string
  productName: string
  printPrice: number
  totalCommission: number
  facebook: number
  other: number
  inPriceForPos: number
  grossRevenue: number
  soldQty: number
  finalPrice: number
}

export interface ReportRow {
  invoiceNo: string
  date: string
  product: string
  customer: string
  phoneCustomer: string
  seller: string
  phoneSaler: string
  source: string
  address: string
  amount: number
}

export interface DeliveryEntry {
  invoiceId: string
  address: string
  deliveryType: 'VET' | 'Domnaksiiksa' | 'Grap' | 'J&T'
  deliveryPrice: number
  deliveryStatus: string
  date: string
}

export interface CommissionEntry {
  id: string
  seller: string
  product: string
  customer: string
  source: string
  date: string
  amount: number
  commission: number
  saleCount?: number
}

export interface SystemRole {
  id: number
  name: string
  pageAccess: string[]
}

export interface SystemUser {
  id: number
  name: string
  role: string
  email: string
  password?: string
  lastLogin: string
  commission: number
}

export interface User {
  id: number
  name: string
  position: string
  email: string
  role: string
  pageAccess?: string[]
  joinDate?: string
}

export interface AuthUser {
  id?: number
  name: string
  email: string
  avatar?: string
  role?: string
  pageAccess?: string[]
}

export interface AuthTokenPair {
  accessToken: string
  refreshToken: string
}
