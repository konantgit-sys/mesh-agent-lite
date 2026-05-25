
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

```bash
# Server A (wait for connections)
python3 agent_light.py --name "node-a"

# Server B — connects to A
python3 agent_light.py --name "node-b" --peer 192.168.1.10:9908
```

### 🔗 Connect to TIE Hub (public relay)

```bash
python3 agent_light.py --name "your-name" --peer 155.212.133.195:9908
```

TIE Hub runs 24/7 on public IP `155.212.133.195:9908`. Connect any time — your agent registers automatically with the mesh network.

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](#)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](#)
[![No deps](https://img.shields.io/badge/deps-0-orange)](#)
[![TCP only](https://img.shields.io/badge/protocol-TCP-lightgrey)](#)

---

## Quick Start (10 seconds)

### 1. Download
```bash
wget https://raw.githubusercontent.com/konantgit-sys/mesh-agent-lite/main/agent_light.py
```

### 2. Run on Server A
```bash
python3 agent_light.py --name "my-node"
```
Agent starts listening on port `9908` (TCP).

### 3. Run on Server B — connects to A
```bash
python3 agent_light.py --name "peer-node" --peer 192.168.1.10:9908
```

**Done.** Agents exchange HELLO, measure ping, generate proof codes.

---

## What You Get

### 🔐 Proof Code
On first contact, each agent generates a unique proof:
```
connection_a7f3-b2c8-91e4.proof
```
This code proves you ran a mesh agent. Save it — it activates your spot when the platform launches.

### 📡 Registration
Agents auto-register with the mesh network. Your proof code is logged on the network dashboard.

### 📊 Status Every 60s
```
[12:34:56] ❤️  uptime=300s peers=3 avg_lat=12.3ms
```

---

## Commands

```bash
# Basic — listen only
python3 agent_light.py --name "node-a"

# Connect to TIE Hub (public)
python3 agent_light.py --name "your-name" --peer 155.212.133.195:9908

# Connect to any peer
python3 agent_light.py --name "node-b" --peer 1.2.3.4:9908

# Connect to multiple peers
python3 agent_light.py --name "node-c" --peer 1.2.3.4:9908 --peer 5.6.7.8:9908

# Quick test (auto-exit after connect + ping)
python3 agent_light.py --test --peer 155.212.133.195:9908

# Custom port
python3 agent_light.py --port 7777 --peer 1.2.3.4:7777
```

---

## Docker

```bash
# Build
docker build -t mesh-agent .

# Run
docker run --rm -p 9908:9908 mesh-agent --name "docker-node"

# With peer
docker run --rm -p 9908:9908 mesh-agent --name "node-2" --peer 155.212.133.195:9908
```

Built on `python:3.11-slim`. Zero Python dependencies.

---

## How It Works

```
┌──────────────┐         TCP          ┌──────────────┐
│  Mesh Agent  │◄────────────────────►│  Mesh Agent  │
│  :9908       │      HELLO/PING      │  :9908       │
└──────────────┘                      └──────────────┘
```

Agents communicate directly over **TCP**. No hub, no cloud, no relay.

**Message types:**
| Type | Purpose |
|------|---------|
| 🤝 HELLO | Peer discovery + proof exchange |
| 📡 PING / PONG | Latency measurement |
| 💬 GOSSIP | Custom data relay |
| 👋 GOODBYE | Disconnect notification |

---

## Requirements

- Python 3.8+
- Nothing else

---

## Proof of First Contact

Every first connection generates a `.proof` file with a unique code:

```
═══════════════════════════════════════════
  MESH AGENT — PROOF OF FIRST CONTACT
═══════════════════════════════════════════
Code: a7f3-b2c8-91e4
File: connection_a7f3-b2c8-91e4.proof
Time: 2026-05-24 17:00:00 UTC
───────────────────────────────────────────
This code proves you ran a mesh agent.
Keep it. It activates your NFT on launch.
───────────────────────────────────────────
Keep your code safe. Activation coming soon.
═══════════════════════════════════════════
```

**Save this file.** When the platform launches, each activation code claims your spot in the network.

---

## Files

| File | Lines | What |
|------|-------|------|
| `agent_light.py` | 430 | Main agent — one file, zero deps |
| `Dockerfile` | 16 | Container image |
| `README.md` | — | This file |

---

## License

MIT. Do whatever you want.

---

**The network is not the technology. The network is the people who ran the agent.**

**May 2026. Mesh Network. Day one.**
