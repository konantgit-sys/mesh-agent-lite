
```
  __  __          _    _   _
 |  \/  |        | |  | | | |
 | \  / |  ___   | |__| | | |     __ _   ___
 | |\/| | / _ \  |  __  | | |    / _` | / __|
 | |  | || (_) | | |  | | | |___| (_| | \__ \
 |_|  |_| \___/  |_|  |_| |______\__,_| |___/

 P2P mesh in one command. No servers. No cloud. No signup.
```

# Mesh Agent Lite

**Zero-dependency P2P mesh agent.** One file. One command. Connected.

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](#)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](#)
[![No deps](https://img.shields.io/badge/deps-0-orange)](#)

---

## 🚀 TIE Agent v2 — HTTP Relay (рекомендуемый способ)

> Работает везде: домашний ПК, VPS, GitHub Actions, Colab, corporate proxy.
> Вся связь через HTTPS — никаких открытых портов не нужно.

### Одна команда
```bash
wget https://raw.githubusercontent.com/konantgit-sys/mesh-agent-lite/main/tie_agent.py
python3 tie_agent.py "имя-агента"
```

Готово. Вы в сети.

### Если создавал агента на сайте — используй ключ
```bash
wget https://raw.githubusercontent.com/konantgit-sys/mesh-agent-lite/main/tie_agent.py
python3 tie_agent.py "имя" --key "tie_..."
```

---

### Что происходит при запуске — по шагам

```
Шаг 1: Загрузка
       tie_agent.py скачивается с GitHub (8 KB)

Шаг 2: Регистрация на Relay
       → POST https://tie-run.v2.site/api/register
       → {"name": "имя-агента"}
       ← {"ok": true, "messages": [...], "new": true}
       
       Relay запоминает агента. Если сообщения уже были — 
       они приходят сразу.

Шаг 3: Фоновый опрос (каждые 2 секунды)
       → POST https://tie-run.v2.site/api/register (с тем же именем)
       ← {"ok": true, "messages": [...]}
       
       Если другой агент отправил сообщение — оно приходит 
       в этом ответе. Реальное время доставки: 1-3 секунды.

Шаг 4: Отправка сообщения
       → POST https://tie-run.v2.site/api/send_agent
       → {"from": "имя-агента", "text": "Привет!", "to": "*"}
       ← {"ok": true, "sent": true}
       
       Сообщение попадает в очередь всем остальным агентам.
       Они получат его при следующем опросе (через 1-2 сек).

Шаг 5: Heartbeat
       Каждый POST /api/register обновляет last_seen.
       Если агент не отвечает >60 секунд — он считается 
       офлайн и удаляется из списка.
```

### Что видит пользователь

```
  ╔══════════════════════════════╗
  ║     TIE Agent — antonio      ║
  ║     relay: tie-run.v2.site   ║
  ╚══════════════════════════════╝

✅ Connected to TIE Relay as 'antonio'

> /peers
📡 Online agents (3):
  · v2bot
  · friend
  · relay-bot

> Всем привет!
✓ Sent: Всем привет!

📨 [friend] И тебе привет!
```

### Команды внутри агента
| Команда | Что делает |
|---------|-----------|
| `/peers` | Показывает кто онлайн |
| `/msg текст` | Альтернативный способ отправки |
| `/quit` | Выход |

Любой текст без `/` в начале = сообщение всем.

### Web-дашборд
Все сообщения и агенты видны в реальном времени:
**https://tie-run.v2.site** — вкладка "Чат"

---

## 🔧 Классический TCP-режим (agent_light.py)

Для прямого P2P соединения между серверами (без relay).

### Быстрый старт

```bash
# Сервер A
python3 agent_light.py --name "node-a"

# Сервер B — подключается к A
python3 agent_light.py --name "node-b" --peer 192.168.1.10:9908
```

### Подключение к публичному TIE Hub
```bash
python3 agent_light.py --name "your-name" --peer 155.212.133.195:9908
```

---

## 📡 Что даёт подключение

### 🔐 Proof Code
При первом контакте каждый агент генерирует уникальный proof:
```
connection_a7f3-b2c8-91e4.proof
```
Этот код доказывает, что вы запустили mesh-агента. Сохраните его — он активирует ваше место при запуске платформы.

### 📊 Статус каждые 60с
```
[12:34:56] ❤️  uptime=300s peers=3 avg_lat=12.3ms
```

---

## 🐳 Docker

```bash
docker run --rm -it \
  -e NAME=my-agent \
  konant/agent-light:latest
```

Сборка образа:
```bash
docker build -t konant/agent-light:latest .
```

---

## 🧪 Тестирование

```bash
# Терминал 1
python3 tie_agent.py "alice"

# Терминал 2
python3 tie_agent.py "bob"
```

В терминале alice пишем: `Привет, боб!`
В терминале bob через 1-3 секунды приходит: `📨 [alice] Привет, боб!`

---

## 📁 Файлы

| Файл | Назначение |
|------|-----------|
| `tie_agent.py` | **Рекомендуемый** — HTTP relay агент (8 KB, без зависимостей) |
| `agent_light.py` | TCP P2P агент для прямых соединений |
| `Dockerfile` | Контейнер для agent_light.py |
| `.github/workflows/` | CI тесты на GitHub Actions |

---

## 🌐 Архитектура

```
┌─────────────┐     HTTPS      ┌──────────────────┐     HTTPS      ┌─────────────┐
│  Ваш агент   │ ──────────▶   │  tie-run.v2.site  │ ◀──────────   │  Агент друга │
│  (любой ПК)  │               │   (HTTP Relay)    │               │  (любой ПК)  │
└─────────────┘               └──────────────────┘               └─────────────┘
                                      │
                                      │ TCP (внутренний)
                                      ▼
                              ┌─────────────────┐
                              │  TIE Mesh Network│
                              │ (31 mesh-service)│
                              └─────────────────┘
```

**TIE Agent v2** — агент общается с relay через обычный HTTPS.  
Relay внутри подключён к полной mesh-сети TIE (31 сервис: Nostr Bridge, DAO, Privacy, ZK, Payment и др.).

---

## 📜 Лицензия

MIT
