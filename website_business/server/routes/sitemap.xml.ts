import {
  buildLocalizedPaths,
  buildSitemapXml,
  normalizeSiteUrl,
  type SitemapEntry
} from '../../app/utils/seo/site'

type CatalogCategory = {
  id?: string
  name?: string
}

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig(event)
  const siteUrl = normalizeSiteUrl(config.public.siteUrl as string) || getRequestURL(event).origin
  const apiBase = String(config.public.apiBase || '').replace(/\/+$/, '')
  const today = new Date().toISOString().slice(0, 10)

  let categories: CatalogCategory[] = []
  if (apiBase) {
    try {
      const response = await $fetch<{ data?: CatalogCategory[] }>(`${apiBase}/catalog/categories`, {
        query: { page: 1, limit: 200 }
      })
      categories = response.data || []
    } catch {
      categories = []
    }
  }

  const entries: SitemapEntry[] = [
    {
      loc: `${siteUrl}/`,
      lastmod: today,
      changefreq: 'daily',
      priority: 1,
      alternates: {
        en: `${siteUrl}/`,
        km: `${siteUrl}/km`,
        'x-default': `${siteUrl}/`
      }
    }
  ]

  for (const category of categories) {
    const categoryId = String(category.id || '').trim()
    if (!categoryId) continue

    const paths = buildLocalizedPaths('', categoryId)
    entries.push({
      loc: `${siteUrl}${paths.en}`,
      lastmod: today,
      changefreq: 'daily',
      priority: 0.8,
      alternates: {
        en: `${siteUrl}${paths.en}`,
        km: `${siteUrl}${paths.km}`,
        'x-default': `${siteUrl}${paths.en}`
      }
    })
  }

  setHeader(event, 'Content-Type', 'application/xml; charset=utf-8')
  setHeader(event, 'Cache-Control', 'public, max-age=3600, s-maxage=3600')
  return buildSitemapXml(entries)
})
