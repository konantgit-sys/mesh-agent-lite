#!/usr/bin/env python3
"""
TIE Agent v2 — HTTP mesh client for TIE Relay.
Connects via HTTPS to tie-run.v2.site (no open ports needed).

Usage:
    python3 tie_agent.py "имя"
    python3 tie_agent.py "имя" --key "tie_..."
"""
import json, time, threading, sys, os

try:
    import urllib.request
    import urllib.error
except:
    print("urllib not available?")
    sys.exit(1)

RELAY_URL = "https://tie-run.v2.site/api"

# ── Parse args ────────────────────────────────────────────────────
NAME = "agent"
KEY = None
for i, a in enumerate(sys.argv[1:], 1):
    if a == "--key" and i < len(sys.argv):
        KEY = sys.argv[i+1]
    elif a == "--name" and i < len(sys.argv):
        NAME = sys.argv[i+1]

if not NAME or NAME == "agent":
    for a in sys.argv[1:]:
        if not a.startswith("--"):
            NAME = a
            break
if NAME == "agent":
    NAME = f"agent-{os.getpid()}"
running = True

def api_post(endpoint, data):
    body = json.dumps(data).encode()
    try:
        req = urllib.request.Request(
            f"{RELAY_URL}/{endpoint}", data=body,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_get(endpoint):
    try:
        req = urllib.request.Request(f"{RELAY_URL}/{endpoint}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"ok": False, "error": str(e)}

def poll_loop():
    global running
    while running:
        data = {"name": NAME}
        if KEY:
            data["key"] = KEY
        result = api_post("register", data)
        if result.get("ok"):
            for msg in result.get("messages", []):
                sender = msg.get("from", "?")
                text = msg.get("text", "")
                if sender != "system":
                    print(f"\n📨 [{sender}] {text}")
                else:
                    print(f"\nℹ️  {text}")
        time.sleep(2)

def send_message(text):
    result = api_post("send", {"from": NAME, "text": text, "to": "*"})
    if result.get("ok"):
        print(f"✓ Sent: {text}")
    else:
        print(f"✗ Failed: {result.get('error', 'unknown')}")

def main():
    global running
    key_display = KEY[:20]+"..." if KEY else "no key"
    print(f"""
  ╔══════════════════════════════╗
  ║     TIE Agent — {NAME:<16} ║
  ║     relay: tie-run.v2.site   ║
  ║     key: {key_display:<22}║
  ╚══════════════════════════════╝
    """)
    
    data = {"name": NAME}
    if KEY:
        data["key"] = KEY
    result = api_post("register", data)
    if result.get("ok"):
        print(f"✅ Connected to TIE Relay as '{NAME}'")
    else:
        print(f"❌ Registration failed: {result.get('error')}")
        return
    
    poller = threading.Thread(target=poll_loop, daemon=True)
    poller.start()
    
    print("\nCommands: /peers  |  /quit")
    print("Type a message and press Enter\n")
    
    try:
        while True:
            cmd = input("> ").strip()
            if not cmd:
                continue
            if cmd == "/quit":
                running = False
                break
            elif cmd == "/peers":
                status = api_get("status")
                agents = status.get("agent_list", [])
                print(f"\n📡 Online agents ({len(agents)}):")
                for a in agents:
                    print(f"  · {a['name']}")
                print()
            else:
                send_message(cmd)
    except (EOFError, KeyboardInterrupt):
        pass
    running = False
    print("\nGoodbye!")

if __name__ == "__main__":
    main()
