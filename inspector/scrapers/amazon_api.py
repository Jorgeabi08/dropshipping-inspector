import boto3
from typing import List, Optional
from datetime import datetime
import logging
from botocore.config import Config
from .base import BaseScraper, Product

logger = logging.getLogger(__name__)

class AmazonAPIClient(BaseScraper):
    """Cliente de Amazon usando la API oficial de Product Advertising"""
    
    def __init__(self, marketplace: str = "amazon.com", region: str = "us-west-2"):
        super().__init__()
        self.marketplace = marketplace
        self.region = region
        
        # Credenciales de la API de Amazon (deben configurarse en variables de entorno)
        self.access_key = os.getenv("AMAZON_ACCESS_KEY")
        self.secret_key = os.getenv("AMAZON_SECRET_KEY")
        self.partner_tag = os.getenv("AMAZON_PARTNER_TAG")
        
        if not all([self.access_key, self.secret_key, self.partner_tag]):
            raise ValueError(
                "Se requieren las credenciales de Amazon PA-API. "
                "Configura AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY y AMAZON_PARTNER_TAG"
            )
        
        # Configurar el cliente de API
        self.client = boto3.client(
            'paapi5',
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(
                region_name=self.region,
                signature_version='v4',
                retries={
                    'max_attempts': 3,
                    'mode': 'standard'
                }
            )
        )
    
    def _convert_to_product(self, item: dict) -> Optional[Product]:
        """Convierte un resultado de la API a nuestro modelo de Product"""
        try:
            # Extraer precio
            price = 0.0
            if 'Offers' in item and 'Listings' in item['Offers']:
                price_info = item['Offers']['Listings'][0]['Price']
                if 'Amount' in price_info:
                    price = float(price_info['Amount'])
                    currency = price_info.get('Currency', 'USD')
            
            # Extraer rating y reviews
            rating = None
            reviews_count = None
            if 'CustomerReviews' in item:
                rating = float(item['CustomerReviews'].get('Rating', 0))
                reviews_count = int(item['CustomerReviews'].get('Count', 0))
            
            return Product(
                title=item.get('ItemInfo', {}).get('Title', {}).get('DisplayValue', ''),
                price=price,
                currency=currency,
                url=item.get('DetailPageURL', ''),
                image_url=item.get('Images', {}).get('Primary', {}).get('Large', {}).get('URL', ''),
                description=item.get('ItemInfo', {}).get('Features', {}).get('DisplayValues', [''])[0],
                seller=item.get('ItemInfo', {}).get('ByLineInfo', {}).get('Brand', ''),
                rating=rating,
                reviews_count=reviews_count
            )
        except Exception as e:
            logger.error(f"Error convirtiendo item: {e}")
            return None
    
    def search_products(self, query: str, limit: int = 20) -> List[Product]:
        """Busca productos usando la API de Amazon"""
        results = []
        page = 1
        items_per_page = min(10, limit)  # API limita a 10 items por petición
        
        try:
            while len(results) < limit:
                response = self.client.search_items(
                    Keywords=query,
                    Resources=[
                        'ItemInfo.Title',
                        'ItemInfo.Features',
                        'ItemInfo.ByLineInfo',
                        'Offers.Listings.Price',
                        'Images.Primary.Large',
                        'CustomerReviews',
                    ],
                    PartnerTag=self.partner_tag,
                    PartnerType='Associates',
                    Marketplace=self.marketplace,
                    ItemCount=items_per_page,
                    ItemPage=page
                )
                
                if 'Items' not in response:
                    break
                
                for item in response['Items']:
                    product = self._convert_to_product(item)
                    if product:
                        results.append(product)
                        if len(results) >= limit:
                            break
                
                if len(response['Items']) < items_per_page:
                    break
                    
                page += 1
                
        except Exception as e:
            logger.error(f"Error en búsqueda de Amazon: {e}")
        
        return results[:limit]
    
    def get_product_details(self, url: str) -> Product:
        """Obtiene detalles de un producto usando la API"""
        # Extraer ASIN de la URL
        asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
        if not asin_match:
            raise ValueError("No se pudo extraer el ASIN de la URL")
        
        asin = asin_match.group(1)
        
        try:
            response = self.client.get_items(
                ItemIds=[asin],
                Resources=[
                    'ItemInfo.Title',
                    'ItemInfo.Features',
                    'ItemInfo.ByLineInfo',
                    'ItemInfo.ContentInfo',
                    'ItemInfo.ProductInfo',
                    'Offers.Listings.Price',
                    'Offers.Listings.Availability',
                    'Images.Primary.Large',
                    'Images.Variants.Large',
                    'CustomerReviews',
                ],
                PartnerTag=self.partner_tag,
                PartnerType='Associates',
                Marketplace=self.marketplace
            )
            
            if 'Items' in response and response['Items']:
                product = self._convert_to_product(response['Items'][0])
                if product:
                    return product
            
            raise ValueError(f"No se encontró el producto con ASIN {asin}")
            
        except Exception as e:
            logger.error(f"Error obteniendo detalles del producto: {e}")
            raise