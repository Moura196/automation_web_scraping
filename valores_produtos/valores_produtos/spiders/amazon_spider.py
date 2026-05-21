from scrapy import Spider, Request


class AmazonSearchSpider(Spider):
    name = "amazon_search"

    def __init__(self, query: str | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query = query or "cadeira"

    def start_requests(self):
        q = self.query.replace(" ", "+")
        url = f"https://www.amazon.com.br/s?k={q}"
        yield Request(url, meta={"playwright": True}, callback=self.parse, dont_filter=True)

    def parse(self, response):
        self.logger.info("Response status: %s", response.status)
        self.logger.info("Response URL: %s", response.url)
        snippet = response.text[:1000].replace("\n", " ").replace("\r", " ")
        self.logger.info("HTML snippet: %s", snippet)

        # Reuse the existing page object implementation for extraction
        try:
            from valores_produtos.pages.amazon_com_br_page import AmazonComBrPage
        except Exception:
            self.logger.exception("Could not import AmazonComBrPage")
            return

        page = AmazonComBrPage(response)
        for produto in page.products():
            yield {
                "titulo": produto.titulo,
                "preco": produto.preco,
                "url": produto.url,
            }

        # follow pagination if present
        next_rel = response.css('ul.a-pagination li.a-last a::attr(href)').get()
        if next_rel:
            yield response.follow(next_rel, meta={"playwright": True}, callback=self.parse)
