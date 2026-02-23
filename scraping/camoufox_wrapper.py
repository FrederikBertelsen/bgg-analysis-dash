from contextlib import contextmanager
from camoufox.sync_api import Camoufox

from backend.logger import ScrapeDBLogger
from scraping.page_wrapper import PageWrapper


class CamoufoxWrapper:
    def __init__(self):
        self._browser = None

    @contextmanager
    def start_browser(
        self,
        headless: bool = False,
        humanize: bool = False,
        enable_cache: bool = True,
        block_images: bool = True,
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
        ) as browser:
            self._browser = browser
            try:
                yield self
            finally:
                self._browser.close()
                self._browser = None

    def new_page(self, logger: ScrapeDBLogger) -> PageWrapper:
        if not self._browser:
            raise RuntimeError(
                "Browser not started. Use start_browser() context manager."
            )

        page = self._browser.new_page()

        return PageWrapper(page, logger)
