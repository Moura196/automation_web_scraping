from pathlib import Path
from dataclasses import asdict, is_dataclass
import re
import pandas as pd


class PandasExportPipeline:
	"""Collect scraped items and export them to EXCEL using pandas when the spider closes."""

	@classmethod
	def from_crawler(cls, crawler):
		pipeline = cls()
		pipeline.crawler = crawler
		return pipeline

	def open_spider(self):
		self.items = []
		self.spider = getattr(self, "crawler", None).spider if getattr(self, "crawler", None) else None

	def _coerce_price(self, value):
		if value is None:
			return None
		if isinstance(value, (int, float)):
			return float(value)

		text = str(value).strip()
		if not text:
			return None

		cleaned = re.sub(r"[^0-9,\.]", "", text)
		if "," in cleaned:
			cleaned = cleaned.replace(".", "").replace(",", ".")

		try:
			return float(cleaned)
		except Exception:
			return None

	def process_item(self, item):
		if is_dataclass(item):
			data = asdict(item)
		else:
			data = dict(item)
		data["preco"] = self._coerce_price(data.get("preco"))
		self.items.append(data)
		return item

	def close_spider(self):
		if not self.items:
			if self.spider:
				self.spider.logger.info("No items scraped; skipping export.")
			else:
				print("No items scraped; skipping export.")
			return

		df = pd.DataFrame(self.items)
		if "preco" in df.columns:
			df["preco"] = pd.to_numeric(df["preco"], errors="coerce")
		out_dir = Path.cwd() / "output"
		out_dir.mkdir(parents=True, exist_ok=True)
		spider_name = self.spider.name if self.spider else "spider"
		fname = out_dir / f"{spider_name}_products.xlsx"
		df.to_excel(fname, index=False)
		if self.spider:
			self.spider.logger.info(f"Wrote {len(self.items)} items to {fname}")
		else:
			print(f"Wrote {len(self.items)} items to {fname}")