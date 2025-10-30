import json
import requests
from pathlib import Path
from datetime import datetime, timedelta

from inspector.config import GUMROAD_PRODUCT_ID, MAX_OFFLINE_DAYS

CACHE_DIR = Path.home() / ".dropshipping_inspector"
CACHE_FILE = CACHE_DIR / "license.json"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

GUMROAD_VERIFY_URL = "https://api.gumroad.com/v2/licenses/verify"


def verify_license_online(license_key: str) -> dict:
    data = {
        "license_key": license_key,
        "product_id": GUMROAD_PRODUCT_ID
    }
    try:
        resp = requests.post(GUMROAD_VERIFY_URL, data=data, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return {"success": False, "message": "No internet connection"}


def cache_license_info(license_key: str, info: dict):
    payload = {
        "license_key": license_key,
        "info": info,
        "last_verified": datetime.utcnow().isoformat()
    }
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f)


def load_cached_license() -> dict | None:
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def verify_license(license_key: str) -> bool:
    response = verify_license_online(license_key)

    if response.get("success"):
        # Licencia válida en Gumroad
        cache_license_info(license_key, response)
        return True

    # Si falla internet o no hay verificación online... pasamos a modo offline
    cached = load_cached_license()
    if cached and cached.get("license_key") == license_key:
        last_verified = datetime.fromisoformat(cached["last_verified"])
        if datetime.utcnow() - last_verified <= timedelta(days=MAX_OFFLINE_DAYS):
            print("⚠️  Sin internet, usando licencia offline temporalmente.")
            return True

    return False
