# systemd Service Setup

## Что это?

**systemd** - это менеджер процессов в Linux, который:
- ✅ Автоматически запускает прокси при загрузке системы
- ✅ Перезапускает при падении (автоматическое восстановление)
- ✅ Управляет логами централизованно
- ✅ Позволяет легко управлять сервисом (start/stop/restart)

---

## 📦 Установка

### 1. Быстрая установка (автоматически)

```bash
sudo ./install_service.sh
```

Скрипт сделает всё сам:
- Скопирует service файл в `/etc/systemd/system/`
- Подставит правильные пути
- Включит автозапуск
- Покажет инструкции

### 2. Ручная установка (если хочешь понять процесс)

```bash
# 1. Скопировать service файл
sudo cp gateway-proxy.service /etc/systemd/system/

# 2. Отредактировать пути (замени /opt/gateway_proxy_v2 на свой путь)
sudo nano /etc/systemd/system/gateway-proxy.service

# 3. Перечитать конфигурацию
sudo systemctl daemon-reload

# 4. Включить автозапуск
sudo systemctl enable gateway-proxy

# 5. Запустить сейчас
sudo systemctl start gateway-proxy
```

---

## 🎮 Управление сервисом

### Основные команды

```bash
# Запустить
sudo systemctl start gateway-proxy

# Остановить
sudo systemctl stop gateway-proxy

# Перезапустить
sudo systemctl restart gateway-proxy

# Проверить статус (работает или нет)
sudo systemctl status gateway-proxy

# Включить автозапуск при загрузке
sudo systemctl enable gateway-proxy

# Выключить автозапуск
sudo systemctl disable gateway-proxy
```

### Просмотр статуса

```bash
# Краткий статус
sudo systemctl status gateway-proxy

# Пример вывода:
● gateway-proxy.service - Payment Gateway WebSocket Proxy Client
   Loaded: loaded (/etc/systemd/system/gateway-proxy.service; enabled)
   Active: active (running) since Mon 2025-10-05 10:30:00 UTC; 2h ago
   ...
```

---

## 📋 Логи

### journalctl - системные логи

```bash
# Все логи сервиса
sudo journalctl -u gateway-proxy

# Последние 100 строк
sudo journalctl -u gateway-proxy -n 100

# Следить в реальном времени (как tail -f)
sudo journalctl -u gateway-proxy -f

# Логи за сегодня
sudo journalctl -u gateway-proxy --since today

# Логи за последний час
sudo journalctl -u gateway-proxy --since "1 hour ago"

# С фильтрацией по ошибкам
sudo journalctl -u gateway-proxy | grep ERROR
```

### Файловые логи (как раньше)

Твои `proxy_20251005.log` **продолжают работать!**

```bash
# Смотреть файловые логи
tail -f proxy_*.log

# Последние 100 строк
tail -n 100 proxy_20251005.log
```

**Итого:** Логи есть в двух местах:
- `journalctl` - для системных событий (старт/стоп/крэш)
- `proxy_*.log` - для бизнес-логики (сообщения, операции)

---

## ⚙️ Изменение настроек

### 1. Изменить .env (настройки прокси)

```bash
# Редактируем
nano .env

# Перезапускаем сервис
sudo systemctl restart gateway-proxy
```

### 2. Изменить routing_config.yaml (роуты)

```bash
# Редактируем
nano routing_config.yaml

# Перезапускаем
sudo systemctl restart gateway-proxy
```

### 3. Изменить сам service файл

```bash
# Редактируем
sudo nano /etc/systemd/system/gateway-proxy.service

# Перечитать конфигурацию
sudo systemctl daemon-reload

# Перезапустить
sudo systemctl restart gateway-proxy
```

---

## 🔄 Обновление кода

Когда код изменился (git pull или новые файлы):

```bash
# 1. Остановить сервис
sudo systemctl stop gateway-proxy

# 2. Обновить код
git pull
# или
cp ~/new_proxy.py ./proxy.py

# 3. Обновить зависимости (если нужно)
./venv/bin/pip install -r requirements.txt

# 4. Запустить снова
sudo systemctl start gateway-proxy

# 5. Проверить
sudo systemctl status gateway-proxy
```

**Или одной командой:**
```bash
sudo systemctl restart gateway-proxy
```

---

## 🔒 Безопасность

Service файл включает защиту:

```ini
NoNewPrivileges=true    # Запрет повышения привилегий
PrivateTmp=true         # Изолированный /tmp
```

Процесс работает от твоего пользователя, **НЕ от root**.

---

## 🚨 Troubleshooting

### Сервис не запускается

```bash
# Проверить статус
sudo systemctl status gateway-proxy

# Посмотреть логи с ошибками
sudo journalctl -u gateway-proxy -n 50

# Проверить конфигурацию
sudo systemd-analyze verify gateway-proxy.service
```

### Сервис постоянно перезапускается

```bash
# Увидеть все попытки запуска
sudo journalctl -u gateway-proxy --since "10 minutes ago"

# Проверить .env файл
cat .env

# Проверить что venv существует
ls -la venv/bin/python
```

### Удалить сервис

```bash
# Остановить и выключить
sudo systemctl stop gateway-proxy
sudo systemctl disable gateway-proxy

# Удалить файл
sudo rm /etc/systemd/system/gateway-proxy.service

# Перечитать
sudo systemctl daemon-reload
```

---

## 📊 Мониторинг

### Проверка состояния

```bash
# Работает ли сервис?
sudo systemctl is-active gateway-proxy

# Включен ли автозапуск?
sudo systemctl is-enabled gateway-proxy

# Когда последний раз запускался?
sudo systemctl show gateway-proxy -p ActiveEnterTimestamp
```

### Статистика перезапусков

```bash
# Сколько раз перезапускался
sudo systemctl show gateway-proxy -p NRestarts
```

---

## 🎯 Best Practices

1. **После любых изменений в коде:**
   ```bash
   sudo systemctl restart gateway-proxy
   ```

2. **Проверяй логи регулярно:**
   ```bash
   sudo journalctl -u gateway-proxy -f
   ```

3. **Мониторь статус:**
   ```bash
   sudo systemctl status gateway-proxy
   ```

4. **Backup конфигов перед изменениями:**
   ```bash
   cp .env .env.backup
   cp routing_config.yaml routing_config.yaml.backup
   ```

---

## 🆚 Сравнение: До vs После

| Действие | Терминал (до) | systemd (после) |
|----------|---------------|-----------------|
| Запуск | `python proxy.py` | `sudo systemctl start gateway-proxy` |
| При закрытии SSH | ❌ Программа умрет | ✅ Продолжает работать |
| При перезагрузке | ❌ Нужно вручную запускать | ✅ Запустится автоматически |
| При падении | ❌ Всё, конец | ✅ Перезапустится через 10 сек |
| Логи | `tail -f proxy.log` | `journalctl -u gateway-proxy -f` |
| Управление | Нет | `start/stop/restart/status` |

---

## ✅ Готово!

После установки сервис будет:
- ✅ Автоматически запускаться при загрузке
- ✅ Перезапускаться при падении (до 5 раз за 200 сек)
- ✅ Логировать в journald + файлы
- ✅ Работать в фоне независимо от SSH

**Production ready!** 🚀
