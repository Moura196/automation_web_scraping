"""
Google Shopping scraper module for Web Scraping Project
Uses Playwright for automated browsing and product data extraction
"""

import asyncio
from typing import List, Optional, Dict
from datetime import datetime
from .logger import get_logger
from .utils import retry_decorator, delay_random
from .output_handler import ScrapingResult

logger = get_logger(__name__)

# Try to import Playwright, but make it optional for initial setup
try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("⚠️ Playwright não instalado. Install com: pip install playwright")


class GoogleShoppingScraper:
    """
    Scraper for Google Shopping using Playwright
    
    Features:
    - Realistic headers and user agent
    - Automatic retry with exponential backoff
    - Rate limiting between requests
    - CloudFlare and bot detection handling
    """
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    BASE_URL = "https://shopping.google.com/search"
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize Google Shopping scraper.
        
        Args:
            headless: Run browser in headless mode (no GUI)
            timeout: Page load timeout in milliseconds
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright não está instalado. Execute: pip install playwright")
        
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def initialize(self):
        """Initialize browser and page"""
        try:
            logger.info("Inicializando Playwright...")
            self.playwright = await async_playwright().start()
            
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )
            
            self.page = await self.browser.new_page()
            self.page.set_default_timeout(self.timeout)
            
            # Set viewport for mobile-like experience to avoid blocks
            await self.page.set_viewport_size({"width": 1280, "height": 720})
            
            logger.info("✓ Playwright inicializado")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Playwright: {str(e)}")
            raise
    
    async def close(self):
        """Close browser and cleanup"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            logger.info("✓ Playwright encerrado")
        except Exception as e:
            logger.error(f"❌ Erro ao fechar Playwright: {str(e)}")
    
    @retry_decorator(max_attempts=3, initial_delay=1.0, backoff_factor=2.0)
    async def search_product(self, query: str) -> List[ScrapingResult]:
        """
        Search for product on Google Shopping.
        
        Args:
            query: Product search query
        
        Returns:
            List of ScrapingResult objects
        
        Raises:
            Exception: If search fails after retries
        """
        if not self.page:
            raise RuntimeError("Browser não inicializado. Chame initialize() primeiro.")
        
        try:
            logger.debug(f"Buscando: {query}")
            
            # Navigate to Google Shopping search
            search_url = f"{self.BASE_URL}?q={query.replace(' ', '+')}"
            await self.page.goto(search_url, wait_until="load")
            
            # Add random delay to avoid detection
            delay_random(0.5, 2.0)
            
            # Wait for products to load
            await self.page.wait_for_selector('[data-item-id]', timeout=10000)
            
            # Extract product data
            results = await self._extract_products()
            
            logger.info(f"✓ {len(results)} resultados encontrados para: {query}")
            return results
        
        except Exception as e:
            logger.error(f"❌ Erro ao buscar {query}: {str(e)}")
            raise
    
    async def _extract_products(self) -> List[ScrapingResult]:
        """
        Extract product information from current page.
        
        Returns:
            List of ScrapingResult objects
        """
        results = []
        
        try:
            # Get all product containers
            products = await self.page.query_selector_all('[data-item-id]')
            logger.debug(f"Encontrados {len(products)} produtos no DOM")
            
            for product in products[:10]:  # Limit to first 10 results
                try:
                    # Extract title
                    title_elem = await product.query_selector('h2')
                    title = await title_elem.text_content() if title_elem else "N/A"
                    
                    # Extract price
                    price_elem = await product.query_selector('[role="text"]')
                    price_text = await price_elem.text_content() if price_elem else "N/A"
                    
                    # Try to parse price
                    price = self._parse_price(price_text)
                    
                    # Extract link
                    link_elem = await product.query_selector('a[href]')
                    link = await link_elem.get_attribute('href') if link_elem else "N/A"
                    
                    # Create result
                    result = ScrapingResult(
                        query=title.strip() if title else "N/A",
                        preco=price,
                        link=link,
                        plataforma="Google Shopping",
                        timestamp=datetime.now().isoformat()
                    )
                    results.append(result)
                
                except Exception as e:
                    logger.debug(f"Erro ao extrair produto: {str(e)}")
                    continue
        
        except Exception as e:
            logger.error(f"Erro ao extrair produtos: {str(e)}")
        
        return results
    
    @staticmethod
    def _parse_price(price_text: str) -> Optional[float]:
        """
        Parse price from text.
        
        Args:
            price_text: Price text (e.g., "R$ 29,90")
        
        Returns:
            Float price or None if parsing fails
        """
        try:
            import re
            # Remove non-numeric characters except decimal/comma
            cleaned = re.sub(r'[^\d,.]', '', price_text)
            # Handle Portuguese decimal format
            if ',' in cleaned:
                cleaned = cleaned.replace('.', '').replace(',', '.')
            return float(cleaned) if cleaned else None
        except Exception:
            return None


async def scrape_google_shopping(queries: List[str], headless: bool = True) -> List[ScrapingResult]:
    """
    Scrape multiple products from Google Shopping.
    
    Args:
        queries: List of search queries
        headless: Run browser headless
    
    Returns:
        List of ScrapingResult objects
    
    Example:
        >>> results = await scrape_google_shopping(['Luva correr', 'Meia algodão'])
        >>> for r in results:
        ...     print(f"{r.query}: R$ {r.preco}")
    """
    scraper = GoogleShoppingScraper(headless=headless)
    results = []
    
    try:
        await scraper.initialize()
        
        for query in queries:
            try:
                query_results = await scraper.search_product(query)
                results.extend(query_results)
            except Exception as e:
                logger.error(f"Falha em: {query}")
                continue
    
    finally:
        await scraper.close()
    
    return results


def scrape_google_shopping_sync(queries: List[str], headless: bool = True) -> List[ScrapingResult]:
    """
    Synchronous wrapper for scraping Google Shopping.
    
    Args:
        queries: List of search queries
        headless: Run browser headless
    
    Returns:
        List of ScrapingResult objects
    """
    return asyncio.run(scrape_google_shopping(queries, headless=headless))
