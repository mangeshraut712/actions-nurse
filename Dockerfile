FROM node:22-bookworm-slim AS memory
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /memory
COPY meterless/package.json meterless/package-lock.json ./
RUN npm ci --no-audit --no-fund && npm run setup
COPY meterless/engine.ts meterless/nurse-memory.ts ./
COPY meterless/seed ./seed

FROM python:3.12-slim-bookworm
WORKDIR /app
COPY --from=memory /usr/local/bin/node /usr/local/bin/node
COPY --from=memory /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx
COPY --from=memory /memory ./meterless
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY nurse.py activity_log.py memory_bridge.py ./
COPY integrations ./integrations
COPY fixtures ./fixtures
COPY docs/fixtures-img/red-actions-permission-failure.png ./docs/fixtures-img/
COPY web ./web
# Optional demo trace path (created empty so health/activity status is stable)
RUN mkdir -p demo/activity
ENV PORT=8787
EXPOSE 8787
CMD ["uvicorn", "nurse:app", "--host", "0.0.0.0", "--port", "8787"]

