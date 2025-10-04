# 📦 Инструкция по установке Gateway Proxy на локальный компьютер

Пошаговое руководство для установки прокси-сервиса на компьютер с платежным шлюзом.

---

## 🎯 Что нужно

### На локальном компьютере должно быть:
- **OS**: Linux / Ubuntu (рекомендуется) или Windows
- **Python**: версия 3.11 или выше
- **Интернет**: стабильное соединение
- **Платежный шлюз**: запущен на `localhost:8080`

### Учетные данные (получаются через Telegram бота):
- Kiosk ID
- JWT Token
- WebSocket URL

---

## 📥 Шаг 1: Подготовка файлов

### Вариант А: Скачать через git (если есть)

```bash
cd /opt
sudo git clone https://your-repository.git
cd gateway_proxy
```

### Вариант Б: Скопировать файлы вручную

1. Создайте папку на локальном компьютере:
```bash
mkdir -p /opt/gateway_proxy
cd /opt/gateway_proxy
```

2. Скопируйте следующие файлы в эту папку:
   - `proxy.py`
   - `requirements.txt`
   - `.env.example`
   - `start_proxy.sh`
   - `README.md`

Можно использовать `scp`, USB флешку или другой способ передачи файлов.

### Вариант В: Скачать как ZIP

```bash
# Если файлы в ZIP архиве
unzip gateway_proxy.zip -d /opt/
cd /opt/gateway_proxy
```

---

## 🔧 Шаг 2: Установка зависимостей

### На Ubuntu/Debian:

```bash
# Обновите систему
sudo apt update

# Установите Python 3.11 (если нет)
sudo apt install python3.11 python3.11-venv python3-pip -y

# Проверьте версию
python3.11 --version
```

### На CentOS/RHEL:

```bash
sudo yum install python311 python311-pip -y
```

### На Windows:

1. Скачайте Python 3.11+ с [python.org](https://www.python.org/downloads/)
2. Установите с опцией "Add Python to PATH"
3. Проверьте: `python --version`

---

## ⚙️ Шаг 3: Настройка окружения

### 3.1 Создайте виртуальное окружение

```bash
cd /opt/gateway_proxy
python3 -m venv venv
```

### 3.2 Активируйте окружение

#### Linux:
```bash
source venv/bin/activate
```

#### Windows:
```powershell
venv\Scripts\activate
```

После активации в начале строки появится `(venv)`.

### 3.3 Установите Python зависимости

```bash
pip install -r requirements.txt
```

Должно установиться:
- `websockets` - для WebSocket соединения
- `aiohttp` - для HTTP запросов к локальному шлюзу
- `python-dotenv` - для загрузки конфигурации из .env

---

## 🔐 Шаг 4: Получение учетных данных

### 4.1 Откройте Telegram бота

Найдите вашего бота в Telegram (ссылка должна быть у администратора).

### 4.2 Создайте киоск

Отправьте команду:
```
/add_kiosk
```

### 4.3 Сохраните учетные данные

Бот выдаст:
```
✅ Kiosk created successfully!

Kiosk ID: KIOSK_001
Connection URL: wss://web-production-efee8.up.railway.app/ws
Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**⚠️ ВАЖНО:** Сохраните токен! Он показывается только один раз.

---

## 📝 Шаг 5: Конфигурация

### 5.1 Создайте файл конфигурации

```bash
cp .env.example .env
```

### 5.2 Отредактируйте .env

```bash
nano .env  # или vi .env, или любой редактор
```

### 5.3 Заполните параметры

```bash
# Вставьте данные из Telegram бота
CLOUD_WS_URL="wss://web-production-efee8.up.railway.app/ws/KIOSK_001"
CLOUD_WS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your_token_here"
KIOSK_ID="KIOSK_001"

# URL локального платежного шлюза (обычно не меняется)
LOCAL_GATEWAY_URL="http://localhost:8080"

# Уровень логирования (INFO для продакшена, DEBUG для отладки)
LOG_LEVEL="INFO"
```

Сохраните файл:
- `Ctrl+O`, `Enter`, `Ctrl+X` (в nano)
- `:wq` (в vi)

---

## 🚀 Шаг 6: Запуск

### Первый запуск (тестирование)

```bash
# Убедитесь что виртуальное окружение активно
source venv/bin/activate

# Запустите прокси
python3 proxy.py
```

Вы должны увидеть:
```
🚀 Payment Gateway Proxy starting...
   Kiosk ID: KIOSK_001
   Cloud URL: wss://...
   Local Gateway: http://localhost:8080
🔌 Connecting to cloud server...
✅ Connected to cloud server
📡 Connection status: connected
```

✅ **Если видите "Connected to cloud server" - всё работает!**

Нажмите `Ctrl+C` для остановки.

---

## 🔄 Шаг 7: Автозапуск (Production)

Для production окружения настройте автоматический запуск при загрузке системы.

### На Linux (systemd)

#### 7.1 Создайте service файл:

```bash
sudo nano /etc/systemd/system/gateway-proxy.service
```

#### 7.2 Вставьте содержимое:

```ini
[Unit]
Description=Payment Gateway Proxy
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/opt/gateway_proxy
Environment="PATH=/opt/gateway_proxy/venv/bin"
EnvironmentFile=/opt/gateway_proxy/.env
ExecStart=/opt/gateway_proxy/venv/bin/python3 /opt/gateway_proxy/proxy.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**⚠️ Замените:**
- `your_username` - на реального пользователя (не root!)
- Путь `/opt/gateway_proxy` - если установили в другое место

#### 7.3 Активируйте service:

```bash
# Перезагрузите конфигурацию systemd
sudo systemctl daemon-reload

# Включите автозапуск
sudo systemctl enable gateway-proxy

# Запустите сервис
sudo systemctl start gateway-proxy

# Проверьте статус
sudo systemctl status gateway-proxy
```

#### 7.4 Просмотр логов:

```bash
# В реальном времени
sudo journalctl -u gateway-proxy -f

# Последние 100 строк
sudo journalctl -u gateway-proxy -n 100

# За сегодня
sudo journalctl -u gateway-proxy --since today
```

#### 7.5 Управление сервисом:

```bash
# Остановить
sudo systemctl stop gateway-proxy

# Перезапустить
sudo systemctl restart gateway-proxy

# Отключить автозапуск
sudo systemctl disable gateway-proxy
```

---

## 🧪 Шаг 8: Тестирование

### 8.1 Проверьте подключение к облаку

Прокси должен быть запущен и подключен.

### 8.2 Отправьте тестовый платеж

1. Откройте Telegram бота
2. Отправьте: `/send_payment`
3. Выберите ваш киоск из списка
4. Введите сумму: `1000`

### 8.3 Проверьте логи прокси

#### Если запущен вручную:
Смотрите вывод в терминале

#### Если запущен как systemd service:
```bash
sudo journalctl -u gateway-proxy -f
```

### 8.4 Что должно быть в логах:

```
📥 Received from cloud: payment_request
💳 Processing payment request: REQ_ABC123
📨 Sending HTTP request to local gateway: Order #9999995, Amount: 150000
```

Если локальный шлюз еще не готов, будет ошибка:
```
❌ Error communicating with local gateway: Connection refused
```

Это нормально на этапе тестирования!

---

## 🔍 Шаг 9: Мониторинг

### 9.1 Проверка статуса сервиса:

```bash
sudo systemctl status gateway-proxy
```

Должно быть: `Active: active (running)`

### 9.2 Просмотр статистики:

Остановите прокси (`Ctrl+C` или `sudo systemctl stop gateway-proxy`), и он выведет статистику:

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

### 9.3 Логи находятся в:

1. Файл в директории прокси: `gateway_proxy_YYYYMMDD.log`
2. Systemd журнал: `sudo journalctl -u gateway-proxy`

---

## ❗ Устранение проблем

### Проблема: "Connection failed: HTTP 403"

**Причина**: Неверный токен или киоск не создан

**Решение**:
```bash
# 1. Создайте новый киоск в боте: /add_kiosk
# 2. Обновите .env с новым токеном
nano /opt/gateway_proxy/.env
# 3. Перезапустите
sudo systemctl restart gateway-proxy
```

### Проблема: "Error communicating with local gateway"

**Причина**: Локальный шлюз не запущен

**Решение**:
```bash
# Проверьте что шлюз работает
curl http://localhost:8080/health

# Проверьте процессы
ps aux | grep -i payment

# Проверьте логи шлюза
```

### Проблема: "ModuleNotFoundError: No module named 'websockets'"

**Причина**: Зависимости не установлены

**Решение**:
```bash
cd /opt/gateway_proxy
source venv/bin/activate
pip install -r requirements.txt
```

### Проблема: Прокси не стартует автоматически

**Решение**:
```bash
# Проверьте статус
sudo systemctl status gateway-proxy

# Проверьте права на файлы
ls -la /opt/gateway_proxy/

# Проверьте логи
sudo journalctl -u gateway-proxy -n 50

# Проверьте что пользователь в service файле существует
cat /etc/systemd/system/gateway-proxy.service
```

---

## 📋 Checklist установки

- [ ] Python 3.11+ установлен
- [ ] Файлы прокси скопированы
- [ ] Виртуальное окружение создано
- [ ] Зависимости установлены
- [ ] Киоск создан через Telegram бота
- [ ] Файл .env настроен с токеном
- [ ] Прокси запускается и подключается к облаку
- [ ] Systemd service настроен (для production)
- [ ] Тестовый платеж проходит

---

## 🎓 Дополнительные материалы

- **QUICK_START.md** - быстрый старт за 5 минут
- **README.md** - полная документация по функциям
- **Telegram бот** - для управления киосками и тестирования

---

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `sudo journalctl -u gateway-proxy -n 100`
2. Проверьте конфигурацию: `cat /opt/gateway_proxy/.env`
3. Проверьте статус: `sudo systemctl status gateway-proxy`
4. Создайте новый киоск если токен истек (срок действия 30 дней)

---

## ✅ Готово!

После успешной установки прокси будет:
- ✅ Автоматически запускаться при загрузке системы
- ✅ Подключаться к облачному серверу
- ✅ Переадресовывать платежные запросы на локальный шлюз
- ✅ Автоматически переподключаться при обрыве связи
- ✅ Вести подробные логи всех операций
