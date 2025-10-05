# Phase 3: Resilience & Monitoring Features

## 🎯 Overview

Phase 3 добавляет функции отказоустойчивости и мониторинга для production-ready deployment.

---

## 📦 Feature 1: Offline Queue

### Что это?

Сохранение сообщений когда WebSocket отключен, с автоматической отправкой при переподключении.

### Как работает:

```
1. WebSocket отключился (обрыв интернета)
2. Пришел ответ от gateway → некуда отправить
3. Сохраняем в очередь (max 10 сообщений)
4. WebSocket переподключился → отправляем всё из очереди
```

### Параметры:

- **Максимальный размер:** 10 сообщений
- **Поведение при переполнении:** Дропаем новые сообщения (старые важнее)
- **Логирование:**
  - `📦 WS disconnected, queued message (5/10)` - сообщение добавлено в очередь
  - `⚠️ Queue full (10/10), dropping message` - очередь переполнена
  - `📤 Flushing 5 queued messages...` - начало отправки очереди
  - `✅ Sent queued message (3 remaining)` - прогресс отправки

### Пример из логов:

```
10:30:00 - INFO - 📥 Received: payment from kiosk-123
10:30:01 - INFO - ✅ Gateway response: HTTP 200
10:30:02 - WARNING - ⚠️ WebSocket connection closed
10:30:02 - WARNING - 📦 WS disconnected, queued message (1/10)
10:30:05 - WARNING - 📦 WS disconnected, queued message (2/10)
10:30:10 - INFO - ✅ Connected to cloud server
10:30:10 - INFO - 📤 Flushing 2 queued messages...
10:30:10 - INFO - ✅ Sent queued message (1 remaining)
10:30:10 - INFO - ✅ Sent queued message (0 remaining)
```

### Когда полезно:

- ✅ Краткосрочные обрывы связи (5-30 секунд)
- ✅ Переключение между сетями
- ✅ Кратковременные проблемы на сервере

### Когда НЕ поможет:

- ❌ Долгий обрыв связи (>1 минута) - очередь переполнится
- ❌ Перезагрузка прокси - очередь в памяти, не сохраняется

---

## 🏥 Feature 2: Health Check Endpoint

### Что это?

HTTP endpoint для проверки статуса прокси без SSH доступа.

### Endpoint:

```
GET http://localhost:9090/health
```

### Response:

```json
{
  "status": "healthy",              // "healthy" | "disconnected" | "error"
  "ws_connected": true,              // WebSocket соединение активно?
  "uptime_seconds": 3600.5,          // Время работы в секундах
  "stats": {
    "messages_received": 156,
    "messages_sent": 156,
    "errors": 2,
    "reconnections": 1
  },
  "queue_size": 0,                   // Сколько сообщений в offline queue
  "routes_configured": 4             // Количество настроенных роутов
}
```

### Статусы:

- **`healthy`** - всё в порядке, WS подключен
- **`disconnected`** - WS отключен, пытается переподключиться
- **`error`** - критическая ошибка (редко)

### Примеры использования:

#### 1. Ручная проверка

```bash
curl http://localhost:9090/health | jq
```

#### 2. Мониторинг скрипт

```bash
#!/bin/bash
# check_proxy_health.sh

RESPONSE=$(curl -s http://localhost:9090/health)
STATUS=$(echo $RESPONSE | jq -r '.status')

if [ "$STATUS" != "healthy" ]; then
    echo "⚠️ Proxy is $STATUS"
    # Отправить алерт в Slack/Email
    exit 1
fi

echo "✅ Proxy is healthy"
exit 0
```

Запускать каждые 30 секунд через cron:
```
* * * * * /path/to/check_proxy_health.sh
* * * * * sleep 30; /path/to/check_proxy_health.sh
```

#### 3. Prometheus метрики (опционально)

Можно добавить экспортер метрик:

```python
# prometheus_exporter.py
from prometheus_client import start_http_server, Gauge
import requests
import time

g_uptime = Gauge('proxy_uptime_seconds', 'Proxy uptime')
g_messages_received = Gauge('proxy_messages_received_total', 'Total messages received')
g_queue_size = Gauge('proxy_queue_size', 'Offline queue size')

def collect_metrics():
    while True:
        try:
            r = requests.get('http://localhost:9090/health')
            data = r.json()

            g_uptime.set(data['uptime_seconds'])
            g_messages_received.set(data['stats']['messages_received'])
            g_queue_size.set(data['queue_size'])
        except:
            pass

        time.sleep(10)

if __name__ == '__main__':
    start_http_server(9091)
    collect_metrics()
```

#### 4. Grafana дашборд

После настройки Prometheus можно построить графики:
- Uptime
- Messages per minute
- Queue size
- Error rate

### Безопасность:

- **Localhost only:** Endpoint доступен только на `localhost:9090`
- Нет внешнего доступа (нужно быть на машине или SSH tunnel)
- Нет аутентификации (т.к. localhost)

Если нужен внешний доступ:
```python
# В коде изменить:
site = web.TCPSite(runner, '0.0.0.0', 9090)  # Вместо 'localhost'

# И добавить basic auth или token
```

---

## 📊 Monitoring Best Practices

### 1. **Локальный мониторинг (на киоске):**

```bash
# Скрипт запускается каждую минуту
* * * * * /usr/local/bin/check_proxy.sh

# check_proxy.sh
#!/bin/bash
STATUS=$(curl -s http://localhost:9090/health | jq -r '.status')
if [ "$STATUS" != "healthy" ]; then
    echo "$(date): Proxy unhealthy" >> /var/log/proxy_alerts.log
fi
```

### 2. **Централизованный мониторинг:**

**Вариант А: Polling с центрального сервера**
- Центральный сервер опрашивает каждый киоск через SSH tunnel
- SSH tunnel: `ssh -L 9090:localhost:9090 kiosk@kiosk-123`
- Затем `curl http://localhost:9090/health`

**Вариант Б: Push метрики в облако** (будущее расширение)
- Прокси периодически отправляет метрики на сервер
- Сервер агрегирует метрики всех киосков
- Дашборд показывает состояние всех киосков

### 3. **Алертинг:**

**Когда алертить:**
- `status != "healthy"` более 2 минут
- `queue_size > 5` (очередь заполняется)
- `errors > 10` за последний час
- `uptime < 60` (частые перезапуски)

**Куда алертить:**
- Slack webhook
- Email
- PagerDuty
- Telegram bot

---

## 🔧 Troubleshooting

### Health endpoint не отвечает

```bash
# Проверить что прокси запущен
sudo systemctl status gateway-proxy

# Проверить что порт 9090 слушается
sudo netstat -tulpn | grep 9090

# Проверить логи
sudo journalctl -u gateway-proxy -n 50
```

### Queue постоянно заполняется

```bash
# Проверить размер очереди
curl http://localhost:9090/health | jq '.queue_size'

# Если queue_size растет → проблема с WS соединением
# Проверить интернет:
ping 8.8.8.8

# Проверить WS сервер:
curl https://your-ws-server.com
```

### Большое количество ошибок

```bash
# Проверить статистику
curl http://localhost:9090/health | jq '.stats'

# Если errors растет → смотреть логи:
sudo journalctl -u gateway-proxy | grep ERROR
```

---

## 📈 Metrics Reference

### Основные метрики:

| Метрика | Описание | Нормальное значение |
|---------|----------|---------------------|
| `uptime_seconds` | Время работы прокси | > 3600 (> 1 час) |
| `messages_received` | Всего получено сообщений | Растет |
| `messages_sent` | Всего отправлено ответов | ≈ messages_received |
| `errors` | Количество ошибок | < 5 в час |
| `reconnections` | Количество переподключений | < 10 в день |
| `queue_size` | Размер offline очереди | 0 (или < 5) |

### Аномалии:

| Симптом | Возможная причина | Действие |
|---------|-------------------|----------|
| `queue_size = 10` | WS отключен долго | Проверить интернет |
| `errors > 50` | Проблема с gateway | Проверить gateway |
| `messages_sent << messages_received` | Очередь переполняется | Проверить WS |
| `uptime_seconds < 300` часто | Прокси крашится | Проверить логи |

---

## 🚀 Quick Start

### 1. Проверить что всё работает:

```bash
# Запустить прокси
sudo systemctl start gateway-proxy

# Подождать 5 секунд

# Проверить health
curl http://localhost:9090/health | jq

# Ожидаемый результат:
{
  "status": "healthy",
  "ws_connected": true,
  ...
}
```

### 2. Настроить мониторинг:

```bash
# Создать скрипт проверки
sudo nano /usr/local/bin/check_proxy_health.sh

# Скопировать пример из раздела "Monitoring Best Practices"

# Сделать исполняемым
sudo chmod +x /usr/local/bin/check_proxy_health.sh

# Добавить в cron
crontab -e
# Добавить: * * * * * /usr/local/bin/check_proxy_health.sh
```

### 3. Протестировать offline queue:

```bash
# В одном терминале - запустить прокси
sudo systemctl start gateway-proxy

# Во втором терминале - симулировать обрыв
# (отключить интернет или перезапустить WS сервер)

# Отправить несколько сообщений через gateway

# Подключить интернет обратно

# Проверить логи - должны быть "Flushing queued messages"
sudo journalctl -u gateway-proxy -n 20
```

---

## ✅ Summary

**Phase 3 добавляет:**
- ✅ Offline Queue (10 сообщений) для краткосрочных обрывов
- ✅ Health Check endpoint для мониторинга
- ✅ Готовая база для централизованного мониторинга

**Production-ready features:**
- Отказоустойчивость при обрывах связи
- Visibility состояния без SSH
- Интеграция с мониторинг системами
