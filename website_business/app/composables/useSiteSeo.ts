import { defaultOgImage, resolveAbsoluteMediaUrl } from '~/utils/seo/media'
import { normalizeSiteUrl } from '~/utils/seo/site'

type JsonLdPayload = Record<string, unknown> | Record<string, unknown>[]

export type PageSeoOptions = {
  title?: string
  description?: string
  keywords?: string
  image?: string
  imageAlt?: string
  jsonLd?: JsonLdPayload
  noindex?: boolean
}

export function useSiteSeo() {
  const config = useRuntimeConfig()
  const route = useRoute()
  const { locale, t } = useI18n()
  const { seo } = useAppConfig()

  const siteName = computed(() => seo?.siteName || t('seo.siteName'))
  const siteUrl = computed(() =>
    normalizeSiteUrl(config.public.siteUrl as string) || (import.meta.client ? window.location.origin : '')
  )
  const apiBase = computed(() => String(config.public.apiBase || ''))

  const canonicalUrl = computed(() => {
    const base = siteUrl.value
    if (!base) return ''
    const path = route.path === '/' ? '/' : route.path
    const query = route.query.category ? `?category=${encodeURIComponent(String(route.query.category))}` : ''
    return `${base}${path}${query}`
  })

  const alternateLinks = computed(() => {
    const base = siteUrl.value
    if (!base) return []

    const category = route.query.category ? `?category=${encodeURIComponent(String(route.query.category))}` : ''
    const enPath = locale.value === 'en' ? route.path : route.path.replace(/^\/km/, '') || '/'
    const kmPath = locale.value === 'km' ? route.path : (route.path === '/' ? '/km' : `/km${route.path}`)

    return [
      { rel: 'alternate', hreflang: 'en', href: `${base}${enPath}${category}` },
      { rel: 'alternate', hreflang: 'km', href: `${base}${kmPath}${category}` },
      { rel: 'alternate', hreflang: 'x-default', href: `${base}${enPath}${category}` }
    ]
  })

  const localeOgTag = computed(() => (locale.value === 'km' ? 'km_KH' : 'en_US'))

  function resolvePageImage(image?: string) {
    if (!image) return defaultOgImage(siteUrl.value)
    return resolveAbsoluteMediaUrl(image, siteUrl.value, apiBase.value)
  }

  function buildJsonLdScripts(payload?: JsonLdPayload) {
    if (!payload) return []
    const nodes = Array.isArray(payload) ? payload : [payload]
    return nodes.map((node, index) => ({
      type: 'application/ld+json',
      key: `jsonld-${String(node['@graph'] ? 'graph' : node['@type'] || index)}`,
      innerHTML: JSON.stringify(node)
    }))
  }

  function applyPageSeo(options?: PageSeoOptions) {
    const title = options?.title || siteName.value
    const description = options?.description || t('home.seoDescription')
    const keywords = options?.keywords || t('seo.keywords')
    const image = resolvePageImage(options?.image)
    const imageAlt = options?.imageAlt || t('seo.defaultOgImageAlt')
    const robots = options?.noindex ? 'noindex, nofollow' : 'index, follow, max-image-preview:large'

    useSeoMeta({
      title,
      description,
      keywords,
      ogTitle: title,
      ogDescription: description,
      ogType: 'website',
      ogUrl: canonicalUrl.value,
      ogSiteName: siteName.value,
      ogImage: image,
      ogImageAlt: imageAlt,
      ogImageWidth: 1200,
      ogImageHeight: 630,
      ogLocale: localeOgTag.value,
      twitterCard: 'summary_large_image',
      twitterTitle: title,
      twitterDescription: description,
      twitterImage: image,
      twitterImageAlt: imageAlt,
      robots
    })

    useHead({
      link: [
        ...(canonicalUrl.value ? [{ rel: 'canonical', href: canonicalUrl.value }] : []),
        ...alternateLinks.value
      ],
      script: buildJsonLdScripts(options?.jsonLd)
    })
  }

  return {
    siteName,
    siteUrl,
    apiBase,
    canonicalUrl,
    applyPageSeo,
    resolvePageImage
  }
}
