# book2pdf frontend Dockerfile
# Next.js 16 + React 19 + Tailwind CSS v4 を開発・本番両方で利用する

# ベースイメージとして Node.js 26 LTS（Alpine 版）を使用する
FROM node:26-alpine AS base

# 作業ディレクトリを /app に設定する
WORKDIR /app

# 依存ファイルを先にコピーしてインストールをキャッシュする
COPY package.json package-lock.json* ./

# 本番依存のみインストールする（開発時もこのステージをベースにする）
RUN npm ci

# アプリケーションソースをコピーする
COPY . .

# 開発用ステージ
# ホットリロードで開発サーバーを起動する
FROM base AS dev
ENV NODE_ENV=development
EXPOSE 3000
CMD ["npm", "run", "dev"]

# ビルドステージ
# Next.js をビルドする
FROM base AS builder
ENV NODE_ENV=production
RUN npm run build

# 本番実行ステージ
# ビルド済みアセットのみを含む最小イメージで起動する
FROM node:26-alpine AS runner
ENV NODE_ENV=production
WORKDIR /app

# 本番に必要なファイルのみコピーする
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/package-lock.json ./package-lock.json
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
CMD ["node", "server.js"]
