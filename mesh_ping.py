#!/usr/bin/env python3
"""
Mesh Ping — простейший тестер mesh-сети.

Задача: проверить что между двумя серверами есть TCP-контакт.

Запуск (сервер):  python3 mesh_ping.py --server
Запуск (клиент):  python3 mesh_ping.py --peer IP:9909

При каждом запуске генерируется уникальный proof-код.
Сохрани его — он активирует NFT, когда появится платформа.
"""

import asyncio, json, time, sys, hashlib, uuid

PORT = 9909

def gen_proof(name):
    raw = f"{uuid.uuid4().hex}:{time.time()}:mesh-birthday-2026"
    h = hashlib.sha256(raw.encode()).hexdigest()[:12]
    code = f"{h[:4]}-{h[4:8]}-{h[8:12]}"
    fname = f"connection_{code}.proof"
    with open(fname, "w") as f:
        f.write("MESH_AGENT_CONNECTION_PROOF\n")
        f.write(f"Name: {name}\n")
        f.write(f"Code: {code}\n")
        f.write(f"Timestamp: {int(time.time())}\n")
        f.write(f"Agent: Mesh Ping v1.0\n")
        f.write("--\n")
        f.write(f"Save this file. It proves you ran a mesh agent\n")
        f.write(f"on {time.strftime('%Y-%m-%d %H:%M UTC')}.\n")
    return code, fname

async def server(port):
    code, fname = gen_proof("ping-server")
    print(f"╔═══ Mesh Ping ═══╗")
    print(f"║ Режим:  сервер  ║")
    print(f"║ Порт:   {port}     ║")
    print(f"╚═════════════════╝")
    print()
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  ⚠️  СОХРАНИ ЭТОТ КОД:")
    print(f"  ┌──────────────────────────────────┐")
    print(f"  │   {code}   │")
    print(f"  └──────────────────────────────────┘")
    print(f"  Файл: {fname}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    srv = await asyncio.start_server(
        lambda r, w: _on_ping(r, w), host="0.0.0.0", port=port
    )
    print(f"[сервер] 👂 Жду входящие на :{port}...")
    async with srv:
        await srv.serve_forever()

async def _on_ping(reader, writer):
    try:
        data = await asyncio.wait_for(reader.readline(), timeout=10)
        msg = json.loads(data.decode())
        if msg.get("kind") == "ping":
            peer_code = msg.get("proof", "?")
            pong = json.dumps({"kind": "pong", "ts": time.time(), "echo": msg.get("ts")}) + "\n"
            writer.write(pong.encode())
            await writer.drain()
            lat = round((time.time() - msg.get("ts", time.time())) * 1000, 1)
            print(f"[сервер] 📩 Принял ping от {peer_code} → pong ({lat}ms)")
    except:
        pass
    finally:
        try: writer.close()
        except: pass

async def client(host, port):
    code, fname = gen_proof("ping-client")
    print(f"╔═══ Mesh Ping ═══╗")
    print(f"║ Режим:  клиент ║")
    print(f"║ Пир:    {host}:{port} ║")
    print(f"╚═════════════════╝")
    print()
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  ⚠️  СОХРАНИ ЭТОТ КОД:")
    print(f"  ┌──────────────────────────────────┐")
    print(f"  │   {code}   │")
    print(f"  └──────────────────────────────────┘")
    print(f"  Файл: {fname}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    print(f"[клиент] 🔌 Соединяюсь с {host}:{port}...")
    try:
        r, w = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=5)
        ping = json.dumps({"kind": "ping", "ts": time.time(), "proof": code}) + "\n"
        w.write(ping.encode())
        await w.drain()
        resp = await asyncio.wait_for(r.readline(), timeout=5)
        pong = json.loads(resp.decode())
        lat = round((time.time() - pong.get("ts", time.time())) * 1000, 1)
        print(f"[клиент] ✅ PONG! latency={lat}ms")
        print()
        print(f"[клиент] 📝 Сохрани файл: {fname}")
        w.close()
        return True
    except Exception as e:
        print(f"[клиент] ❌ Ошибка: {e}")
        return False

async def main():
    host = None
    is_server = True
    for i, a in enumerate(sys.argv):
        if a == "--server": is_server = True
        if a == "--peer" and i+1 < len(sys.argv):
            host = sys.argv[i+1]
            is_server = False
    if host:
        await client(*host.split(":"))
    else:
        task = asyncio.create_task(server(PORT))
        await task

if __name__ == "__main__":
    asyncio.run(main())
