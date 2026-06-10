import { SOCIAL_LINKS, TELEGRAM_URL } from './config/social-links'

export default defineAppConfig({
  ui: {
    colors: {
      primary: 'primary',
      neutral: 'slate',
      success: 'gold',
      warning: 'primary'
    },
    footer: {
      slots: {
        root: 'border-t border-default',
        left: 'text-sm text-muted'
      }
    }
  },
  seo: {
    siteName: 'Anya Music School'
  },
  social: SOCIAL_LINKS,
  floatingTelegram: {
    enabled: true,
    to: TELEGRAM_URL
  },
  banner: {
    interval: 5000,
    colorMode: true,
    notifications: [
      { icon: 'i-lucide-megaphone', key: 'newArrivals' },
      { icon: 'i-lucide-sparkles', key: 'browseCatalog' },
      { icon: 'i-lucide-package', key: 'qualityProducts' }
    ],
    social: SOCIAL_LINKS
  },
  header: {
    title: 'Anya Music School',
    to: '/'
  },
  footer: {
    nav: SOCIAL_LINKS
  }
})
