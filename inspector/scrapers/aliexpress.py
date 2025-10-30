import requests
from bs4 import BeautifulSoup
from typing import List
from time import sleep
import json
import re
from .base import BaseScraper, Product
import random

class AliExpressScraper(BaseScraper):
    """Scraper específico para AliExpress"""
    
    def __init__(self, sleep_between: float = 2.0, use_proxies: bool = False):
        super().__init__(sleep_between, use_proxies)
        self.base_url = "https://www.aliexpress.com"
        self.api_url = "https://www.aliexpress.com/fn/search-pc/index"
        # Rotación de User-Agents
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
        ]
        
    def _get_headers(self):
        """Obtiene headers aleatorios para cada petición"""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Referer": "https://www.aliexpress.com/",
        }

    def search_products(self, query: str, limit: int = 20) -> List[Product]:
        results = []
        page = 1
        
        while len(results) < limit:
            try:
                params = {
                    "searchText": query,
                    "page": page,
                    "pageSize": min(50, limit),  # AliExpress permite hasta 50 items por página
                }
                
                response = requests.get(
                    self.api_url,
                    params=params,
                    headers=self._get_headers(),
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                
                # Verificar si hay resultados
                products = data.get("items", [])
                if not products:
                    break
                
                for item in products:
                    if len(results) >= limit:
                        break
                        
                    try:
                        title = item.get("title", "").strip()
                        url = f"{self.base_url}/item/{item.get('productId')}.html"
                        
                        # Precio y moneda
                        price_info = item.get("price", {})
                        price = float(price_info.get("minAmount", {}).get("value", 0))
                        currency = price_info.get("minAmount", {}).get("currency", "USD")
                        
                        # Imagen
                        image_url = item.get("image", {}).get("imgUrl")
                        if image_url and not image_url.startswith("http"):
                            image_url = f"https:{image_url}"
                        
                        # Rating y reviews
                        rating = float(item.get("evaluation", {}).get("starRating", 0))
                        reviews_count = int(item.get("evaluation", {}).get("totalCount", 0))
                        
                        # Vendedor
                        seller = item.get("store", {}).get("storeName")
                        
                        if title and url:
                            product = Product(
                                title=title,
                                price=price,
                                currency=currency,
                                url=url,
                                image_url=image_url,
                                seller=seller,
                                rating=rating,
                                reviews_count=reviews_count
                            )
                            results.append(product)
                            
                    except (KeyError, ValueError, TypeError) as e:
                        print(f"Error procesando producto: {e}")
                        continue
                
                page += 1
                sleep(self.sleep_between)
                
            except requests.RequestException as e:
                print(f"Error en la solicitud: {e}")
                break
                
        return results[:limit]

    def get_product_details(self, url: str) -> Product:
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            
            # AliExpress usa mucho JavaScript, intentamos extraer los datos del script
            script_pattern = re.compile(r'window\._dida_config_\._init_data_\s*=\s*({.*?});', re.DOTALL)
            match = script_pattern.search(response.text)
            
            if not match:
                raise ValueError("No se pudieron encontrar los datos del producto")
                
            data = json.loads(match.group(1))
            product_data = data.get("data", {}).get("productInfo", {})
            
            # Extraer información
            title = product_data.get("subject", "")
            
            # Precio
            price_info = product_data.get("priceInfo", {})
            price = float(price_info.get("price", 0))
            currency = price_info.get("currency", "USD")
            
            # Descripción
            description = product_data.get("description", "")
            
            # Vendedor
            store_info = product_data.get("storeInfo", {})
            seller = store_info.get("storeName")
            
            # Rating y reviews
            evaluation = product_data.get("evaluation", {})
            rating = float(evaluation.get("starRating", 0))
            reviews_count = int(evaluation.get("totalCount", 0))
            
            # Stock
            stock = None
            inventory = product_data.get("inventory", {})
            if inventory:
                stock = int(inventory.get("totalQuantity", 0))
            
            # Imagen principal
            image_url = None
            images = product_data.get("imageInfo", {}).get("images", [])
            if images:
                image_url = images[0].get("url")
                if image_url and not image_url.startswith("http"):
                    image_url = f"https:{image_url}"
            
            return Product(
                title=title,
                price=price,
                currency=currency,
                url=url,
                description=description,
                seller=seller,
                rating=rating,
                reviews_count=reviews_count,
                stock=stock,
                image_url=image_url
            )
            
        except requests.RequestException as e:
            print(f"Error obteniendo detalles del producto: {e}")
            raise
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error procesando datos del producto: {e}")
            raise