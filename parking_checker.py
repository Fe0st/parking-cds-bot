import re

import requests

# URL страницы паркинга Чёрная речка (паркинг 678 выбирается на странице)
URL = "https://www.cds.spb.ru/complex/chyornaya-rechka/parking/"

# Номера интересующих парковочных мест
# Оставляем только нужные: 66, 29, 25, 86 и 6
PARKING_SPOTS = ["66", "29", "25", "86", "6"]


def parse_numbers_from_page(html: str) -> dict[str, str]:
    """
    На странице внутри data-атрибута лежит большой JSON, где есть пары
    \"number\":\"<номер>\",\"status\":\"<статус>\".

    Мы вытащим все такие пары через regex, чтобы не парсить весь JSON целиком.
    """
    pattern = re.compile(r'"number":"(\d+)"\s*,\s*"status":"(\w+)"')
    matches = pattern.findall(html)

    result: dict[str, str] = {}
    for number, status in matches:
        # Если одно и то же место встретится несколько раз, первый статус нам достаточен
        result.setdefault(number, status)
    return result


def check_parking_spots():
    try:
        response = requests.get(URL, timeout=15)
        response.raise_for_status()

        spots_map = parse_numbers_from_page(response.text)

        for spot in PARKING_SPOTS:
            status = spots_map.get(spot)
            if status is None:
                # Место не числится среди свободных -> считаем занятым
                text_status = "❌"
            elif status == "free":
                text_status = "✅"
            else:
                # На всякий случай обрабатываем любые другие статусы как «занято»
                text_status = "❌"

            print(f"Место {spot}: {text_status}")

    except requests.RequestException as e:
        print(f"Ошибка при запросе к {URL}: {e}")


if __name__ == "__main__":
    check_parking_spots()



