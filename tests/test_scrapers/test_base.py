import unittest
from datetime import datetime
from inspector.scrapers.base import Product, BaseScraper

class TestProduct(unittest.TestCase):
    """Test para la clase Product"""
    
    def test_product_creation(self):
        """Prueba la creación básica de un producto"""
        product = Product(
            title="Test Product",
            price=99.99,
            currency="USD",
            url="https://example.com/product"
        )
        
        self.assertEqual(product.title, "Test Product")
        self.assertEqual(product.price, 99.99)
        self.assertEqual(product.currency, "USD")
        self.assertEqual(product.url, "https://example.com/product")
        self.assertIsNone(product.description)
        self.assertIsNone(product.seller)
        self.assertIsInstance(product.scrape_date, datetime)

    def test_product_full_creation(self):
        """Prueba la creación de un producto con todos los campos"""
        product = Product(
            title="Test Product",
            price=99.99,
            currency="USD",
            url="https://example.com/product",
            image_url="https://example.com/image.jpg",
            description="Test description",
            seller="Test Seller",
            rating=4.5,
            reviews_count=100,
            shipping_cost=5.99,
            stock=10
        )
        
        self.assertEqual(product.image_url, "https://example.com/image.jpg")
        self.assertEqual(product.description, "Test description")
        self.assertEqual(product.seller, "Test Seller")
        self.assertEqual(product.rating, 4.5)
        self.assertEqual(product.reviews_count, 100)
        self.assertEqual(product.shipping_cost, 5.99)
        self.assertEqual(product.stock, 10)

class MockScraper(BaseScraper):
    """Implementación mock del scraper base para testing"""
    
    def search_products(self, query: str, limit: int = 20):
        return [
            Product(
                title=f"Test Product {i}",
                price=99.99,
                currency="USD",
                url=f"https://example.com/product/{i}"
            )
            for i in range(min(3, limit))
        ]
    
    def get_product_details(self, url: str):
        return Product(
            title="Test Product Details",
            price=99.99,
            currency="USD",
            url=url,
            description="Test description",
            seller="Test Seller"
        )

class TestBaseScraper(unittest.TestCase):
    """Test para la clase BaseScraper"""
    
    def setUp(self):
        self.scraper = MockScraper()
    
    def test_search_products(self):
        """Prueba la búsqueda de productos"""
        products = self.scraper.search_products("test")
        
        self.assertEqual(len(products), 3)
        self.assertIsInstance(products[0], Product)
        self.assertEqual(products[0].title, "Test Product 0")
    
    def test_get_product_details(self):
        """Prueba la obtención de detalles de un producto"""
        product = self.scraper.get_product_details("https://example.com/product/1")
        
        self.assertIsInstance(product, Product)
        self.assertEqual(product.title, "Test Product Details")
        self.assertEqual(product.description, "Test description")
        self.assertEqual(product.seller, "Test Seller")
    
    def test_export_to_csv(self):
        """Prueba la exportación a CSV"""
        import os
        import csv
        
        products = self.scraper.search_products("test")
        test_file = "test_export.csv"
        
        try:
            self.scraper.export_to_csv(products, test_file)
            
            # Verificar que el archivo existe
            self.assertTrue(os.path.exists(test_file))
            
            # Verificar el contenido del CSV
            with open(test_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                self.assertEqual(len(rows), 3)
                self.assertEqual(rows[0]['title'], "Test Product 0")
                self.assertEqual(rows[0]['price'], "99.99")
                self.assertEqual(rows[0]['currency'], "USD")
                
        finally:
            # Limpiar el archivo de prueba
            if os.path.exists(test_file):
                os.remove(test_file)

if __name__ == '__main__':
    unittest.main()