#!/usr/bin/env python3
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from .license_check import verify_license, cache_license_info, load_cached_license
from .config import APP_CONFIG, MARKETPLACE_CONFIG
from .scrapers.mercadolibre import MercadoLibreScraper
from .scrapers.amazon import AmazonScraper
from .scrapers.aliexpress import AliExpressScraper


def main():
    license_key = input("Ingresa tu licencia para continuar: ").strip()

    if not verify_license(license_key):
        print("❌ Licencia inválida o expirada. Compra una en Gumroad.")
        exit(1)

    print("✅ Licencia verificada. ¡Bienvenido Dropshipper Pro 🛸!")
    # Aquí inicia tu scraping


def check_license(license_key: str) -> bool:
    # En modo desarrollo, omitir verificación de licencia
    if APP_CONFIG.get("DEV_MODE"):
        print("[DEV] Omitiendo verificación de licencia")
        return True

    # Intenta cargar cache primero
    cached = load_cached_license()
    if cached and cached.get("license_key") == license_key:
        info = cached.get("info", {})
        if info.get("success"):
            print("[cache] Licencia válida (cached).")
            return True

    # Verificación online
    print("Verificando licencia en Gumroad...")
    res = verify_license(license_key, APP_CONFIG["PRODUCT_ID"])
    if res.get("success"):
        cache_license_info(license_key, res)
        print("Licencia válida.")
        return True

    print("Licencia inválida o expirada.")
    return False
