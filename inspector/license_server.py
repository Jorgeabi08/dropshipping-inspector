"""Simple license validation service for Dropshipping Inspector.

This service can run in two modes:
- Local mode (default): validate against a local JSON DB (`inspector/licenses_db.json`).
- Gumroad proxy mode: forward verification requests to Gumroad's verify API (set
  environment variable `LICENSE_USE_GUMROAD=true`).

Usage (development):
  export FLASK_APP=inspector.license_server
  python -m inspector.license_server

Or run directly: python inspector/license_server.py
"""
from flask import Flask, request, jsonify
import os
import json
from pathlib import Path
import requests
from datetime import datetime

APP = Flask(__name__)
BASE_DIR = Path(__file__).parent
DB_FILE = BASE_DIR / "licenses_db.json"
GUMROAD_VERIFY_URL = "https://api.gumroad.com/v2/licenses/verify"
USE_GUMROAD = os.getenv("LICENSE_USE_GUMROAD", "false").lower() in ("1", "true", "yes")
# API key to protect the /verify endpoint. If empty, auth is disabled (useful for
# local demos). For production, set LICENSE_SERVER_API_KEY to a strong secret and
# protect the service behind TLS.
LICENSE_SERVER_API_KEY = os.getenv("LICENSE_SERVER_API_KEY", "")


def _check_api_key(req):
    """Returns (ok, error_response). If LICENSE_SERVER_API_KEY is not set,
    authentication is skipped (backwards compatible for demos). Otherwise the
    client must send X-API-KEY header with the configured value.
    """
    if not LICENSE_SERVER_API_KEY:
        return True, {}

    key = req.headers.get("X-API-KEY") or req.args.get("api_key") or req.form.get("api_key")
    if key == LICENSE_SERVER_API_KEY:
        return True, {}
    return False, {"success": False, "message": "invalid or missing api key"}


def verify_with_gumroad(license_key: str, product_id: str, timeout: int = 10) -> dict:
    try:
        resp = requests.post(GUMROAD_VERIFY_URL, data={
            "license_key": license_key,
            "product_id": product_id
        }, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        return {"success": False, "message": f"Gumroad API error: {e}"}


def verify_local(license_key: str, product_id: str) -> dict:
    if not DB_FILE.exists():
        return {"success": False, "message": "local license DB not found"}
    try:
        data = json.loads(DB_FILE.read_text(encoding="utf-8"))
        licenses = data.get("licenses", [])
        now = datetime.utcnow()
        for lic in licenses:
            if lic.get("license_key") == license_key and lic.get("product_id") == product_id:
                if not lic.get("active", True):
                    return {"success": False, "message": "license revoked/disabled"}
                exp = lic.get("expires")
                if exp:
                    exp_dt = datetime.fromisoformat(exp)
                    if now > exp_dt:
                        return {"success": False, "message": "license expired"}
                # success
                return {"success": True, "message": "ok", "license": lic}
        return {"success": False, "message": "license not found"}
    except Exception as e:
        return {"success": False, "message": f"local DB error: {e}"}


@APP.route("/verify", methods=["POST"])
def verify():
    # Accept json or form data
    # Authenticate request if API key is configured
    ok, err = _check_api_key(request)
    if not ok:
        return jsonify(err), 401

    payload = request.get_json(silent=True) or request.form
    license_key = payload.get("license_key")
    product_id = payload.get("product_id")
    if not license_key or not product_id:
        return jsonify({"success": False, "message": "license_key and product_id required"}), 400

    if USE_GUMROAD:
        res = verify_with_gumroad(license_key, product_id)
        return jsonify(res)
    else:
        res = verify_local(license_key, product_id)
        return jsonify(res)


def run(port: int = 5000):
    APP.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    run()
