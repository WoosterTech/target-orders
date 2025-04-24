import functools
import time
from pathlib import Path

from playwright.sync_api import sync_playwright
from pydantic import AnyHttpUrl, BaseModel
from rich.console import Console

from target_orders.models import Order

BASE_URL = "https://www.target.com/"


class SiteUrls(BaseModel):
    base: AnyHttpUrl
    relative_login: str
    orders: str

    def get_login_url(self) -> str:
        return str(AnyHttpUrl(f"{self.base}{self.relative_login}"))

    def _get_FOO_url(self, field: str) -> str:
        if not hasattr(self, field):
            raise KeyError(f"Field {field} does not exist for {self.__class__}")

        return str(AnyHttpUrl(f"{self.base}{getattr(self, field)}"))

    get_orders_url = functools.partialmethod(_get_FOO_url, "orders")


target_urls = SiteUrls(base=BASE_URL, relative_login="login/", orders="orders/")  # pyright: ignore[reportArgumentType]
login_cookies_path = Path("target_login.json")

console = Console()
# os.environ["PWDEBUG"] = "1"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    if login_cookies_path.exists():
        console.print("Loading cookies from file...")
        context = browser.new_context(storage_state=login_cookies_path)
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

    # # Go to Purchase History
    page.goto(target_urls.get_orders_url())
    # print("Press Enter to continue...")
    # input()

    # # Wait for the page to load
    time.sleep(5)

    # # Grab transaction elements (this selector may change and need tweaking)
    orders = page.query_selector_all("div[data-test='order-details-link']")

    console.print(f"Found {len(orders)} orders.")

    first_order = Order.parse_html(orders[0].inner_html())

    console.print(first_order)

    # for order in orders:
    #     try:
    #         date = order.query_selector(".order-date").inner_text()
    #         total = order.query_selector(".order-total").inner_text()
    #         print(f"Date: {date}, Total: {total}")
    #     except Exception as e:
    #         print("Error parsing order:", e)

    context.storage_state(path="target_login.json")
    browser.close()
