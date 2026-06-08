// https://nuxt.com/docs/api/configuration/nuxt-config
import { defineNuxtConfig } from 'nuxt/config'

export default defineNuxtConfig({
  modules: [
    '@nuxt/eslint',
    '@nuxt/image',
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
    url: process.env.NUXT_PUBLIC_SITE_URL || 'https://anyamusicschool.com',
    name: 'Anya Music School'
  },

  nitro: {
    prerender: {
      routes: [
        '/',
        '/km',
        '/sitemap.xml',
        '/robots.txt'
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
    domains: ['images.unsplash.com'],
    quality: 80,
    format: ['webp']
  },

  ogImage: {
    zeroRuntime: true
  },

  runtimeConfig: {
    public: {
      siteUrl: process.env.NUXT_PUBLIC_SITE_URL || 'https://anyamusicschool.com',
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000/api/v1'
    }
  }
})
