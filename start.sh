#!/bin/bash
cd /home/agent/data/mesh-agent-lite

# Relay на :8443
nohup python3 -m relay.server --port 8443 --host 0.0.0.0 > /tmp/relay.log 2>&1 &
echo "Relay PID: $!"

# Агент на :9908
nohup python3 simple_agent.py --name "hub" --port 9908 > /tmp/agent.log 2>&1 &
echo "Agent PID: $!"


# DHT Agent A (:9998)
nohup python3 dht_agent.py --port 9998 --relay 127.0.0.1:8443 > /tmp/dht_a.log 2>&1 &
echo "DHT-A PID: $!"

# DHT Agent B (:9999)
nohup python3 dht_agent.py --port 9999 --relay 127.0.0.1:8443 > /tmp/dht_b.log 2>&1 &
echo "DHT-B PID: $!"

echo "Оба DHT агента запущены"
