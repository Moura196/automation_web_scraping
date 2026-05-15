from web_poet import WebPage, BrowserResponse
from valores_produtos.items import Produto


class AmazonComBrPage(WebPage):
    """Page object for domain amazon.com.br

    Sample URLs:
    - (none provided)

    """

    def __init__(self, response: BrowserResponse):
        self.response = response

    def products(self):
        """Return iterable of `Produto` instances extracted from search results."""
        # Amazon search results extraction
        for item in self.response.css('div.s-result-item[data-component-type="s-search-result"]'):
            title = item.css('h2 a span::text').get() or item.css('span.a-size-medium::text').get()
            price_whole = item.css('.a-price-whole::text').get()
            price_frac = item.css('.a-price-fraction::text').get()
            price = None
            if price_whole:
                price = price_whole.strip()
                if price_frac:
                    price += price_frac.strip()
            rel = item.css('h2 a::attr(href)').get() or item.css('a.a-link-normal::attr(href)').get()
            url = self.response.urljoin(rel) if rel else None
            yield Produto(titulo=title.strip() if title else None, preco=price, url=url)
