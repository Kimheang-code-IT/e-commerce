import type { Product } from '~/types'

export type InvoiceReopenLine = {
  productId?: number
  product?: string
  qty?: number
  price?: number
  total?: number
  inStock?: number
  outPrice?: number
  salePrice?: number
  image?: string
  categoryId?: string
  category?: string
  status?: string
}

export type PosCartItem = {
  /** Stable row id (same product may appear on multiple lines at different prices). */
  lineId: string
  product: Product
  qty: number
  /** Sale unit price for this line (FIFO batch or manual edit). */
  unitPrice?: number
  /** True when cashier edited price on this line (kept during FIFO resync). */
  manualPrice?: boolean
}

export function createCartLineId(): string {
  return `line-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

export function getCatalogUnitPrice(product: Product): number {
  return Number(product.salePrice ?? product.outPrice ?? 0)
}

export function productFromInvoiceLine(line: InvoiceReopenLine, index: number): Product | null {
  const id = Number(line.productId || 0)
  if (!id || id <= 0) return null
  const status = String(line.status || 'active')
  const normalizedStatus: Product['status'] =
    status === 'inactive' || status === 'out_of_stock' ? status : 'active'
  return {
    id,
    image: String(line.image || ''),
    name: String(line.product || `Product ${id}`),
    category: String(line.category || ''),
    categoryId: String(line.categoryId || ''),
    inPrice: 0,
    outPrice: Number(line.outPrice ?? line.price ?? 0),
    salePrice: Number(line.salePrice ?? line.outPrice ?? line.price ?? 0),
    commission: 0,
    totalStock: 0,
    inStock: Number(line.inStock ?? 0),
    sold: 0,
    added: 0,
    damaged: 0,
    status: normalizedStatus,
    createdAt: new Date().toISOString(),
  }
}

export function unitPriceFromLine(line: InvoiceReopenLine, product: Product): number | undefined {
  const catalog = getCatalogUnitPrice(product)
  const linePrice = Number(line.price ?? 0)
  if (linePrice > 0 && Math.abs(linePrice - catalog) > 0.001) {
    return linePrice
  }
  return undefined
}

export function getLineUnitPrice(item: PosCartItem): number {
  if (item.unitPrice != null && Number.isFinite(item.unitPrice)) {
    return Number(item.unitPrice)
  }
  return getCatalogUnitPrice(item.product)
}

export function isLinePriceCustom(item: PosCartItem): boolean {
  return Boolean(item.manualPrice)
}

export function getLineTotal(item: PosCartItem): number {
  return getLineUnitPrice(item) * Number(item.qty || 0)
}

/** Invoice / print rows: separate lines per price; reference label when same product name. */
export function buildInvoiceDisplayRows(cart: PosCartItem[]) {
  const countByName = new Map<string, number>()
  for (const item of cart) {
    const name = (item.product.name || '').trim()
    countByName.set(name, (countByName.get(name) || 0) + 1)
  }
  const refIndexByName = new Map<string, number>()

  return cart.map((item, index) => {
    const name = (item.product.name || '').trim()
    const duplicateName = (countByName.get(name) || 0) > 1
    let priceRef = ''
    if (duplicateName) {
      const next = (refIndexByName.get(name) || 0) + 1
      refIndexByName.set(name, next)
      priceRef = String.fromCharCode(64 + next) // A, B, C…
    }
    const unitPrice = getLineUnitPrice(item)
    const editedPrice = Boolean(item.manualPrice)

    return {
      item,
      lineKey: item.lineId || `row-${index}`,
      rowNo: index + 1,
      unitPrice,
      lineTotal: getLineTotal(item),
      showPriceRef: duplicateName,
      priceRef,
      editedPrice,
    }
  })
}

export function mapCartToApiLines(cart: PosCartItem[]) {
  const merged = new Map<
    number,
    { productId: number; qty: number; lineTotal: number; unitPrice?: number }
  >()

  for (const item of cart) {
    const productId = item.product.id
    const qty = Number(item.qty || 0)
    const unitPrice = getLineUnitPrice(item)
    const lineTotal = unitPrice * qty
    const existing = merged.get(productId)

    if (!existing) {
      merged.set(productId, {
        productId,
        qty,
        lineTotal,
        unitPrice: item.manualPrice ? unitPrice : undefined,
      })
      continue
    }

    existing.qty += qty
    existing.lineTotal += lineTotal
    if (item.manualPrice || existing.unitPrice != null) {
      existing.unitPrice = existing.qty > 0 ? existing.lineTotal / existing.qty : unitPrice
    }
  }

  return Array.from(merged.values()).map((row) => ({
    productId: row.productId,
    qty: row.qty,
    unitPrice: row.unitPrice,
  }))
}

export function buildCheckoutPayload(input: {
  customerName: string
  customerPhone: string
  customerAddress: string
  deliveryType: string
  deliveryPrice: number
  deliveryDate: string
  discountAmount: number
  paymentMethod: string
  deliveryStatus: string
  sellerId?: number
  lines: Array<{ productId: number; qty: number; unitPrice?: number }>
}) {
  return {
    customerName: input.customerName,
    customerPhone: input.customerPhone,
    customerAddress: input.customerAddress,
    source: 'other',
    deliveryType: input.deliveryType,
    deliveryPrice: Number(input.deliveryPrice || 0),
    deliveryDate: input.deliveryDate,
    discountAmount: Number(input.discountAmount || 0),
    paymentMethod: input.paymentMethod || 'cash',
    deliveryStatus: input.deliveryStatus || 'pending',
    sellerId: input.sellerId,
    lines: input.lines
  }
}

export function handleApiError(error: any, fallback = 'Request failed') {
  return String(error?.data?.message || error?.message || fallback)
}

export function resetCustomerForm() {
  return {
    customerType: 'Customer',
    customerName: '',
    customerPhone: '',
    customerAddress: '',
    addressNote: '',
    deliveryType: 'VET',
    deliveryPrice: 2,
    deliveryDate: new Date().toISOString(),
    paymentMethod: 'cash',
    deliveryStatus: 'pending',
    sellerId: undefined as number | undefined
  }
}
