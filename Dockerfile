# syntax=docker/dockerfile:1.4
# Mesh Agent Lite — P2P mesh агент + тесты всех модулей связи
# Включает: phase0, relay, sdk, core, coordination, phase1, CLI, examples
# Multi-stage build, <120MB final image

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

# === CORE: Transport, Identity, Crypto ===
COPY phase0/ phase0/

# === RELAY: NAT traversal ===
COPY relay/ relay/

# === SDK: Agent API ===
COPY sdk/ sdk/

# === PHASE 1: Discovery + Reputation ===
COPY phase1/ phase1/

# === CORE: Chrono DB, Reputation ===
COPY core/ core/

# === COORDINATION: Dedup, Consumer Group ===
COPY coordination/ coordination/

# === TOOLS ===
COPY cli_v2.py connect_direct.py connect_peers.py ./

# === EXAMPLES ===
COPY examples/ examples/

# === MAIN AGENTS ===
COPY mesh_agent.py mesh_ping.py simple_agent.py ./

# === TESTS ===
COPY test_suite.py ./

# === DOCS ===
COPY SPEC_CAPABILITIES.md INSTRUCTIONS.md ./

# Non-root user
RUN useradd -m -u 1000 mesh && chown -R mesh:mesh /app
USER mesh

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python3 -c "import socket; s=socket.socket(); s.connect(('localhost',9908)); s.close()" || exit 1

# Default: show capabilities
CMD ["python3", "-c", "print('Mesh Agent Lite — Docker'); print('Запусти: docker run --rm mesh-agent-lite python3 test_suite.py --hub HOST:PORT'); print('Или: docker run --rm mesh-agent-lite python3 cli_v2.py --port 9908')"]
