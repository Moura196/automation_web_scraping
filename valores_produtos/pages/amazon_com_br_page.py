from web_poet import WebPage
from valores_produtos.items import Produto


class AmazonComBrPage(WebPage):
    """Page object for domain amazon.com.br

    Sample URLs:
    - (none provided)

    """

    def __init__(self, response):
        self.response = response

    def products(self):
        """Return iterable of `Produto` instances extracted from search results."""
        raise NotImplementedError('Implement extraction logic.')
