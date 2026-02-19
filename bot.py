import logging
import os
from datetime import datetime

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from parking_checker import PARKING_SPOTS, URL, parse_numbers_from_page

import requests

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

MOSCOW_TZ = pytz.timezone("Europe/Moscow")

BUTTON_CHECK = "Проверить сейчас 🔍"

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [[BUTTON_CHECK]],
    resize_keyboard=True,
)


def fetch_status() -> str:
    """Запрашивает страницу и возвращает готовый текст отчёта."""
    resp = requests.get(URL, timeout=15)
    resp.raise_for_status()

    spots_map = parse_numbers_from_page(resp.text)

    today = datetime.now(MOSCOW_TZ).strftime("%d.%m.%Y %H:%M")
    all_free = all(spots_map.get(spot) == "free" for spot in PARKING_SPOTS)
    header_icon = "✅" if all_free else "❌"

    lines = [f"Паркинг на {today}: {header_icon}", ""]

    for spot in PARKING_SPOTS:
        status = spots_map.get(spot)
        if status == "free":
            icon = "✅"
            text = "свободно"
        else:
            icon = "❌"
            text = "продано/занято" if status is None else f"продано/занято (статус: {status})"
        lines.append(f"Место {spot}: {icon} — {text}")

    return "\n".join(lines)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Бот мониторинга паркинга ЖК Чёрная речка.\n"
        "Нажмите кнопку ниже, чтобы проверить статус прямо сейчас.\n"
        "Ежедневный отчёт приходит автоматически в 08:00 МСК.",
        reply_markup=MAIN_KEYBOARD,
    )


async def handle_check_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Запрашиваю данные...")
    try:
        text = fetch_status()
    except Exception as e:
        logger.error("Ошибка при получении статуса: %s", e)
        text = f"Ошибка при получении данных: {e}"
    await update.message.reply_text(text, reply_markup=MAIN_KEYBOARD)


async def send_daily_report(app: Application) -> None:
    """Отправляет ежедневный отчёт во все чаты из CHAT_IDS."""
    chat_ids = os.environ["TG_CHAT_ID"].split(",")
    try:
        text = fetch_status()
    except Exception as e:
        logger.error("Ошибка в ежедневном отчёте: %s", e)
        text = f"Ошибка при получении данных: {e}"

    for chat_id in chat_ids:
        await app.bot.send_message(chat_id=chat_id.strip(), text=text)


async def post_init(app: Application) -> None:
    """Запускает планировщик после старта event loop."""
    scheduler = AsyncIOScheduler(timezone=MOSCOW_TZ)
    scheduler.add_job(
        send_daily_report,
        trigger="cron",
        hour=8,
        minute=0,
        args=[app],
    )
    scheduler.start()
    app.bot_data["scheduler"] = scheduler


def main() -> None:
    token = os.environ.get("TG_BOT_TOKEN")
    webhook_url = os.environ.get("WEBHOOK_URL")  # например: https://example.com/webhook
    webhook_port = int(os.environ.get("WEBHOOK_PORT", "8443"))
    webhook_secret = os.environ.get("WEBHOOK_SECRET", "")

    if not token:
        raise RuntimeError("Не задана переменная окружения TG_BOT_TOKEN")
    if not webhook_url:
        raise RuntimeError("Не задана переменная окружения WEBHOOK_URL")
    if not os.environ.get("TG_CHAT_ID"):
        raise RuntimeError("Не задана переменная окружения TG_CHAT_ID")

    app = Application.builder().token(token).post_init(post_init).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.Text([BUTTON_CHECK]), handle_check_button))

    logger.info("Запуск бота с webhook на %s, порт %d", webhook_url, webhook_port)
    app.run_webhook(
        listen="0.0.0.0",
        port=webhook_port,
        secret_token=webhook_secret if webhook_secret else None,
        webhook_url=f"{webhook_url.rstrip('/')}/webhook",
    )


if __name__ == "__main__":
    main()
