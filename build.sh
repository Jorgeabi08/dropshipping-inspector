#!/bin/bash
set -e  # Detener si ocurre un error

APP_NAME="dropshipping-inspector"
VERSION="0.2.0"
DIST_DIR="dist"
ZIP_NAME="${APP_NAME}-${VERSION}.zip"

echo "🚀 Iniciando proceso de build para $APP_NAME v$VERSION"

# 1️⃣ Limpiar builds anteriores
echo "🧹 Limpiando directorios previos..."
rm -rf build "$DIST_DIR" *.egg-info

# 2️⃣ Crear wheel (.whl)
echo "📦 Generando wheel..."
python3 setup.py bdist_wheel

# 3️⃣ Crear directorio temporal para empaquetar
echo "📂 Preparando paquete para Gumroad..."
mkdir -p "$DIST_DIR/package"
cp -r inspector "$DIST_DIR/package/"
cp README.md setup.py "$DIST_DIR/package/" 2>/dev/null || true
cp licenses_db.json "$DIST_DIR/package/" 2>/dev/null || true

# 4️⃣ Copiar el wheel recién generado
cp "$DIST_DIR"/*.whl "$DIST_DIR/package/"

# 5️⃣ Empaquetar en zip
cd "$DIST_DIR"
zip -r "../$ZIP_NAME" package >/dev/null
cd ..

# 6️⃣ Limpiar temporal
rm -rf "$DIST_DIR/package"

echo "✅ Build completado exitosamente."
echo "📁 Archivo listo para Gumroad: $ZIP_NAME"
