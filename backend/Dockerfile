# ── Image de base ─────────────────────────────────────────────
FROM node:20-alpine AS base
WORKDIR /app
ENV NODE_ENV=production

# ── Dépendances ───────────────────────────────────────────────
FROM base AS deps
COPY package.json ./
RUN npm install --omit=dev && npm cache clean --force

# ── Image finale ──────────────────────────────────────────────
FROM base AS runner
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Utilisateur non-root
RUN addgroup -S blockside && adduser -S blockside -G blockside
USER blockside

EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD wget -qO- http://localhost:3001/health || exit 1

CMD ["node", "server.js"]
