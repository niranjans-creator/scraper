from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError
)

from src.parser import BigBasketParser


class BigBasketScraper:

    def __init__(self, headless=True):

        self.headless = headless
        self.parser = BigBasketParser()

    # =====================================================
    # SCRAPE PRODUCT
    # =====================================================

    def scrape_product(self, url):

        with sync_playwright() as p:

            browser = None
            context = None

            try:

                print(
                    f"Opening product: {url}"
                )

                # -------------------------------------------------
                # Launch Chromium
                # -------------------------------------------------

                browser = p.chromium.launch(
                    headless=self.headless
                )

                # -------------------------------------------------
                # Browser context
                # -------------------------------------------------

                context = browser.new_context(

                    viewport={
                        "width": 1440,
                        "height": 900
                    },

                    user_agent=(
                        "Mozilla/5.0 "
                        "(Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 "
                        "(KHTML, like Gecko) "
                        "Chrome/131.0.0.0 "
                        "Safari/537.36"
                    ),

                    locale="en-IN",

                    timezone_id="Asia/Kolkata"
                )

                page = context.new_page()

                # -------------------------------------------------
                # Open page
                # -------------------------------------------------

                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=60000
                )

                # -------------------------------------------------
                # Allow JavaScript to render
                # -------------------------------------------------

                page.wait_for_timeout(
                    5000
                )

                # -------------------------------------------------
                # Scroll entire page
                # -------------------------------------------------

                self.scroll_page(
                    page
                )

                page.wait_for_timeout(
                    3000
                )

                # -------------------------------------------------
                # Scroll back to top
                # -------------------------------------------------

                page.evaluate(
                    "window.scrollTo(0, 0)"
                )

                page.wait_for_timeout(
                    1000
                )

                # -------------------------------------------------
                # Get final HTML
                # -------------------------------------------------

                html = page.content()

                # -------------------------------------------------
                # Parse product
                # -------------------------------------------------

                product = self.parser.parse(
                    html
                )

                return product

            except PlaywrightTimeoutError as e:

                raise Exception(
                    "BigBasket page took too long to load."
                ) from e

            except Exception as e:

                raise Exception(
                    f"Failed to scrape BigBasket product: {e}"
                ) from e

            finally:

                if context is not None:

                    try:
                        context.close()
                    except Exception:
                        pass

                if browser is not None:

                    try:
                        browser.close()
                    except Exception:
                        pass

    # =====================================================
    # SCROLL PAGE
    # =====================================================

    @staticmethod
    def scroll_page(page):

        for _ in range(8):

            page.mouse.wheel(
                0,
                1200
            )

            page.wait_for_timeout(
                800
            )

        page.evaluate(
            "window.scrollTo(0, 0)"
        )