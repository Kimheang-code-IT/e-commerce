import { SOCIAL_LINKS, type SocialLink } from '~/config/social-links'

export function useSocialLinks() {
  const appConfig = useAppConfig()

  return computed<SocialLink[]>(() => {
    const fromConfig = (appConfig as { social?: SocialLink[] }).social
    if (fromConfig?.length) return fromConfig
    return SOCIAL_LINKS
  })
}
