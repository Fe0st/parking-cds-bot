import os
import textwrap
from datetime import datetime
from typing import Dict

import requests

from parking_checker import URL, PARKING_SPOTS, parse_numbers_from_page


def build_report(spots_map: Dict[str, str]) -> str:
    """
    Формируем текст для Telegram: по одному месту в строке, с галочкой/крестиком.
    В заголовке указываем текущую дату.
    """
    today = datetime.now().strftime("%d.%m.%Y")
    lines = [f"Сводка по паркингу на {today}:"]

    for spot in PARKING_SPOTS:
        status = spots_map.get(spot)
        if status == "free":
            icon = "✅"
            text = "свободно"
        else:
            icon = "❌"
            text = "занято (или не в списке свободных)"

        lines.append(f"Место {spot}: {icon} — {text}")

    return "\n".join(lines)


def send_telegram_message(token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        },
        timeout=15,
    )
    resp.raise_for_status()


def main() -> None:
    token = os.environ.get("TG_BOT_TOKEN")
    chat_id = os.environ.get("TG_CHAT_ID")

    if not token or not chat_id:
        print(
            textwrap.dedent(
                """
                Не заданы переменные окружения TG_BOT_TOKEN и/или TG_CHAT_ID.
                Пример запуска:
                  TG_BOT_TOKEN=\"123456:ABC...\" TG_CHAT_ID=\"123456789\" python3 send_parking_report.py
                """
            ).strip()
        )
        return

    resp = requests.get(URL, timeout=15)
    resp.raise_for_status()

    spots_map = parse_numbers_from_page(resp.text)
    report = build_report(spots_map)

    send_telegram_message(token, chat_id, report)
    print("Отчёт отправлен в Telegram.")


if __name__ == "__main__":
    main()


