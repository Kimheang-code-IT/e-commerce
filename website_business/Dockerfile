FROM node:20-alpine AS build

WORKDIR /app
RUN corepack enable

COPY package.json pnpm-lock.yaml ./
ENV CI=true
RUN pnpm install --frozen-lockfile

COPY . .

ARG NUXT_PUBLIC_SITE_URL=https://anyamusicschool.com
ARG NUXT_PUBLIC_API_BASE=https://anyamusicschool.com/api/v1
ENV NUXT_PUBLIC_SITE_URL=$NUXT_PUBLIC_SITE_URL
ENV NUXT_PUBLIC_API_BASE=$NUXT_PUBLIC_API_BASE

RUN pnpm run build

FROM node:20-alpine AS runner

WORKDIR /app
ENV NODE_ENV=production
ENV NUXT_HOST=0.0.0.0
ENV NUXT_PORT=3000

COPY --from=build /app/.output ./.output

EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
