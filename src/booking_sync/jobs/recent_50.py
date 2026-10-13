from src.booking_sync.logging_config import logger
from src.booking_sync.jobs.base_job import run_job

def recent_50_logic(bookings_page, sync_service):
    bookings_page.navigate_to_bookings()
    bookings_page.set_sort_to_purchase_date_desc()
    
    target_count = 50
    processed_refs = set()
    page_num = 1
    
    while len(processed_refs) < target_count:
        logger.info(f"Reading page {page_num}...")
        bookings = bookings_page.extract_current_page_bookings()
        
        if not bookings:
            logger.warning("No bookings found on this page. Stopping.")
            break
            
        new_on_page = 0
        for b in bookings:
            ref = b.get("booking_reference")
            if ref and ref not in processed_refs:
                sync_service.sync_booking(b)
                processed_refs.add(ref)
                new_on_page += 1
                if len(processed_refs) >= target_count:
                    break
                    
        if len(processed_refs) >= target_count:
            logger.info("Reached target of 50 unique bookings.")
            break
            
        if new_on_page == 0:
            logger.warning("No new unique bookings found. Potential infinite loop or end of data. Stopping.")
            break
            
        has_next = bookings_page.go_to_next_page()
        if not has_next:
            logger.info("No more pages available.")
            break
            
        page_num += 1

    if len(processed_refs) < target_count:
        logger.warning(f"Job incomplete: Only retrieved {len(processed_refs)} out of {target_count} bookings.")

if __name__ == "__main__":
    run_job("recent_50", recent_50_logic)
