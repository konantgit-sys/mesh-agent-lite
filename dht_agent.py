#!/usr/bin/env python3
"""
DHT Agent — демон Kademlia DHT поверх relay.
Запуск: python3 dht_agent.py --port 9998 --relay 127.0.0.1:8443
"""
import asyncio, json, time, uuid, sys, os, signal, logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase0.dht_kademlia import KBucket, node_id_from_pubkey, K

log = logging.getLogger("dht-agent")

class DHTAgent:
    def __init__(self, port: int, relay_host: str, relay_port: int):
        self.port = port
        self.relay_addr = (relay_host, relay_port)
        self.pubkey = uuid.uuid4().hex
        self.node_id = node_id_from_pubkey(self.pubkey)
        self.buckets = [KBucket(0, 160)]
        self.peers = {}  # addr -> info
        self.running = False
        self._server = None

    async def start(self):
        self.running = True
        
        # TCP сервер для пиров
        self._server = await asyncio.start_server(
            self._handle_peer, "0.0.0.0", self.port)
        
        # Подключение к relay
        await self._connect_relay()
        
        print(f"[DHT] Агент запущен")
        print(f"  Pubkey: {self.pubkey[:16]}...")
        print(f"  NodeID: {self.node_id.hex()[:16]}...")
        print(f"  Порт:   {self.port}")
        print(f"  Relay:  {self.relay_addr[0]}:{self.relay_addr[1]}")
        print()
        
        async with self._server:
            await self._server.serve_forever()

    async def _connect_relay(self):
        try:
            r, w = await asyncio.wait_for(
                asyncio.open_connection(*self.relay_addr), 5)
            hello = json.dumps({
                "kind": 0, "pubkey": self.pubkey, "name": f"dht-{self.port}",
                "content": {"type": "register", "port": self.port, "ts": time.time()}
            }).encode() + b"\n"
            w.write(hello)
            await asyncio.wait_for(w.drain(), 3)
            print(f"  ✅ Подключился к relay на {self.relay_addr[0]}:{self.relay_addr[1]}")
            w.close()
        except Exception as e:
            print(f"  ⚠️ Не смог подключиться к relay: {e}")

    async def _handle_peer(self, reader, writer):
        addr = writer.get_extra_info('peername')
        try:
            data = await asyncio.wait_for(reader.readline(), 10)
            msg = json.loads(data.decode())
            
            # Регистрация пира
            if msg.get("kind") in (0, 1):
                peer_pk = msg.get("pubkey", "?")
                peer_port = msg.get("content", {}).get("port", 0)
                peer_name = msg.get("name", "?")
                peer_addr = f"{addr[0]}:{peer_port}" if peer_port else f"{addr[0]}:{addr[1]}"
                
                # Добавляем в K-bucket
                peer_nid = node_id_from_pubkey(peer_pk)
                self.buckets[0].add_node(peer_nid, peer_addr, peer_pk)
                self.peers[peer_addr] = {
                    "pubkey": peer_pk, "name": peer_name, "ts": time.time()
                }
                
                # Ответ с нашими данными
                resp = json.dumps({
                    "kind": 0, "pubkey": self.pubkey, "name": f"dht-{self.port}",
                    "content": {
                        "type": "dht_ok", "port": self.port,
                        "node_id": self.node_id.hex(),
                        "buckets": len(self.buckets), "peers": len(self.peers)
                    }
                }).encode() + b"\n"
                writer.write(resp)
                await writer.drain()
                print(f"  🤝 Пир найден: {peer_name} ({peer_addr})")
        except Exception as e:
            pass
        finally:
            try: writer.close()
            except: pass

    async def find_peer(self, target_pubkey: str) -> dict | None:
        """Поиск пира по pubkey через bucket."""
        target_nid = node_id_from_pubkey(target_pubkey)
        best = None
        best_dist = None
        for addr, info in self.peers.items():
            peer_nid = node_id_from_pubkey(info["pubkey"])
            d = int.from_bytes(target_nid, 'big') ^ int.from_bytes(peer_nid, 'big')
            if best_dist is None or d < best_dist:
                best = addr
                best_dist = d
        if best:
            return {"addr": best, **self.peers[best]}
        return None

    def stats(self) -> dict:
        return {
            "port": self.port,
            "pubkey": self.pubkey[:16],
            "node_id": self.node_id.hex()[:16],
            "peers": len(self.peers),
            "buckets": len(self.buckets),
            "uptime": round(time.time() - self._start_ts, 1) if hasattr(self, '_start_ts') else 0
        }


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="DHT Agent — Kademlia над relay")
    parser.add_argument("--port", type=int, default=9998, help="Порт DHT агента")
    parser.add_argument("--relay", default="127.0.0.1:8443", help="Адрес relay")
    args = parser.parse_args()
    
    relay_host, relay_port = args.relay.split(":")
    agent = DHTAgent(args.port, relay_host, int(relay_port))
    agent._start_ts = time.time()
    
    try:
        await agent.start()
    except KeyboardInterrupt:
        print("\n[DHT] Остановка...")

if __name__ == "__main__":
    asyncio.run(main())
