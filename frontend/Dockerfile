# book2pdf frontend Dockerfile
# Next.js 15 + React 19 + Tailwind CSS v4 を開発・本番両方で利用する

FROM node:22-slim AS base
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm cache clean --force && npm ci
COPY . .

FROM base AS dev
ENV NODE_ENV=development
EXPOSE 3000
CMD ["npm", "run", "dev"]

FROM base AS builder
ENV NODE_ENV=production
RUN npm run build

FROM node:22-slim AS runner
ENV NODE_ENV=production
WORKDIR /app
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/package-lock.json ./package-lock.json
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
CMD ["node", "server.js"]
