# parking-cds-bot

Telegram-бот для мониторинга парковочных мест ЖК Чёрная речка (паркинг 678).

## Возможности

- Ежедневный отчёт в 08:00 МСК
- Кнопка **"Проверить сейчас 🔍"** для запроса актуального статуса в любой момент
- Webhook-режим (работает на Raspberry Pi без внешних CI/CD)

---

## Деплой на Raspberry Pi

### 1. Клонировать репозиторий

```bash
git clone git@github.com:Fe0st/parking-cds-bot.git /home/pi/parking-cds-bot
cd /home/pi/parking-cds-bot
```

### 2. Создать виртуальное окружение и установить зависимости

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

### 3. Создать файл `.env`

```bash
cat > /home/pi/parking-cds-bot/.env << 'EOF'
TG_BOT_TOKEN=123456:ABC...
TG_CHAT_ID=123456789
WEBHOOK_URL=https://your-domain.com
WEBHOOK_PORT=8443
WEBHOOK_SECRET=your_random_secret_string
EOF
chmod 600 /home/pi/parking-cds-bot/.env
```

- `WEBHOOK_URL` — публичный HTTPS-адрес, куда Telegram будет слать обновления
- `WEBHOOK_PORT` — порт, на котором слушает бот (Telegram поддерживает: 443, 80, 88, 8443)
- `WEBHOOK_SECRET` — произвольная строка для защиты endpoint (опционально, но рекомендуется)
- `TG_CHAT_ID` — можно указать несколько через запятую: `123456789,987654321`

### 4. Настроить nginx как reverse proxy

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate     /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location /webhook {
        proxy_pass http://127.0.0.1:8443/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Получить SSL-сертификат через Let's Encrypt:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 5. Установить systemd-юнит

```bash
sudo cp parking-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable parking-bot
sudo systemctl start parking-bot
```

Проверить статус:
```bash
sudo systemctl status parking-bot
journalctl -u parking-bot -f
```

---

## Переменные окружения

| Переменная       | Обязательная | Описание                                      |
|------------------|:------------:|-----------------------------------------------|
| `TG_BOT_TOKEN`   | ✅           | Токен бота от @BotFather                      |
| `TG_CHAT_ID`     | ✅           | ID чата(ов) для ежедневных отчётов            |
| `WEBHOOK_URL`    | ✅           | Публичный HTTPS-адрес сервера                 |
| `WEBHOOK_PORT`   |              | Порт (по умолчанию: 8443)                     |
| `WEBHOOK_SECRET` |              | Секрет для верификации запросов от Telegram   |
