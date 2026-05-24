# Mesh Agent Lite — Instructions

## Quick Start (two machines)

### Machine A — first node

```bash
wget https://raw.githubusercontent.com/konantgit-sys/mesh-agent-lite/main/agent_light.py
python3 agent_light.py --name "node-a"
```

Agent starts on port `9908` and waits for peers.

### Machine B — connect to A

```bash
wget https://raw.githubusercontent.com/konantgit-sys/mesh-agent-lite/main/agent_light.py
python3 agent_light.py --name "node-b" --peer IP_OF_A:9908
```

Replace `IP_OF_A` with the actual IP or hostname of Machine A.

### What happens

1. Agents exchange HELLO → establish P2P connection
2. Each generates a unique proof code → saved as `connection_XXXX-XXXX-XXXX.proof`
3. Both register with the mesh network automatically
4. PING runs every 30s → latency displayed
5. Status summary every 60s

---

## Network setup

### Same local network (LAN)

Use private IPs:
```bash
# Machine A: 192.168.1.10
python3 agent_light.py --name "node-a"

# Machine B: 192.168.1.11
python3 agent_light.py --name "node-b" --peer 192.168.1.10:9908
```

### Over the internet

Machine A must have port `9908` open (or forwarded in router):
```bash
# Machine A with public IP 1.2.3.4
python3 agent_light.py --name "node-a"

# Machine B from anywhere
python3 agent_light.py --name "node-b" --peer 1.2.3.4:9908
```

**Firewall:** ensure TCP port 9908 is open on Machine A.

---

## Test mode

Quick connectivity check (auto-exit after HELLO + PING):

```bash
# Machine A
python3 agent_light.py --name "server-a"

# Machine B — test
python3 agent_light.py --test --peer IP_OF_A:9908
```

Expected output:
```
✅ OK   (connection established)
✅ 0.4ms  (PING latency)
```

---

## Proof codes

On first connection, a `.proof` file appears in the current directory:

```
connection_a7f3-b2c8-91e4.proof
```

**Save this file.** It proves you ran an agent. When the platform launches, each code activates your spot in the mesh network.

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---------|-------------|-----|
| `Connection refused` | Wrong IP or port | Check IP + port 9908 open |
| `timed out` | Firewall blocking | Open TCP 9908 inbound |
| Agent starts but no peers | No `--peer` flag | Add `--peer HOST:PORT` |
| Proof not saved | Write permission | Run in writable directory |

---

## Docker

```bash
# Build
docker build -t mesh-agent .

# Run
docker run --rm -p 9908:9908 mesh-agent --name "docker-node"

# With peer
docker run --rm -p 9908:9908 mesh-agent \
  --name "remote-node" --peer 1.2.3.4:9908
```

No additional ports needed. Single container, single file.
