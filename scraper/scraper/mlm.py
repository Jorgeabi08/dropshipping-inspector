# scraper/mlm.py
import requests
from bs4 import BeautifulSoup
import csv
from time import sleep

def ml_listings_search(query, limit=20, sleep_between=1.0):
    """
    Ejemplo muy simple (stub). MercadoLibre suele tener protección anti-scraping;
    para producción añade rotación de UA, proxies, retrasos, y respeta robots.txt.
    """
    results = []
    base = "https://listado.mercadolibre.com.mx"
    q = query.replace(" ", "-")
    url = f"{base}/{q}"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; InspectorBot/1.0)"}

    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    items = soup.select("li.results-item") or soup.select("li.ui-search-layout__item")

    for i, item in enumerate(items):
        if i >= limit:
            break
        title_tag = item.select_one("h2, .ui-search-item__title")
        price_tag = item.select_one(".price-tag-text-sr-only, .price__fraction")
        link_tag = item.select_one("a")
        title = title_tag.get_text(strip=True) if title_tag else ""
        price = price_tag.get_text(strip=True) if price_tag else ""
        link = link_tag["href"] if link_tag and link_tag.has_attr("href") else ""
        results.append({"title": title, "price": price, "link": link})
        sleep(sleep_between)
    return results

def export_csv(items, path="ml_results.csv"):
    keys = items[0].keys() if items else []
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(keys))
        writer.writeheader()
        writer.writerows(items)
