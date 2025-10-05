# Установка Gateway Proxy на Linux сервер

Пошаговая инструкция установки и настройки на production сервере (киоске).

---

## 📋 Требования

### Система:
- **OS:** Ubuntu 20.04+ / Debian 11+ / CentOS 8+ / любой Linux с systemd
- **Python:** 3.9 или выше
- **Права:** sudo доступ
- **Сеть:** доступ в интернет

### Проверка версии Python:

```bash
python3 --version
# Должно быть: Python 3.9.x или выше
```

Если Python старый или отсутствует:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip -y

# CentOS/RHEL
sudo yum install python39 python39-pip -y
```

---

## 🚀 Установка (пошагово)

### Шаг 1: Перенос проекта на сервер

**Вариант А: Через SCP (если файлы у тебя локально)**

```bash
# С твоего компьютера
scp -r /Users/korolkovnikolai/gateway_proxy_v2 user@kiosk-server:/home/user/

# Подключиться к серверу
ssh user@kiosk-server
```

**Вариант Б: Через Git (рекомендуется)**

```bash
# На сервере
cd /opt
sudo git clone https://github.com/korolkovko/gateway_proxy_v2.git
sudo chown -R $USER:$USER gateway_proxy_v2
cd gateway_proxy_v2
```

**Вариант В: Через rsync**

```bash
# С твоего компьютера
rsync -avz /Users/korolkovnikolai/gateway_proxy_v2/ user@kiosk-server:/opt/gateway_proxy_v2/
```

---

### Шаг 2: Установка зависимостей

```bash
# Перейти в папку проекта
cd /opt/gateway_proxy_v2

# Создать виртуальное окружение
python3 -m venv venv

# Активировать
source venv/bin/activate

# Установить зависимости
pip install --upgrade pip
pip install -r requirements.txt

# Проверить что всё установилось
pip list
```

**Ожидаемый результат:**
```
Package         Version
--------------- -------
aiohttp         3.9.0
python-dotenv   1.0.0
PyYAML          6.0
textual         0.47.0
websockets      12.0
```

---

### Шаг 3: Создать .env файл

```bash
# Скопировать пример
cp .env.example .env

# Отредактировать
nano .env
```

**Содержимое .env:**

```bash
# WebSocket сервер (ОБЯЗАТЕЛЬНО)
WS_SERVER_URL="wss://your-server.railway.app/ws"

# Токен авторизации (ОБЯЗАТЕЛЬНО)
WS_TOKEN="your_jwt_token_here"

# Путь к конфигу роутинга (опционально, default: routing_config.yaml)
ROUTING_CONFIG_PATH="routing_config.yaml"

# Уровень логирования (опционально, default: INFO)
# Варианты: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL="INFO"

# ID киоска (опционально, для идентификации)
KIOSK_ID="kiosk-001"
```

**Сохранить:** `Ctrl+O`, `Enter`, `Ctrl+X`

**Проверить:**
```bash
cat .env
```

---

### Шаг 4: Настроить routing_config.yaml

```bash
nano routing_config.yaml
```

**Пример конфигурации:**

```yaml
# Роуты для разных типов операций
routes:
  payment:
    url: "http://127.0.0.1:8011/api/v1/dcpayment/payment"
    timeout: 35

  fiscal:
    url: "http://127.0.0.1:8012/api/v1/fiscal/print"
    timeout: 35

  kds:
    url: "http://127.0.0.1:8013/api/v1/kds/send"
    timeout: 35

  print:
    url: "http://127.0.0.1:8014/api/v1/printer/print"
    timeout: 35

# Дефолтный роут (если operation_type не найден)
default:
  url: "http://127.0.0.1:8000/api/v1/default"
  timeout: 35
```

**Важно:** Убедись что URLs указывают на правильные gateway на киоске!

**Проверить:**
```bash
cat routing_config.yaml
```

---

### Шаг 5: Тестовый запуск (вручную)

Перед установкой как systemd service, проверим что всё работает:

```bash
# Активировать venv (если не активирован)
source venv/bin/activate

# Запустить прокси
python3 proxy.py
```

**Ожидаемый вывод:**
```
2025-10-05 10:30:00 - INFO - 🚀 Payment Gateway Proxy starting...
2025-10-05 10:30:00 - INFO -    WS Server: wss://your-server.railway.app/ws
2025-10-05 10:30:00 - INFO -    Routing config loaded with 4 routes
2025-10-05 10:30:00 - INFO - 🏥 Health check server started on http://localhost:9090/health
2025-10-05 10:30:01 - INFO - Connecting to WS server: wss://your-server.railway.app/ws
2025-10-05 10:30:02 - INFO - ✅ Connected to cloud server
```

**Проверить health endpoint** (в другом терминале):
```bash
curl http://localhost:9090/health | jq
```

**Ожидаемый ответ:**
```json
{
  "status": "healthy",
  "ws_connected": true,
  "uptime_seconds": 5.2,
  "stats": {
    "messages_received": 0,
    "messages_sent": 0,
    "errors": 0,
    "reconnections": 0
  },
  "queue_size": 0,
  "routes_configured": 4
}
```

**Остановить прокси:** `Ctrl+C`

---

### Шаг 6: Установить как systemd service

```bash
# Убедись что находишься в папке проекта
cd /opt/gateway_proxy_v2

# Запустить скрипт установки
sudo ./install_service.sh
```

**Вывод скрипта:**
```
🚀 Installing Gateway Proxy as systemd service...
📂 Installation directory: /opt/gateway_proxy_v2
📋 Copying service file to /etc/systemd/system...
🔧 Updating paths in service file...
👤 Setting service user to: youruser
🔄 Reloading systemd daemon...
✅ Enabling service for autostart...
Created symlink /etc/systemd/system/multi-user.target.wants/gateway-proxy.service → /etc/systemd/system/gateway-proxy.service.

✅ Installation complete!

📚 Available commands:
  sudo systemctl start gateway-proxy      # Start the service
  sudo systemctl stop gateway-proxy       # Stop the service
  sudo systemctl restart gateway-proxy    # Restart the service
  sudo systemctl status gateway-proxy     # Check status
  sudo journalctl -u gateway-proxy -f     # View logs (real-time)

🎯 To start now, run:
  sudo systemctl start gateway-proxy
```

---

### Шаг 7: Запустить сервис

```bash
# Запустить
sudo systemctl start gateway-proxy

# Проверить статус
sudo systemctl status gateway-proxy
```

**Ожидаемый вывод:**
```
● gateway-proxy.service - Payment Gateway WebSocket Proxy Client
   Loaded: loaded (/etc/systemd/system/gateway-proxy.service; enabled; vendor preset: enabled)
   Active: active (running) since Sat 2025-10-05 10:35:00 UTC; 5s ago
 Main PID: 12345 (python)
    Tasks: 3
   Memory: 25.6M
   CGroup: /system.slice/gateway-proxy.service
           └─12345 /opt/gateway_proxy_v2/venv/bin/python /opt/gateway_proxy_v2/proxy.py

Oct 05 10:35:00 kiosk systemd[1]: Started Payment Gateway WebSocket Proxy Client.
Oct 05 10:35:00 kiosk python[12345]: 2025-10-05 10:35:00 - INFO - 🚀 Payment Gateway Proxy starting...
Oct 05 10:35:00 kiosk python[12345]: 2025-10-05 10:35:00 - INFO - ✅ Connected to cloud server
```

**Проверить health:**
```bash
curl http://localhost:9090/health | jq '.status'
# Ответ: "healthy"
```

---

## ✅ Проверка установки

### 1. Проверить что сервис запущен

```bash
sudo systemctl status gateway-proxy
```

Должно быть: `Active: active (running)`

### 2. Проверить логи

```bash
# Последние 50 строк
sudo journalctl -u gateway-proxy -n 50

# В реальном времени
sudo journalctl -u gateway-proxy -f
```

### 3. Проверить health endpoint

```bash
curl http://localhost:9090/health | jq
```

### 4. Проверить файловые логи

```bash
ls -lh proxy_*.log
tail -f proxy_$(date +%Y%m%d).log
```

### 5. Проверить автозапуск

```bash
# Перезагрузить сервер
sudo reboot

# После перезагрузки - проверить что сервис запустился
sudo systemctl status gateway-proxy
# Должен быть: Active: active (running)
```

---

## 🔧 Управление сервисом

### Основные команды:

```bash
# Запустить
sudo systemctl start gateway-proxy

# Остановить
sudo systemctl stop gateway-proxy

# Перезапустить
sudo systemctl restart gateway-proxy

# Статус
sudo systemctl status gateway-proxy

# Включить автозапуск
sudo systemctl enable gateway-proxy

# Выключить автозапуск
sudo systemctl disable gateway-proxy

# Логи
sudo journalctl -u gateway-proxy -f
```

---

## 📝 Обновление кода

Когда есть новая версия кода:

```bash
# 1. Перейти в папку проекта
cd /opt/gateway_proxy_v2

# 2. Остановить сервис
sudo systemctl stop gateway-proxy

# 3. Обновить код
git pull origin main
# или скопировать новые файлы через scp/rsync

# 4. Обновить зависимости (если requirements.txt изменился)
source venv/bin/activate
pip install -r requirements.txt

# 5. Запустить снова
sudo systemctl start gateway-proxy

# 6. Проверить
sudo systemctl status gateway-proxy
curl http://localhost:9090/health | jq '.status'
```

**Или одной командой:**
```bash
cd /opt/gateway_proxy_v2 && \
sudo systemctl stop gateway-proxy && \
git pull && \
source venv/bin/activate && \
pip install -r requirements.txt && \
sudo systemctl start gateway-proxy && \
sleep 2 && \
sudo systemctl status gateway-proxy
```

---

## 📊 Настройка мониторинга

### 1. Создать скрипт проверки health

```bash
sudo nano /usr/local/bin/check_proxy_health.sh
```

**Содержимое:**

```bash
#!/bin/bash

RESPONSE=$(curl -s http://localhost:9090/health)
STATUS=$(echo $RESPONSE | jq -r '.status')

if [ "$STATUS" != "healthy" ]; then
    echo "$(date): ⚠️ Proxy is $STATUS" >> /var/log/proxy_alerts.log
    # Опционально: отправить уведомление
    # curl -X POST https://slack.com/webhook -d "{\"text\":\"Proxy $STATUS\"}"
    exit 1
fi

echo "$(date): ✅ Proxy is healthy" >> /var/log/proxy_health.log
exit 0
```

**Сделать исполняемым:**
```bash
sudo chmod +x /usr/local/bin/check_proxy_health.sh
```

### 2. Добавить в cron (каждую минуту)

```bash
crontab -e
```

**Добавить строку:**
```
* * * * * /usr/local/bin/check_proxy_health.sh
```

**Проверить что работает:**
```bash
# Подождать минуту
sleep 60

# Проверить логи
tail /var/log/proxy_health.log
```

---

## 🐛 Troubleshooting

### Проблема 1: Сервис не запускается

```bash
# Проверить статус
sudo systemctl status gateway-proxy

# Посмотреть детальные логи
sudo journalctl -u gateway-proxy -n 100

# Проверить .env файл
cat /opt/gateway_proxy_v2/.env

# Проверить права на файлы
ls -la /opt/gateway_proxy_v2/

# Проверить что venv существует
ls -la /opt/gateway_proxy_v2/venv/bin/python
```

### Проблема 2: WebSocket не подключается

```bash
# Проверить интернет
ping 8.8.8.8

# Проверить доступность WS сервера
curl -I https://your-server.railway.app

# Проверить токен в .env
cat .env | grep WS_TOKEN

# Посмотреть ошибки подключения в логах
sudo journalctl -u gateway-proxy | grep "Connection failed"
```

### Проблема 3: Health endpoint не отвечает

```bash
# Проверить что прокси запущен
sudo systemctl status gateway-proxy

# Проверить что порт 9090 слушается
sudo netstat -tulpn | grep 9090
# или
sudo ss -tulpn | grep 9090

# Проверить firewall
sudo ufw status
# Если порт закрыт - открыть (только для localhost это не нужно)
```

### Проблема 4: Gateway не доступен

```bash
# Проверить что gateway запущен
curl http://127.0.0.1:8011/health
# (или другой порт из routing_config.yaml)

# Проверить routing_config.yaml
cat /opt/gateway_proxy_v2/routing_config.yaml

# Посмотреть ошибки gateway в логах прокси
sudo journalctl -u gateway-proxy | grep "Gateway error"
```

### Проблема 5: Логи переполняют диск

```bash
# Проверить размер логов
du -h /opt/gateway_proxy_v2/proxy_*.log

# Ротация работает автоматически (10MB max)
# Но можно вручную почистить старые:
cd /opt/gateway_proxy_v2
ls -lht proxy_*.log
rm proxy_20251001.log  # Удалить старые
```

---

## 🔒 Безопасность

### 1. Права доступа

```bash
# Проверить владельца файлов
ls -la /opt/gateway_proxy_v2/

# Должен быть твой пользователь, не root
# Если нет - исправить:
sudo chown -R youruser:youruser /opt/gateway_proxy_v2/
```

### 2. .env файл (секреты)

```bash
# Убедиться что .env не читается другими
chmod 600 /opt/gateway_proxy_v2/.env
ls -la .env
# Должно быть: -rw------- (только владелец читает/пишет)
```

### 3. Firewall

```bash
# Health endpoint на localhost - внешний доступ не нужен
# Но если нужен - открыть порт:
sudo ufw allow 9090/tcp

# Проверить
sudo ufw status
```

---

## 📈 Оптимизация производительности

### 1. Уровень логирования на production

```bash
nano /opt/gateway_proxy_v2/.env

# Изменить на INFO (не DEBUG)
LOG_LEVEL="INFO"

# Перезапустить
sudo systemctl restart gateway-proxy
```

### 2. Ограничить размер логов journald

```bash
sudo nano /etc/systemd/journald.conf

# Раскомментировать и установить:
SystemMaxUse=500M
SystemMaxFileSize=100M

# Перезапустить journald
sudo systemctl restart systemd-journald
```

### 3. Проверить ресурсы

```bash
# CPU и память
systemctl status gateway-proxy

# Детальная статистика
systemd-cgtop | grep gateway-proxy
```

---

## 📦 Backup и восстановление

### Backup конфигурации

```bash
# Создать backup
tar -czf gateway-proxy-backup-$(date +%Y%m%d).tar.gz \
  /opt/gateway_proxy_v2/.env \
  /opt/gateway_proxy_v2/routing_config.yaml \
  /etc/systemd/system/gateway-proxy.service

# Скопировать на другой сервер
scp gateway-proxy-backup-*.tar.gz backup-server:/backups/
```

### Восстановление

```bash
# Распаковать backup
tar -xzf gateway-proxy-backup-20251005.tar.gz

# Восстановить файлы
sudo cp opt/gateway_proxy_v2/.env /opt/gateway_proxy_v2/
sudo cp opt/gateway_proxy_v2/routing_config.yaml /opt/gateway_proxy_v2/
sudo cp etc/systemd/system/gateway-proxy.service /etc/systemd/system/

# Перезапустить
sudo systemctl daemon-reload
sudo systemctl restart gateway-proxy
```

---

## ✅ Финальный чек-лист

После установки проверь:

- [ ] Сервис запущен: `sudo systemctl status gateway-proxy`
- [ ] WS подключен: `curl http://localhost:9090/health | jq '.ws_connected'` = `true`
- [ ] Логи пишутся: `tail -f proxy_$(date +%Y%m%d).log`
- [ ] Автозапуск включен: `sudo systemctl is-enabled gateway-proxy` = `enabled`
- [ ] Health endpoint работает: `curl http://localhost:9090/health`
- [ ] Мониторинг настроен: `crontab -l | grep check_proxy`
- [ ] Gateway доступны: `curl http://127.0.0.1:8011/health`

---

## 🆘 Поддержка

Если возникли проблемы:

1. **Собрать диагностику:**
   ```bash
   echo "=== System Info ===" > diagnostic.log
   uname -a >> diagnostic.log
   python3 --version >> diagnostic.log

   echo "=== Service Status ===" >> diagnostic.log
   sudo systemctl status gateway-proxy >> diagnostic.log

   echo "=== Logs (last 100) ===" >> diagnostic.log
   sudo journalctl -u gateway-proxy -n 100 >> diagnostic.log

   echo "=== Health Check ===" >> diagnostic.log
   curl -s http://localhost:9090/health >> diagnostic.log

   echo "=== Config ===" >> diagnostic.log
   cat /opt/gateway_proxy_v2/routing_config.yaml >> diagnostic.log
   ```

2. **Отправить diagnostic.log** команде поддержки

3. **Проверить документацию:**
   - [SYSTEMD_SETUP.md](SYSTEMD_SETUP.md) - Управление systemd
   - [PHASE3_FEATURES.md](PHASE3_FEATURES.md) - Health check и мониторинг
   - [README.md](README.md) - Общая информация

---

## 🎯 Готово!

Теперь прокси:
- ✅ Запущен как systemd service
- ✅ Автоматически стартует при загрузке
- ✅ Перезапускается при падении
- ✅ Логирует в journald и файлы
- ✅ Доступен через health endpoint
- ✅ Мониторится автоматически

**Production ready!** 🚀
