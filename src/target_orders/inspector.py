import os
from playwright.sync_api import sync_playwright
import sys

# Enable Playwright Inspector
os.environ["PWDEBUG"] = "1"

html_file = sys.argv[1] if len(sys.argv) > 1 else "orders_page.html"
file_url = f"file://{os.path.abspath(html_file)}"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(file_url)
    print(f"Loaded: {file_url}")
    print("Use the Playwright Inspector to interact and find selectors.")
    input("Press Enter to close...")
    browser.close()
