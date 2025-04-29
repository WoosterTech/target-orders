import contextlib
import functools
import time
from os import PathLike
from pathlib import Path

from playwright._impl._errors import Error
from playwright.sync_api import Browser, sync_playwright
from playwright.sync_api._generated import BrowserContext, Page
from pydantic import AnyHttpUrl, BaseModel
from rich.console import Console
from rich.progress import track

from target_orders.models import Orders

BASE_URL = "https://www.target.com/"


class SiteUrls(BaseModel):
    base: AnyHttpUrl
    relative_login: str
    orders: str

    def _get_FOO_url(self, field: str) -> str:
        if not hasattr(self, field):
            raise KeyError(f"Field {field} does not exist for {self.__class__}")

        return str(AnyHttpUrl(f"{self.base}{getattr(self, field)}"))

    get_orders_url = functools.partialmethod(_get_FOO_url, "orders")

    get_login_url = functools.partialmethod(_get_FOO_url, "relative_login")


target_urls = SiteUrls(base=BASE_URL, relative_login="login/", orders="orders/")  # pyright: ignore[reportArgumentType]
login_cookies_path = Path("target_login.json")

console = Console()


def _make_page(
    browser: Browser, storage_state: Path | None = None
) -> tuple[BrowserContext, Page]:
    browser_context = browser.new_context(storage_state=storage_state)
    page = browser_context.new_page()

    return browser_context, page


def parse_orders_from_html(html: str | Path, *, debug: bool = False) -> Orders:
    """Parse orders from HTML.

    Args:
        html (str | PathLike): HTML string or path to HTML file.
        debug (bool): If True, debug information will be printed.

    Returns:
        Orders: A list of orders.
    """
    if isinstance(html, PathLike):
        html = Path(html).read_text(encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not debug)
        context = browser.new_context()
        page = context.new_page()
        page.set_content(html)
        orders_div = page.query_selector_all("div[data-test='order-details-link']")

    return Orders.parse_elements(orders_div)


def get_orders(
    cookies_path: Path | None = None, *, loading_delay: int = 5, debug: bool = False
) -> Orders:
    """Get orders from Target.com.

    Args:
        cookies_path (Path | None): Path to the cookies file. If None, a new session will be created.
        loading_delay (int): Number of seconds to wait for the page to load.
        debug (bool): If True, debug information will be printed and html will be saved to a file.

    Returns:
        Orders: A list of orders.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        if cookies_path and cookies_path.exists():
            console.print("Loading cookies from file...")
            context, page = _make_page(browser, storage_state=cookies_path)
        else:
            console.print("No cookies found, starting a new session...")
            context, page = _make_page(browser)
            page.goto(target_urls.get_login_url())
            console.print("Log in manually and then press Enter here...")
            console.input()

        console.print("Logged in, now going to purchase history...")

        # Go to Purchase History
        with contextlib.suppress(Error):
            page.goto(target_urls.get_orders_url())

        # Wait for the page to load
        for _ in track(
            range(loading_delay), description="Waiting for purchase history to load..."
        ):
            time.sleep(1)

        if debug:
            debug_path = Path("output/")

            debug_path.mkdir(parents=True, exist_ok=True)
            orders_html_path = debug_path / "orders.html"
            orders_html_path.write_text(page.content(), encoding="utf-8")
            console.print(f"[yellow bold]Saved orders HTML to {orders_html_path}[/]")

        orders = Orders.parse_elements(
            page.query_selector_all("div[data-test='order-details-link']")
        )

        console.print(f"[cyan bold]Found {len(orders)} orders.[/]")

        if cookies_path is not None:
            context.storage_state(path=cookies_path)
        browser.close()

    return orders


if __name__ == "__main__":
    console.print("[bold cyan]Starting Target Orders...[/]")
    # orders = get_orders(cookies_path=login_cookies_path, debug=True)
    orders_html_path = Path("output/orders.html")
    if not orders_html_path.exists():
        console.print("[red]Orders HTML file not found![/]")
        exit(1)
    orders_str = orders_html_path.read_text(encoding="utf-8")
    orders = Orders.parse_html(orders_str)
    console.print(orders)
    # console.print("[bold green]Orders:[/]")
    # for idx, order in enumerate(orders, start=1):
    #     console.print(f"{idx}: {order.order_number}")
    # console.print("\n[bold magenta]Done![/]")
