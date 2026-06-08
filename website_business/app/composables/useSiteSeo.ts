import { normalizeSiteUrl } from '~/utils/seo/site'

export function useSiteSeo() {
  const config = useRuntimeConfig()
  const route = useRoute()
  const { locale, t } = useI18n()
  const { seo } = useAppConfig()

  const siteName = computed(() => seo?.siteName || t('seo.siteName'))
  const siteUrl = computed(() =>
    normalizeSiteUrl(config.public.siteUrl as string) || (import.meta.client ? window.location.origin : '')
  )

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

  function applyPageSeo(options?: {
    title?: string
    description?: string
    keywords?: string
  }) {
    const title = options?.title || siteName.value
    const description = options?.description || t('home.seoDescription')
    const keywords = options?.keywords || t('seo.keywords')

    useSeoMeta({
      title,
      description,
      keywords,
      ogTitle: title,
      ogDescription: description,
      ogType: 'website',
      ogUrl: canonicalUrl.value,
      ogSiteName: siteName.value,
      twitterCard: 'summary_large_image',
      twitterTitle: title,
      twitterDescription: description,
      robots: 'index, follow, max-image-preview:large'
    })

    useHead({
      link: [
        ...(canonicalUrl.value ? [{ rel: 'canonical', href: canonicalUrl.value }] : []),
        ...alternateLinks.value
      ]
    })
  }

  return {
    siteName,
    siteUrl,
    canonicalUrl,
    applyPageSeo
  }
}
