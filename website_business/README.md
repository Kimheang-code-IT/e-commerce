# Anya Music School — public website

Nuxt 4 catalog site at **https://anyamusicschool.com**.

## Google Search (SEO)

The site is built for search engines:

- **SSR** — product content is rendered on the server for crawlers
- **`/robots.txt`** — allows all pages, points to sitemap
- **`/sitemap.xml`** — home + category pages (EN/KM), refreshed from the API
- **Meta tags** — title, description, keywords, Open Graph, Twitter Card
- **JSON-LD** — Organization, WebSite, Product list, CollectionPage
- **Canonical + hreflang** — English and Khmer locales

### 1. Set production URL

In the repo root `.env`:

```env
NUXT_PUBLIC_SITE_URL=https://anyamusicschool.com
NUXT_PUBLIC_API_BASE=https://anyamusicschool.com/api/v1
```

Rebuild the website container after changing env:

```bash
./build-admin.sh --website-only
```

### 2. Verify URLs work

```bash
curl -s https://anyamusicschool.com/robots.txt
curl -s https://anyamusicschool.com/sitemap.xml
```

You should see `Allow: /`, `Sitemap: https://anyamusicschool.com/sitemap.xml`, and XML with your category URLs.

### 3. Google Search Console

1. Open [Google Search Console](https://search.google.com/search-console)
2. Add property: **https://anyamusicschool.com**
3. Choose **HTML tag** verification
4. Copy the **content** value only (e.g. `abc123xyz`)
5. Add to root `.env`:

```env
NUXT_PUBLIC_GOOGLE_SITE_VERIFICATION=abc123xyz
```

6. Rebuild and deploy:

```bash
./build-admin.sh --website-only
```

7. Click **Verify** in Search Console
8. Go to **Sitemaps** → submit: `https://anyamusicschool.com/sitemap.xml`
9. Use **URL inspection** on the homepage → **Request indexing**

Indexing usually takes a few days to a few weeks. New products appear in the sitemap on the next request (cached ~1 hour).

### Alternative verification

Drop Google's HTML file (e.g. `google123abc.html`) into `website_business/public/` and rebuild.

## Local dev

```bash
cd website_business
cp .env.example .env
pnpm install
pnpm dev
```

Open http://localhost:3000
