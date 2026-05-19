#!/usr/bin/env python3
"""
Simple Agent — простейший P2P агент для mesh-сети.

Что делает:
- Принимает TCP соединения на указанном порту
- Эхо-ответы: любое сообщение возвращает отправителю
- Счётчик сообщений: считает принятые, переданные, ошибки
- Relay: пересылает сообщения другим подключённым пирам
- Генерирует proof-код при запуске (для NFT)
- Heartbeat каждые 30 сек — статистика работы

Запуск:
  python3 simple_agent.py --port 9908 --name "my-agent"
  python3 simple_agent.py --port 9908 --name "relay" --relay-to IP:PORT
"""

import asyncio
import json
import time
import uuid
import hashlib
import argparse
import sys

# ═══ КОНФИГ ═══
HEARTBEAT_INTERVAL = 30
DEAD_AFTER = 120


class SimpleAgent:
    """Простейший P2P агент."""

    def __init__(self, name: str, port: int, relay_to: list = None):
        self.name = name
        self.port = port
        self.pubkey = uuid.uuid4().hex * 4
        self._start_time = time.time()
        self._msg_count = 0
        self._relay_count = 0
        self._err_count = 0
        self._peers = {}       # pubkey -> {"host": str, "port": int, "name": str}
        self._last_seen = {}   # pubkey -> float
        self._relay_targets = relay_to or []
        self._running = False

        # Proof-код (для NFT)
        proof_raw = f"{self.pubkey}:{time.time()}:simple-agent-v1:mesh-birthday-2026"
        proof_hash = hashlib.sha256(proof_raw.encode()).hexdigest()[:12]
        self._proof_code = f"{proof_hash[:4]}-{proof_hash[4:8]}-{proof_hash[8:12]}"
        self._proof_file = f"connection_{self._proof_code}.proof"

        try:
            with open(self._proof_file, "w") as f:
                f.write("SIMPLE_AGENT_PROOF\n")
                f.write(f"Name: {self.name}\n")
                f.write(f"Code: {self._proof_code}\n")
                f.write(f"Timestamp: {int(time.time())}\n")
                f.write(f"Agent: Simple Agent v1.0\n")
                f.write(f"--\n")
                f.write(f"Save this file. It proves you ran a mesh agent\n")
                f.write(f"on {time.strftime('%Y-%m-%d %H:%M UTC')}.\n")
        except:
            self._proof_file = None

    async def start(self):
        """Запуск агента."""
        print(f"╔═══ Simple Mesh Agent ═══╗")
        print(f"║ Имя:    {self.name}")
        print(f"║ Порт:   {self.port}")
        print(f"║ Relay:  {len(self._relay_targets)}")
        print(f"╚══════════════════════════╝")
        print()
        self._running = True

        # TCP сервер
        server = await asyncio.start_server(
            self._handle_connection, host="0.0.0.0", port=self.port
        )
        print(f"[{self.name}] 📡 Слушаю на :{self.port}")
        print()

        # Proof-код
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"  🎂 MESH NETWORK — ДЕНЬ РОЖДЕНИЯ! 🎂")
        print(f"")
        print(f"  ⚠️  СОХРАНИ ЭТОТ КОД:")
        print(f"  ┌──────────────────────────────────┐")
        print(f"  │   {self._proof_code}   │")
        print(f"  └──────────────────────────────────┘")
        print(f"  Файл: {self._proof_file}")
        print(f"")
        print(f"  Этот код — пропуск в историю.")
        print(f"  Когда появится платформа — каждый")
        print(f"  код активирует NFT.")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()

        # Подключение к relay-целям
        for target in self._relay_targets:
            host, port = target.split(":")
            asyncio.create_task(self._connect_to_peer(host, int(port)))

        # Heartbeat
        asyncio.create_task(self._heartbeat())

        async with server:
            await server.serve_forever()

    async def _handle_connection(self, reader, writer):
        """Входящее TCP соединение."""
        peer = writer.get_extra_info('peername')
        try:
            data = await asyncio.wait_for(reader.readline(), timeout=15)
            msg = json.loads(data.decode())
            self._msg_count += 1

            kind = msg.get("kind", 0)
            from_pk = msg.get("pubkey", "unknown")
            from_name = msg.get("name", from_pk[:12])

            self._last_seen[from_pk] = time.time()

            if kind == 1:  # HELLO
                content = msg.get("content", {})
                host = content.get("host", peer[0])
                port = content.get("port", 0)
                name = content.get("name", from_pk[:12])
                self._peers[from_pk] = {"host": host, "port": port, "name": name}

                # Регистрируем пира
                print(f"[{self.name}] 🤝 Пир {name} ({host}:{port})")

                # Ответ HELLO
                pong = json.dumps({
                    "kind": 1, "pubkey": self.pubkey, "name": self.name,
                    "content": {
                        "host": "0.0.0.0", "port": self.port,
                        "name": self.name, "ts": time.time(),
                        "proof": self._proof_code
                    }
                }).encode() + b"\n"
                writer.write(pong)
                await writer.drain()

            elif kind == 2:  # PING
                content = msg.get("content", {})
                nonce = content.get("nonce", "")
                ts = content.get("ts", 0)
                lat = round((time.time() - ts) * 1000, 1) if ts else 0

                pong = json.dumps({
                    "kind": 3, "pubkey": self.pubkey, "name": self.name,
                    "content": {
                        "ack_for": nonce, "ts": time.time(),
                        "latency_ms": lat
                    }
                }).encode() + b"\n"
                writer.write(pong)
                await writer.drain()
                print(f"[{self.name}] 📡 PING от {from_name} → {lat}ms")

            elif kind == 10:  # ECHO / DATA
                content = msg.get("content", {})
                payload = content.get("payload", "")
                print(f"[{self.name}] 📩 Эхо от {from_name}: {str(payload)[:60]}")

                # Эхо-ответ
                echo = json.dumps({
                    "kind": 11, "pubkey": self.pubkey, "name": self.name,
                    "content": {
                        "echo": payload, "original_from": from_pk,
                        "ts": time.time()
                    }
                }).encode() + b"\n"
                writer.write(echo)
                await writer.drain()

                # Relay — пересылаем другим пирам (без повторного relay)
                if payload and not str(payload).startswith("[relayed]"):
                    await self._relay_message(from_pk, payload)

            elif kind == 11:  # ECHO_RESPONSE
                content = msg.get("content", {})
                echo = content.get("echo", "")
                print(f"[{self.name}] ↩️ Эхо-ответ: {str(echo)[:60]}")

            elif kind == 99:  # GOODBYE
                print(f"[{self.name}] 👋 {from_name} отключился")
                self._peers.pop(from_pk, None)
                self._last_seen.pop(from_pk, None)

        except asyncio.TimeoutError:
            pass
        except Exception as e:
            self._err_count += 1
        finally:
            try:
                writer.close()
            except:
                pass

    async def _relay_message(self, exclude_pk: str, payload: str):
        """Переслать сообщение всем пирам кроме отправителя."""
        for pk, peer in self._peers.items():
            if pk == exclude_pk:
                continue
            try:
                r, w = await asyncio.wait_for(
                    asyncio.open_connection(peer["host"], peer["port"]), timeout=3
                )
                msg = json.dumps({
                    "kind": 10, "pubkey": self.pubkey, "name": self.name,
                    "content": {
                        "payload": f"[relayed] {payload}",
                        "relay_from": exclude_pk[:12],
                        "ts": time.time()
                    }
                }).encode() + b"\n"
                w.write(msg)
                await asyncio.wait_for(w.drain(), timeout=2)
                w.close()
                self._relay_count += 1
            except:
                pass

    async def _connect_to_peer(self, host: str, port: int):
        """Подключиться к пиру."""
        print(f"[{self.name}] 🔌 Подключаюсь к {host}:{port}...")
        try:
            r, w = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=5
            )
            hello = json.dumps({
                "kind": 1, "pubkey": self.pubkey, "name": self.name,
                "content": {
                    "host": "0.0.0.0", "port": self.port,
                    "name": self.name, "ts": time.time(),
                    "proof": self._proof_code
                }
            }).encode() + b"\n"
            w.write(hello)
            await asyncio.wait_for(w.drain(), timeout=3)
            print(f"[{self.name}] ✅ Подключён к {host}:{port}")
            w.close()

            # Регистрируем пира
            pk = f"direct:{host}:{port}"
            self._peers[pk] = {"host": host, "port": port, "name": f"peer@{host}"}
            self._last_seen[pk] = time.time()
        except Exception as e:
            print(f"[{self.name}] ❌ Не могу подключиться к {host}:{port}: {e}")

    async def _heartbeat(self):
        """Периодический вывод статистики."""
        while self._running:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            now = time.time()
            elapsed = (now - self._start_time) / 60

            # Очистка мёртвых пиров
            dead = [pk for pk, ts in self._last_seen.items()
                    if now - ts > DEAD_AFTER]
            for pk in dead:
                name = self._peers.get(pk, {}).get("name", pk[:12])
                print(f"[{self.name}] 💀 Пир {name} мёртв")
                self._peers.pop(pk, None)
                self._last_seen.pop(pk, None)

            peers_alive = len(self._peers)
            print(f"[{self.name}] ❤️ {elapsed:.0f}м "
                  f"peers={peers_alive} "
                  f"msgs={self._msg_count} "
                  f"relay={self._relay_count} "
                  f"errs={self._err_count}"
                  f"{' | proof: ' + self._proof_code if peers_alive > 0 else ''}")


def main():
    parser = argparse.ArgumentParser(description="Simple Mesh Agent")
    parser.add_argument("--port", type=int, default=9908, help="TCP порт")
    parser.add_argument("--name", type=str, default=f"agent_{uuid.uuid4().hex[:4]}", help="Имя агента")
    parser.add_argument("--peer", type=str, action="append", help="Пир: host:port")
    parser.add_argument("--test", action="store_true", help="Тест-режим (30 мин)")

    args = parser.parse_args()

    agent = SimpleAgent(name=args.name, port=args.port, relay_to=args.peer)

    try:
        asyncio.run(agent.start())
    except KeyboardInterrupt:
        print(f"\n[{args.name}] 👋 Завершено")


if __name__ == "__main__":
    main()
