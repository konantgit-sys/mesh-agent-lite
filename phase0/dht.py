"""DHT Store — заглушка для SDK без IPFS.

В оригинальном p2p-agent-mesh DHT требует IPFS daemon.
В mesh-agent-lite DHT отключён — используется Nostr kind:39010 discovery.
"""

class DHTStore:
    """Заглушка для обратной совместимости с AgentMesh SDK."""
    
    def __init__(self, *args, **kwargs):
        self._store = {}
    
    async def put(self, key: str, value: str, ttl: int = 3600) -> bool:
        return False
    
    async def get(self, key: str) -> str | None:
        return None
    
    async def stop(self):
        pass
