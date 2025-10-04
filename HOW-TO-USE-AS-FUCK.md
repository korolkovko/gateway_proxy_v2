# 🚀 Как запустить Gateway Proxy - Простая инструкция

## Запуск с нуля (первый раз)

### 1. Установка зависимостей

```bash
cd /Users/korolkovnikolai/gateway_proxy_v2/
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

### 2. Настройка конфигурации

Откройте `.env` и убедитесь что там заполнено:

```bash
WS_SERVER_URL='wss://web-production-a21a7.up.railway.app/ws'
WS_TOKEN='ваш_токен'
LOG_LEVEL='INFO'
```

### 3. Запуск визуального интерфейса

```bash
./venv/bin/python monitor.py
```

### 4. В интерфейсе нажмите кнопку "▶ START"

Готово! Прокси запущен.

---

## Обычный запуск (не первый раз)

```bash
cd /Users/korolkovnikolai/gateway_proxy_v2/
./venv/bin/python monitor.py
```

Нажмите "▶ START" в интерфейсе.

---

## Что делает визуальный интерфейс

- **Control** (клавиша `1`) - запуск/остановка прокси, статистика
- **Logs** (клавиша `2`) - логи в реальном времени
- **Settings** (клавиша `3`) - настройки WS сервера и токена
- **Routes** (клавиша `4`) - настройка роутинга сообщений

### Кнопки управления:
- `▶ START` - запустить прокси
- `■ STOP` - остановить прокси
- `↻ RESTART` - перезапустить прокси

### Горячие клавиши:
- `q` - выход из программы

---

## Запуск без визуального интерфейса (консольный режим)

Если нужен только прокси без TUI:

```bash
./venv/bin/python proxy.py
```

---

## Что делает прокси

1. Подключается к WebSocket серверу (`WS_SERVER_URL`)
2. Авторизуется токеном (`WS_TOKEN`)
3. Получает сообщения от сервера
4. Обрабатывает ping/pong (`{"type": "ping"}` → `{"type": "pong"}`)
5. Маршрутизирует сообщения в локальный gateway по настройкам из `routing_config.yaml`
6. Отправляет ответы обратно на сервер

---

## Проверка работы

После запуска вы должны увидеть:
```
🚀 Payment Gateway Proxy starting...
   WS Server: wss://web-production-a21a7.up.railway.app/ws
   Routing config loaded with X routes
✅ Connected to cloud server
```

Статистика покажет:
- RECEIVED - сколько сообщений получено
- SENT - сколько отправлено
- ERRORS - сколько ошибок

---

## Решение проблем

### Не запускается venv
```bash
# Пересоздайте виртуальное окружение
rm -rf venv
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

### Ошибка "Connection failed"
- Проверьте интернет
- Проверьте `WS_SERVER_URL` в `.env`
- Проверьте что токен не истек

### Ошибки подключения к gateway
- Убедитесь что локальный gateway запущен
- Проверьте URL в `routing_config.yaml`

---

## Файлы конфигурации

- `.env` - основные настройки (URL сервера, токен)
- `routing_config.yaml` - маршрутизация сообщений к gateway
- `proxy_YYYYMMDD.log` - логи работы (создаются автоматически)

---

## Быстрая команда (одной строкой)

```bash
cd /Users/korolkovnikolai/gateway_proxy_v2/ && ./venv/bin/python monitor.py
```
