# Multi-stage: generate Nuxt SPA into nginx image (no separate frontend container).
FROM node:20-alpine AS frontend-build

WORKDIR /app
RUN corepack enable

COPY Frontend/package.json Frontend/pnpm-lock.yaml ./
ENV CI=true
RUN pnpm install --frozen-lockfile

COPY Frontend/app ./app
COPY Frontend/public ./public
COPY Frontend/i18n ./i18n
COPY Frontend/nuxt.config.ts ./
COPY Frontend/tsconfig.json ./
COPY Frontend/eslint.config.mjs ./
COPY Frontend/vitest.config.ts ./

# Baked into the client bundle at generate time (override with docker compose build.args).
ARG NUXT_PUBLIC_SITE_URL=
ARG NUXT_PUBLIC_API_BASE=/api/v1
ARG NUXT_PUBLIC_USE_BACKEND_API=true
ENV NUXT_PUBLIC_SITE_URL=$NUXT_PUBLIC_SITE_URL
ENV NUXT_PUBLIC_API_BASE=$NUXT_PUBLIC_API_BASE
ENV NUXT_PUBLIC_USE_BACKEND_API=$NUXT_PUBLIC_USE_BACKEND_API

RUN pnpm exec nuxi generate

FROM nginx:1.27-alpine

COPY --from=frontend-build /app/.output/public /usr/share/nginx/html

# Self-signed TLS for port 443 (local Wi‑Fi / LAN); replace with real certs in production
RUN apk add --no-cache openssl \
    && mkdir -p /etc/nginx/ssl \
    && openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
        -subj "/CN=localhost/O=ecom-local" \
        -keyout /etc/nginx/ssl/self.key \
        -out /etc/nginx/ssl/self.crt

COPY nginx/conf.d/00-upstream.conf /etc/nginx/conf.d/00-upstream.conf
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY nginx/snippets/wifi-proxy.conf /etc/nginx/snippets/wifi-proxy.conf
