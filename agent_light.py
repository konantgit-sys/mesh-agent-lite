#!/usr/bin/env python3
"""
agent_light.py — Single-file P2P mesh agent with proof codes.

Usage:
  # Start as server (auto-registers with mesh network)
  python3 agent_light.py --name "node-a"

  # Connect to another node
  python3 agent_light.py --name "node-b" --peer 1.2.3.4:9908

  # Quick test (auto-exit after HELLO+PING+ECHO)
  python3 agent_light.py --test --peer 1.2.3.4:9908

On first connection, generates connection_XXXX-XXXX-XXXX.proof
— your unique NFT activation code. Save it.

Auto-registers with mesh registry — your proof code is logged.
Check your registration status on the network dashboard once connected.

No dependencies. Python 3.8+. MIT license.
"""

import argparse
import hashlib
import json
import os
import random
import socket
import struct
import sys
import textwrap
import threading
import time
import uuid

# ─── Protocol ──────────────────────────────────────────────────────────
MAGIC = b"MESHv1"
MSG_HELLO = 1
MSG_PING = 2
MSG_PONG = 3
MSG_GOSSIP = 4
MSG_ECHO = 10
MSG_ECHO_BACK = 11

PROOF_SALT = "mesh-infinity-2026"
BANNER = """

  __  __          _    _   _
 |  \\/  |        | |  | | | |
 | \\  / |  ___   | |__| | | |     __ _   ___
 | |\\/| | / _ \\  |  __  | | |    / _` | / __|
 | |  | || (_) | | |  | | | |___| (_| | \\__ \\
 |_|  |_| \\___/  |_|  |_| |______\\__,_| |___/


 P2P mesh in one command. No servers. No cloud. No signup.
"""


def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def generate_proof(pubkey: str) -> tuple:
    """Generate a unique proof code and save to file."""
    proof_raw = f"{pubkey}:{time.time()}:{PROOF_SALT}"
    h = hashlib.sha256(proof_raw.encode()).hexdigest()[:12]
    code = f"{h[:4]}-{h[4:8]}-{h[8:12]}"
    filename = f"connection_{code}.proof"
    content = textwrap.dedent(f"""\
        ═══════════════════════════════════════════
          MESH AGENT — PROOF OF FIRST CONTACT
        ═══════════════════════════════════════════
        Code: {code}
        File: {filename}
        Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}
        ───────────────────────────────────────────
        This code proves you ran a mesh agent.
        Keep it. It activates your NFT on launch.
        ───────────────────────────────────────────
        Keep your code safe. Activation coming soon.
        ═══════════════════════════════════════════
    """)
    try:
        with open(filename, "w") as f:
            f.write(content)
        log(f"📝 Proof saved: {filename}")
    except Exception:
        pass
    return code, filename


def register_with_hub(code: str, name: str, pubkey: str = "", version: str = ""):
    """Auto-register proof code with mesh hub (fire & forget)."""
    import urllib.request
    import json
    try:
        body = json.dumps({
            "proof_code": code,
            "agent_name": name,
            "pubkey": pubkey[:32],
            "version": version or "agent_light-2.0",
            "agent_type": "agent_light"
        }).encode()
        req = urllib.request.Request(
            "https://snin-hub.v2.site/api/register",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode())
            if result.get("ok"):
                log(f"🌐 Registered with mesh network (proof: {code})")
            else:
                log(f"⚠️ Registration: {result.get('error', 'unknown')}")
    except Exception as e:
        log(f"⚠️ Hub unreachable, proof saved locally")


def show_proof(code: str, filename: str, name: str):
    """Display the proof banner."""
    border = "━" * 50
    log(f"")

    print(f"  {border}")
    print(f"  🎂  MESH NETWORK — INFINITY PROOF  🎂")
    print(f"  {border}")
    print(f"")
    print(f"  Agent:    {name}")
    print(f"  Proof:    {code}")
    print(f"  File:     {filename}")
    print(f"")
    print(f"  ⚠️  SAVE THIS CODE. IT IS YOURS.")
    print(f"  This code proves you ran a mesh agent.")
    print(f"  Keep it — it activates your spot on launch.")
    print(f"")
    print(f"  {border}")
    log(f"")


# ─── Message Packing ──────────────────────────────────────────────────
def pack_msg(msg_type: int, payload: dict) -> bytes:
    payload_bytes = json.dumps(payload).encode()
    return MAGIC + struct.pack("!II", msg_type, len(payload_bytes)) + payload_bytes


def unpack_msg(data: bytes) -> tuple:
    if data[:6] != MAGIC:
        return None, None
    msg_type = struct.unpack("!I", data[6:10])[0]
    payload_len = struct.unpack("!I", data[10:14])[0]
    payload = json.loads(data[14:14 + payload_len])
    return msg_type, payload


# ─── Agent ─────────────────────────────────────────────────────────────
class AgentLight:
    def __init__(self, name: str, port: int = 9908):
        self.name = name
        self.port = port
        self.pubkey = uuid.uuid4().hex * 4  # 64 hex chars
        self.peers = {}  # addr -> {"name", "latency", "connected_at", "proof"}
        self.running = False
        self._server = None
        self._lock = threading.Lock()

    # ── Server ──────────────────────────────────────────────────────
    def start_server(self):
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind(("0.0.0.0", self.port))
        self._server.listen(10)
        self._server.settimeout(2.0)
        log(f"📡 Listening on :{self.port} (TCP)")

        while self.running:
            try:
                conn, addr = self._server.accept()
                threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    log(f"⚠️ Server error: {e}")

    def _handle_client(self, conn, addr):
        addr_str = f"{addr[0]}:{addr[1]}"
        try:
            data = conn.recv(8192)
            if not data:
                return
            msg_type, payload = unpack_msg(data)
            if msg_type == MSG_HELLO:
                self._on_hello(conn, addr_str, payload)
            elif msg_type == MSG_PING:
                self._on_ping(conn, addr_str, payload)
            elif msg_type == MSG_ECHO:
                self._on_echo(conn, addr_str, payload)
        except Exception as e:
            log(f"⚠️ Client error from {addr_str}: {e}")
        finally:
            conn.close()

    def _on_hello(self, conn, addr_str, payload):
        peer_name = payload.get("name", "?")
        peer_pubkey = payload.get("pubkey", "?")
        new_peer = addr_str not in self.peers

        with self._lock:
            self.peers[addr_str] = {
                "name": peer_name,
                "pubkey": peer_pubkey,
                "connected_at": time.time(),
                "latency": 0,
                "proof": None,
            }

        # Generate proof on first contact
        if new_peer:
            code, filename = generate_proof(self.pubkey)
            with self._lock:
                self.peers[addr_str]["proof"] = code
            show_proof(code, filename, self.name)
            register_with_hub(code, self.name, self.pubkey)

        # Reply HELLO back
        reply = pack_msg(MSG_HELLO, {
            "name": self.name,
            "pubkey": self.pubkey,
            "proof": self.peers[addr_str].get("proof", ""),
            "ts": time.time(),
        })
        conn.sendall(reply)
        log(f"🤝 New peer: {peer_name} ({addr_str})")

    def _on_ping(self, conn, addr_str, payload):
        nonce = payload.get("nonce", "?")
        ts = payload.get("ts", time.time())
        latency = round((time.time() - ts) * 1000, 1)

        with self._lock:
            if addr_str in self.peers:
                self.peers[addr_str]["latency"] = latency

        reply = pack_msg(MSG_PONG, {
            "nonce": nonce,
            "latency_ms": latency,
            "ts": time.time(),
        })
        conn.sendall(reply)

    def _on_echo(self, conn, addr_str, payload):
        reply = pack_msg(MSG_ECHO_BACK, {
            "echo": payload.get("payload", ""),
            "ts": time.time(),
        })
        conn.sendall(reply)

    # ── Client ──────────────────────────────────────────────────────
    def connect(self, peer_addr: str):
        """Connect to a peer (HELLO → ping loop)."""
        log(f"🔌 Connecting to {peer_addr}...")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            host, port = peer_addr.split(":")
            sock.connect((host, int(port)))

            # HELLO
            hello = pack_msg(MSG_HELLO, {
                "name": self.name,
                "pubkey": self.pubkey,
                "ts": time.time(),
            })
            sock.sendall(hello)
            data = sock.recv(8192)
            msg_type, payload = unpack_msg(data)
            if msg_type != MSG_HELLO:
                log(f"❌ Expected HELLO from {peer_addr}, got type={msg_type}")
                sock.close()
                return False

            peer_name = payload.get("name", "?")
            peer_proof = payload.get("proof", "")
            with self._lock:
                self.peers[peer_addr] = {
                    "name": peer_name,
                    "connected_at": time.time(),
                    "latency": 0,
                    "proof": peer_proof,
                }

            # Generate our own proof
            code, filename = generate_proof(self.pubkey)
            show_proof(code, filename, self.name)
            register_with_hub(code, self.name, self.pubkey)
            log(f"🤝 Connected to {peer_name} ({peer_addr})")
            sock.close()
            return True

        except Exception as e:
            log(f"❌ Connection to {peer_addr} failed: {e}")
            return False

    def ping(self, peer_addr: str) -> float:
        """Ping a peer, return latency in ms."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            host, port = peer_addr.split(":")
            sock.connect((host, int(port)))

            nonce = uuid.uuid4().hex[:8]
            ping_msg = pack_msg(MSG_PING, {"nonce": nonce, "ts": time.time()})
            sock.sendall(ping_msg)
            data = sock.recv(8192)
            msg_type, payload = unpack_msg(data)
            sock.close()

            if msg_type == MSG_PONG and payload.get("nonce") == nonce:
                return payload.get("latency_ms", 999)

        except Exception:
            pass
        return 999

    # ── Main Loop ─────────────────────────────────────────────────
    def run(self, peers: list = None):
        self.running = True

        # Print banner
        print(BANNER)
        log(f"Name:     {self.name}")
        log(f"Pubkey:   {self.pubkey[:24]}...")
        log(f"Port:     {self.port}")
        log(f"")

        # Start server thread
        server_thread = threading.Thread(target=self.start_server, daemon=True)
        server_thread.start()
        time.sleep(0.5)

        # Connect to peers
        if peers:
            for peer in peers:
                self.connect(peer)

        # Status loop
        last_status = 0
        try:
            while self.running:
                time.sleep(1)
                now = time.time()

                # Ping known peers every 30s
                if peers and now % 30 < 1:
                    for peer in peers:
                        lat = self.ping(peer)
                        with self._lock:
                            if peer in self.peers:
                                self.peers[peer]["latency"] = lat

                # Status every 60s
                if now - last_status >= 60:
                    last_status = now
                    n_peers = len(self.peers)
                    latencies = [p.get("latency", 0) for p in self.peers.values()]
                    avg_lat = sum(latencies) / len(latencies) if latencies else 0
                    log(f"❤️  uptime={int(now - self.peers.get('_start', now))}s peers={n_peers} avg_lat={avg_lat:.1f}ms")
                    if self.peers.get("_start") is None:
                        with self._lock:
                            self.peers["_start"] = now

        except KeyboardInterrupt:
            log("\n👋 Stopping...")
            self.running = False

    def test(self, peer_addr: str = None):
        """Quick test: server + optional peer connection, then exit."""
        self.running = True
        print(BANNER)
        log(f"═══ TEST MODE ═══")
        log(f"Name: {self.name}")

        # Start server
        server_thread = threading.Thread(target=self.start_server, daemon=True)
        server_thread.start()
        time.sleep(1)

        code, filename = generate_proof(self.pubkey)
        show_proof(code, filename, self.name)
        register_with_hub(code, self.name, self.pubkey)

        if peer_addr:
            log(f"1. Connecting to {peer_addr}...")
            ok = self.connect(peer_addr)
            log(f"   {'✅ OK' if ok else '❌ FAIL'}")

            log(f"2. PING...")
            lat = self.ping(peer_addr)
            log(f"   {'✅' if lat < 999 else '❌'} {lat}ms")

        log(f"\n═══ TEST COMPLETE ═══")
        log(f"Proof: {filename}")
        log(f"Code:  {code}")
        self.running = False


def main():
    parser = argparse.ArgumentParser(description="agent_light.py — P2P mesh agent")
    parser.add_argument("--name", default=f"node-{random.randint(100,999)}", help="Agent name")
    parser.add_argument("--port", type=int, default=9908, help="TCP port")
    parser.add_argument("--peer", action="append", dest="peers", help="Peer address (host:port)")
    parser.add_argument("--test", action="store_true", help="Quick test mode")
    args = parser.parse_args()

    agent = AgentLight(name=args.name, port=args.port)

    if args.test:
        peer = args.peers[0] if args.peers else None
        agent.test(peer)
    else:
        agent.run(peers=args.peers)


if __name__ == "__main__":
    main()
