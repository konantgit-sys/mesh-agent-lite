# syntax=docker/dockerfile:1.4
# Mesh Agent Lite — P2P mesh агент для тестирования связи
# Multi-stage build, <100MB final image

# === Stage 1: builder ===
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt ./
RUN pip install --user --no-cache-dir -r requirements.txt

# === Stage 2: runtime ===
FROM python:3.11-slim AS runtime

WORKDIR /app

# Runtime libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 ca-certificates netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy pip packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY phase0/ phase0/
COPY relay/ relay/
COPY sdk/ sdk/
COPY mesh_agent.py mesh_ping.py simple_agent.py test_suite.py requirements.txt ./

# Non-root user
RUN useradd -m -u 1000 mesh && chown -R mesh:mesh /app
USER mesh

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python3 -c "import socket; s=socket.socket(); s.connect(('localhost',9908)); s.close(); print('ok')" || exit 1

# Default: show help
CMD ["python3", "simple_agent.py", "--help"]
