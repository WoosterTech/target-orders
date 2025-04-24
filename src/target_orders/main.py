import functools
import time
from pathlib import Path

from playwright.sync_api import sync_playwright
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
            context = browser.new_context(storage_state=cookies_path)
        else:
            console.print("No cookies found, starting a new session...")
            context = browser.new_context()
            # Wait for the user to log in manually
            console.print("Log in manually and then press Enter here...")
            console.input()

        page = context.new_page()

        # Go to Target login page
        page.goto(target_urls.get_login_url())

        console.print("Logged in, now going to purchase history...")

        # Go to Purchase History
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
    console.print("Starting Target Orders...")
    orders = get_orders(cookies_path=login_cookies_path, debug=True)
    console.print(orders)
    console.print("Done!")
