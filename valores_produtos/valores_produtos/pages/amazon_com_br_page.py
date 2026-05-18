from web_poet import WebPage, BrowserResponse
from valores_produtos.items import Produto
import re


class AmazonComBrPage(WebPage):
    """Page object for domain amazon.com.br

    Sample URLs:
    - (none provided)

    """

    def __init__(self, response: BrowserResponse):
        self.response = response

    def _clean_text(self, text: str | None) -> str | None:
        if not text:
            return None
        return " ".join(text.split()).strip()

    def _parse_price_from_parts(self, whole: str | None, frac: str | None) -> float | None:
        if not whole:
            return None
        whole_clean = re.sub(r"[^0-9]", "", whole)
        if frac:
            frac_clean = re.sub(r"[^0-9]", "", frac)
            try:
                return float(f"{int(whole_clean)}.{int(frac_clean):02d}")
            except Exception:
                return None
        try:
            return float(whole_clean)
        except Exception:
            return None

    def _parse_price_from_text(self, text: str | None) -> float | None:
        if not text:
            return None
        s = re.sub(r"[^0-9,\.]", "", text).strip()
        # Convert localized number (1.234,56) to 1234.56
        s = s.replace(".", "").replace(",", ".") if "," in s else s
        try:
            return float(s)
        except Exception:
            return None

    def products(self):
        """Return iterable of `Produto` instances extracted from search results or a product page."""

        # If this response is a product detail page, prefer page-title selectors
        prod_title = self.response.css('#productTitle::text, span#productTitle::text').get()
        if prod_title:
            title = self._clean_text(prod_title)
            price_text = (
                self.response.css('#priceblock_ourprice::text, #priceblock_dealprice::text, .a-price .a-offscreen::text').get()
            )
            price = self._parse_price_from_text(price_text)
            url = self.response.url
            yield Produto(titulo=title, preco=price, url=url)
            return

        # Otherwise, iterate search-result listings
        for item in self.response.css('div.s-result-item[data-component-type="s-search-result"]'):
            title = (
                item.css('h2 a span::text').get()
                or item.css('h2 a::text').get()
                or item.css('span.a-size-medium::text').get()
                or item.css('span.a-size-base-plus::text').get()
                or item.css('img::attr(alt)').get()
            )
            title = self._clean_text(title) if title else None

            price_whole = item.css('.a-price-whole::text').get()
            price_frac = item.css('.a-price-fraction::text').get()
            price_text = item.css('.a-price .a-offscreen::text').get()

            price = None
            if price_whole or price_frac:
                price = self._parse_price_from_parts(price_whole, price_frac)
            elif price_text:
                price = self._parse_price_from_text(price_text)

            rel = item.css('h2 a::attr(href)').get() or item.css('a.a-link-normal::attr(href)').get()
            url = self.response.urljoin(rel) if rel else None

            yield Produto(titulo=title, preco=price, url=url)
