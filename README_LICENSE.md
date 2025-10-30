Cómo funciona el control de licencias
====================================

Resumen
- Este repositorio incluye una verificación de licencias basada en Gumroad.
- Para activar el producto el cliente debe proporcionar la "license key" que Gumroad
  le entrega tras la compra.

Activación (cliente)
- Uso rápido:

  1. Copia `.env.template` a `.env` y establece `GUMROAD_PRODUCT_ID` con tu product_id.
  2. Ejecuta:

     python cli.py activate --license <LICENSE_KEY>

  3. Si la verificación remota con la API de Gumroad es correcta, la licencia queda cacheada
     en `~/.dropshipping_inspector/license.json`.

Validación remota (vendedor/opcional)
- Para mayor control (renta/suscripción) puedes ejecutar un servicio propio que valide
  keys y configurarlo mediante `LICENSE_VALIDATION_URL` en `.env`. En ese caso, el
  CLI puede usar tu endpoint en lugar de la verificación pública.

Servicio de validación local (ejemplo)
- Este repositorio incluye un ejemplo de servicio de validación en `inspector/license_server.py`.
  - Por defecto el servicio lee `inspector/licenses_db.json` y responde en `/verify`.
  - Para usarlo, ejecuta:

    python -m inspector.license_server

  - Prueba local (cliente):

    curl -X POST -d "license_key=TEST-LOCAL-KEY&product_id=TU_PRODUCT_ID_DE_GUMROAD" http://localhost:5000/verify

  - Para producción, habilita reenvío a Gumroad (si lo deseas) estableciendo
    `LICENSE_USE_GUMROAD=true` en el entorno del servicio.

  Autenticación (API key)
  - El servicio puede protegerse con una API key configurando la variable
    `LICENSE_SERVER_API_KEY` en el entorno del servicio. Si está configurada,
    todas las peticiones POST a `/verify` deben incluir el header
    `X-API-KEY: <tu_api_key>` o `api_key` en el body/form.

    Ejemplo con curl usando la API key definida en el compose (`test_local_key_please_change`):

      curl -X POST -H "X-API-KEY: test_local_key_please_change" -d "license_key=TEST-LOCAL-KEY&product_id=TU_PRODUCT_ID_DE_GUMROAD" http://localhost:5000/verify

    - Para producción: usa una clave fuerte, ejecuta el servicio detrás de HTTPS,
      y limita el acceso por IP o autenticación adicional.

Notas de seguridad
- Este servicio es un ejemplo para demos y control básico; para un despliegue
  en producción deberías:
  - Proteger el endpoint con autenticación (API key/IP allowlist).
  - Usar HTTPS y WAF/Rate limiting.
  - Mantener un proceso de revocación y auditoría de keys.

Notas de seguridad
- El mecanismo actual usa la API pública de verificación de Gumroad si no se configura
  `LICENSE_VALIDATION_URL`. Eso evita incluir secretos en el cliente. Si necesitas
  una solución más segura, implementa un servicio de validación en tu infraestructura
  que mantenga control sobre keys y revocación.
