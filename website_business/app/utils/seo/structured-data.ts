import type { CourseCardItem } from '~/components/common/CourseCard.vue'
import { productSalePrice, resolveAbsoluteMediaUrl } from '~/utils/seo/media'

type JsonLdNode = Record<string, unknown>

const DEFAULT_DESCRIPTION =
  'Anya Music School — musical instruments and accessories in Cambodia. Browse guitars and more with specs, models, and prices.'

export function buildOrganizationJsonLd(
  siteUrl: string,
  siteName: string,
  sameAs: string[] = []
): JsonLdNode {
  return {
    '@type': ['Organization', 'MusicSchool'],
    '@id': `${siteUrl}/#organization`,
    name: siteName,
    url: siteUrl,
    description: DEFAULT_DESCRIPTION,
    logo: {
      '@type': 'ImageObject',
      url: `${siteUrl}/image/logo.png`
    },
    address: {
      '@type': 'PostalAddress',
      addressCountry: 'KH'
    },
    ...(sameAs.length ? { sameAs } : {})
  }
}

export function buildWebSiteJsonLd(siteUrl: string, siteName: string): JsonLdNode {
  return {
    '@type': 'WebSite',
    '@id': `${siteUrl}/#website`,
    name: siteName,
    url: siteUrl,
    description: DEFAULT_DESCRIPTION,
    publisher: { '@id': `${siteUrl}/#organization` },
    inLanguage: ['en-US', 'km-KH']
  }
}

export function buildProductJsonLd(
  item: CourseCardItem,
  siteUrl: string,
  apiBase?: string
): JsonLdNode {
  const name = [item.model, item.name].filter(Boolean).join(' ').trim() || item.name
  const price = productSalePrice(item)
  const image = item.image
    ? resolveAbsoluteMediaUrl(String(item.image), siteUrl, apiBase)
    : undefined
  const productUrl = item.category
    ? `${siteUrl}/?category=${encodeURIComponent(String(item.category))}`
    : siteUrl

  return {
    '@type': 'Product',
    name,
    description: name,
    image: image ? [image] : undefined,
    brand: {
      '@type': 'Brand',
      name: item.model || name
    },
    offers: {
      '@type': 'Offer',
      price: price > 0 ? price.toFixed(2) : undefined,
      priceCurrency: 'USD',
      availability: 'https://schema.org/InStock',
      url: productUrl
    }
  }
}

export function buildProductListJsonLd(
  products: CourseCardItem[],
  siteUrl: string,
  apiBase?: string,
  limit = 40
): JsonLdNode {
  return {
    '@type': 'ItemList',
    '@id': `${siteUrl}/#product-list`,
    numberOfItems: products.length,
    itemListElement: products.slice(0, limit).map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      item: buildProductJsonLd(item, siteUrl, apiBase)
    }))
  }
}

export function buildCatalogJsonLd(options: {
  siteUrl: string
  siteName: string
  products: CourseCardItem[]
  apiBase?: string
  categoryName?: string
  sameAs?: string[]
}) {
  const { siteUrl, siteName, products, apiBase, categoryName, sameAs = [] } = options
  const graph: JsonLdNode[] = [
    buildOrganizationJsonLd(siteUrl, siteName, sameAs),
    buildWebSiteJsonLd(siteUrl, siteName)
  ]

  if (products.length) {
    graph.push(buildProductListJsonLd(products, siteUrl, apiBase))
  }

  if (categoryName) {
    graph.push({
      '@type': 'CollectionPage',
      name: categoryName,
      url: siteUrl,
      isPartOf: { '@id': `${siteUrl}/#website` }
    })
  }

  return {
    '@context': 'https://schema.org',
    '@graph': graph
  }
}
