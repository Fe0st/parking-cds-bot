import re

import requests
from bs4 import BeautifulSoup

# URL страницы паркинга Чёрная речка (паркинг 678 выбирается на странице)
URL = "https://www.cds.spb.ru/complex/chyornaya-rechka/parking/"

# Номера интересующих парковочных мест
# Проверяем: 66, 29, 86, 6, 83, 84, 5, 8
PARKING_SPOTS = ["66", "29", "86", "6", "83", "84", "5", "8"]


def parse_numbers_from_page(html: str) -> dict[str, str]:
    """
    На странице внутри data-атрибута лежит большой JSON, где есть пары
    \"number\":\"<номер>\",\"status\":\"<статус>\".

    ВАЖНО: Фильтруем места по паркингу 678 (guid_building: D3536DFA-3A03-43B2-911B-AF73A4CEBC83)
    Это необходимо, т.к. место может быть свободно в одном паркинге, но продано в другом.
    
    Место считается свободным ТОЛЬКО если:
    1. Оно имеет статус "free"
    2. И относится к паркингу 678 (имеет правильный guid_building)
    
    Если место отсутствует в JSON для паркинга 678 или имеет другой статус - считаем проданным.
    """
    # GUID паркинга 678
    PARKING_678_GUID = "D3536DFA-3A03-43B2-911B-AF73A4CEBC83"
    
    result: dict[str, str] = {}
    
    # Для каждого интересующего нас места ищем полную запись в JSON
    for spot in PARKING_SPOTS:
        # Ищем запись, содержащую number и guid_building
        pattern = re.compile(
            r'\{[^}]{0,2000}"number":"' + spot + r'"[^}]{0,2000}\}',
            re.DOTALL
        )
        matches = pattern.findall(html)
        
        # Проверяем каждую найденную запись
        for record in matches:
            guid_match = re.search(r'"guid_building":"([^"]+)"', record)
            status_match = re.search(r'"status":"(\w+)"', record)
            
            if guid_match and status_match:
                guid = guid_match.group(1)
                status = status_match.group(1)
                
                # Если место из паркинга 678 и свободно - сохраняем
                if guid == PARKING_678_GUID and status == "free":
                    result[spot] = status
                    break  # Достаточно одной записи из паркинга 678
    
    return result


def check_svg_for_parking_678() -> dict[str, bool]:
    """
    Проверяет SVG файл паркинга 678 для дополнительной проверки статуса мест.
    Возвращает словарь {номер_места: True если свободно, False если продано}
    """
    try:
        svg_url = "https://www.cds.spb.ru/images/floor_layout_parking/svg/chr678.svg"
        svg_resp = requests.get(svg_url, timeout=15)
        svg_resp.raise_for_status()
        
        soup = BeautifulSoup(svg_resp.text, "html.parser")
        result = {}
        
        # Проверяем каждое интересующее нас место
        for spot in PARKING_SPOTS:
            rect = soup.find("rect", {"id": f"PAR-{spot}"})
            if rect:
                # Если элемент найден в SVG, считаем что место существует
                # Но без data-enabled мы не можем точно определить статус из SVG
                # Поэтому просто отмечаем, что место найдено
                result[spot] = True
            else:
                # Если место не найдено в SVG - возможно продано
                result[spot] = False
                
        return result
    except Exception:
        # Если не удалось загрузить SVG, возвращаем пустой словарь
        return {}


def check_parking_spots():
    try:
        response = requests.get(URL, timeout=15)
        response.raise_for_status()

        spots_map = parse_numbers_from_page(response.text)

        for spot in PARKING_SPOTS:
            status = spots_map.get(spot)
            # СТРОГАЯ ЛОГИКА: место считается свободным ТОЛЬКО если оно явно имеет статус "free"
            # Если место отсутствует в JSON или имеет другой статус - считаем проданным
            # Это важно, т.к. место может быть свободно в одном паркинге, но продано в другом
            if status == "free":
                text_status = "✅"
            else:
                # Место не найдено или имеет другой статус -> считаем проданным
                text_status = "❌"

            print(f"Место {spot}: {text_status}")

    except requests.RequestException as e:
        print(f"Ошибка при запросе к {URL}: {e}")


if __name__ == "__main__":
    check_parking_spots()



