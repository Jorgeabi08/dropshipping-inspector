"""Demo para ProxyManager sin realizar peticiones externas.
Muestra add/get/report_success/report_failure.
"""
from inspector.utils.proxy_manager import ProxyManager, Proxy


def demo():
    pm = ProxyManager()
    # Limpiar proxies existentes en cache durante demo (no destructivo en disco)
    pm.proxies = []

    # Añadir proxies de ejemplo (no funcionales) para demostrar la rotación
    p1 = Proxy(host='192.0.2.1', port=8080)
    p2 = Proxy(host='198.51.100.2', port=3128)
    pm.add_proxy(p1)
    pm.add_proxy(p2)

    print('Proxies añadidos:', [p.url for p in pm.proxies])

    p = pm.get_proxy()
    print('Proxy obtenido:', p.url if p else None)

    if p:
        print('Reportando fallo en proxy...')
        pm.report_failure(p)
        print('Fails del proxy:', p.fails)

    # Forzar éxito en siguiente proxy
    p_next = pm.get_proxy()
    if p_next:
        pm.report_success(p_next)
        print('Proxy siguiente marcado como success, fails:', p_next.fails)


if __name__ == '__main__':
    demo()
