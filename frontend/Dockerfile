FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG NEXT_PUBLIC_BACKEND_URL
ARG NEXT_PUBLIC_OIDC_AUTHORITY
ARG NEXT_PUBLIC_OIDC_CLIENT_ID
ARG NEXT_PUBLIC_OIDC_REDIRECT_URI
ARG NEXT_PUBLIC_OIDC_SCOPE="openid profile"
ENV NEXT_PUBLIC_BACKEND_URL=$NEXT_PUBLIC_BACKEND_URL \
    NEXT_PUBLIC_OIDC_AUTHORITY=$NEXT_PUBLIC_OIDC_AUTHORITY \
    NEXT_PUBLIC_OIDC_CLIENT_ID=$NEXT_PUBLIC_OIDC_CLIENT_ID \
    NEXT_PUBLIC_OIDC_REDIRECT_URI=$NEXT_PUBLIC_OIDC_REDIRECT_URI \
    NEXT_PUBLIC_OIDC_SCOPE=$NEXT_PUBLIC_OIDC_SCOPE

RUN npm run build

FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0 \
    PORT=3000

RUN addgroup --system --gid 10001 appgroup \
    && adduser --system --uid 10001 --ingroup appgroup appuser

COPY --from=builder --chown=appuser:appgroup /app/.next/standalone ./
COPY --from=builder --chown=appuser:appgroup /app/.next/static ./.next/static

USER 10001:10001
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD wget -q --spider http://127.0.0.1:3000/ || exit 1

CMD ["node", "server.js"]
