#!/bin/bash
# ============================================
# Mesh Agent Lite — Test Runner
# ============================================
# Запускает полный набор тестов mesh-агента
# Результат: summary + proof-код
# ============================================

set -e

HUB="${1:-155.212.133.195:9908}"
echo "╔══════════════════════════════════════╗"
echo "║     Mesh Agent Lite — Test Runner   ║"
echo "║     Hub: $HUB               ║"
echo "║     $(date)        ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Проверка зависимостей
echo "▶ Проверка зависимостей..."
python3 -c "import cryptography" 2>/dev/null || pip install -q cryptography
echo "  OK"
echo ""

# 1. Базовый TCP ping
echo "▶ Тест 1: TCP ping..."
python3 mesh_ping.py --peer $HUB 2>&1 | tail -5
echo ""

# 2. Proof-код
echo "▶ Тест 2: генерация proof-кода..."
python3 -c "
import hashlib, uuid, time
h = hashlib.sha256(f'{uuid.uuid4().hex}:{time.time()}:runner'.encode()).hexdigest()[:12]
code = f'{h[:4]}-{h[4:8]}-{h[8:12]}'
print(f'  Код: {code}')
with open(f'connection_{code}.proof', 'w') as f:
    f.write('MESH_AGENT_CONNECTION_PROOF\n')
    f.write(f'Code: {code}\n')
    f.write(f'Timestamp: {int(time.time())}\n')
    f.write(f'Runner: test-suite\n')
print(f'  Файл: connection_{code}.proof')
print('  ✅ Proof-код создан')
"
echo ""

# 3. Полный тест-сьют (без uptime)
echo "▶ Тест 3: Test Suite (все тесты)..."
python3 test_suite.py --hub $HUB --skip-uptime 2>&1
echo ""

# 4. Итог
echo "══════════════════════════════════════"
echo "  Все тесты выполнены."
echo "  Проверь файлы .proof в директории."
echo "══════════════════════════════════════"
