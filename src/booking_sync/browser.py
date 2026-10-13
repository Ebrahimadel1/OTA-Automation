import os
import time
import random
import pyotp
from playwright.sync_api import sync_playwright, Page, BrowserContext
from .config import Config
from .logging_config import logger

class PortalBrowser:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None

    def start(self) -> BrowserContext:
        self.playwright = sync_playwright().start()
        storage_state_path = "storage_state.json"
        
        self.browser = self.playwright.chromium.launch(
            headless=Config.HEADLESS,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        if os.path.exists(storage_state_path):
            logger.info("Loading existing session from storage_state.json")
            self.context = self.browser.new_context(
                storage_state=storage_state_path,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
        else:
            logger.info("No storage state found, starting fresh session")
            self.context = self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            
        return self.context

    def close(self):
        if self.context:
            self.context.storage_state(path="storage_state.json")
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def human_delay(self, min_ms=1000, max_ms=3000):
        """Sleeps for a random duration between min_ms and max_ms to simulate human behavior."""
        delay = random.uniform(min_ms / 1000.0, max_ms / 1000.0)
        time.sleep(delay)

    def type_like_human(self, page: Page, selector: str, text: str):
        """Simulates human typing safely without dropping characters."""
        locator = page.locator(selector).first
        locator.clear()
        # Using fill is much safer for React/Vue sites as it doesn't drop characters 
        # and ignores keyboard layout issues for special characters like '@'.
        locator.fill(text)
        self.human_delay(300, 600)

    def login_if_needed(self, page: Page):
        """Checks if login is required and performs it safely with human-like delays."""
        logger.info("Navigating to bookings page to check auth state...")
        try:
            # Using networkidle here allows Cloudflare and redirects to settle before we check for login elements
            page.goto(f"{Config.GYG_BASE_URL}/bookings", wait_until="networkidle", timeout=20000)
        except Exception as e:
            logger.warning(f"Goto bookings page warned: {e}")
        
        # Wait up to 15 seconds for either the email input (login page) or a Bookings header
        try:
            page.wait_for_selector('input#email, input[name="email"], text="Bookings"', timeout=15000)
        except Exception:
            logger.warning("Neither login nor bookings text appeared immediately. Taking screenshot...")
            page.screenshot(path="debug_login_check.png", full_page=True)
            self.human_delay(2000, 3000)
        
        email_locator = page.locator('input#email, input[name="email"]').first
        
        if email_locator.is_visible():
            logger.info("Login required. Attempting login...")
            
            self.type_like_human(page, 'input#email, input[name="email"]', Config.GYG_LOGIN_EMAIL)
            self.human_delay(500, 1500)
            
            password_locator = page.locator('input#password, input[name="password"]').first
            if password_locator.is_visible():
                self.type_like_human(page, 'input#password, input[name="password"]', Config.GYG_LOGIN_PASSWORD)
                self.human_delay(500, 1500)
                
            page.keyboard.press("Enter")
            logger.info("Submitted login form. Waiting for next step...")
            
            # Wait for either 2FA or successful login
            self.human_delay(5000, 7000)
            
            page.screenshot(path="debug_after_login.png", full_page=True)
            
            # Check if 2FA is needed
            content = page.content().lower()
            if "second-factor" in page.url or "two-factor" in content or "enter code" in content or page.locator('.p-inputotp-input').count() > 0:
                logger.info("2FA appears to be requested. Generating TOTP...")
                
                # Ensure the TOTP code has sufficient validity time
                remaining = 30 - (time.time() % 30)
                if remaining < 8:
                    logger.info(f"Only {remaining:.1f}s left in current TOTP window. Waiting for new window...")
                    time.sleep(remaining + 1)

                totp = pyotp.TOTP(Config.GYG_TOTP_SECRET)
                code = totp.now()
                logger.info(f"Generated fresh TOTP code (valid for {30 - (time.time() % 30):.1f}s)")
                
                otp_inputs = page.locator('.p-inputotp-input')
                if otp_inputs.count() > 0:
                    logger.info("Found PrimeVue OTP inputs. Focusing and typing code...")
                    otp_inputs.first.click()
                    self.human_delay(200, 400)
                    page.keyboard.type(code, delay=120)
                else:
                    logger.info("Typing code into focused element...")
                    page.keyboard.type(code, delay=120)
                    
                self.human_delay(500, 1000)
                
                verify_btn = page.locator('button:has-text("Verify code")')
                if verify_btn.is_visible():
                    logger.info("Clicking 'Verify code' button...")
                    verify_btn.click()
                else:
                    page.keyboard.press("Enter")
                    
                # Wait for redirect away from auth pages
                try:
                    page.wait_for_url(lambda u: "second-factor" not in u and "login" not in u and "auth" not in u, timeout=20000)
                    logger.info(f"Redirect complete after 2FA: {page.url}")
                except Exception as e:
                    logger.warning(f"Wait for post-2FA redirect warning: {e}")
                    
                self.human_delay(2000, 3000)
                page.screenshot(path="debug_after_2fa.png", full_page=True)
                
            logger.info("Login process finished. Saving session state.")
            self.context.storage_state(path="storage_state.json")
        else:
            # Check if we actually reached the bookings page
            if page.locator('text="Bookings"').first.is_visible() or "bookings" in page.url.lower():
                logger.info("Already logged in.")
            else:
                page.screenshot(path="debug_unknown_state.png", full_page=True)
                raise Exception("Could not determine login state. Saved debug_unknown_state.png")
            
        # Navigate somewhere else before going to bookings directly, as requested
        logger.info("Simulating human behavior: navigating to another page first...")
        try:
            page.goto(f"{Config.GYG_BASE_URL}/products", wait_until="domcontentloaded", timeout=15000)
        except Exception as e:
            logger.warning(f"Goto products page warned: {e}")
        self.human_delay(3000, 5000)
