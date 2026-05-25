#!/usr/bin/env python3
"""
TIE Agent — HTTP mesh client for TIE Relay.
Connects via HTTPS to tie-relay.v2.site (no raw TCP needed).
"""

import json
import time
import threading
import sys
import os

try:
    import urllib.request
    import urllib.error
except:
    print("urllib not available?")
    sys.exit(1)

RELAY_URL = "https://tie-run.v2.site/api"
NAME = sys.argv[1] if len(sys.argv) > 1 else f"agent-{os.getpid()}"
running = True

def api_post(endpoint, data):
    """Send POST to relay."""
    body = json.dumps(data).encode()
    try:
        req = urllib.request.Request(
            f"{RELAY_URL}/{endpoint}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_get(endpoint):
    """Send GET to relay."""
    try:
        req = urllib.request.Request(f"{RELAY_URL}/{endpoint}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"ok": False, "error": str(e)}

def poll_loop():
    """Continuously poll for messages."""
    global running
    while running:
        # Register + get messages
        result = api_post("register", {"name": NAME})
        if result.get("ok"):
            msgs = result.get("messages", [])
            for msg in msgs:
                sender = msg.get("from", "?")
                text = msg.get("text", "")
                if sender != "system":
                    print(f"\n📨 [{sender}] {text}")
                else:
                    print(f"\nℹ️  {text}")
        time.sleep(2)

def send_message(text):
    """Send a message to all agents."""
    result = api_post("send", {"from": NAME, "text": text, "to": "*"})
    if result.get("ok"):
        print(f"✓ Sent: {text}")
    else:
        print(f"✗ Failed: {result.get('error', 'unknown')}")

def main():
    global running
    
    print(f"""
  ╔══════════════════════════════╗
  ║     TIE Agent — {NAME:<16} ║
  ║     relay: tie-relay.v2.site ║
  ╚══════════════════════════════╝
    """)
    
    # Register
    result = api_post("register", {"name": NAME})
    if result.get("ok"):
        print(f"✅ Connected to TIE Relay as '{NAME}'")
    else:
        print(f"❌ Registration failed: {result.get('error')}")
        return
    
    # Start poller
    poller = threading.Thread(target=poll_loop, daemon=True)
    poller.start()
    
    print("\nCommands: /msg <text>  |  /peers  |  /quit")
    print("Type a message and press Enter\n")
    
    try:
        while True:
            cmd = input("> ").strip()
            if not cmd:
                continue
            if cmd == "/quit":
                running = False
                print("Goodbye!")
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
        running = False
        print("\nGoodbye!")

if __name__ == "__main__":
    main()
