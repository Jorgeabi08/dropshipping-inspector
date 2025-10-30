# cli.py
import argparse
import os
import sys
from dotenv import load_dotenv

# Prefer the inspector package license_check (exists at inspector/license_check.py)
from inspector.license_check import verify_license, cache_license_info, load_cached_license
from scraper.scraper.mlm import ml_listings_search, export_csv

# Load environment variables from .env if present
load_dotenv()
PRODUCT_ID = os.getenv("GUMROAD_PRODUCT_ID", "TU_PRODUCT_ID_DE_GUMROAD")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "10"))

def main():
	def check_and_cache(license_key: str):
    # Intenta cargar cache primero
    cached = load_cached_license()
    if cached and cached.get("license_key") == license_key:
        info = cached.get("info", {})
        if info.get("success"):
            print("[cache] Licencia válida (cached).")
            return True, info

    # Verificación online (Gumroad)
    print("Verificando licencia en Gumroad...")
    res = verify_license(license_key, PRODUCT_ID)
    if res.get("success"):
        print("Licencia válida. Guardando cache.")
        cache_license_info(license_key, res)
        return True, res
    else:
        print("Licencia NO válida:", res.get("message"))
        return False, res


def cmd_activate(args):
    """Activa (verifica y guarda) una license key para uso posterior."""
    ok, info = check_and_cache(args.license)
    if ok:
        print("Licencia activada correctamente.")
    else:
        print("No se pudo activar la licencia.")


def cmd_scrape(args):
    ok, info = check_and_cache(args.license)
    if not ok:
        print("Acceso denegado. Compra el producto en Gumroad para activar.")
        sys.exit(1)

    print(f"Corriendo scraper para query: {args.query} (limit={args.limit})")
    items = ml_listings_search(args.query, limit=args.limit, sleep_between=0.5)
    if not items:
        print("No se encontraron items o hubo un error en el scraping.")
        return
    export_csv(items, path=args.output)
    print(f"Exportado {len(items)} filas a {args.output}")


def main():
    parser = argparse.ArgumentParser(prog="inspector")
    sub = parser.add_subparsers(dest="cmd")

    p_activate = sub.add_parser("activate", help="Activar y cachear una license key")
    p_activate.add_argument("--license", required=True, help="Tu license key de Gumroad")

    p_scrape = sub.add_parser("scrape", help="Scrapea MercadoLibre (ejemplo)")
    p_scrape.add_argument("--query", required=True)
    p_scrape.add_argument("--limit", type=int, default=30)
    p_scrape.add_argument("--output", default="ml_results.csv")
    p_scrape.add_argument("--license", required=True, help="Tu license key de Gumroad")

    args = parser.parse_args()
    if args.cmd == "scrape":
        cmd_scrape(args)
    elif args.cmd == "activate":
        cmd_activate(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
