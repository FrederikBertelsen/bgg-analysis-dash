from contextlib import contextmanager
from typing import Optional
from camoufox.sync_api import Camoufox
from playwright.sync_api import sync_playwright

from backend.logger import ScrapeTaskLogger
from scraping.page_wrapper import PageWrapper


class CamoufoxWrapper:
    def __init__(self):
        self._browser = None

    @contextmanager
    def start_browser(
        self,
        headless: bool = True,
        humanize: bool = False,
        enable_cache: bool = True,
        block_images: bool = False,
    ):
        """
        Context manager that launches Camoufox and yields this wrapper.

            with CamoufoxWrapper().start_browser() as browser:
                page = browser.new_page()
                page.goto("https://example.com")

        """

        with Camoufox(
            headless=headless,
            humanize=humanize,
            enable_cache=enable_cache,
            block_images=block_images,
            geoip=False,
        ) as browser:
        # with sync_playwright() as p:
        #     browser = p.chromium.launch(headless=headless)
            
            self._browser = browser
            try:
                yield self
            finally:
                self._browser.close()
                self._browser = None

    def new_page(self, logger: Optional[ScrapeTaskLogger] = None) -> PageWrapper:
        if not self._browser:
            raise RuntimeError(
                "Browser not started. Use start_browser() context manager."
            )

        page = self._browser.new_page()

        return PageWrapper(page, logger)
