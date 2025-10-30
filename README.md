# Dropshipping Inspector

Una herramienta para buscar y analizar productos en diferentes marketplaces (MercadoLibre, Amazon, AliExpress).

## Características

- Búsqueda en múltiples marketplaces
- Soporte para proxies
- Exportación a CSV
- Manejo de licencias
- Sistema anti-detección

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

Búsqueda simple (ejemplo):
```bash
python cli.py scrape --query "iphone" --license TU_LICENCIA
```

Ejecutar pruebas rápidas en vivo (limitadas a 1 item por marketplace):

```bash
python scripts/smoke_run.py --query "smartwatch" --limit 1
```

Demo de ProxyManager (sin llamadas de red):

```bash
python scripts/proxy_demo.py
```

Pruebas unitarias mínimas (sin red):

```bash
python -m unittest tests/test_imports.py
```

## Configuración

Puedes configurar los siguientes aspectos:
- Proxies
- País de búsqueda
- Límite de resultados
- Tiempo entre peticiones

## Notas

- Las búsquedas en vivo pueden ser bloqueadas por los sitios; usa límites bajos y respeta delays.
- Para Amazon considera usar Product Advertising API (requiere claves).
- Si quieres que ejecute una búsqueda de prueba ahora, indícame la consulta.
