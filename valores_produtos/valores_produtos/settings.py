import scrapy_poet
import scrapy_zyte_api

BOT_NAME = "valores_produtos"

SPIDER_MODULES = ["valores_produtos.spiders"]
NEWSPIDER_MODULE = "valores_produtos.spiders"

ADDONS = {
    scrapy_poet.Addon: 300,
    scrapy_zyte_api.Addon: 500,
}

SCRAPY_POET_DISCOVER = ["valores_produtos.pages"]

ZYTE_API_KEY = "9d90c31a21094a1a84c195f7e08a1337"

# --- scrapy-playwright integration (enable if scrapy-playwright is installed) ---
# Requires `scrapy-playwright` in the environment. See requirements.txt.
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

# Use asyncio reactor for Playwright integration
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Default browser for Playwright (chromium, firefox, webkit)
PLAYWRIGHT_BROWSER_TYPE = "chromium"

# Optional launch options
PLAYWRIGHT_LAUNCH_OPTIONS = {"headless": True}
