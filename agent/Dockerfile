# Production Dockerfile for Pi Agent Service (Option C: Local Hardened)
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY tsconfig.json ./
COPY src/ ./src/
COPY skills/ ./skills/
RUN npm run build

FROM node:20-alpine AS runner

WORKDIR /app

RUN apk add --no-cache curl

ENV NODE_ENV=production \
    PI_AGENT_PORT=3001

COPY package*.json ./
RUN npm ci --omit=dev

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/skills ./skills

EXPOSE 3001

HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:3001/health || exit 1

CMD ["node", "dist/server.js"]
