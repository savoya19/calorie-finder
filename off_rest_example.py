# file: off_rest_example.py
import requests

BASE = "https://world.openfoodfacts.org"

HEADERS = {
    "User-Agent": "Darcons-Trade-CalorieFetcher/1.0 (+https://darcons-trade.example)"
}

def get_product_by_barcode(barcode: str, fields=None, lang="ru", country="ru") -> dict:
    """
    Получение конкретного продукта по штрихкоду (API v2).
    """
    if fields is None:
        fields = "code,product_name,nutriments,brands,quantity,serving_size,language,lang,lc"
    url = f"{BASE}/api/v2/product/{barcode}"
    params = {"fields": fields, "lc": lang, "cc": country}
    r = requests.get(url, headers=HEADERS, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def search_products(query: str, page_size=5, fields=None, lang="ru", country="ru") -> dict:
    """
    Поиск продуктов по тексту (Search API v2).
    Пример фильтра: можно добавлять tags и условия по нутриентам.
    """
    if fields is None:
        fields = "code,product_name,brands,nutriments,quantity,serving_size,ecoscore_grade"
    url = f"{BASE}/api/v2/search"
    params = {
        "search_terms": query,
        "fields": fields,
        "page_size": page_size,
        "lc": lang,
        "cc": country,
    }
    r = requests.get(url, headers=HEADERS, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def extract_kcal(nutriments: dict) -> dict:
    """
    Извлекает калорийность и БЖУ.
    Возвращает значения на 100 г и на порцию (если доступно).
    """
    get = nutriments.get
    data = {
        "kcal_100g": get("energy-kcal_100g") or get("energy-kcal_value"),
        "protein_100g": get("proteins_100g"),
        "fat_100g": get("fat_100g"),
        "carbs_100g": get("carbohydrates_100g"),
        "kcal_serving": get("energy-kcal_serving"),
        "protein_serving": get("proteins_serving"),
        "fat_serving": get("fat_serving"),
        "carbs_serving": get("carbohydrates_serving"),
    }
    return {k: v for k, v in data.items() if v is not None}

if __name__ == "__main__":
    # Пример 1: по штрихкоду
    barcode = "5449000000996"  # Coca-Cola 0.33 л (пример; замените своим)
    prod = get_product_by_barcode(barcode)
    if prod.get("product"):
        p = prod["product"]
        print("Название:", p.get("product_name"))
        print("Бренд:", p.get("brands"))
        print("Упаковка:", p.get("quantity"))
        print("Порция:", p.get("serving_size"))
        print("Нутриенты:", extract_kcal(p.get("nutriments", {})))
    else:
        print("Продукт не найден")

    # Пример 2: поиск по названию
    res = search_products("творог 5%", page_size=3)
    for i, p in enumerate(res.get("products", []), 1):
        print(f"\nРезультат {i}:")
        print("Штрихкод:", p.get("code"))
        print("Название:", p.get("product_name"))
        print("Бренд:", p.get("brands"))
        print("Нутриенты:", extract_kcal(p.get("nutriments", {})))
