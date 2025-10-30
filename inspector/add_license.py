"""Small helper to add licenses to the local licenses_db.json for the validation
service. This is intended for offline/demo use only.
"""
import argparse
import json
from pathlib import Path
from datetime import datetime

DB_FILE = Path(__file__).parent / "licenses_db.json"


def load_db():
    if DB_FILE.exists():
        return json.loads(DB_FILE.read_text(encoding="utf-8"))
    return {"licenses": []}


def save_db(data):
    DB_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def add_license(license_key, product_id, expires=None, notes=None):
    data = load_db()
    entry = {
        "license_key": license_key,
        "product_id": product_id,
        "active": True,
        "expires": expires,
        "notes": notes,
    }
    data.setdefault("licenses", []).append(entry)
    save_db(data)
    print("Added license:", license_key)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("license_key")
    parser.add_argument("product_id")
    parser.add_argument("--expires", help="ISO datetime string, e.g. 2025-12-31T23:59:59", default=None)
    parser.add_argument("--notes", default=None)
    args = parser.parse_args()
    add_license(args.license_key, args.product_id, args.expires, args.notes)


if __name__ == "__main__":
    main()
