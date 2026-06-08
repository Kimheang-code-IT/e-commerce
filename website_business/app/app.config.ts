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
  floatingTelegram: {
    enabled: true,
    to: 'https://t.me/yourusername'
  },
  banner: {
    interval: 5000,
    colorMode: true,
    notifications: [
      { icon: 'i-lucide-megaphone', key: 'newArrivals' },
      { icon: 'i-lucide-sparkles', key: 'browseCatalog' },
      { icon: 'i-lucide-package', key: 'qualityProducts' }
    ],
    social: [
      {
        icon: 'i-simple-icons-facebook',
        to: 'https://facebook.com',
        label: 'Facebook',
        class: 'bg-[#1877F2] hover:bg-[#166fe5]'
      },
      {
        icon: 'i-simple-icons-telegram',
        to: 'https://telegram.org',
        label: 'Telegram',
        class: 'bg-[#26A5E4] hover:bg-[#1f95d0]'
      },
      {
        icon: 'i-simple-icons-youtube',
        to: 'https://youtube.com',
        label: 'YouTube',
        class: 'bg-[#FF0000] hover:bg-[#e60000]'
      },
      {
        icon: 'i-simple-icons-linkedin',
        to: 'https://linkedin.com',
        label: 'LinkedIn',
        class: 'bg-[#0A66C2] hover:bg-[#0958aa]'
      }
    ]
  },
  header: {
    title: 'Anya Music School',
    to: '/'
  },
  footer: {
    nav: [
      { slug: 'about' },
      { slug: 'team' },
      { slug: 'careers' },
      { slug: 'jobs' },
      { slug: 'contact' },
      { slug: 'terms' },
      { slug: 'privacy' },
      { slug: 'refund' },
      { slug: 'cookies' },
      { slug: 'faq' }
    ],
    social: [
      { icon: 'i-simple-icons-facebook', to: 'https://facebook.com', label: 'Facebook' },
      { icon: 'i-simple-icons-x', to: 'https://x.com', label: 'X' },
      { icon: 'i-simple-icons-youtube', to: 'https://youtube.com', label: 'YouTube' },
      { icon: 'i-simple-icons-linkedin', to: 'https://linkedin.com', label: 'LinkedIn' },
      { icon: 'i-simple-icons-instagram', to: 'https://instagram.com', label: 'Instagram' }
    ]
  }
})
