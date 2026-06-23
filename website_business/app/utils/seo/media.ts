import { normalizeSiteUrl } from '~/utils/seo/site'

export const DEFAULT_OG_IMAGE_PATH = '/image/favicon-192.png'

export function defaultOgImage(siteUrl: string) {
  const base = normalizeSiteUrl(siteUrl)
  return base ? `${base}${DEFAULT_OG_IMAGE_PATH}` : DEFAULT_OG_IMAGE_PATH
}

export function apiOriginFromBase(apiBase: string | undefined, siteUrl: string) {
  const raw = String(apiBase || '').trim()
  if (!raw) return normalizeSiteUrl(siteUrl)
  try {
    const url = new URL(raw)
    return `${url.protocol}//${url.host}`
  } catch {
    return normalizeSiteUrl(siteUrl)
  }
}

/** Absolute URL for Open Graph / JSON-LD images. */
export function resolveAbsoluteMediaUrl(
  src: string | undefined,
  siteUrl: string,
  apiBase?: string
) {
  const value = String(src || '').trim()
  if (!value) return defaultOgImage(siteUrl)

  if (value.startsWith('http://') || value.startsWith('https://')) {
    return value
  }

  const site = normalizeSiteUrl(siteUrl)
  const apiOrigin = apiOriginFromBase(apiBase, site)
  const origin = value.startsWith('/uploads') ? apiOrigin : site
  if (!origin) return value.startsWith('/') ? value : `/${value}`
  return value.startsWith('/') ? `${origin}${value}` : `${origin}/${value}`
}

export function productSalePrice(item: {
  outPrice?: string | number
  totalPrice?: string | number
  discountPrice?: string | number
}) {
  const out = Number(item.outPrice ?? item.totalPrice ?? 0)
  const sale = Number(item.discountPrice ?? 0)
  if (sale > 0 && sale < out) return sale
  return out
}
