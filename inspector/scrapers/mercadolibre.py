import requests
from bs4 import BeautifulSoup
from time import sleep
import random
import logging
import json
from typing import List, Optional, Dict, Union
from datetime import datetime
from .base import BaseScraper, Product
import re
from urllib.parse import urlencode, quote_plus

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MercadoLibreScraper(BaseScraper):
    """Scraper específico para MercadoLibre usando web scraping con soporte API para detalles"""
    
    def __init__(self, country_code: str = "MLM", sleep_between: float = 1.0, use_proxies: bool = False):
        super().__init__(sleep_between, use_proxies)
        self.country_code = country_code.upper()
        # En México y otros países la URL base es diferente
        if self.country_code == "MLM":
            self.base_url = "https://listado.mercadolibre.com.mx"
        elif self.country_code == "MLB":
            self.base_url = "https://lista.mercadolivre.com.br"
        else:
            country = self.country_code.lower()[2:]
            self.base_url = f"https://listado.mercadolibre.com.{country}"
        self.api_base_url = "https://api.mercadolibre.com"
        
        # Headers realistas
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Connection": "keep-alive",
            # Avoid 'br' (brotli) because the requests library does not
            # decode brotli by default and that can leave resp.text garbled.
            "Accept-Encoding": "gzip, deflate",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Cache-Control": "max-age=0",
        }
        
        # Endpoints de la API (para uso futuro)
        self.endpoints = {
            "search": f"/sites/{country_code}/search",
            "item": "/items",
            "category": f"/sites/{country_code}/categories",
        }
        
        # Cacheo de categorías y currencies
        self._categories_cache = {}
        self._currency_cache = self._get_currency_symbol(country_code)
        
    def _get_currency_symbol(self, country_code: str) -> str:
        """Retorna el símbolo de moneda según el país"""
        currencies = {
            "MLM": "MXN",  # Peso mexicano
            "MLA": "ARS",  # Peso argentino
            "MLB": "BRL",  # Real brasileño
            "MCO": "COP",  # Peso colombiano
            "MLC": "CLP",  # Peso chileno
            "MLU": "UYU",  # Peso uruguayo
            "MPE": "PEN",  # Sol peruano
            "MEC": "USD",  # Dólar (Ecuador)
            "MLV": "VES",  # Bolívar venezolano
            "MPA": "USD",  # Dólar (Panamá)
            "MRD": "DOP",  # Peso dominicano
        }
        return currencies.get(country_code, "USD")
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Dict:
        """Realiza una petición a la API con reintentos"""
        session = self._get_session()
        retries = 3
        last_error = None
        
        for attempt in range(retries):
            try:
                response = session.get(
                    url,
                    params=params,
                    headers=self.api_headers,
                    timeout=10
                )
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                last_error = e
                if attempt < retries - 1:
                    sleep_time = self.sleep_between * (attempt + 1)
                    logger.warning(f"Intento {attempt + 1} falló, esperando {sleep_time}s: {e}")
                    sleep(sleep_time)
                continue
        
        raise last_error or Exception("Error desconocido en la petición")
    
    def get_categories(self) -> Dict[str, str]:
        """Obtiene las categorías disponibles para el país"""
        if self._categories_cache:
            return self._categories_cache
            
        url = f"{self.api_base_url}{self.endpoints['category']}"
        try:
            data = self._make_request(url)
            if isinstance(data, list):
                categories = {cat.get('name'): cat.get('id') for cat in data}
            elif isinstance(data, dict):
                items = data.get('results') or data.get('categories') or []
                categories = {cat.get('name'): cat.get('id') for cat in items}
            self._categories_cache = categories
            return categories
        except Exception as e:
            logger.error(f"Error obteniendo categorías: {e}")
            return {}

    def search_products(self, query: str, limit: int = 20) -> List[Product]:
        """Busca productos usando web scraping"""
        results = []
        page = 1
        
        while len(results) < limit:
            try:
                url = f"{self.base_url}/{quote_plus(query)}_Desde_{50*(page-1)+1}"
                logger.info(f"Buscando '{query}' (página {page})")
                
                session = self._get_session()
                response = session.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, "lxml")
                
                # MercadoLibre usa diferentes clases según el país/versión
                selectors = [
                    "li.ui-search-layout__item",  # Nuevo diseño
                    "div.ui-search-result",       # Diseño alternativo
                    "li.results-item"             # Diseño clásico
                ]
                
                items = []
                for selector in selectors:
                    items = soup.select(selector)
                    if items:
                        break
                
                # Si no encontramos items con los selectores principales,
                # intentar con los nuevos selectores de diseño 2023
                if not items:
                    logger.debug("Intentando selectores alternativos...")
                    items = soup.select("div[class*='ui-search-layout__item']")
                
                if not items:
                    logger.warning("No se encontraron items en la página")
                    # Debug: guardar HTML para análisis
                    with open("debug_ml.html", "w", encoding="utf-8") as f:
                        f.write(response.text)
                    logger.debug(f"HTML guardado en debug_ml.html")
                    break
                
                for item in items:
                    if len(results) >= limit:
                        break
                        
                    try:
                        # Título (múltiples selectores)
                        # Títulos: incluir selectores del nuevo diseño (poly-*) y viejos
                        title_selectors = [
                            "a.poly-component__title",
                            ".poly-component__title",
                            "h3.poly-component__title-wrapper a",
                            ".ui-search-item__title",
                            "h2.ui-search-item__title",
                            "span.main-title"
                        ]
                        title = None
                        for selector in title_selectors:
                            title_elem = item.select_one(selector)
                            if title_elem:
                                title = title_elem.text.strip()
                                break
                        
                        if not title:
                            continue
                        
                        # Precio y moneda
                        # Precio: admitir andes-money-amount used en el diseño actual
                        price_elem = item.select_one(
                            ".price-tag-fraction, .price__fraction, .andes-money-amount__fraction"
                        )
                        price = 0.0
                        if price_elem:
                            # Normalizar: eliminar caracteres no numéricos excepto dot/comma
                            raw = price_elem.text.strip().replace('.', '').replace(',', '')
                            try:
                                price = float(raw)
                            except ValueError:
                                price = 0.0

                        currency_elem = item.select_one(
                            ".price-tag-symbol, .andes-money-amount__currency-symbol"
                        )
                        currency = currency_elem.text.strip() if currency_elem else self._currency_cache
                        
                        # URL y imagen
                        # URL: preferir el enlace del título (poly-component__title) o el primer enlace
                        link = item.select_one("a.poly-component__title, a[href*='/MLM-'], a")
                        if not link or not link.has_attr('href'):
                            continue
                        url = link['href']
                        
                        img = item.select_one("img.ui-search-result-image__element, img.poly-component__picture")
                        image_url = img['src'] if img and img.has_attr('src') else None
                        
                        # Vendedor (cuando está disponible)
                        seller_elem = item.select_one(".ui-search-official-store-label, .poly-component__seller")
                        seller = seller_elem.text.strip() if seller_elem else None
                        
                        # Envío gratis
                        shipping_elem = item.select_one(".ui-search-item__shipping, .poly-component__shipping")
                        shipping_cost = 0.0 if shipping_elem and "gratis" in shipping_elem.text.lower() else None
                        
                        product = Product(
                            title=title,
                            price=price,
                            currency=currency,
                            url=url,
                            image_url=image_url,
                            seller=seller,
                            shipping_cost=shipping_cost
                        )
                        results.append(product)
                        
                    except (AttributeError, KeyError, ValueError) as e:
                        logger.error(f"Error procesando item: {e}")
                        continue
                
                page += 1
                sleep(self.sleep_between)
                
            except Exception as e:
                logger.error(f"Error en la búsqueda: {e}")
                break
        
        return results[:limit]

    def get_product_details(self, url: str) -> Product:
        """Obtiene detalles de un producto usando web scraping"""
        try:
            session = self._get_session()
            response = session.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            
            # Título
            title = ""
            title_elem = soup.select_one("h1.ui-pdp-title")
            if title_elem:
                title = title_elem.text.strip()
            
            # Precio
            price = 0.0
            currency = self._currency_cache
            price_elem = soup.select_one(".ui-pdp-price__second-line .andes-money-amount__fraction")
            if price_elem:
                try:
                    price = float(price_elem.text.replace(',', ''))
                except ValueError:
                    pass
            
            currency_elem = soup.select_one(".ui-pdp-price__second-line .andes-money-amount__currency-symbol")
            if currency_elem:
                currency = currency_elem.text.strip()
            
            # Descripción
            description = None
            desc_elem = soup.select_one(".ui-pdp-description__content")
            if desc_elem:
                description = desc_elem.text.strip()
            
            # Vendedor
            seller = None
            seller_elem = soup.select_one(".ui-pdp-seller__link-trigger")
            if seller_elem:
                seller = seller_elem.text.strip()
            
            # Rating y reviews
            rating = None
            reviews_count = None
            rating_elem = soup.select_one(".ui-pdp-reviews__rating__summary__average")
            if rating_elem:
                try:
                    rating = float(rating_elem.text)
                except ValueError:
                    pass
            
            reviews_elem = soup.select_one(".ui-pdp-reviews__amount")
            if reviews_elem:
                try:
                    reviews_count = int(re.search(r'\d+', reviews_elem.text).group())
                except (AttributeError, ValueError):
                    pass
            
            # Imagen
            image_url = None
            img = soup.select_one(".ui-pdp-gallery__figure img")
            if img and img.has_attr('src'):
                image_url = img['src']
            
            # Envío
            shipping_cost = None
            shipping_elem = soup.select_one(".ui-pdp-media__title")
            if shipping_elem and "gratis" in shipping_elem.text.lower():
                shipping_cost = 0.0
            
            # Stock
            stock = None
            stock_elem = soup.select_one(".ui-pdp-buybox__quantity__available")
            if stock_elem:
                try:
                    stock = int(re.search(r'\d+', stock_elem.text).group())
                except (AttributeError, ValueError):
                    pass
            
            return Product(
                title=title,
                price=price,
                currency=currency,
                url=url,
                description=description,
                image_url=image_url,
                seller=seller,
                rating=rating,
                reviews_count=reviews_count,
                shipping_cost=shipping_cost,
                stock=stock
            )
            
        except Exception as e:
            logger.error(f"Error obteniendo detalles del producto: {e}")
            raise