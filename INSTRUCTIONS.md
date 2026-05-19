# Mesh Agent Lite — Инструкция по запуску

## Быстрый старт (2 машины)

### Машина 1 (наша сторона) — уже запущена

```bash
# Relay на 8443
docker-compose up -d relay

# Simple Agent на 9908
docker-compose run -d agent --name "hub" --port 9908
```

### Машина 2 (твоя сторона)

```bash
# 1. Скачать репозиторий
git clone https://github.com/konantgit-sys/mesh-agent-lite.git
cd mesh-agent-lite

# 2. Собрать Docker образ
docker build -t mesh-agent-lite .

# 3. Проверить связь с хабом (одна команда)
docker run --rm mesh-agent-lite python3 mesh_ping.py --peer HUB_IP:9908

# 4. Запустить агента и подключиться к хабу
docker run --rm -p 9908:9908 mesh-agent-lite \
  python3 simple_agent.py --name "remote" --peer HUB_IP:9908
```

## Тесты

### Полный набор (на второй машине, после сборки)

```bash
# Все тесты разом (2-3 минуты)
docker run --rm mesh-agent-lite \
  python3 test_suite.py --hub HUB_IP:9908

# Только TCP + Echo (быстро)
docker run --rm mesh-agent-lite \
  python3 test_suite.py --hub HUB_IP:9908 --skip-uptime

# Только нагрузочный тест
docker run --rm mesh-agent-lite \
  python3 test_suite.py --hub HUB_IP:9908 --test load
```

### Без Docker

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Запустить простой тест
python3 mesh_ping.py --peer HUB_IP:9908

# 3. Запустить агента
python3 simple_agent.py --name "remote" --peer HUB_IP:9908 --test
```

## Docker Compose (полный стек на одной машине)

```bash
# Запуск relay + agent
docker-compose up -d

# Relay на :8443, агент на :9908
docker-compose ps

# Тесты
docker-compose run test

# Остановка
docker-compose down
```

## Что проверяет каждый тест

| Тест | Команда | Что проверяет |
|------|---------|---------------|
| TCP | `mesh_ping.py --peer HOST:PORT` | Базовая TCP связность |
| HELLO | `simple_agent.py --peer HOST:PORT` | Регистрация пира |
| PING/PONG | `test_suite.py --test tcp` | Задержка канала |
| Echo | `test_suite.py --test echo` | Двусторонняя передача |
| Relay | `docker-compose up -d relay` | NAT traversal |
| Load | `test_suite.py --test load` | Пропускная способность |
| Uptime | `test_suite.py --test uptime` | Стабильность |
| Proof | `test_suite.py --test proof` | Генерация NFT-кодов |

## Proof-коды (NFT будущего)

Каждый запуск `simple_agent.py` или `mesh_agent.py` генерирует уникальный код.

```
⚠️  СОХРАНИ ЭТОТ КОД:
┌──────────────────────────────────┐
│   a7f3-b2c8-91e4               │
└──────────────────────────────────┘
Файл: connection_a7f3-b2c8-91e4.proof
```

**Что делать с кодом:**
1. Файл `.proof` создаётся в текущей директории
2. Сохрани его — он подтверждает что ты запустил агента
3. Когда появится платформа — каждый код активирует NFT первого подключения

## Параметры окружения

| Переменная | По умолчанию | Описание |
|------------|-------------|----------|
| `RELAY_PORT` | 8443 | Порт relay |
| `AGENT_PORT` | 9908 | Порт агента |
| `AGENT_NAME` | mesh-node | Имя агента |
| `AGENT_PEER` | — | Адрес пира (host:port) |

## Связь с хабом

Хаб работает на адресе: **155.212.133.195:9908**

```bash
# Быстрая проверка
python3 mesh_ping.py --peer 155.212.133.195:9908

# Полноценное подключение
python3 simple_agent.py --name "test-node" --peer 155.212.133.195:9908 --test
```

## Архитектура

```
Машина 1 (наша)          Машина 2 (твоя)
┌──────────────────┐    ┌──────────────────┐
│  relay (:8443)   │◄──►│  simple_agent    │
│  simple_agent    │    │  --peer 1.2.3.4  │
│  (:9908)         │    │  (:9908)         │
└──────────────────┘    └──────────────────┘
        │                      │
        └────── TCP P2P ───────┘
```

Все сообщения — TCP поверх JSON. Без центрального сервера, без облаков, без регистрации.
