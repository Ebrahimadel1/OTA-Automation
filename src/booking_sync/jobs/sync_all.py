from src.booking_sync.logging_config import logger
from src.booking_sync.jobs.base_job import run_job
from src.booking_sync.jobs.upcoming_7_days import upcoming_7_days_logic
from src.booking_sync.jobs.recent_50 import recent_50_logic

def sync_all_logic(bookings_page, sync_service):
    logger.info("==========================================")
    logger.info("Phase 1: Syncing Recent 50 Bookings (Clean default portal)")
    logger.info("==========================================")
    try:
        recent_50_logic(bookings_page, sync_service)
    except Exception as e:
        logger.error(f"Error during recent_50 phase: {e}")

    logger.info("==========================================")
    logger.info("Phase 2: Syncing Upcoming 7 Days Bookings (Date filtered)")
    logger.info("==========================================")
    try:
        bookings_page.reset_page()
        upcoming_7_days_logic(bookings_page, sync_service)
    except Exception as e:
        logger.error(f"Error during upcoming_7_days phase: {e}")

if __name__ == "__main__":
    run_job("sync_all", sync_all_logic)
