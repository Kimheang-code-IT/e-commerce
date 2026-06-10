export interface SocialLink {
  icon: string
  to: string
  /** English only — not passed through i18n. */
  label: string
  class?: string
}

export const SOCIAL_LINKS: SocialLink[] = [
  {
    icon: 'i-simple-icons-facebook',
    to: 'https://www.facebook.com/saladontreianya?mibextid=wwXIfr',
    label: 'Facebook',
    class: 'bg-[#1877F2] hover:bg-[#166fe5]'
  },
  {
    icon: 'i-simple-icons-telegram',
    to: 'https://t.me/Info_Anya_music_school',
    label: 'Telegram',
    class: 'bg-[#26A5E4] hover:bg-[#1f95d0]'
  },
  {
    icon: 'i-simple-icons-tiktok',
    to: 'https://www.tiktok.com/@anyamusicschool?_r=1&_t=ZS-9756P2TesyX',
    label: 'TikTok',
    class: 'bg-black hover:bg-neutral-800'
  }
]

export const TELEGRAM_URL = SOCIAL_LINKS[1]!.to
