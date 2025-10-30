from typing import Dict
from pathlib import Path
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la aplicación
# inspector/config.py

GUMROAD_ACCESS_TOKEN = "9UTTpwkH8wqZzUpJClR7V5U_OVXCtyRSMa2JCxxANqM"
GUMROAD_PRODUCT_ID = "o2xfKnZNXut3d2a2nlIYmf69p2WBmvWJNWhGl9Lax-0"

LICENSE_SERVER_ENABLED = False  # usamos Gumroad API
MAX_OFFLINE_DAYS = 7  # gracia si no hay internet


# Configuración por marketplace
MARKETPLACE_CONFIG: Dict[str, Dict] = {
    "mercadolibre": {
        "country_code": "MLM",  # México por defecto
        "sleep_between": 1.0,
        "max_retries": 3,
    },
    "amazon": {
        "marketplace": "amazon.com",
        "sleep_between": 2.0,
        "max_retries": 3,
    },
    "aliexpress": {
        "marketplace": "aliexpress.com",
        "sleep_between": 2.0,
        "max_retries": 3,
    }
}

# Asegurarse de que existe el directorio de exportación
Path(APP_CONFIG["DEFAULT_EXPORT_DIR"]).mkdir(exist_ok=True)
