export type SitemapEntry = {
  loc: string
  lastmod?: string
  changefreq?: 'always' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'yearly' | 'never'
  priority?: number
  alternates?: Record<string, string>
}

function escapeXml(value: string) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll('\'', '&apos;')
}

export function normalizeSiteUrl(value: string | undefined) {
  const raw = String(value || '').trim()
  if (!raw) return ''
  return raw.replace(/\/+$/, '')
}

export function buildLocalizedPaths(path = '', categoryId = '') {
  const normalizedPath = path ? `/${path.replace(/^\/+/, '')}` : ''
  const query = categoryId ? `?category=${encodeURIComponent(categoryId)}` : ''
  const en = normalizedPath ? `${normalizedPath}${query}` : query ? `/${query}` : '/'
  const km = normalizedPath ? `/km${normalizedPath}${query}` : query ? `/km${query}` : '/km'
  return { en, km }
}

export function buildSitemapXml(entries: SitemapEntry[]) {
  const urls = entries.map((entry) => {
    const altLinks = Object.entries(entry.alternates || {})
      .map(([lang, href]) =>
        `    <xhtml:link rel="alternate" hreflang="${escapeXml(lang)}" href="${escapeXml(href)}" />`
      )
      .join('\n')

    return [
      '  <url>',
      `    <loc>${escapeXml(entry.loc)}</loc>`,
      entry.lastmod ? `    <lastmod>${escapeXml(entry.lastmod)}</lastmod>` : '',
      entry.changefreq ? `    <changefreq>${entry.changefreq}</changefreq>` : '',
      entry.priority != null ? `    <priority>${entry.priority.toFixed(1)}</priority>` : '',
      altLinks,
      '  </url>'
    ].filter(Boolean).join('\n')
  }).join('\n')

  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    urls,
    '</urlset>'
  ].join('\n')
}

export function buildRobotsTxt(siteUrl: string) {
  const base = normalizeSiteUrl(siteUrl)
  const sitemapLine = base ? `Sitemap: ${base}/sitemap.xml` : ''
  return [
    'User-agent: *',
    'Allow: /',
    '',
    sitemapLine
  ].filter(Boolean).join('\n')
}
