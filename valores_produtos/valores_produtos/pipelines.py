from pathlib import Path
import pandas as pd


class PandasExportPipeline:
	"""Collect scraped items and export them to CSV using pandas when the spider closes."""

	def open_spider(self, spider):
		self.items = []

	def process_item(self, item, spider):
		self.items.append(dict(item))
		return item

	def close_spider(self, spider):
		if not self.items:
			spider.logger.info("No items scraped; skipping export.")
			return

		df = pd.DataFrame(self.items)
		out_dir = Path.cwd() / "output"
		out_dir.mkdir(parents=True, exist_ok=True)
		fname = out_dir / f"{spider.name}_products.csv"
		df.to_csv(fname, index=False)
		spider.logger.info(f"Wrote {len(self.items)} items to {fname}")
# TODO: não implementa transformações/export.