"""Browser setup and LinkedIn login."""
import os
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

_playwright = None
_browser: Browser = None
_context: BrowserContext = None
_page: Page = None


def get_page(headless: bool = False) -> Page:
    global _playwright, _browser, _context, _page
    if _page:
        return _page
    _playwright = sync_playwright().start()
    _browser = _playwright.chromium.launch(headless=headless)
    _context = _browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    )
    _page = _context.new_page()
    return _page


def login(page: Page, email: str = "", password: str = "") -> bool:
    print("[LOGIN] Opening LinkedIn...")
    page.goto("https://www.linkedin.com/login")
    page.wait_for_timeout(1500)

    if "feed" in page.url or "jobs" in page.url:
        print("[LOGIN] Already logged in.")
        return True

    if email and password:
        page.fill("#username", email)
        page.fill("#password", password)
        page.click('[type="submit"]')
        page.wait_for_timeout(3000)
    else:
        print("[LOGIN] Please log in manually in the browser window.")
        input("Press Enter once you are logged in and see your LinkedIn feed...")

    if "checkpoint" in page.url:
        print("[LOGIN] 2FA/checkpoint — complete in browser window.")
        input("Press Enter once done...")

    if "feed" in page.url or "jobs" in page.url or "mynetwork" in page.url:
        print("[LOGIN] Success.")
        return True

    # Give user one more chance
    print("[LOGIN] Not on feed yet. Complete login in browser then press Enter.")
    input("Press Enter when logged in...")
    return True


def close():
    global _playwright, _browser, _context, _page
    if _browser:
        _browser.close()
    if _playwright:
        _playwright.stop()
    _page = _context = _browser = _playwright = None
