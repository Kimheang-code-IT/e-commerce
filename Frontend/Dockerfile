# Optional: build static assets only. Main deploy: host nginx serves Frontend/.output/public after `pnpm exec nuxi generate`.
# Output: /app/.output/public
FROM node:20-alpine AS build

WORKDIR /app
RUN corepack enable && corepack prepare pnpm@10.30.3 --activate

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./
ENV CI=true
RUN pnpm install --frozen-lockfile

COPY app ./app
COPY public ./public
COPY i18n ./i18n
COPY nuxt.config.ts ./
COPY tsconfig.json ./
COPY eslint.config.mjs ./
COPY vitest.config.ts ./

ARG NUXT_PUBLIC_SITE_URL=https://admin.anyamusicschool.com
ARG NUXT_PUBLIC_API_BASE=/api/v1
ARG NUXT_PUBLIC_USE_BACKEND_API=true
ENV NUXT_PUBLIC_SITE_URL=$NUXT_PUBLIC_SITE_URL
ENV NUXT_PUBLIC_API_BASE=$NUXT_PUBLIC_API_BASE
ENV NUXT_PUBLIC_USE_BACKEND_API=$NUXT_PUBLIC_USE_BACKEND_API

RUN pnpm exec nuxi generate

# Static files at /app/.output/public (copy into nginx or host volume as needed).
