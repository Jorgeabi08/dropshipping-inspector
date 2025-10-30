"""Pequeña herramienta para ejecutar búsquedas de prueba en los scrapers.
Usa límites muy bajos para evitar sobrecargar servicios.
"""
from inspector.scrapers.amazon import AmazonScraper
from inspector.scrapers.mercadolibre import MercadoLibreScraper
from inspector.scrapers.aliexpress import AliExpressScraper
import argparse

def run_all(query, limit=1):
    print("== MercadoLibre ==")
    ml = MercadoLibreScraper(use_proxies=False)
    try:
        res = ml.search_products(query, limit=limit)
        print(f"ML returned {len(res)} items")
        for p in res:
            print(p.title[:120], p.price, p.currency, p.url)
    except Exception as e:
        print("ML error:", e)

    print("\n== AliExpress ==")
    ae = AliExpressScraper(use_proxies=False)
    try:
        res = ae.search_products(query, limit=limit)
        print(f"AE returned {len(res)} items")
        for p in res:
            print(p.title[:120], p.price, p.currency, p.url)
    except Exception as e:
        print("AE error:", e)

    print("\n== Amazon (page search) ==")
    am = AmazonScraper(use_proxies=False)
    try:
        res = am.search_products(query, limit=limit)
        print(f"AM returned {len(res)} items")
        for p in res:
            print(p.title[:120], p.price, p.currency, p.url)
    except Exception as e:
        print("AM error:", e)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', required=True)
    parser.add_argument('--limit', type=int, default=1)
    args = parser.parse_args()
    run_all(args.query, limit=args.limit)
