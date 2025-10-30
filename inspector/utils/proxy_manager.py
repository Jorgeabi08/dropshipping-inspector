import requests
from typing import List, Dict, Optional
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import os

@dataclass
class Proxy:
    """Clase para representar un proxy"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"
    last_used: datetime = datetime.now()
    fails: int = 0
    
    @property
    def url(self) -> str:
        """Retorna la URL del proxy en formato para requests"""
        auth = f"{self.username}:{self.password}@" if self.username and self.password else ""
        return f"{self.protocol}://{auth}{self.host}:{self.port}"
    
    def to_dict(self) -> dict:
        """Convierte el proxy a diccionario para requests"""
        return {self.protocol: self.url}

class ProxyManager:
    """Administrador de proxies con rotación y manejo de fallos"""
    
    def __init__(self, cooldown_minutes: int = 5, max_fails: int = 3):
        self.proxies: List[Proxy] = []
        self.cooldown = timedelta(minutes=cooldown_minutes)
        self.max_fails = max_fails
        self.cache_file = "proxy_cache.json"
        self._load_cache()
    
    def _load_cache(self):
        """Carga proxies desde el cache"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    for proxy_data in data:
                        proxy_data['last_used'] = datetime.fromisoformat(proxy_data['last_used'])
                        self.proxies.append(Proxy(**proxy_data))
            except (json.JSONDecodeError, KeyError):
                print("Error loading proxy cache")
    
    def _save_cache(self):
        """Guarda proxies en el cache"""
        try:
            data = []
            for proxy in self.proxies:
                proxy_dict = proxy.__dict__.copy()
                proxy_dict['last_used'] = proxy_dict['last_used'].isoformat()
                data.append(proxy_dict)
            
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving proxy cache: {e}")
    
    def add_proxy(self, proxy: Proxy):
        """Añade un nuevo proxy al pool"""
        self.proxies.append(proxy)
        self._save_cache()
    
    def add_proxies_from_list(self, proxy_list: List[str]):
        """Añade proxies desde una lista de strings en formato host:port"""
        for proxy_str in proxy_list:
            try:
                host, port = proxy_str.split(':')
                self.add_proxy(Proxy(host=host, port=int(port)))
            except ValueError:
                print(f"Invalid proxy format: {proxy_str}")
    
    def get_proxy(self) -> Optional[Proxy]:
        """Obtiene un proxy disponible"""
        now = datetime.now()
        available_proxies = [
            p for p in self.proxies
            if p.fails < self.max_fails and (now - p.last_used) > self.cooldown
        ]
        
        if not available_proxies:
            return None
            
        proxy = random.choice(available_proxies)
        proxy.last_used = now
        self._save_cache()
        return proxy
    
    def report_failure(self, proxy: Proxy):
        """Reporta un fallo en el proxy"""
        proxy.fails += 1
        self._save_cache()
    
    def report_success(self, proxy: Proxy):
        """Reporta un éxito en el proxy"""
        proxy.fails = 0
        self._save_cache()

class ProxySession(requests.Session):
    """Sesión de requests con soporte para proxies"""
    
    def __init__(self, proxy_manager: ProxyManager):
        super().__init__()
        self.proxy_manager = proxy_manager
        self.current_proxy = None
    
    def _get_new_proxy(self):
        """Obtiene un nuevo proxy y lo configura en la sesión"""
        self.current_proxy = self.proxy_manager.get_proxy()
        if self.current_proxy:
            self.proxies = self.current_proxy.to_dict()
        else:
            self.proxies = None
    
    def request(self, method, url, **kwargs):
        """Sobrescribe el método request para manejar proxies"""
        retries = 3
        last_exception = None
        
        for _ in range(retries):
            if not self.current_proxy:
                self._get_new_proxy()
            
            try:
                response = super().request(method, url, **kwargs)
                if response.status_code == 200:
                    if self.current_proxy:
                        self.proxy_manager.report_success(self.current_proxy)
                    return response
                elif response.status_code in [403, 407, 408, 429, 503]:
                    # Códigos que indican problemas con el proxy
                    raise requests.RequestException(f"Proxy error: {response.status_code}")
                else:
                    return response
                    
            except requests.RequestException as e:
                last_exception = e
                if self.current_proxy:
                    self.proxy_manager.report_failure(self.current_proxy)
                self.current_proxy = None
                
        raise last_exception if last_exception else requests.RequestException("All retries failed")