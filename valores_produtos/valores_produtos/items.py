from dataclasses import dataclass
from typing import Optional


@dataclass
class Produto:
	titulo: Optional[str] = None
	"""The product title, as a string or None if not found."""

	preco: Optional[str] = None
	"""The product price, as a string (currency included) or None."""

	url: Optional[str] = None
	"""The product URL as a string or None if not available."""

