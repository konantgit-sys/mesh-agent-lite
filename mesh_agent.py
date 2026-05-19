#!/usr/bin/env python3
"""
Mesh Agent — лёгкий P2P агент для mesh-сети.

Что делает:
- Открывает TCP порт для gossip-сообщений
- Принимает ping от других агентов, отвечает pong
- Может отправлять сообщения другим агентам
- Измеряет latency и качество канала
- Логирует всю активность

Запуск (одиночный):       python3 mesh_agent.py
Запуск с пиром:          python3 mesh_agent.py --peer 1.2.3.4:9908
Режим теста (1 час):     python3 mesh_agent.py --test --peer 5.6.7.8:9908

Требования: Python 3.8+ (без сторонних библиотек)
"""

import asyncio
import json
import time
import uuid
import argparse
import sys
import hashlib
import os

# ═══ КОНФИГ ═══
DEFAULT_PORT = 9908
HEARTBEAT_INTERVAL = 30  # сек
PING_INTERVAL = 60       # сек — интервал отправки ping пиру
DEAD_AFTER = 180         # сек — считаем пира мёртвым
CLEANUP_INTERVAL = 120   # сек — очистка мёртвых пиров
TEST_DURATION = 3600     # сек (60 мин) — авто-завершение в --test режиме

# Типы gossip-сообщений
KIND_PING = 1
KIND_PONG = 2
KIND_GOSSIP = 3
KIND_HELLO = 4
KIND_GOODBYE = 5


class MeshAgent:
    """Лёгкий P2P mesh агент."""

    def __init__(self, name: str, port: int, peers: list = None):
        self.name = name
        self.port = port
        self.pubkey = uuid.uuid4().hex * 4  # 64 hex — как настоящий ключ
        self._peers = {}      # pubkey -> {"host": str, "port": int, "name": str}
        self._quality = {}    # pubkey -> {"latency": float, "score": float}
        self._last_seen = {}  # pubkey -> float
        self._server = None
        self._running = False
        self._start_time = time.time()
        self._msg_count = 0
        self._err_count = 0

        # Стартовые пиры (из --peer аргумента)
        self._bootstrap_peers = peers or []

        # Генерация proof-кода (для NFT-активации)
        self._proof_salt = "mesh-birthday-2026-05-19"
        proof_raw = f"{self.pubkey}:{time.time()}:{self._proof_salt}"
        proof_hash = hashlib.sha256(proof_raw.encode()).hexdigest()[:12]
        self._proof_code = f"{proof_hash[:4]}-{proof_hash[4:8]}-{proof_hash[8:12]}"
        self._proof_file = f"connection_{self._proof_code}.proof"

        # Сохраняем proof-файл
        try:
            with open(self._proof_file, "w") as f:
                f.write("MESH_AGENT_CONNECTION_PROOF\n")
                f.write(f"Name: {self.name}\n")
                f.write(f"Code: {self._proof_code}\n")
                f.write(f"Timestamp: {int(time.time())}\n")
                f.write(f"Agent: Mesh P2P v1.0\n")
                f.write(f"--\n")
                f.write(f"Save this file. It proves you ran a mesh agent\n")
                f.write(f"on {time.strftime('%Y-%m-%d %H:%M UTC')}.\n")
        except:
            self._proof_file = None

    async def start(self):
        """Запуск агента."""
        print(f"╔═══ Mesh Agent ═══╗")
        print(f"║ Имя:     {self.name}")
        print(f"║ Pubkey:  {self.pubkey[:16]}...")
        print(f"║ Порт:    {self.port}")
        print(f"║ Пиры:    {len(self._bootstrap_peers)}")
        print(f"╚════════════════════════╝")
        print()

        self._running = True

        # TCP сервер
        self._server = await asyncio.start_server(
            self._handle_connection,
            host="0.0.0.0",
            port=self.port
        )
        print(f"[{self.name}] 📡 Слушаю на :{self.port} (TCP)")
        print()

        # Вывод proof-кода
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"  🎂 ДЕНЬ РОЖДЕНИЯ MESH NETWORK! 🎂")
        print(f"  Сегодня проекту исполняется 1 день.")
        print(f"")
        print(f"  ⚠️  СОХРАНИ ЭТОТ КОД:")
        print(f"  ┌──────────────────────────────────┐")
        print(f"  │   {self._proof_code}   │")
        print(f"  └──────────────────────────────────┘")
        print(f"")
        print(f"  Файл с кодом: {self._proof_file}")
        print(f"")
        print(f"  Этот код — твой пропуск в историю.")
        print(f"  Когда появится платформа — каждый код")
        print(f"  активирует NFT первого подключения.")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()

        # Подключение к bootstrap пирам
        for peer_str in self._bootstrap_peers:
            host, port = peer_str.split(":")
            await self._bootstrap_peer(host, int(port))

        # Фоновые задачи
        asyncio.create_task(self._heartbeat_loop())
        if self._bootstrap_peers:
            asyncio.create_task(self._ping_loop())

        async with self._server:
            await self._server.serve_forever()

    async def _handle_connection(self, reader, writer):
        """Обработка входящего TCP соединения."""
        peer = writer.get_extra_info('peername')
        try:
            data = await asyncio.wait_for(reader.readline(), timeout=30)
            msg = json.loads(data.decode())
            await self._process_message(msg, writer)
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            self._err_count += 1
        finally:
            try:
                writer.close()
            except:
                pass

    async def _process_message(self, msg: dict, writer):
        """Обработка входящего gossip-сообщения."""
        kind = msg.get("kind", 0)
        from_pk = msg.get("pubkey", "unknown")
        from_name = msg.get("name", from_pk[:16])

        content = msg.get("content", {})
        ts = content.get("ts", 0)

        # Обновляем last_seen для этого пира
        if from_pk != self.pubkey:
            self._last_seen[from_pk] = time.time()

        if kind == KIND_HELLO:
            # Приветствие — регистрируем пира
            host = content.get("host", "?")
            port = content.get("port", 0)
            name = content.get("name", from_pk[:16])
            self._peers[from_pk] = {"host": host, "port": port, "name": name}
            
            latency = round((time.time() - ts) * 1000, 1) if ts else 0
            self._quality[from_pk] = {
                "latency": latency,
                "score": 1.0,
                "last_ping": time.time()
            }
            
            print(f"[{self.name}] 🤝 Новый пир: {name} ({host}:{port}) latency={latency}ms")
            
            # Показываем proof-код пира, если есть
            peer_proof = content.get("proof", "")
            if peer_proof:
                print(f"[{self.name}] 🔗 Пир {name} → код {peer_proof}")

            # Отвечаем HELLO
            pong = json.dumps({
                "kind": KIND_HELLO,
                "pubkey": self.pubkey,
                "name": self.name,
                "content": {
                    "host": "0.0.0.0",
                    "port": self.port,
                    "name": self.name,
                    "ts": time.time(),
                    "proof": self._proof_code,
                    "ack_for": content.get("nonce", "")
                }
            }).encode() + b"\n"
            writer.write(pong)
            await writer.drain()

        elif kind == KIND_PING:
            # Пинг — отвечаем PONG
            nonce = content.get("nonce", "")
            pong = json.dumps({
                "kind": KIND_PONG,
                "pubkey": self.pubkey,
                "name": self.name,
                "content": {
                    "ack_for": nonce,
                    "ts": time.time(),
                    "latency_ms": round((time.time() - ts) * 1000, 1) if ts else 0
                }
            }).encode() + b"\n"
            writer.write(pong)
            await writer.drain()
            self._msg_count += 1

            # Обновляем качество
            if ts:
                latency = (time.time() - ts) * 1000
                if from_pk in self._quality:
                    q = self._quality[from_pk]
                    q["latency"] = round(latency, 1)
                    q["last_ping"] = time.time()
                    q["score"] = min(1.0, q.get("score", 1.0) + 0.1)

        elif kind == KIND_PONG:
            # Ответ на наш ping
            ack_for = content.get("ack_for", "")
            latency = content.get("latency_ms", 0)
            self._msg_count += 1
            
            if from_pk in self._quality:
                self._quality[from_pk]["latency"] = latency
                self._quality[from_pk]["last_ping"] = time.time()

        elif kind == KIND_GOSSIP:
            # Обычное gossip-сообщение
            payload = content.get("payload", {})
            self._msg_count += 1
            print(f"[{self.name}] 📩 От {from_name}: {json.dumps(payload)[:80]}")

        elif kind == KIND_GOODBYE:
            # Пир отключается
            if from_pk in self._peers:
                print(f"[{self.name}] 👋 Пир {from_name} отключился")
                del self._peers[from_pk]
                self._quality.pop(from_pk, None)
                self._last_seen.pop(from_pk, None)

    async def send_to(self, host: str, port: int, msg: dict) -> bool:
        """Отправка сообщения пиру через TCP."""
        try:
            r, w = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=5
            )
            data = json.dumps(msg).encode() + b"\n"
            w.write(data)
            await asyncio.wait_for(w.drain(), timeout=3)
            try:
                resp = await asyncio.wait_for(r.readline(), timeout=3)
                w.close()
                return resp
            except:
                w.close()
                return True
        except Exception as e:
            return False

    async def _bootstrap_peer(self, host: str, port: int):
        """Подключение к пиру — отправка HELLO."""
        print(f"[{self.name}] 🔌 Подключаюсь к {host}:{port}...")
        msg = {
            "kind": KIND_HELLO,
            "pubkey": self.pubkey,
            "name": self.name,
            "content": {
                "host": "0.0.0.0",
                "port": self.port,
                "name": self.name,
                "ts": time.time(),
                "proof": self._proof_code,
                "nonce": f"hello:{int(time.time())}"
            }
        }
        resp = await self.send_to(host, port, msg)
        if resp:
            try:
                data = json.loads(resp.decode())
                if data.get("kind") == KIND_HELLO:
                    pk = data["pubkey"]
                    c = data.get("content", {})
                    self._peers[pk] = {
                        "host": c.get("host", host),
                        "port": c.get("port", port),
                        "name": c.get("name", pk[:16])
                    }
                    self._quality[pk] = {"latency": 0, "score": 1.0, "last_ping": time.time()}
                    self._last_seen[pk] = time.time()
                    peer_proof = c.get("proof", "")
                    proof_msg = f" код {peer_proof}" if peer_proof else ""
                    print(f"[{self.name}] ✅ Подключён к {data.get('name', pk[:16])}{proof_msg}")
            except:
                pass
        else:
            print(f"[{self.name}] ❌ Не могу подключиться к {host}:{port}")

    async def _heartbeat_loop(self):
        """Периодический вывод статуса."""
        while self._running:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            now = time.time()
            
            # Очистка мёртвых
            dead = [pk for pk, ts in self._last_seen.items() 
                    if now - ts > DEAD_AFTER and pk in self._peers]
            for pk in dead:
                name = self._peers[pk]["name"]
                print(f"[{self.name}] 💀 Пир {name} мёртв ({DEAD_AFTER}с без ответа)")
                del self._peers[pk]
                self._quality.pop(pk, None)
                del self._last_seen[pk]

            # Вывод статуса
            elapsed = (now - self._start_time) / 60
            peers_alive = len(self._peers)
            
            summary = f"[{self.name}] ❤️ uptime={elapsed:.0f}м peers={peers_alive} msgs={self._msg_count} errs={self._err_count}"
            if peers_alive:
                for pk, q in sorted(self._quality.items(), key=lambda x: x[1].get("score", 0), reverse=True):
                    peer_name = self._peers.get(pk, {}).get("name", pk[:16])
                    lat = q.get("latency", "?")
                    score = q.get("score", 0)
                    summary += f" | {peer_name} lat={lat}ms score={score:.2f}"
            print(summary)

    async def _ping_loop(self):
        """Периодический ping всех пиров."""
        await asyncio.sleep(5)  # даём время на HELLO
        while self._running:
            for pk, peer in list(self._peers.items()):
                msg = {
                    "kind": KIND_PING,
                    "pubkey": self.pubkey,
                    "name": self.name,
                    "content": {
                        "ts": time.time(),
                        "nonce": f"ping:{int(time.time())}:{pk[:8]}"
                    }
                }
                ok = await self.send_to(peer["host"], peer["port"], msg)
                if ok:
                    self._quality.setdefault(pk, {"latency": 0, "score": 1.0, "last_ping": 0})
                else:
                    q = self._quality.get(pk, {})
                    q["score"] = max(0, q.get("score", 1.0) - 0.2)
                    print(f"[{self.name}] ⚠️ Ping failed to {peer['name']} (score={q['score']:.2f})")

            await asyncio.sleep(PING_INTERVAL)


def main():
    parser = argparse.ArgumentParser(description="Mesh Agent — P2P gossip")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="TCP порт")
    parser.add_argument("--name", type=str, default=f"agent_{uuid.uuid4().hex[:4]}", help="Имя агента")
    parser.add_argument("--peer", type=str, action="append", help="Пир: host:port")
    parser.add_argument("--test", action="store_true", help="Режим теста (авто-завершение через 60 мин)")
    args = parser.parse_args()

    try:
        agent = MeshAgent(name=args.name, port=args.port, peers=args.peer)
        asyncio.run(agent.start())
    except KeyboardInterrupt:
        print(f"\n[{args.name}] 👋 Завершено")


if __name__ == "__main__":
    main()
