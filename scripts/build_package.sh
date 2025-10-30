#!/usr/bin/env sh
# Build Python package (wheel + sdist) and create a ZIP deliverable for Gumroad
set -e

echo "Installing build tool..."
python -m pip install --upgrade build >/dev/null 2>&1 || true

echo "Building wheel and sdist..."
python -m build

PKG_DIR="dist_package"
ZIP_NAME="dropshipping-inspector-package.zip"

rm -rf "$PKG_DIR" "$ZIP_NAME"
mkdir -p "$PKG_DIR"

echo "Collecting files into $PKG_DIR"
cp -r PROPRIETARY_LICENSE.txt README_LICENSE.md .env.template "$PKG_DIR/" || true
cp -r dist "$PKG_DIR/" || true
cp -r inspector "$PKG_DIR/" || true

echo "Creating zip $ZIP_NAME"
cd "$PKG_DIR" && zip -r ../"$ZIP_NAME" ./* >/dev/null 2>&1 || true
cd - >/dev/null 2>&1 || true

echo "Done. Created $ZIP_NAME and built artifacts in dist/."
