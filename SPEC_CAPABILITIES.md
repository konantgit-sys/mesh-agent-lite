# Mesh Agent Lite — Capabilities Specification

## Источник: p2p-agent-mesh (открытый код)

### Layer 0 — Transport (Транспорт) [CORE]

| # | Возможность | Модуль | Статус | Тест |
|---|-------------|--------|--------|------|
| 0.1 | TCP P2P соединение (HELLO/PING/PONG) | `phase0/transport.py` | ✅ Есть | test_tcp_transport.py |
| 0.2 | Ed25519 идентичность + подпись | `phase0/identity.py` | ✅ Есть | test_identity.py |
| 0.3 | X25519 handshake (шифрование) | `phase0/handshake.py` | ✅ Есть | test_tls_transport.py |
| 0.4 | WAL буфер (SQLite, replay) | `phase0/wal.py` | ✅ Есть | test_wal.py |
| 0.5 | SigGate (подпись верификация) | `phase0/sig_gate.py` | ✅ Есть | test_sig_gate.py |
| 0.6 | **Kademlia DHT** (peer discovery) | `phase0/dht_kademlia.py` | 🆕 Добавить | test_kademlia.py |

### Layer 1 — SDK (Agent API) [CORE]

| # | Возможность | Модуль | Статус | Тест |
|---|-------------|--------|--------|------|
| 1.1 | AgentMesh (emit/listen/query) | `sdk/agent.py` | ✅ Есть | test_agent.py |
| 1.2 | Phase1 SDK (discovery + репутация) | `phase1/` | 🆕 Добавить | test_agent.py |
| 1.3 | Relay (NAT traversal) | `relay/server.py`, `relay/client.py` | ✅ Есть | — |

### Layer 2 — Coordination (Координация) [EXTENDED]

| # | Возможность | Модуль | Статус | Тест |
|---|-------------|--------|--------|------|
| 2.1 | Репутация пиров | `core/reputation.py` | 🆕 Добавить | test_reputation.py |
| 2.2 | Дедупликация сообщений | `coordination/dedup.py` | 🆕 Добавить | test_coordination.py |
| 2.3 | Consumer Group (групповая подписка) | `coordination/consumer_group.py` | 🆕 Добавить | test_coordination.py |
| 2.4 | Raft консенсус | `coordination/raft.py` | ⬆️ Опционально | test_coordination.py |
| 2.5 | Coordinator (лидерство) | `coordination/coordinator.py` | ⬆️ Опционально | test_coordination.py |

### Layer 3 — Pilot (DAO) [EXTENDED]

| # | Возможность | Модуль | Статус | Тест |
|---|-------------|--------|--------|------|
| 3.1 | SNIN DAO Chain | `pilot/snin_dao_chain.py` | ⬆️ Опционально | test_chain.py |

### Layer 4 — Tools (Инструменты) [CORE]

| # | Возможность | Модуль | Статус | Тест |
|---|-------------|--------|--------|------|
| 4.1 | CLI запуск агента | `cli.py` | 🆕 Добавить | — |
| 4.2 | Прямое TCP соединение | `connect_direct.py` | 🆕 Добавить | — |
| 4.3 | Peer discovery | `connect_peers.py` | 🆕 Добавить | — |
| 4.4 | Пример: LangGraph | `examples/3_agent_langgraph.py` | 🆕 Добавить | — |
| 4.5 | Пример: Signal Mesh | `examples/3_agent_signal_mesh.py` | 🆕 Добавить | — |

---

## Legacy Стек (текущий mesh-agent-lite)

```
mesh_agent.py           — TCP агент + proof-коды
mesh_ping.py            — ping-тестер
simple_agent.py         — echo/relay/counter агент
test_suite.py           — 8 тестов (100%)
```

## Что добавляется

```
phase0/dht_kademlia.py  — Kademlia DHT (вместо заглушки)
phase1/                 — Agent SDK (discovery + reputation)
core/reputation.py      — Репутация пиров
coordination/dedup.py   — Дедупликация
cli.py                  — CLI запуск
connect_direct.py       — Прямое TCP соединение
connect_peers.py        — Peer discovery
docs/                   — Документация
examples/               — Примеры
```

## Тестируемые сценарии на другой машине

1. **TCP P2P** — запустить агента, подключиться к хабу, HELLO/PING/PONG
2. **DHT discovery** — запустить Kademlia, найти пиров без хаба
3. **WAL buffer** — отправить сообщения, перезапустить, проверить replay
4. **Relay** — пройти NAT через relay-сервер
5. **Reputation** — отправить N сообщений, проверить рейтинг пира
6. **Dedup** — отправить дубликаты, проверить что пришёл только 1
7. **Proof-code** — сгенерировать SHA256 код, сохранить в файл
8. **CLI** — запуск через `python3 cli.py --agent test --port 9908`
9. **Direct connect** — `python3 connect_direct.py`
10. **Peer discovery** — `python3 connect_peers.py`
