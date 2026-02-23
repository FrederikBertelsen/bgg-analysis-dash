from playwright.sync_api import Page, Locator
import random


class PageWrapper:
    def __init__(self, page: Page, print_exceptions: bool = True):
        self.page = page
        self.print_exceptions = print_exceptions

    def _print_error(self, context: str, e: Exception):
        if self.print_exceptions:
            print(f"Error {context}: {e}")

    def content(self) -> str:
        try:
            return self.page.content()
        except Exception as e:
            self._print_error("getting content", e)
            raise

    def goto(self, url: str, retries: int = 2):
        attempts = 0
        while True:
            try:
                self.page.goto(url, wait_until="domcontentloaded", timeout=15000)
                return
            except Exception as e:
                if attempts >= retries:
                    self._print_error(f"going to {url}", e)
                    raise

                attempts += 1
                self._print_error(f"going to {url} (attempt {attempts}/{retries})", e)
                # small random backoff before retrying
                self.sleep_random(500, 1500)

    def locator(self, selector: str, has_text: str | None = None) -> Locator:
        try:
            return self.page.locator(selector, has_text=has_text)
        except Exception as e:
            self._print_error(f'locating "{selector}"', e)
            raise

    def click(self, selector: str, has_text: str | None = None) -> bool:
        try:
            elm = self.locator(selector, has_text=has_text).first

            if elm is None:
                return False

            elm.click(no_wait_after=True)
            return True
        except Exception as e:
            self._print_error(f'clicking element "{selector}"', e)
            return False

    def get_text(self, selector: str, has_text: str | None = None) -> str | None:
        try:
            return self.locator(selector, has_text=has_text).first.text_content()
        except Exception as e:
            self._print_error(f'getting text "{selector}"', e)
            return None

    def get_texts(self, selector: str, has_text: str | None = None) -> list[str] | None:
        try:
            return self.locator(selector, has_text=has_text).all_text_contents()
        except:
            self._print_error(
                f'getting texts "{selector}"',
                Exception("locator/all_text_contents failed"),
            )
            return None

    def get_attribute(
        self, selector: str, attribute: str, has_text: str | None = None
    ) -> str | None:
        try:
            return self.locator(selector, has_text=has_text).first.get_attribute(
                attribute
            )
        except:
            self._print_error(
                f'getting attribute "{attribute}" from "{selector}"',
                Exception("get_attribute failed"),
            )
            return None

    def get_attributes(
        self, selector: str, attribute: str, has_text: str | None = None
    ) -> list[str] | None:
        try:
            elms = self.locator(selector, has_text=has_text)
            return [
                attr
                for attr in [
                    el.get_attribute(attribute) for el in elms.element_handles()
                ]
                if attr is not None
            ]
        except:
            self._print_error(
                f'getting attributes "{attribute}" from "{selector}"',
                Exception("get_attributes failed"),
            )
            return None

    def login(
        self,
        username_selector: str,
        password_selector: str,
        submit_selector: str,
        username: str,
        password: str,
    ) -> bool:
        try:
            self.page.fill(username_selector, username)
            self.sleep_random(500, 1000)
            self.page.fill(password_selector, password)
            self.sleep_random(500, 1000)
            self.page.click(submit_selector)
            self.sleep_random(500, 1000)
            return True
        except Exception as e:
            self._print_error("logging in", e)
            return False

    def wait_for_selector(self, selector: str, timeout: int = 5000) -> bool:
        try:
            elm = self.page.wait_for_selector(selector, timeout=timeout)
            return elm is not None
        except Exception as e:
            self._print_error(f'waiting for "{selector}"', e)
            raise

    def wait_for_idle(self, timeout: int = 5000):
        try:
            self.page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception as e:
            self._print_error("waiting for network idle", e)
            raise

    def exists(self, selector: str, has_text: str | None = None) -> bool:
        try:
            return self.page.locator(selector, has_text=has_text).first is not None
        except Exception as e:
            self._print_error(f'checking existence of "{selector}"', e)
            raise

    def sleep(self, ms: int):
        try:
            self.page.wait_for_timeout(ms)
        except Exception as e:
            self._print_error(f"sleeping for {ms}ms", e)
            raise

    def sleep_random(self, min_ms: int = 100, max_ms: int = 500):
        ms = random.randint(min_ms, max_ms)
        self.sleep(ms)

    def evaluate_js(self, script: str):
        try:
            return self.page.evaluate(script)
        except Exception as e:
            self._print_error("evaluating js", e)
            raise

    def evaluate_js_with_args(self, script: str, *args):
        try:
            return self.page.evaluate(script, *args)
        except Exception as e:
            self._print_error("evaluating js with args", e)
            raise

    def close(self):
        try:
            self.page.close()
        except Exception as e:
            self._print_error("closing page", e)
            raise
