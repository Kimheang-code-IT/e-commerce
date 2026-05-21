# Optional: build static assets only (main deploy path is nginx/Dockerfile which runs nuxi generate).
# Output: /app/.output/public
FROM node:20-alpine AS build

WORKDIR /app
RUN corepack enable

COPY package.json pnpm-lock.yaml ./
ENV CI=true
RUN pnpm install --frozen-lockfile

COPY app ./app
COPY public ./public
COPY i18n ./i18n
COPY nuxt.config.ts ./
COPY tsconfig.json ./
COPY eslint.config.mjs ./
COPY vitest.config.ts ./

ARG NUXT_PUBLIC_SITE_URL=
ARG NUXT_PUBLIC_API_BASE=/api/v1
ARG NUXT_PUBLIC_USE_BACKEND_API=true
ENV NUXT_PUBLIC_SITE_URL=$NUXT_PUBLIC_SITE_URL
ENV NUXT_PUBLIC_API_BASE=$NUXT_PUBLIC_API_BASE
ENV NUXT_PUBLIC_USE_BACKEND_API=$NUXT_PUBLIC_USE_BACKEND_API

RUN pnpm exec nuxi generate

# Static files at /app/.output/public (copy into nginx or host volume as needed).
