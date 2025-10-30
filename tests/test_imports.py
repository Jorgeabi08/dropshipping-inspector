import unittest

class ImportTests(unittest.TestCase):
    def test_scraper_imports(self):
        # Verifica que los módulos y clases se puedan importar
        from inspector.scrapers.amazon import AmazonScraper
        from inspector.scrapers.mercadolibre import MercadoLibreScraper
        from inspector.scrapers.aliexpress import AliExpressScraper
        a = AmazonScraper(use_proxies=False)
        m = MercadoLibreScraper(use_proxies=False)
        e = AliExpressScraper(use_proxies=False)
        self.assertIsNotNone(a)
        self.assertIsNotNone(m)
        self.assertIsNotNone(e)

    def test_proxy_manager(self):
        from inspector.utils.proxy_manager import ProxyManager, Proxy
        pm = ProxyManager()
        # Usar estado en memoria para test
        pm.proxies = []
        pm.add_proxy(Proxy(host='127.0.0.1', port=8080))
        self.assertGreaterEqual(len(pm.proxies), 1)
        p = pm.get_proxy()
        # get_proxy puede devolver None si cooldown y tiempos bloquean,
        # pero no debe lanzar excepción
        try:
            _ = p.url if p else None
        except Exception as e:
            self.fail(f'Proxy access raised: {e}')

if __name__ == '__main__':
    unittest.main()
