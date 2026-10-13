import pytz
from datetime import datetime, timedelta
from src.booking_sync.config import Config
from src.booking_sync.logging_config import logger
from src.booking_sync.jobs.base_job import run_job

def get_date_range():
    tz = pytz.timezone(Config.PORTAL_TIMEZONE)
    now = datetime.now(tz)
    start_date = now.strftime("%Y-%m-%d")
    end_date = (now + timedelta(days=7)).strftime("%Y-%m-%d")
    return start_date, end_date

def upcoming_7_days_logic(bookings_page, sync_service):
    start_date, end_date = get_date_range()
    
    bookings_page.navigate_to_bookings()
    
    success = bookings_page.set_activity_date_filter(start_date, end_date)
    if not success:
        logger.error("Failed to set activity date filter. Aborting to avoid syncing wrong data.")
        return
        
    processed_refs = set()
    page_num = 1
    
    while True:
        logger.info(f"Reading page {page_num} for date range {start_date} to {end_date}...")
        bookings = bookings_page.extract_current_page_bookings()
        
        if not bookings:
            logger.info("No bookings found on this page. Stopping.")
            break
            
        new_on_page = 0
        for b in bookings:
            ref = b.get("booking_reference")
            if ref and ref not in processed_refs:
                sync_service.sync_booking(b)
                processed_refs.add(ref)
                new_on_page += 1
                
        if new_on_page == 0:
            logger.warning("No new unique bookings found on this page. Stopping.")
            break
            
        has_next = bookings_page.go_to_next_page()
        if not has_next:
            logger.info("No more pages available.")
            break
            
        page_num += 1

if __name__ == "__main__":
    run_job("upcoming_7_days", upcoming_7_days_logic)
