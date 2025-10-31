#!/usr/bin/env python3
import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from inspector.license_check import verify_license, cache_license_info, load_cached_license
from inspector.config import APP_CONFIG, MARKETPLACE_CONFIG
from inspector.scrapers.mercadolibre import MercadoLibreScraper
from inspector.scrapers.amazon import AmazonScraper
from inspector.scrapers.aliexpress import AliExpressScraper

console = Console()

# === CONFIGURACIÓN DEL MODO DEMO ===
DEMO_LICENSE = "DEMO-ACCESS"
DEMO_FILE = os.path.expanduser("~/.inspector_demo_cache.json")
DEMO_DAYS = 3  # Duración del demo en días


def check_demo_validity() -> bool:
    """Controla que el modo demo solo dure ciertos días."""
    if not os.path.exists(DEMO_FILE):
        with open(DEMO_FILE, "w") as f:
            json.dump({"start_date": datetime.now().isoformat()}, f)
        return True

    try:
        with open(DEMO_FILE, "r") as f:
            data = json.load(f)
        start_date = datetime.fromisoformat(data.get("start_date"))
        if datetime.now() - start_date > timedelta(days=DEMO_DAYS):
            return False
        return True
    except Exception:
        return True


def check_license(license_key: str) -> bool:
    """Verifica la licencia o activa modo demo."""
    if license_key == DEMO_LICENSE:
        if not check_demo_validity():
            console.print("[bold red]⏰ Tu período de prueba ha expirado.[/bold red]")
            console.print("Compra la licencia completa en Gumroad para continuar.")
            sys.exit(1)

        console.print("[bold yellow]🧪 Modo DEMO activado (válido por 3 días).[/bold yellow]")
        console.print("[dim]Nota: los resultados están limitados a los 3 primeros productos.[/dim]")
        return True

    # En modo desarrollo, omitir verificación de licencia
    if APP_CONFIG.get("DEV_MODE"):
        console.print("[DEV] Omitiendo verificación de licencia")
        return True

    # Intenta cargar cache primero
    cached = load_cached_license()
    if cached and cached.get("license_key") == license_key:
        info = cached.get("info", {})
        if info.get("success"):
            console.print("[cache] Licencia válida (cached).")
            return True

    # Verificación online
    console.print("Verificando licencia en Gumroad...")
    res = verify_license(license_key, APP_CONFIG["PRODUCT_ID"])
    if res.get("success"):
        cache_license_info(license_key, res)
        console.print("[bold green]✅ Licencia válida.[/bold green]")
        return True

    console.print("[bold red]❌ Licencia inválida o expirada.[/bold red]")
    return False


def get_scraper(marketplace: str, country_code: Optional[str] = None, use_proxies: bool = False, proxy_list: Optional[List[str]] = None):
    """Retorna el scraper apropiado según el marketplace seleccionado."""
    config = MARKETPLACE_CONFIG.get(marketplace, {})

    if marketplace == "mercadolibre":
        scraper = MercadoLibreScraper(
            country_code=country_code or config.get("country_code", "MLM"),
            sleep_between=config.get("sleep_between", 1.0),
            use_proxies=use_proxies
        )
    elif marketplace == "amazon":
        scraper = AmazonScraper(
            marketplace=config.get("marketplace", "amazon.com"),
            sleep_between=config.get("sleep_between", 2.0),
            use_proxies=use_proxies
        )
    elif marketplace == "aliexpress":
        scraper = AliExpressScraper(
            sleep_between=config.get("sleep_between", 2.0),
            use_proxies=use_proxies
        )
    else:
        raise ValueError(f"Marketplace no soportado: {marketplace}")

    if use_proxies and proxy_list:
        scraper.add_proxies_from_list(proxy_list)

    return scraper


def main():
    parser = argparse.ArgumentParser(prog="inspector")
    subparsers = parser.add_subparsers(dest="command")

    # Comando: scrape
    scrape_parser = subparsers.add_parser("scrape", help="Buscar productos")
    scrape_parser.add_argument(
        "marketplace",
        choices=["mercadolibre", "amazon", "aliexpress"],
        help="Marketplace donde buscar"
    )
    scrape_parser.add_argument(
        "--query",
        required=True,
        help="Término de búsqueda"
    )
    scrape_parser.add_argument(
        "--country",
        help="Código de país (ejemplo: MLM para México)",
        default=None
    )
    scrape_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Número máximo de resultados"
    )
    scrape_parser.add_argument(
        "--license",
        required=True,
        help="Clave de licencia o usa DEMO-ACCESS para modo demo"
    )
    scrape_parser.add_argument(
        "--use-proxies",
        action="store_true",
        help="Usar proxies para las peticiones"
    )
    scrape_parser.add_argument(
        "--proxy-list",
        help="Archivo con lista de proxies (uno por línea en formato host:port)",
        type=argparse.FileType('r')
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if not check_license(args.license):
        return

    if args.command == "scrape":
        try:
            proxy_list = None
            if args.proxy_list:
                proxy_list = [line.strip() for line in args.proxy_list if line.strip()]

            scraper = get_scraper(
                args.marketplace,
                args.country,
                use_proxies=args.use_proxies,
                proxy_list=proxy_list
            )

            console.print(f"🔍 Buscando '{args.query}' en [bold]{args.marketplace}[/bold]...")
            if args.use_proxies:
                console.print("🌐 Usando proxies para las peticiones...")

            products = scraper.search_products(args.query, args.limit)

            # Si está en modo demo, limitar resultados
            if args.license == DEMO_LICENSE:
                products = products[:3]

            if not products:
                console.print("[bold red]No se encontraron resultados.[/bold red]")
                return

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = Path(APP_CONFIG["DEFAULT_EXPORT_DIR"]) / f"{args.marketplace}_{timestamp}.csv"
            scraper.export_to_csv(products, filename)

            console.print(f"[bold green]✅ Se encontraron {len(products)} productos.[/bold green]")
            console.print(f"📁 Resultados exportados a: {filename}")

        except Exception as e:
            console.print(f"[bold red]Error inesperado:[/bold red] {e}")


if __name__ == "__main__":
    main()
