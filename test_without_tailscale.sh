#!/bin/bash
# Полный тест без Tailscale

echo "=========================================="
echo "🧪 ТЕСТ БЕЗ TAILSCALE"
echo "=========================================="

echo ""
echo "1️⃣ Останавливаем Tailscale..."
sudo systemctl stop tailscaled
sleep 2

echo ""
echo "2️⃣ Проверяем что Tailscale остановлен..."
if systemctl is-active --quiet tailscaled; then
    echo "❌ Tailscale всё ещё работает!"
    exit 1
else
    echo "✅ Tailscale остановлен"
fi

echo ""
echo "3️⃣ Тестируем WebSocket соединение..."
cd /home/sadmin/Documents/gateway_proxy
source venv/bin/activate
python test_ws.py

echo ""
echo "=========================================="
echo "4️⃣ Если работает, запускаем прокси..."
echo "   Команда: python proxy.py"
echo ""
echo "5️⃣ Для включения Tailscale обратно:"
echo "   sudo systemctl start tailscaled"
echo "=========================================="
