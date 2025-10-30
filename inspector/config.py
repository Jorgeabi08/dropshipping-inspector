from pathlib import Path

# ==========================
# Datos generales de la app
# ==========================
APP_NAME = "Dropshipping Inspector"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Tu Nombre o Marca"
APP_DESCRIPTION = "Herramienta avanzada de scraping para marketplaces (AliExpress, Amazon, MercadoLibre)."

# ==========================
# Configuración de licencia
# ==========================
GUMROAD_PRODUCT_ID = "abc123xyz"  # Cambia por tu Product ID real
MAX_OFFLINE_DAYS = 7

# ==========================
# Configuración de entorno
# ==========================
BASE_DIR = Path(__file__).resolve().parent
EXPORT_DIR = BASE_DIR / "exports"
EXPORT_DIR.mkdir(exist_ok=True)

APP_CONFIG = {
    "NAME": APP_NAME,
    "VERSION": APP_VERSION,
    "AUTHOR": APP_AUTHOR,
    "DESCRIPTION": APP_DESCRIPTION,
    "PRODUCT_ID": GUMROAD_PRODUCT_ID,
    "MAX_OFFLINE_DAYS": MAX_OFFLINE_DAYS,
    "DEFAULT_EXPORT_DIR": str(EXPORT_DIR),
    "DEV_MODE": True,  # Cambia a False cuando empaquetes para producción
}

# ==========================
# Configuración de scrapers
# ==========================
MARKETPLACE_CONFIG = {
    "mercadolibre": {"country_code": "MLM", "sleep_between": 1.0},
    "amazon": {"marketplace": "amazon.com", "sleep_between": 2.0},
    "aliexpress": {"sleep_between": 2.0},
}
