```
  __  __          _    _   _
 |  \/  |        | |  | | | |
 | \  / |  ___   | |__| | | |     __ _   ___
 | |\/| | / _ \  |  __  | | |    / _` | / __|
 | |  | || (_) | | |  | | | |___| (_| | \__ \
 |_|  |_| \___/  |_|  |_| |______\__,_| |___/
```

**P2P mesh in one command.** No servers. No clouds. No registration.

```bash
python3 mesh_agent.py --peer 123.45.67.89:9908
```

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](#)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](#)
[![Zero deps](https://img.shields.io/badge/dependencies-0-orange)](#)
[![TCP only](https://img.shields.io/badge/protocol-TCP-lightgrey)](#)

---

## 🎂 BIRTHDAY: MESH NETWORK IS BORN 🎂

**May 19, 2026** — the day the mesh network went public.

Everyone who runs an agent and connects to another peer gets a **unique proof code**. The file `connection_XXXX-XXXX-XXXX.proof` is generated automatically.

**Why?** When the platform launches — each code activates a **first-connection NFT**.

```
⚠️  SAVE THIS CODE:
┌──────────────────────────────────┐
│   a7f3-b2c8-91e4               │
└──────────────────────────────────┘
File: connection_a7f3-b2c8-91e4.proof
```

---

## How to verify you ran it

1. Run the agent → get a code + `connection_XXXX-XXXX-XXXX.proof` file
2. Open an **Issue** in this repository (green "New issue" button)
3. Title: `Connection: XXXX-XXXX-XXXX`
4. Paste the proof file contents into the body
5. Done. You're in the registry.

GitHub Issues = public blockchain-light. Each Issue is tied to a GitHub account, can't be deleted, can't be edited. The perfect first-connection ledger.

---

## What is this?

A lightweight P2P agent that spawns a mesh network between servers in 5 seconds.

- **One agent** — just a TCP server
- **Two agents** — mesh with automatic routing
- **Three or more** — distributed network with quality scoring

Agents discover each other, measure latency, pick the best channel. Real-time. All P2P.

---

## Quick start in 10 seconds

```bash
# 1. Download
wget -O mesh_agent.py https://github.com/USERNAME/mesh-p2p-agent/raw/main/mesh_agent.py

# 2. Run (on server A)
python3 mesh_agent.py --name "server-a"

# 3. Run (on server B) — connects to A
python3 mesh_agent.py --name "server-b" --peer IP_A:9908
```

Done. Agents exchange HELLO, start pinging, show codes and latency.

---

## What you'll see

```
╔═══ Mesh Agent ═══╗
║ Name:    server-b
║ Pubkey:  f8c9eabfd28c4375...
║ Port:    9908
║ Peers:   1
╚════════════════════════╝

[server-b] 📡 Listening on :9908 (TCP)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🎂 BIRTHDAY: MESH NETWORK IS BORN 🎂
  ⚠️  SAVE THIS CODE:
  ┌──────────────────────────────────┐
  │   a7f3-b2c8-91e4               │
  └──────────────────────────────────┘
  File: connection_a7f3-b2c8-91e4.proof
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[server-b] 🔌 Connecting to 5.6.7.8:9908...
[server-b] 🤝 New peer: server-a (5.6.7.8:9908) latency=12.3ms
[server-b] 🔗 Peer server-a → code d4e5-f6a7-b8c9

--- 30 seconds later ---

[server-b] ❤️ uptime=5m peers=1 msgs=12 errs=0 | server-a lat=12.3ms score=1.00
```

---

## Quick connectivity test

For a fast "can server A reach server B" check:

```bash
# On server A:
python3 mesh_ping.py --server

# On server B:
python3 mesh_ping.py --peer IP_A:9909
```

Also generates a proof code. Counts too.

```
[client] ✅ PONG! latency=0.3ms
[client] 📝 Save file: connection_a7f3-b2c8-91e4.proof
```

---

## Docker

```bash
docker build -t mesh-agent .
docker run --rm -p 9908:9908 mesh-agent --name "my-container"
# With a peer:
docker run --rm -p 9908:9908 mesh-agent --name "node-2" --peer 1.2.3.4:9908
```

---

## Commands

```bash
# Basic run
python3 mesh_agent.py --name "my-node"

# Connect to multiple peers at once
python3 mesh_agent.py --peer 1.2.3.4:9908 --peer 5.6.7.8:9908

# Test mode (auto-exit after 60 min)
python3 mesh_agent.py --test --peer 1.2.3.4:9908

# Custom port
python3 mesh_agent.py --port 7777 --peer 1.2.3.4:7777
```

---

## How it works

```
┌──────────────┐         TCP          ┌──────────────┐
│  Mesh Agent  │◄────────────────────►│  Mesh Agent  │
│  :9908       │      gossip          │  :9908       │
└──────────────┘                      └──────────────┘
       ▲                                      ▲
       │                TCP                    │
       └──────────────────────────────────────┘
                      ┌──────────────┐
                      │  Mesh Agent  │
                      │  :9908       │
                      └──────────────┘
```

Each agent = server + client simultaneously. Messages flow directly P2P. No central hub.

**Message types:**

| Type | Purpose |
|------|---------|
| 🤝 HELLO | New peer connect + proof code exchange |
| 📡 PING / PONG | Connectivity check + latency measurement |
| 💬 GOSSIP | User data |
| 👋 GOODBYE | Disconnect |

**Quality scoring:** each peer gets a channel score (0.0–1.0). Drops on errors, rises on successful pongs.

---

## Repository files

| File | Lines | Purpose |
|------|-------|---------|
| `mesh_agent.py` | 381 | Full P2P agent: mesh, HELLO, PING, GOSSIP |
| `mesh_ping.py` | 123 | Quick tester: ping → pong, minimal code |
| `Dockerfile` | 10 | Containerization for mesh_agent.py |
| `LICENSE` | 21 | MIT |
| `.gitignore` | 4 | Ignore temp files |

---

## Requirements

- Python 3.8+
- Nothing else

---

## License

MIT. Do whatever you want.

---

**A network isn't technology. A network is the people who ran the agent.**

**May 19, 2026. Mesh Network. Day one.**
