import requests
from bs4 import BeautifulSoup
from typing import List, Optional, Dict
from time import sleep
import re
from .base import BaseScraper, Product
import random
import json
from datetime import datetime
import logging
from urllib.parse import urlencode, quote_plus

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AmazonScraper(BaseScraper):
    """Scraper específico para Amazon con mejoras anti-detección"""
    
    def __init__(self, marketplace: str = "amazon.com", sleep_between: float = 5.0, use_proxies: bool = False):
        super().__init__(sleep_between, use_proxies)
        self.marketplace = marketplace
        self.base_url = f"https://www.{marketplace}"
        
        # Headers más realistas con variaciones de navegador
        self.default_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Sec-CH-UA-Full-Version": '"99.0.4844.51"',
            "viewport-width": "1920",
            "device-memory": "8",
        }
        
        # User agents más actualizados y variados
        self.user_agents = [
            # Chrome en Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36",
            # Firefox en Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0",
            # Safari en MacOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
            # Edge en Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36 Edg/94.0.992.47",
            # Chrome en MacOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
            # Firefox en Linux
            "Mozilla/5.0 (X11; Linux x86_64; rv:93.0) Gecko/20100101 Firefox/93.0"
        ]
        
        # Configuración de reintento adaptativo
        self.retry_delays = [1, 2, 4, 8, 16]  # Retrasos exponenciales
        self.max_retries = 5
        
    def _get_headers(self) -> Dict[str, str]:
        """Genera headers realistas y diferentes para cada petición"""
        headers = self.default_headers.copy()
        headers["User-Agent"] = random.choice(self.user_agents)
        
        # Añadir variación realista
        if random.random() < 0.3:  # 30% de las veces
            headers["DNT"] = "1"
        
        if random.random() < 0.5:  # 50% de las veces
            headers["Pragma"] = "no-cache"
        
        return headers
    
    def _get_random_delay(self) -> float:
        """Genera un retraso aleatorio pero realista entre peticiones"""
        base_delay = self.sleep_between
        # Añadir variación aleatoria de ±30%
        variation = random.uniform(-0.3, 0.3)
        return max(0.5, base_delay * (1 + variation))
    
    def _clean_price(self, price_str: str) -> float:
        """Limpia y convierte el string de precio a float"""
        try:
            # Manejar diferentes formatos de precio
            price_str = price_str.replace(',', '').replace('$', '')
            # Buscar el primer número que parezca un precio
            matches = re.findall(r'\d+\.?\d*', price_str)
            if matches:
                return float(matches[0])
            return 0.0
        except (ValueError, TypeError, AttributeError):
            return 0.0
    
    def _extract_product_id(self, url: str) -> Optional[str]:
        """Extrae el ID del producto de una URL de Amazon"""
        patterns = [
            r'/dp/([A-Z0-9]{10})/?',
            r'/product/([A-Z0-9]{10})/?',
            r'/gp/product/([A-Z0-9]{10})/?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def _build_search_url(self, query: str, page: int = 1) -> str:
        """Construye una URL de búsqueda válida"""
        params = {
            'k': query,
            'ref': f'sr_pg_{page}',
            'page': page,
            '_encoding': 'UTF8',
            'sprefix': f'{quote_plus(query)},aps',
            'crid': f'{random.randint(100000000, 999999999)}',
        }
        
        # Añadir parámetros adicionales que hacen la búsqueda más realista
        if random.random() < 0.5:
            params['qid'] = datetime.now().strftime('%Y%m%d%H%M%S')
        
        return f"{self.base_url}/s?{urlencode(params)}"
    
    def _warmup_session(self):
        """Realiza algunas peticiones preliminares para simular comportamiento de navegador"""
        urls = [
            self.base_url,  # Página principal
            f"{self.base_url}/gp/bestsellers",  # Best Sellers
            f"{self.base_url}/gp/help/customer/display.html"  # Página de ayuda
        ]
        
        logger.info("Iniciando fase de calentamiento...")
        for url in urls:
            try:
                headers = self._get_headers()
                session = self._get_session()
                response = session.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    logger.debug(f"Calentamiento exitoso para: {url}")
                    # Guardar cookies importantes si la sesión soporta cookies
                    try:
                        session.cookies.update(response.cookies)
                    except Exception:
                        pass
                sleep(self._get_random_delay() * 2)  # Espera más larga entre peticiones de warmup
            except Exception as e:
                logger.warning(f"Error en calentamiento: {e}")
                continue
        logger.info("Calentamiento completado")

    def _make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """Realiza una petición HTTP con reintentos y manejo de errores"""
        headers = self._get_headers()
        session = self._get_session()
        
        # Realizar calentamiento solo en la primera petición
        if not hasattr(self, '_warmed_up'):
            self._warmup_session()
            self._warmed_up = True
        
        for i, delay in enumerate(self.retry_delays):
            try:
                response = session.request(
                    method,
                    url,
                    headers=headers,
                    timeout=10,
                    **kwargs
                )
                
                # Verificar si fuimos bloqueados o redirigidos a un captcha
                if "robot" in response.text.lower() or "captcha" in response.text.lower():
                    logger.warning(f"Detectado como bot en el intento {i+1}")
                    sleep(delay)
                    continue
                
                response.raise_for_status()
                return response
                
            except requests.RequestException as e:
                logger.warning(f"Error en la petición (intento {i+1}): {e}")
                if i == len(self.retry_delays) - 1:  # Último intento
                    logger.error(f"Error final después de {len(self.retry_delays)} intentos: {e}")
                    return None
                sleep(delay)
        
        return None

    def search_products(self, query: str, limit: int = 20) -> List[Product]:
        """Busca productos en Amazon con mejor manejo de errores y anti-detección"""
        results = []
        page = 1
        
        while len(results) < limit:
            url = self._build_search_url(query, page)
            logger.info(f"Buscando en página {page}: {url}")
            
            response = self._make_request(url)
            if not response:
                break
                
            soup = BeautifulSoup(response.text, "lxml")
            
            # Detectar página sin resultados
            no_results = soup.select_one("div.s-no-results-result-box-text")
            if no_results:
                logger.info("No se encontraron más resultados")
                break
            
            # Diferentes selectores para productos (Amazon cambia su HTML frecuentemente)
            product_selectors = [
                "div.s-result-item[data-component-type='s-search-result']",
                "div.sg-col-4-of-12.s-result-item",
                "div.sg-col-4-of-16.s-result-item",
            ]
            
            products = []
            for selector in product_selectors:
                products = soup.select(selector)
                if products:
                    break
            
            if not products:
                logger.warning("No se encontraron productos en la página")
                break
            
            for product in products:
                if len(results) >= limit:
                    break
                
                try:
                    # Título del producto (múltiples selectores)
                    title = None
                    for title_selector in ["h2 span.a-text-normal", "span.a-text-normal", "h2.a-text-normal"]:
                        title_elem = product.select_one(title_selector)
                        if title_elem:
                            title = title_elem.text.strip()
                            break
                    
                    if not title:
                        continue
                    
                    # URL del producto
                    url = None
                    url_elem = product.select_one("a.a-link-normal[href*='/dp/']")
                    if url_elem and 'href' in url_elem.attrs:
                        url = url_elem['href']
                        if not url.startswith('http'):
                            url = self.base_url + url
                    
                    if not url:
                        continue
                    
                    # Precio (múltiples formatos)
                    price = 0.0
                    price_whole = product.select_one("span.a-price-whole")
                    price_fraction = product.select_one("span.a-price-fraction")
                    
                    if price_whole:
                        price = self._clean_price(price_whole.text)
                        if price_fraction:
                            try:
                                price += float(f"0.{price_fraction.text}")
                            except ValueError:
                                pass
                    
                    # Imagen
                    image_url = None
                    img = product.select_one("img.s-image")
                    if img and 'src' in img.attrs:
                        image_url = img['src']
                    
                    # Rating
                    rating = None
                    rating_elem = product.select_one("i.a-icon-star-small, span.a-icon-alt")
                    if rating_elem:
                        try:
                            rating_text = rating_elem.text
                            rating = float(re.search(r'(\d+(\.\d+)?)', rating_text).group(1))
                        except (AttributeError, ValueError):
                            pass
                    
                    # Reviews
                    reviews_count = None
                    reviews_elem = product.select_one("span.a-size-base.s-underline-text")
                    if reviews_elem:
                        try:
                            reviews_count = int(reviews_elem.text.replace(",", ""))
                        except ValueError:
                            pass
                    
                    # Vendedor
                    seller = None
                    seller_elem = product.select_one("span.a-size-base.a-color-secondary")
                    if seller_elem:
                        seller = seller_elem.text.strip()
                    
                    # Prime
                    is_prime = bool(product.select_one("i.a-icon-prime"))
                    
                    # Envío
                    shipping_cost = None
                    shipping_elem = product.select_one("span.a-color-secondary:contains('shipping')")
                    if shipping_elem:
                        shipping_text = shipping_elem.text.strip()
                        if "FREE" not in shipping_text.upper():
                            shipping_cost = self._clean_price(shipping_text)
                    
                    product = Product(
                        title=title,
                        price=price,
                        currency="USD",  # TODO: Detectar moneda según marketplace
                        url=url,
                        image_url=image_url,
                        rating=rating,
                        reviews_count=reviews_count,
                        seller=seller,
                        shipping_cost=shipping_cost
                    )
                    
                    results.append(product)
                    logger.debug(f"Producto encontrado: {title}")
                
                except Exception as e:
                    logger.error(f"Error procesando producto: {e}")
                    continue
            
            page += 1
            delay = self._get_random_delay()
            logger.debug(f"Esperando {delay:.2f} segundos antes de la siguiente página")
            sleep(delay)
        
        return results[:limit]

    def get_product_details(self, url: str) -> Product:
        """Obtiene detalles completos de un producto con mejor manejo de errores"""
        logger.info(f"Obteniendo detalles del producto: {url}")
        
        # Extraer ID del producto
        product_id = self._extract_product_id(url)
        if not product_id:
            raise ValueError(f"No se pudo extraer el ID del producto de la URL: {url}")
        
        # Usar URL canónica
        url = f"{self.base_url}/dp/{product_id}"
        response = self._make_request(url)
        
        if not response:
            raise requests.RequestException("No se pudo obtener la página del producto")
        
        soup = BeautifulSoup(response.text, "lxml")
        
        # Título (múltiples selectores)
        title = None
        title_selectors = ["#productTitle", "#title", "h1.product-title"]
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.text.strip()
                break
        
        if not title:
            raise ValueError("No se pudo encontrar el título del producto")
        
        # Precio (múltiples formatos)
        price = 0.0
        price_selectors = [
            "#priceblock_ourprice",
            "#priceblock_saleprice",
            "#price_inside_buybox",
            "span.a-price span.a-offscreen",
            "span.a-color-price"
        ]
        
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price = self._clean_price(price_elem.text)
                if price > 0:
                    break
        
        # Descripción
        description = ""
        # 1. Descripción principal
        desc_elem = soup.select_one("#productDescription")
        if desc_elem:
            description = desc_elem.text.strip()
        
        # 2. Bullet points
        if not description:
            bullets = soup.select("#feature-bullets li")
            if bullets:
                description = "\n".join([b.text.strip() for b in bullets if not "hide" in b.get("class", [])])
        
        # 3. Detalles técnicos
        if not description:
            details = soup.select("#prodDetails .a-spacing-small")
            if details:
                description = "\n".join([d.text.strip() for d in details])
        
        # Imagen
        image_url = None
        img_selectors = [
            "#landingImage",
            "#imgBlkFront",
            "#main-image",
        ]
        for selector in img_selectors:
            img = soup.select_one(selector)
            if img:
                # Amazon guarda las URLs de imágenes en diferentes atributos
                for attr in ['src', 'data-old-hires', 'data-a-dynamic-image']:
                    if attr in img.attrs:
                        if attr == 'data-a-dynamic-image':
                            # Este atributo contiene un JSON con diferentes tamaños
                            try:
                                image_data = json.loads(img[attr])
                                image_url = max(image_data.items(), key=lambda x: int(x[1][0]))[0]
                                break
                            except json.JSONDecodeError:
                                continue
                        else:
                            image_url = img[attr]
                            break
                if image_url:
                    break
        
        # Vendedor
        seller = None
        seller_selectors = [
            "#sellerProfileTriggerId",
            "#merchant-info a",
            "span.author a",
            "a#bylineInfo"
        ]
        for selector in seller_selectors:
            seller_elem = soup.select_one(selector)
            if seller_elem:
                seller = seller_elem.text.strip()
                break
        
        # Rating
        rating = None
        rating_selectors = [
            "#acrPopover",
            "span.a-icon-alt",
            "#averageCustomerReviews .a-icon-star"
        ]
        for selector in rating_selectors:
            rating_elem = soup.select_one(selector)
            if rating_elem:
                try:
                    if 'title' in rating_elem.attrs:
                        rating_text = rating_elem['title']
                    else:
                        rating_text = rating_elem.text
                    rating = float(re.search(r'(\d+(\.\d+)?)', rating_text).group(1))
                    break
                except (AttributeError, ValueError):
                    continue
        
        # Reviews count
        reviews_count = None
        reviews_selectors = [
            "#acrCustomerReviewText",
            "#reviewsMedley .a-size-base"
        ]
        for selector in reviews_selectors:
            reviews_elem = soup.select_one(selector)
            if reviews_elem:
                try:
                    reviews_count = int(re.search(r'\d+', reviews_elem.text.replace(",", "")).group())
                    break
                except (AttributeError, ValueError):
                    continue
        
        # Stock
        stock = None
        stock_selectors = [
            "#availability",
            "#outOfStock",
            "#availabilityInsideBuyBox_feature_div"
        ]
        for selector in stock_selectors:
            stock_elem = soup.select_one(selector)
            if stock_elem:
                text = stock_elem.text.lower()
                if "out of stock" in text or "unavailable" in text:
                    stock = 0
                elif "in stock" in text:
                    stock_match = re.search(r'(\d+)', text)
                    stock = int(stock_match.group(1)) if stock_match else 1
                break
        
        # Shipping
        shipping_cost = None
        shipping_elem = soup.select_one("#price-shipping-message")
        if shipping_elem:
            text = shipping_elem.text.lower()
            if "free" not in text:
                shipping_match = re.search(r'\$\s*(\d+(\.\d{2})?)', text)
                if shipping_match:
                    shipping_cost = float(shipping_match.group(1))
        
        return Product(
            title=title,
            price=price,
            currency="USD",  # TODO: Detectar moneda según marketplace
            url=url,
            description=description,
            seller=seller,
            rating=rating,
            reviews_count=reviews_count,
            stock=stock,
            shipping_cost=shipping_cost,
            image_url=image_url
        )