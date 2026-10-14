import re
from playwright.sync_api import Page
from src.booking_sync.browser import PortalBrowser
from src.booking_sync.config import Config
from src.booking_sync.logging_config import logger
from src.booking_sync.portal.parser import parse_booking_card

class BookingsPage:
    def __init__(self, browser_adapter: PortalBrowser, page: Page):
        self.browser_adapter = browser_adapter
        self.page = page
        self.base_url = f"{Config.GYG_BASE_URL}/bookings"
        self.current_page_num = 1
        self.query_params = {}

    def get_current_url(self) -> str:
        params = dict(self.query_params)
        params["page_default"] = str(self.current_page_num)
        query_str = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.base_url}?{query_str}"

    def navigate_to_bookings(self, page_num: int = 1):
        self.query_params = {}
        self.current_page_num = page_num
        target_url = self.get_current_url()
        logger.info(f"Navigating to Bookings page: {target_url}...")
        self.page.goto(target_url, wait_until="domcontentloaded")
        self.browser_adapter.human_delay(2000, 3000)

        # Check if auth was lost or redirected to login
        if "/auth/login" in self.page.url or "login" in self.page.url.lower():
            logger.info("Auth redirect detected in navigate_to_bookings. Triggering login...")
            self.browser_adapter.login_if_needed(self.page)
            self.page.goto(target_url, wait_until="domcontentloaded")
            self.browser_adapter.human_delay(2000, 3000)

        # If any filter is currently active in the UI, clear it
        try:
            clear_btn = self.page.locator('button:has-text("Clear"), a:has-text("Clear")').first
            if clear_btn.is_visible(timeout=1500):
                clear_btn.click()
                self.browser_adapter.human_delay(500, 1000)
        except Exception:
            pass

    def set_sort_to_purchase_date_desc(self):
        logger.info("Ensuring sort is Purchase date descending...")
        # Sort is purchase date descending by default on the portal
        self.browser_adapter.human_delay(500, 1000)

    def set_activity_date_filter(self, start_date: str, end_date: str) -> bool:
        """Sets the activity date filter to the specified range via verified URL parameters."""
        logger.info(f"Setting Activity Date filter to: {start_date} -> {end_date} via URL")
        self.query_params["filter_activity_date_from"] = start_date
        self.query_params["filter_activity_date_to"] = end_date
        self.current_page_num = 1
        target_url = self.get_current_url()
        self.page.goto(target_url, wait_until="domcontentloaded")
        self.browser_adapter.human_delay(2000, 3000)
        return True

    def go_to_page(self, page_num: int) -> bool:
        """Navigates directly to the specified page number."""
        self.current_page_num = page_num
        target_url = self.get_current_url()
        logger.info(f"Navigating to page {page_num}: {target_url}...")
        self.page.goto(target_url, wait_until="domcontentloaded")
        self.browser_adapter.human_delay(2000, 3000)
        return True

    def has_next_page(self) -> bool:
        """Checks if there is a next page enabled in the paginator."""
        try:
            next_btns = self.page.locator('button.p-paginator-next:not(.p-disabled):not([disabled]), button[aria-label="Next Page"]:not(.p-disabled):not([disabled])')
            count = next_btns.count()
            for i in range(count):
                if next_btns.nth(i).is_visible():
                    return True
        except Exception as e:
            logger.warning(f"Error checking next page button: {e}")
        return False

    def go_to_next_page(self) -> bool:
        """Navigates to the next page if available."""
        if not self.has_next_page():
            logger.info("No next page available (next button disabled or missing).")
            return False
        return self.go_to_page(self.current_page_num + 1)

    def _return_to_bookings_list(self, current_page_url: str, card_locator_str: str = 'div.border.rounded-lg.mb-4'):
        """Safely returns to the bookings list after extracting email using go_back, with direct recovery if needed."""
        try:
            self.page.go_back(wait_until="domcontentloaded")
            self.browser_adapter.human_delay(1000, 1500)
            if "/auth/login" in self.page.url:
                self.browser_adapter.login_if_needed(self.page)
                self.page.goto(current_page_url, wait_until="domcontentloaded")
            
            # Wait for booking list indicator with valid Playwright selectors
            self.page.wait_for_selector('button:has-text("Show details"), button:has-text("Hide details"), div.border.rounded-lg.mb-4', timeout=12000)
            return
        except Exception as e:
            logger.warning(f"go_back() had issue ({e}). Recovering with direct goto...")

        # Fallback: Navigate directly back to current_page_url
        try:
            if "/auth/login" in self.page.url:
                self.browser_adapter.login_if_needed(self.page)
            self.page.goto(current_page_url, wait_until="domcontentloaded")
            self.browser_adapter.human_delay(2000, 3000)
            self.page.wait_for_selector('button:has-text("Show details"), button:has-text("Hide details"), div.border.rounded-lg.mb-4', timeout=20000)
        except Exception as e2:
            logger.warning(f"Recovery goto encountered issue: {e2}")

    def extract_current_page_bookings(self) -> list:
        logger.info(f"Extracting bookings from page {self.current_page_num}...")
        bookings = []
        
        # Dismiss cookie banner if present
        try:
            cookie_btn = self.page.locator('button:has-text("Only essential"), button:has-text("I agree")').first
            if cookie_btn.is_visible(timeout=3000):
                cookie_btn.click()
                self.browser_adapter.human_delay(500, 1000)
        except Exception:
            pass

        # Wait for booking cards to render
        try:
            self.page.wait_for_selector('button:has-text("Show details"), button:has-text("Hide details"), div.border.rounded-lg.mb-4', timeout=20000)
        except Exception as e:
            logger.warning(f"No booking cards found within timeout: {e}")
            if "/auth/login" in self.page.url or "login" in self.page.url.lower():
                logger.warning("Session expired while extracting page! Re-logging in...")
                self.browser_adapter.login_if_needed(self.page)
                self.page.goto(self.get_current_url(), wait_until="domcontentloaded")
                self.browser_adapter.human_delay(2000, 3000)
                try:
                    self.page.wait_for_selector('button:has-text("Show details"), button:has-text("Hide details"), div.border.rounded-lg.mb-4', timeout=15000)
                except Exception:
                    return bookings
            else:
                return bookings

        # Locate booking cards using verified container selectors
        card_locator_str = 'div.border.rounded-lg.mb-4'
        cards = self.page.locator(card_locator_str)
        count = cards.count()
        if count == 0:
            card_locator_str = 'div:has(> * button:has-text("Show details"))'
            cards = self.page.locator(card_locator_str)
            count = cards.count()

        logger.info(f"Found {count} booking cards on current page.")
        current_page_url = self.get_current_url()
        
        for i in range(count):
            try:
                try:
                    card = self.page.locator(card_locator_str).nth(i)
                    card.wait_for(state="attached", timeout=10000)
                    card.scroll_into_view_if_needed()
                    self.browser_adapter.human_delay(300, 600)
                except Exception as e:
                    logger.warning(f"Retrying card {i} scroll: {e}")
                    self.browser_adapter.human_delay(1000, 1500)
                    card = self.page.locator(card_locator_str).nth(i)
                    card.scroll_into_view_if_needed()
                
                show_details_btn = card.locator('button:has-text("Show details")')
                if show_details_btn.is_visible():
                    show_details_btn.click()
                    self.browser_adapter.human_delay(1500, 2000)
                    
                # Expand pricing breakdown arrow
                breakdown_btn = card.locator('button[data-testid="toggle-commission-breakdown"], button[aria-label="Show breakdown"], button:has(.i-chevron-right)')
                if breakdown_btn.is_visible():
                    try:
                        breakdown_btn.click()
                        self.browser_adapter.human_delay(500, 1000)
                    except Exception as e:
                        logger.warning(f"Could not click breakdown button for card {i}: {e}")

                expanded_text = card.inner_text()
                booking_data = parse_booking_card(expanded_text)
                ref = booking_data.get("booking_reference")
                
                # Step to extract Customer Email if not already extracted from card
                if not booking_data.get("customer_email"):
                    # Check if the email element already exists in the card DOM
                    email_el = card.locator('[data-testid="lead-traveler-email"], a[href^="mailto:"]').first
                    if email_el.is_visible():
                        card_email = email_el.inner_text().strip()
                        if "@reply.getyourguide.com" in card_email or ("@" in card_email and "support" not in card_email.lower()):
                            booking_data["customer_email"] = card_email
                            logger.info(f"Extracted customer email directly from card for {ref}: {card_email}")

                if not booking_data.get("customer_email"):
                    msg_btn = card.locator('button:has-text("Message customer")')
                    if msg_btn.is_visible():
                        try:
                            logger.info(f"Opening 'Message customer' for {ref} to extract email...")
                            msg_btn.click()
                            
                            # Wait for page/email to load
                            try:
                                self.page.wait_for_selector('a[href*="@reply.getyourguide.com"], [data-testid="lead-traveler-email"], text="Lead traveler"', timeout=6000)
                            except Exception:
                                self.browser_adapter.human_delay(1500, 2000)
                            
                            page_html = self.page.content()
                            reply_matches = re.findall(r'\b([a-zA-Z0-9_.+-]+@reply\.getyourguide\.com)\b', page_html)
                            if reply_matches:
                                booking_data["customer_email"] = reply_matches[0]
                                logger.info(f"Extracted customer email: {booking_data['customer_email']}")
                            else:
                                other_matches = re.findall(r'\b([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\b', page_html)
                                valid_emails = [
                                    em for em in other_matches 
                                    if not any(ign in em.lower() for ign in ["support@", "customer.care@", "supplier-support@", "help@"])
                                    and not (em.lower().endswith("@getyourguide.com") and not em.lower().endswith("@reply.getyourguide.com"))
                                ]
                                if valid_emails:
                                    booking_data["customer_email"] = valid_emails[0]
                                    logger.info(f"Extracted customer email: {booking_data['customer_email']}")
                                else:
                                    logger.info("No valid customer email found in conversation view.")
                        except Exception as e:
                            logger.warning(f"Could not extract email for {ref}: {e}")
                        finally:
                            # Return back to bookings list directly via go_back
                            self._return_to_bookings_list(current_page_url, card_locator_str)
                        
                        # Collapse card if Hide details is still visible
                        try:
                            card_after = self.page.locator(card_locator_str).nth(i)
                            hide_details_btn = card_after.locator('button:has-text("Hide details")')
                            if hide_details_btn.is_visible():
                                hide_details_btn.click()
                                self.browser_adapter.human_delay(300, 500)
                        except Exception:
                            pass
                else:
                    # Collapse card back if we didn't navigate away
                    hide_details_btn = card.locator('button:has-text("Hide details")')
                    if hide_details_btn.is_visible():
                        hide_details_btn.click()
                        self.browser_adapter.human_delay(300, 500)
                
                if ref:
                    logger.info(f"Extracted booking {ref} ({booking_data.get('product_title', 'Unknown Title')[:35]}...)")
                    bookings.append(booking_data)
                else:
                    logger.warning("Could not extract booking reference from card, skipping...")
            except Exception as card_error:
                logger.error(f"Error processing card index {i} on page {self.current_page_num}: {card_error}")
                try:
                    self._return_to_bookings_list(current_page_url, card_locator_str)
                except Exception:
                    pass
                continue
                
        return bookings

