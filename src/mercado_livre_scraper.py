"""
Mercado Livre scraper module for Web Scraping Project
Uses public API (https://api.mercadolibre.com) for product searches
"""

import requests
from typing import List, Optional, Dict
from datetime import datetime
from .logger import get_logger
from .utils import retry_with_backoff, delay_random
from .output_handler import ScrapingResult

logger = get_logger(__name__)


class MercadoLivreScraper:
    """
    Scraper for Mercado Livre using public API
    
    Features:
    - Free public API (no authentication required)
    - Automatic retry with backoff
    - Rate limiting between requests
    - Brazilian marketplace (site ML Brasil)
    """
    
    BASE_URL = "https://api.mercadolibre.com/sites/MLB/search"
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    REQUEST_TIMEOUT = 15  # seconds
    
    def __init__(self, limit: int = 10):
        """
        Initialize Mercado Livre scraper.
        
        Args:
            limit: Maximum results per query (default 10)
        """
        self.limit = min(limit, 50)  # ML API max is 50
    
    def search_product(self, query: str) -> List[ScrapingResult]:
        """
        Search for product on Mercado Livre API.
        
        Args:
            query: Product search query
        
        Returns:
            List of ScrapingResult objects
        """
        def _fetch():
            logger.debug(f"Buscando em Mercado Livre: {query}")
            
            params = {
                'q': query,
                'limit': self.limit,
                'sort': 'price_asc'  # Sort by lowest price
            }
            
            response = requests.get(
                self.BASE_URL,
                params=params,
                headers=self.HEADERS,
                timeout=self.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            return response.json()
        
        try:
            # Retry with backoff
            data = retry_with_backoff(
                _fetch,
                max_attempts=3,
                initial_delay=1.0
            )
            
            results = self._parse_results(data, query)
            logger.info(f"✓ {len(results)} resultados encontrados em Mercado Livre: {query}")
            
            return results
        
        except Exception as e:
            logger.error(f"❌ Erro ao buscar em Mercado Livre '{query}': {str(e)}")
            return []
    
    def _parse_results(self, data: Dict, query: str) -> List[ScrapingResult]:
        """
        Parse API response and extract products.
        
        Args:
            data: API response data
            query: Original search query
        
        Returns:
            List of ScrapingResult objects
        """
        results = []
        
        try:
            items = data.get('results', [])
            
            for item in items[:self.limit]:
                try:
                    # Extract product information
                    title = item.get('title', 'N/A')
                    price = item.get('price')
                    link = item.get('permalink', 'N/A')
                    
                    # Create result
                    result = ScrapingResult(
                        query=title,
                        preco=float(price) if price else None,
                        link=link,
                        plataforma="Mercado Livre",
                        timestamp=datetime.now().isoformat()
                    )
                    results.append(result)
                
                except Exception as e:
                    logger.debug(f"Erro ao processar item: {str(e)}")
                    continue
        
        except Exception as e:
            logger.error(f"Erro ao parsear resultados: {str(e)}")
        
        return results
    
    def search_multiple(self, queries: List[str]) -> List[ScrapingResult]:
        """
        Search multiple products.
        
        Args:
            queries: List of search queries
        
        Returns:
            List of all ScrapingResult objects
        """
        all_results = []
        
        for i, query in enumerate(queries):
            try:
                results = self.search_product(query)
                all_results.extend(results)
                
                # Rate limiting - random delay between requests
                if i < len(queries) - 1:  # Don't delay after last query
                    delay_random(0.5, 1.5)
            
            except Exception as e:
                logger.error(f"Erro ao processar query {i+1}/{len(queries)}: {str(e)}")
                continue
        
        return all_results


def scrape_mercado_livre(queries: List[str], limit: int = 10) -> List[ScrapingResult]:
    """
    Scrape multiple products from Mercado Livre.
    
    Args:
        queries: List of search queries
        limit: Maximum results per query
    
    Returns:
        List of ScrapingResult objects
    
    Example:
        >>> results = scrape_mercado_livre(['Luva correr', 'Meia algodão'])
        >>> for r in results:
        ...     print(f"{r.query}: R$ {r.preco}")
    """
    scraper = MercadoLivreScraper(limit=limit)
    return scraper.search_multiple(queries)


# Test function
def test_mercado_livre_api():
    """Test the Mercado Livre API connection"""
    logger.info("Testando conexão com API Mercado Livre...")
    
    try:
        scraper = MercadoLivreScraper()
        results = scraper.search_product("Luva correr")
        
        if results:
            logger.info(f"✓ Teste bem-sucedido! Encontrados {len(results)} produtos")
            for result in results[:3]:
                logger.info(f"  - {result.query[:50]}... R$ {result.preco}")
        else:
            logger.warning("⚠️ Nenhum resultado encontrado no teste")
    
    except Exception as e:
        logger.error(f"❌ Erro no teste: {str(e)}")
