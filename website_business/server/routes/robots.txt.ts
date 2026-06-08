import { buildRobotsTxt, normalizeSiteUrl } from '../../app/utils/seo/site'

export default defineEventHandler((event) => {
  const config = useRuntimeConfig(event)
  const siteUrl = normalizeSiteUrl(config.public.siteUrl as string) || getRequestURL(event).origin

  setHeader(event, 'Content-Type', 'text/plain; charset=utf-8')
  setHeader(event, 'Cache-Control', 'public, max-age=86400')
  return buildRobotsTxt(siteUrl)
})
