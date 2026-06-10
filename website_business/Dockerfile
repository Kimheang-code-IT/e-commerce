FROM node:22-alpine AS build

WORKDIR /app
RUN corepack enable && corepack prepare pnpm@11.1.3 --activate

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./
ENV CI=true
RUN pnpm install --frozen-lockfile

COPY . .

ARG NUXT_PUBLIC_SITE_URL=https://anyamusicschool.com
ARG NUXT_PUBLIC_API_BASE=https://anyamusicschool.com/api/v1
ARG NUXT_PUBLIC_GOOGLE_SITE_VERIFICATION=
ARG NUXT_PUBLIC_BING_SITE_VERIFICATION=
ENV NUXT_PUBLIC_SITE_URL=$NUXT_PUBLIC_SITE_URL
ENV NUXT_PUBLIC_API_BASE=$NUXT_PUBLIC_API_BASE
ENV NUXT_PUBLIC_GOOGLE_SITE_VERIFICATION=$NUXT_PUBLIC_GOOGLE_SITE_VERIFICATION
ENV NUXT_PUBLIC_BING_SITE_VERIFICATION=$NUXT_PUBLIC_BING_SITE_VERIFICATION

RUN pnpm run build

FROM node:22-alpine AS runner

WORKDIR /app
ENV NODE_ENV=production
ENV NUXT_HOST=0.0.0.0
ENV NUXT_PORT=3000

COPY --from=build /app/.output ./.output

EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
