import os
import atexit
from src.booking_sync.config import Config
from src.booking_sync.logging_config import logger
from src.booking_sync.browser import PortalBrowser
from src.booking_sync.airtable_client import AirtableClient
from src.booking_sync.sync_service import SyncService
from src.booking_sync.portal.bookings_page import BookingsPage

class LockManager:
    def __init__(self, lock_file: str):
        self.lock_file = lock_file

    def acquire(self):
        if os.path.exists(self.lock_file):
            logger.error(f"Job is already running. Lock file {self.lock_file} exists.")
            return False
        with open(self.lock_file, "w") as f:
            f.write("locked")
        return True

    def release(self):
        if os.path.exists(self.lock_file):
            os.remove(self.lock_file)

def run_job(job_name: str, job_func):
    lock = LockManager(f"{job_name}.lock")
    if not lock.acquire():
        return
        
    atexit.register(lock.release)
    
    logger.info(f"--- Starting Job: {job_name} ---")
    browser_adapter = PortalBrowser()
    try:
        context = browser_adapter.start()
        page = context.new_page()
        browser_adapter.login_if_needed(page)
        
        bookings_page = BookingsPage(browser_adapter, page)
        
        airtable_client = AirtableClient()
        sync_service = SyncService(airtable_client)
        
        job_func(bookings_page, sync_service)
        
        sync_service.print_report()
    except Exception as e:
        logger.error(f"Job {job_name} failed: {e}")
    finally:
        browser_adapter.close()
        lock.release()
        logger.info(f"--- Finished Job: {job_name} ---")
