FROM python:3.11-slim

LABEL description="Mesh Agent Light — P2P mesh agent with infinity proofs"
LABEL version="2.0.0"

WORKDIR /app

# Копируем агента
COPY agent_light.py /app/agent_light.py

# HEALTHCHECK — проверка что процесс жив
HEALTHCHECK --interval=60s --timeout=10s --start-period=5s --retries=3 \
  CMD python3 -c "import socket; s=socket.socket(); s.settimeout(5); s.connect(('127.0.0.1', 9908)); s.close()" || exit 1

# По умолчанию — агент без пиров (жди подключения)
CMD ["python3", "/app/agent_light.py", "--name", "docker-agent"]
