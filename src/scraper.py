"""
Main scraper orchestrator for Web Scraping Project
Coordinates multiple scrapers with fallback strategy
"""

from typing import List, Optional, Callable
from .logger import get_logger
from .output_handler import ScrapingResult
from .mercado_livre_scraper import scrape_mercado_livre, MercadoLivreScraper
from .utils import delay_random

logger = get_logger(__name__)

# Try to import Google Shopping scraper (optional, requires Playwright)
try:
    from .google_shopping_scraper import scrape_google_shopping_sync
    GOOGLE_SHOPPING_AVAILABLE = True
except ImportError:
    GOOGLE_SHOPPING_AVAILABLE = False
    logger.warning("⚠️ Google Shopping scraper não disponível (Playwright não instalado)")


class ScraperOrchestrator:
    """
    Main orchestrator for web scraping operations
    
    Strategy:
    1. Primary: Google Shopping (Playwright-based) - FREE tier 1
    2. Fallback: Mercado Livre API - FREE tier 1 (always available)
    3. Future: SerpAPI, Bright Data (PAID tier 2)
    """
    
    def __init__(self, prefer_google: bool = True, use_fallback: bool = True):
        """
        Initialize scraper orchestrator.
        
        Args:
            prefer_google: Try Google Shopping first (default True)
            use_fallback: Use Mercado Livre fallback if Google fails (default True)
        """
        self.prefer_google = prefer_google and GOOGLE_SHOPPING_AVAILABLE
        self.use_fallback = use_fallback
    
    def scrape_products(self, queries: List[str], 
                       headless: bool = True) -> List[ScrapingResult]:
        """
        Scrape products using orchestrated strategy.
        
        Args:
            queries: List of product queries
            headless: Run browser headless (for Google Shopping)
        
        Returns:
            List of ScrapingResult objects
        """
        results = []
        failed_queries = []
        
        logger.info(f"Iniciando busca para {len(queries)} produtos...")
        
        # Strategy 1: Try Google Shopping first (if available)
        if self.prefer_google:
            logger.info("📌 TIER 1: Tentando Google Shopping (Playwright)...")
            
            try:
                results = scrape_google_shopping_sync(queries, headless=headless)
                
                if results:
                    logger.info(f"✓ Google Shopping: {len(results)} resultados obtidos")
                    return results
                else:
                    logger.warning("⚠️ Google Shopping retornou 0 resultados")
                    failed_queries = queries
            
            except Exception as e:
                logger.warning(f"⚠️ Google Shopping falhou: {str(e)}")
                failed_queries = queries
        else:
            logger.info("📌 Google Shopping desabilitado ou indisponível")
            failed_queries = queries
        
        # Strategy 2: Fallback to Mercado Livre
        if self.use_fallback and failed_queries:
            logger.info(f"📌 TIER 1 FALLBACK: Usando Mercado Livre API para {len(failed_queries)} produtos...")
            
            try:
                ml_results = scrape_mercado_livre(failed_queries)
                
                if ml_results:
                    logger.info(f"✓ Mercado Livre: {len(ml_results)} resultados obtidos")
                    results.extend(ml_results)
                else:
                    logger.warning("⚠️ Mercado Livre retornou 0 resultados")
            
            except Exception as e:
                logger.error(f"❌ Mercado Livre também falhou: {str(e)}")
        
        # Log final results
        if results:
            logger.info(f"✅ Busca concluída: {len(results)} produtos encontrados")
        else:
            logger.error("❌ Nenhum resultado obtido em nenhuma plataforma")
        
        return results
    
    def scrape_with_retry(self, queries: List[str], 
                         max_attempts: int = 2,
                         headless: bool = True) -> List[ScrapingResult]:
        """
        Scrape products with retry logic.
        
        Args:
            queries: List of product queries
            max_attempts: Maximum retry attempts
            headless: Run browser headless
        
        Returns:
            List of ScrapingResult objects
        """
        results = []
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"Tentativa {attempt + 1}/{max_attempts}...")
                
                attempt_results = self.scrape_products(queries, headless=headless)
                results.extend(attempt_results)
                
                if attempt_results:
                    break  # Success, no need to retry
            
            except Exception as e:
                logger.error(f"Erro na tentativa {attempt + 1}: {str(e)}")
                
                if attempt < max_attempts - 1:
                    delay_random(2.0, 5.0)  # Wait before retry
        
        return results
    
    def get_status(self) -> dict:
        """
        Get current scraper status and availability.
        
        Returns:
            Status dictionary with available scrapers
        """
        return {
            'google_shopping': GOOGLE_SHOPPING_AVAILABLE,
            'mercado_livre': True,  # Always available
            'preferred': 'google_shopping' if self.prefer_google else 'mercado_livre',
            'fallback_enabled': self.use_fallback
        }


# Global orchestrator instance
_default_orchestrator: Optional[ScraperOrchestrator] = None


def get_orchestrator() -> ScraperOrchestrator:
    """
    Get or create default scraper orchestrator.
    
    Returns:
        ScraperOrchestrator instance
    """
    global _default_orchestrator
    
    if _default_orchestrator is None:
        _default_orchestrator = ScraperOrchestrator()
    
    return _default_orchestrator


def scrape_products(queries: List[str], headless: bool = True) -> List[ScrapingResult]:
    """
    Scrape products using default orchestrator.
    
    Args:
        queries: List of product queries
        headless: Run browser headless
    
    Returns:
        List of ScrapingResult objects
    
    Example:
        >>> results = scrape_products(['Luva correr', 'Meia algodão'])
        >>> for r in results:
        ...     print(f"{r.query}: R$ {r.preco}")
    """
    orchestrator = get_orchestrator()
    return orchestrator.scrape_products(queries, headless=headless)


def get_scraper_status() -> dict:
    """
    Get current scraper configuration and status.
    
    Returns:
        Status dictionary
    """
    orchestrator = get_orchestrator()
    return orchestrator.get_status()


# Test function
def test_orchestrator():
    """Test the scraper orchestrator"""
    logger.info("Testando orquestrador de scrapers...")
    
    orchestrator = ScraperOrchestrator()
    status = orchestrator.get_status()
    
    logger.info(f"Status do orquestrador:")
    logger.info(f"  - Google Shopping: {'✓' if status['google_shopping'] else '✗'}")
    logger.info(f"  - Mercado Livre: {'✓' if status['mercado_livre'] else '✗'}")
    logger.info(f"  - Preferência: {status['preferred']}")
    logger.info(f"  - Fallback: {'✓' if status['fallback_enabled'] else '✗'}")
    
    # Test with a simple query
    test_queries = ['Luva correr']
    logger.info(f"\nTestando busca com query: {test_queries}")
    
    try:
        results = orchestrator.scrape_products(test_queries, headless=True)
        
        if results:
            logger.info(f"✓ Teste bem-sucedido! {len(results)} produtos encontrados")
            for result in results[:3]:
                logger.info(f"  - {result.query[:50]}... R$ {result.preco} ({result.plataforma})")
        else:
            logger.warning("⚠️ Nenhum resultado encontrado no teste")
    
    except Exception as e:
        logger.error(f"❌ Erro no teste: {str(e)}")
