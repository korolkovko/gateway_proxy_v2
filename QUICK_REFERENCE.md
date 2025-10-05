# Gateway Proxy - Quick Reference

Шпаргалка для быстрого доступа к командам.

---

## 🚀 Быстрая установка

```bash
# 1. Перенести проект на сервер
cd /opt
git clone https://github.com/korolkovko/gateway_proxy_v2.git
cd gateway_proxy_v2

# 2. Установить зависимости
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Настроить .env
cp .env.example .env
nano .env  # Заполнить WS_SERVER_URL и WS_TOKEN

# 4. Настроить routing
nano routing_config.yaml  # Проверить URLs gateway

# 5. Установить systemd service
sudo ./install_service.sh

# 6. Запустить
sudo systemctl start gateway-proxy
```

---

## 📋 Управление сервисом

```bash
# Запуск/остановка
sudo systemctl start gateway-proxy
sudo systemctl stop gateway-proxy
sudo systemctl restart gateway-proxy

# Статус
sudo systemctl status gateway-proxy

# Автозапуск
sudo systemctl enable gateway-proxy   # Включить
sudo systemctl disable gateway-proxy  # Выключить

# Логи
sudo journalctl -u gateway-proxy -f         # Реальное время
sudo journalctl -u gateway-proxy -n 100     # Последние 100 строк
sudo journalctl -u gateway-proxy --since "1 hour ago"
```

---

## 🔍 Мониторинг

```bash
# Health check
curl http://localhost:9090/health | jq

# Только статус
curl -s http://localhost:9090/health | jq -r '.status'

# Файловые логи
tail -f proxy_$(date +%Y%m%d).log

# Проверить очередь
curl -s http://localhost:9090/health | jq '.queue_size'
```

---

## 🔄 Обновление

```bash
cd /opt/gateway_proxy_v2
sudo systemctl stop gateway-proxy
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl start gateway-proxy
sudo systemctl status gateway-proxy
```

---

## ⚙️ Конфигурация

### .env файл
```bash
nano /opt/gateway_proxy_v2/.env
# Изменить → Рестарт сервиса
sudo systemctl restart gateway-proxy
```

### routing_config.yaml
```bash
nano /opt/gateway_proxy_v2/routing_config.yaml
# Изменить → Рестарт сервиса
sudo systemctl restart gateway-proxy
```

### Уровни логирования
- `DEBUG` - Полные JSON payloads (для отладки)
- `INFO` - Краткие сводки (production)
- `WARNING` - Только предупреждения
- `ERROR` - Только ошибки

---

## 🐛 Диагностика

```bash
# Статус сервиса
sudo systemctl status gateway-proxy

# Ошибки подключения
sudo journalctl -u gateway-proxy | grep "Connection failed"

# Ошибки gateway
sudo journalctl -u gateway-proxy | grep "Gateway error"

# Проверка WS сервера
curl -I https://your-server.railway.app

# Проверка gateway
curl http://127.0.0.1:8011/health

# Проверка портов
sudo netstat -tulpn | grep 9090
```

---

## 📊 Статистика

```bash
# Health endpoint
curl http://localhost:9090/health | jq '.stats'

# Journalctl статистика
sudo journalctl -u gateway-proxy | grep "Hourly Statistics" | tail -1

# Файловые логи
grep "📊 Final Statistics" proxy_*.log | tail -1
```

---

## 🔒 Безопасность

```bash
# Права на .env
chmod 600 /opt/gateway_proxy_v2/.env

# Владелец файлов
sudo chown -R $USER:$USER /opt/gateway_proxy_v2/

# Проверка
ls -la /opt/gateway_proxy_v2/.env
```

---

## 📦 Backup

```bash
# Создать backup
tar -czf gateway-proxy-backup-$(date +%Y%m%d).tar.gz \
  /opt/gateway_proxy_v2/.env \
  /opt/gateway_proxy_v2/routing_config.yaml \
  /etc/systemd/system/gateway-proxy.service

# Восстановить
tar -xzf gateway-proxy-backup-20251005.tar.gz
sudo cp opt/gateway_proxy_v2/.env /opt/gateway_proxy_v2/
sudo systemctl restart gateway-proxy
```

---

## 🆘 Частые проблемы

### Сервис не запускается
```bash
sudo journalctl -u gateway-proxy -n 50
cat /opt/gateway_proxy_v2/.env
ls -la /opt/gateway_proxy_v2/venv/bin/python
```

### WS не подключается
```bash
ping 8.8.8.8
curl -I https://your-server.railway.app
cat /opt/gateway_proxy_v2/.env | grep WS_
```

### Health endpoint не отвечает
```bash
sudo systemctl status gateway-proxy
sudo netstat -tulpn | grep 9090
curl http://localhost:9090/health
```

### Очередь переполняется
```bash
curl -s http://localhost:9090/health | jq '.queue_size'
sudo journalctl -u gateway-proxy | grep "Queue full"
# Проблема с WS - проверить соединение
```

---

## 📚 Документация

- **[LINUX_INSTALL_GUIDE.md](LINUX_INSTALL_GUIDE.md)** - Полная инструкция установки
- **[SYSTEMD_SETUP.md](SYSTEMD_SETUP.md)** - Работа с systemd
- **[PHASE3_FEATURES.md](PHASE3_FEATURES.md)** - Health check и offline queue
- **[MIGRATION_PING_PONG.md](MIGRATION_PING_PONG.md)** - Миграция ping/pong
- **[README.md](README.md)** - Общая информация

---

## ✅ Проверка после установки

```bash
# 1. Сервис запущен
sudo systemctl is-active gateway-proxy  # → active

# 2. WS подключен
curl -s http://localhost:9090/health | jq -r '.ws_connected'  # → true

# 3. Автозапуск включен
sudo systemctl is-enabled gateway-proxy  # → enabled

# 4. Логи пишутся
tail -5 proxy_$(date +%Y%m%d).log

# 5. Health работает
curl http://localhost:9090/health | jq -r '.status'  # → healthy
```

---

## 🎯 Production чек-лист

- [ ] .env настроен (WS_SERVER_URL, WS_TOKEN)
- [ ] routing_config.yaml настроен (URLs gateway)
- [ ] Сервис запущен и в статусе active
- [ ] WS подключен (ws_connected = true)
- [ ] Автозапуск включен (enabled)
- [ ] Health endpoint отвечает
- [ ] Логи пишутся
- [ ] Мониторинг настроен (cron check)
- [ ] Backup конфигурации сделан

---

**Всё готово! 🚀**
