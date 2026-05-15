from web_poet import WebPage, BrowserResponse
from valores_produtos.items import Produto


class GoogleComPage(WebPage):
    """Page object for domain google.com

    Sample URLs:
    - celular
    - televisao

    """

    def __init__(self, response: BrowserResponse):
        self.response = response

    def products(self):
        """Return iterable of `Produto` instances extracted from search results."""
        # Generic extraction for search results (Google and other non-Amazon sites).
        containers = self.response.css('div.g, div.sh-dgr__content, article, div.s-item, div.rc')
        seen = set()
        for node in containers:
            title = node.css('h3::text').get()
            if not title:
                title = node.css('a h3::text').get() or node.css('.title::text').get()
            price = node.css('.a-offscreen::text, .price::text, ._s7::text').get()
            link = node.css('a::attr(href)').get()
            if not link:
                continue
            full = self.response.urljoin(link)
            if full in seen:
                continue
            seen.add(full)
            yield Produto(titulo=title.strip() if title else None, preco=price.strip() if price else None, url=full)
