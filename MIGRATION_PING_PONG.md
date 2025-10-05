# Migration: Remove JSON ping/pong

## ⚠️ ВАЖНО: Координация с сервером

Этот файл содержит изменения для удаления JSON ping/pong из клиента.

**НЕ ПРИМЕНЯЙ ЭТИ ИЗМЕНЕНИЯ** пока сервер не перестанет отправлять `{"type": "ping"}`!

---

## 📋 Порядок действий:

### 1. Сервер убирает JSON ping/pong
   - Команда разработки применяет изменения на сервере
   - Сервер перестает отправлять `{"type": "ping"}`
   - Сервер перестает ожидать `{"type": "pong"}`

### 2. Тестирование на dev/stage
   - Проверить что встроенный WebSocket ping/pong работает
   - Убедиться что соединение остается живым

### 3. Применить изменения на клиенте
   - Убрать обработку JSON ping/pong из proxy.py
   - Деплой на киоски

---

## 🔧 Изменения в proxy.py

### УБРАТЬ эти строки из `handle_message()`:

```python
# Handle ping/pong
if data.get('type') == 'ping':
    pong_response = {'type': 'pong'}
    await self.websocket.send(json.dumps(pong_response))
    self.logger.info(f"📤 SENT pong response")
    self.logger.info("=" * 80)
    return
```

### После удаления `handle_message()` будет начинаться так:

```python
async def handle_message(self, message: str):
    """Handle incoming message from WS server"""
    try:
        # Parse JSON from WS server
        data = json.loads(message)

        # Extract routing headers from headers object or top level
        headers = data.get('headers', {})
        kiosk_id = headers.get('header-kiosk-id') or data.get('Header-Kiosk-Id')
        operation_type = headers.get('header-operation-type') or data.get('Header-Operation-Type')

        # Log summary on INFO, full payload on DEBUG
        self.logger.info(f"📥 Received: {operation_type or 'unknown'} from kiosk {kiosk_id or 'unknown'}")
        self.logger.debug(f"Full message: {json.dumps(data, ensure_ascii=False, indent=2)}")

        # Count messages
        self.stats['messages_received'] += 1

        # ... rest of the code
```

---

## ✅ Проверка после миграции:

1. Клиент подключается к серверу
2. WebSocket ping/pong работает автоматически (проверить в логах websocket библиотеки на DEBUG)
3. При обрыве сети клиент переподключается
4. Нет лишних логов про ping/pong
5. Бизнес-сообщения обрабатываются как раньше

---

## 🔙 Откат (если что-то пошло не так):

Вернуть обработку JSON ping/pong:

```python
# В начале handle_message() после парсинга JSON:
if data.get('type') == 'ping':
    pong_response = {'type': 'pong'}
    await self.websocket.send(json.dumps(pong_response))
    return
```

---

## 📞 Контакты:

Если есть вопросы - пиши в канал команды или мне напрямую.

**Статус миграции:** ⏳ Ждем изменений на сервере
