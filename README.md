# Payment Gateway Proxy

Прокси-сервис для связи локального платежного шлюза с облачным сервером через WebSocket.

## 📋 Назначение

Этот сервис устанавливается на локальный компьютер рядом с платежным шлюзом и выполняет следующие функции:

1. **Подключается к облачному серверу** через WebSocket
2. **Получает запросы на оплату** от облачного сервера
3. **Преобразует WebSocket сообщения** в HTTP запросы к локальному шлюзу
4. **Отправляет ответы** обратно на облачный сервер
5. **Автоматически переподключается** при обрыве связи

## 🏗️ Архитектура

```
┌─────────────────┐                    ┌──────────────────┐                    ┌─────────────────┐
│  Cloud Server   │◄──── WebSocket ───►│  Proxy Service   │◄───── HTTP ───────►│ Payment Gateway │
│   (Railway)     │                    │  (This service)  │                    │  (localhost)    │
└─────────────────┘                    └──────────────────┘                    └─────────────────┘
   wss://...                              gateway_proxy/                         http://localhost:8080
```

## 📦 Требования

- **OS**: Linux / macOS / Windows
- **Python**: 3.11 или выше
- **Интернет**: Стабильное соединение с облачным сервером
- **Локальный шлюз**: Запущенный платежный шлюз на `localhost:8080`

## 🚀 Установка

### 1. Скачайте файлы

Скопируйте всю папку `gateway_proxy/` на локальный компьютер с платежным шлюзом.

### 2. Создайте файл конфигурации

```bash
cd gateway_proxy
cp .env.example .env
```

### 3. Отредактируйте `.env`

Откройте `.env` в текстовом редакторе и заполните:

```bash
# Получите через Telegram бота: /add_kiosk
CLOUD_WS_URL="wss://web-production-efee8.up.railway.app/ws/KIOSK_001"
CLOUD_WS_TOKEN="your_jwt_token_from_bot"
KIOSK_ID="KIOSK_001"

# URL локального платежного шлюза (обычно не нужно менять)
LOCAL_GATEWAY_URL="http://localhost:8080"

# Уровень логирования (DEBUG для отладки, INFO для продакшена)
LOG_LEVEL="INFO"
```

### 4. Установите зависимости

#### На Linux/macOS:

```bash
# Используйте готовый скрипт
./start_proxy.sh
```

#### Или вручную:

```bash
# Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

#### На Windows:

```powershell
# Создайте виртуальное окружение
python -m venv venv
venv\Scripts\activate

# Установите зависимости
pip install -r requirements.txt
```

## ▶️ Запуск

### Вариант 1: Через скрипт (Linux/macOS)

```bash
./start_proxy.sh
```

### Вариант 2: Вручную

```bash
# Активируйте окружение
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate  # Windows

# Загрузите переменные окружения
export $(cat .env | grep -v '^#' | xargs)  # Linux/macOS
# или вручную установите переменные на Windows

# Запустите прокси
python3 proxy.py
```

## 📊 Что вы увидите при запуске

```
🚀 Payment Gateway Proxy starting...
   Kiosk ID: KIOSK_001
   Cloud URL: wss://web-production-efee8.up.railway.app/ws/KIOSK_001
   Local Gateway: http://localhost:8080
🔌 Connecting to cloud server...
✅ Connected to cloud server
📡 Connection status: connected
```

## 🔄 Обработка платежей

### Поток данных:

1. **Облачный сервер → Прокси** (WebSocket):
```json
{
  "type": "payment_request",
  "data": {
    "request_id": "REQ_ABC123",
    "kiosk_id": "KIOSK_001",
    "order_id": 9999995,
    "sum": 150000
  }
}
```

2. **Прокси → Локальный шлюз** (HTTP POST):
```json
POST http://localhost:8080/payment
{
  "kiosk_id": "kiosk_001",
  "order_id": 9999995,
  "sum": 150000
}
```

3. **Локальный шлюз → Прокси** (HTTP Response):
```json
{
  "status": "success",
  "sum": 150000,
  "currency": "RUB",
  "payment_method": "card",
  ...
}
```

4. **Прокси → Облачный сервер** (WebSocket):
```json
{
  "type": "payment_response",
  "data": {
    "request_id": "REQ_ABC123",
    "status": "SUCCESS",
    "sum": 150000,
    "currency": "RUB",
    "payment_method": "card",
    "timestamp": "2025-10-01T12:00:00Z",
    "payment_data": { ... }
  }
}
```

## 📝 Логирование

Прокси создает лог-файлы с именем `gateway_proxy_YYYYMMDD.log` в текущей директории.

### Просмотр логов в реальном времени:

```bash
tail -f gateway_proxy_$(date +%Y%m%d).log
```

### Уровни логирования:

- **DEBUG**: Все сообщения, включая детали запросов/ответов
- **INFO**: Основные события (подключение, платежи)
- **WARNING**: Предупреждения и переподключения
- **ERROR**: Ошибки

## 🔧 Устранение проблем

### ❌ Ошибка: "CLOUD_WS_URL not set"

**Проблема**: Не настроены переменные окружения

**Решение**:
```bash
# Проверьте файл .env
cat .env

# Убедитесь что все переменные заполнены
# Загрузите переменные:
export $(cat .env | grep -v '^#' | xargs)
```

### ❌ Ошибка: "Connection failed: HTTP 403"

**Проблема**: Неверный токен или киоск не создан

**Решение**:
1. Создайте новый киоск в Telegram боте: `/add_kiosk`
2. Обновите `CLOUD_WS_TOKEN` и `CLOUD_WS_URL` в `.env`
3. Перезапустите прокси

### ❌ Ошибка: "Error communicating with local gateway"

**Проблема**: Локальный платежный шлюз не запущен или недоступен

**Решение**:
1. Убедитесь, что платежный шлюз запущен:
```bash
curl http://localhost:8080/health
```

2. Проверьте порт в `.env` (`LOCAL_GATEWAY_URL`)

3. Если платежный шлюз на другом порту, измените URL:
```bash
LOCAL_GATEWAY_URL="http://localhost:8010"
```

### ❌ Ошибка: "Connection lost. Reconnecting..."

**Проблема**: Потеряна связь с облачным сервером

**Решение**: Прокси автоматически переподключится через 5 секунд. Если проблема повторяется:
1. Проверьте интернет-соединение
2. Проверьте, что облачный сервер доступен
3. Проверьте логи на наличие ошибок авторизации

## 📊 Статистика

При остановке (Ctrl+C) прокси выводит статистику:

```
==================================================
📊 Proxy Statistics:
   Messages received: 145
   Messages sent: 143
   HTTP requests: 72
   HTTP errors: 2
   Reconnections: 1
==================================================
```

## 🛑 Остановка

Нажмите **Ctrl+C** для graceful shutdown

## 🔄 Автозапуск (Linux)

Для автоматического запуска при загрузке системы создайте systemd service:

### 1. Создайте файл service:

```bash
sudo nano /etc/systemd/system/gateway-proxy.service
```

### 2. Добавьте содержимое:

```ini
[Unit]
Description=Payment Gateway Proxy
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/gateway_proxy
ExecStart=/path/to/gateway_proxy/start_proxy.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Активируйте:

```bash
sudo systemctl daemon-reload
sudo systemctl enable gateway-proxy
sudo systemctl start gateway-proxy

# Проверка статуса
sudo systemctl status gateway-proxy

# Просмотр логов
sudo journalctl -u gateway-proxy -f
```

## 🧪 Тестирование

### Тест 1: Проверка подключения к облаку

```bash
# Запустите прокси
./start_proxy.sh

# В логах должно быть:
# ✅ Connected to cloud server
```

### Тест 2: Отправка тестового платежа

1. В Telegram боте: `/send_payment`
2. Выберите ваш киоск
3. Введите сумму: `1000`
4. Проверьте логи прокси - должно быть:
```
📥 Received from cloud: payment_request
💳 Processing payment request: REQ_...
📨 Sending HTTP request to local gateway: Order #..., Amount: 100000
```

### Тест 3: Проверка работы без локального шлюза

Если локальный шлюз еще не готов, прокси все равно подключится к облаку и будет логировать ошибки при попытке отправить запрос к шлюзу.

## 📞 Поддержка

При проблемах проверьте:
1. Логи прокси: `tail -f gateway_proxy_*.log`
2. Статус локального шлюза: `curl http://localhost:8080/health`
3. Переменные окружения: `cat .env`

## 🔐 Безопасность

- **Не публикуйте** файл `.env` с токенами
- **Храните токены** в безопасном месте
- **Токены истекают** через 30 дней - создайте новый киоск при необходимости
- Прокси работает **только локально** и не открывает внешние порты

## 📁 Структура файлов

```
gateway_proxy/
├── proxy.py              # Основной код прокси
├── requirements.txt      # Python зависимости
├── .env.example         # Пример конфигурации
├── .env                 # Ваша конфигурация (НЕ КОМИТИТЬ!)
├── start_proxy.sh       # Скрипт запуска (Linux/macOS)
├── README.md            # Эта документация
└── gateway_proxy_*.log  # Логи (создаются автоматически)
```

## ✅ Готово!

Прокси настроен и готов к работе!
