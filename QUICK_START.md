# 🚀 Быстрый старт Gateway Proxy

## За 5 минут

### 1️⃣ Получите учетные данные (Telegram бот)

```
/add_kiosk
```

Сохраните:
- Kiosk ID (например: `KIOSK_001`)
- JWT Token (длинная строка)
- WebSocket URL

### 2️⃣ Настройте конфигурацию

```bash
cd gateway_proxy
cp .env.example .env
nano .env  # или используйте любой редактор
```

Заполните в `.env`:
```bash
CLOUD_WS_URL="wss://web-production-efee8.up.railway.app/ws/KIOSK_001"
CLOUD_WS_TOKEN="ваш_токен_из_бота"
KIOSK_ID="KIOSK_001"
LOCAL_GATEWAY_URL="http://localhost:8080"
LOG_LEVEL="INFO"
```

### 3️⃣ Запустите

#### Linux/macOS:
```bash
./start_proxy.sh
```

#### Windows:
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
set /p < .env  # загрузить переменные
python proxy.py
```

### 4️⃣ Проверьте

Вы должны увидеть:
```
🚀 Payment Gateway Proxy starting...
🔌 Connecting to cloud server...
✅ Connected to cloud server
```

## ✅ Готово!

Теперь прокси:
- ✅ Подключен к облачному серверу
- ✅ Ждет платежные запросы
- ✅ Автоматически переподключается при обрыве

---

## 🧪 Тестирование

### Отправьте тестовый платеж:

1. В Telegram боте: `/send_payment`
2. Выберите ваш киоск
3. Введите сумму: `1000`

### Проверьте логи:

```bash
tail -f gateway_proxy_$(date +%Y%m%d).log
```

Должны увидеть:
```
📥 Received from cloud: payment_request
💳 Processing payment request: REQ_...
📨 Sending HTTP request to local gateway...
```

---

## ⚠️ Важно!

**Перед тестированием убедитесь:**
- ✅ Платежный шлюз запущен на `localhost:8080`
- ✅ Есть интернет-соединение
- ✅ Токен не истек (действителен 30 дней)

**Если платежный шлюз не готов:**
Прокси все равно подключится к облаку, но будет выдавать ошибки при попытке отправить запрос к шлюзу. Это нормально для тестирования!

---

## 📞 Проблемы?

### Не подключается к облаку:
```bash
# Проверьте токен и URL в .env
cat .env

# Создайте новый киоск если токен истек
# В Telegram боте: /add_kiosk
```

### Ошибка подключения к локальному шлюзу:
```bash
# Проверьте что шлюз работает
curl http://localhost:8080/health

# Если порт другой, измените LOCAL_GATEWAY_URL в .env
```

### Нужна помощь:
Смотрите полную документацию в `README.md`
