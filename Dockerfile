# ── Stage 1: builder ───────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh

WORKDIR /app

COPY . .

RUN uv pip install --system .

# ── Stage 2: runtime ───────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages and entrypoint from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/wallet-mcp /usr/local/bin/wallet-mcp
COPY --from=builder /app/src /app/src

# Persistent wallet data volume
RUN mkdir -p /data
VOLUME ["/data"]

# Non-root user for security
RUN useradd -m mcpuser && chown -R mcpuser:mcpuser /app /data
USER mcpuser

ENV WALLET_DATA_DIR=/data \
    PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "from wallet_mcp.server import mcp; print('ok')" || exit 1

ENTRYPOINT ["wallet-mcp"]
CMD ["streamable-http", "--host", "0.0.0.0", "--port", "8000"]
