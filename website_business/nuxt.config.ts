// https://nuxt.com/docs/api/configuration/nuxt-config
import { defineNuxtConfig } from 'nuxt/config'

const apiBase = process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000/api/v1'
const siteUrl = process.env.NUXT_PUBLIC_SITE_URL || 'https://anyamusicschool.com'
const googleSiteVerification =
  process.env.NUXT_PUBLIC_GOOGLE_SITE_VERIFICATION || '5BNRjT7h8ONl_lUjaoiXOK6LM8gIpF0dHmd-8ltN63A'
const bingSiteVerification =
  process.env.NUXT_PUBLIC_BING_SITE_VERIFICATION || '3E6BA499AB5B23085685831BC87434D3'

const verificationMeta = [
  ...(googleSiteVerification
    ? [{ name: 'google-site-verification', content: googleSiteVerification }]
    : []),
  ...(bingSiteVerification ? [{ name: 'msvalidate.01', content: bingSiteVerification }] : [])
]

function hostnameFromUrl(value: string) {
  try {
    return new URL(value).hostname
  } catch {
    return ''
  }
}

const imageDomains = [
  'images.unsplash.com',
  hostnameFromUrl(apiBase),
  hostnameFromUrl(siteUrl)
].filter((host): host is string => Boolean(host))

export default defineNuxtConfig({
  modules: [
    '@nuxt/eslint',
    '@nuxt/image',
    '@nuxtjs/color-mode',
    '@nuxt/ui',
    '@nuxtjs/i18n',
    'nuxt-og-image'
  ],

  components: [
    {
      path: '~/components',
      ignore: ['layouts/**']
    },
    {
      path: '~/components/layouts',
      pathPrefix: false
    },
    {
      path: '~/components/common',
      pathPrefix: false
    }
  ],

  devtools: {
    enabled: true
  },

  css: ['~/assets/css/main.css'],

  colorMode: {
    preference: 'system',
    fallback: 'light',
    classSuffix: ''
  },

  experimental: {
    asyncContext: true
  },

  compatibilityDate: '2024-07-11',

  site: {
    url: siteUrl,
    name: 'Anya Music School'
  },

  app: {
    head: {
      charset: 'utf-8',
      viewport: 'width=device-width, initial-scale=1',
      meta: verificationMeta
    }
  },

  nitro: {
    prerender: {
      routes: [
        '/',
        '/km',
        '/sitemap.xml',
        '/robots.txt',
        '/site.webmanifest'
      ],
      crawlLinks: false,
      autoSubfolderIndex: false,
      failOnError: false
    }
  },

  eslint: {
    config: {
      stylistic: {
        commaDangle: 'never',
        braceStyle: '1tbs'
      }
    }
  },

  i18n: {
    locales: [
      { code: 'en', name: 'English', language: 'en-US', file: 'en.json' },
      { code: 'km', name: 'ខ្មែរ', language: 'km-KH', file: 'km.json' }
    ],
    defaultLocale: 'en',
    strategy: 'prefix_except_default',
    langDir: 'locales',
    restructureDir: 'i18n',
    detectBrowserLanguage: {
      useCookie: true,
      cookieKey: 'i18n_redirected',
      redirectOn: 'root'
    }
  },

  fonts: {
    providers: {
      google: false,
      bunny: false,
      fontshare: false,
      fontsource: false,
      adobe: false
    },
    families: [
      { name: 'Public Sans', provider: 'npm' },
      { name: 'Kantumruy Pro', provider: 'npm' },
      { name: 'Noto Sans Khmer', provider: 'npm' }
    ]
  },

  icon: {
    provider: 'iconify'
  },

  image: {
    domains: imageDomains,
    quality: 80,
    format: ['webp', 'jpeg', 'png'],
    densities: [1, 2]
  },

  ogImage: {
    zeroRuntime: true
  },

  runtimeConfig: {
    public: {
      siteUrl,
      apiBase,
      googleSiteVerification,
      bingSiteVerification
    }
  }
})
