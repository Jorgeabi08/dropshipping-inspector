from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import requests
import csv
from ..utils.proxy_manager import ProxyManager, ProxySession

@dataclass
class Product:
    """Clase que representa un producto encontrado"""
    title: str
    price: float
    currency: str
    url: str
    image_url: Optional[str] = None
    description: Optional[str] = None
    seller: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    shipping_cost: Optional[float] = None
    stock: Optional[int] = None
    scrape_date: datetime = field(default_factory=datetime.now)

class BaseScraper(ABC):
    """Clase base abstracta para todos los scrapers"""
    
    def __init__(self, sleep_between: float = 1.0, use_proxies: bool = False):
        self.sleep_between = sleep_between
        self.proxy_manager = ProxyManager() if use_proxies else None
        self.session = ProxySession(self.proxy_manager) if use_proxies else None
        
        # Headers base que pueden ser sobreescritos por las implementaciones
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    def _get_session(self):
        """Retorna la sesión apropiada (con o sin proxies)"""
        return self.session if self.session else requests
    
    @abstractmethod
    def search_products(self, query: str, limit: int = 20) -> List[Product]:
        """Busca productos y retorna una lista de resultados"""
        pass

    @abstractmethod
    def get_product_details(self, url: str) -> Product:
        """Obtiene detalles completos de un producto específico"""
        pass

    def export_to_csv(self, products: List[Product], filename: str):
        """Exporta la lista de productos a un archivo CSV"""
        if not products:
            return
            
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            # Obtener todos los campos de la clase Product
            fields = [field for field in Product.__dataclass_fields__]
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            
            for product in products:
                # Convertir datetime a string para CSV
                product_dict = product.__dict__.copy()
                if isinstance(product_dict['scrape_date'], datetime):
                    product_dict['scrape_date'] = product_dict['scrape_date'].isoformat()
                writer.writerow(product_dict)

    def add_proxy(self, host: str, port: int, username: Optional[str] = None, 
                 password: Optional[str] = None, protocol: str = "http"):
        """Añade un proxy al pool de proxies"""
        if self.proxy_manager:
            from ..utils.proxy_manager import Proxy
            self.proxy_manager.add_proxy(Proxy(
                host=host,
                port=port,
                username=username,
                password=password,
                protocol=protocol
            ))

    def add_proxies_from_list(self, proxy_list: List[str]):
        """Añade una lista de proxies en formato host:port"""
        if self.proxy_manager:
            self.proxy_manager.add_proxies_from_list(proxy_list)