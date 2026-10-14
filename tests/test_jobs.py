import pytest
from src.booking_sync.jobs.recent_50 import recent_50_logic
from src.booking_sync.jobs.upcoming_7_days import upcoming_7_days_logic
from src.booking_sync.jobs.sync_all import sync_all_logic

class MockBookingsPage:
    def __init__(self, num_bookings=55, per_page=10):
        self.num_bookings = num_bookings
        self.per_page = per_page
        self.current_page = 1
        self.sort_set = False
        self.filter_set = False
        self.navigated = False

    def navigate_to_bookings(self):
        self.navigated = True
        self.current_page = 1

    def set_sort_to_purchase_date_desc(self):
        self.sort_set = True

    def set_activity_date_filter(self, start_date, end_date):
        self.filter_set = True
        return True

    def reset_page(self):
        self.current_page = 1

    def extract_current_page_bookings(self):
        start_idx = (self.current_page - 1) * self.per_page
        end_idx = min(start_idx + self.per_page, self.num_bookings)
        bookings = []
        for i in range(start_idx, end_idx):
            bookings.append({"booking_reference": f"GYG_{i}"})
        return bookings

    def go_to_next_page(self):
        max_pages = (self.num_bookings + self.per_page - 1) // self.per_page
        if self.current_page < max_pages:
            self.current_page += 1
            return True
        return False

class MockSyncService:
    def __init__(self):
        self.synced = []
    
    def sync_booking(self, b):
        self.synced.append(b["booking_reference"])

def test_recent_50_logic():
    page = MockBookingsPage(num_bookings=55) # 5.5 pages
    sync = MockSyncService()
    
    recent_50_logic(page, sync)
    
    assert page.navigated
    assert page.sort_set
    assert len(sync.synced) == 50 # Stops exactly at 50
    assert sync.synced[-1] == "GYG_49"

def test_recent_50_logic_less_than_50():
    page = MockBookingsPage(num_bookings=25)
    sync = MockSyncService()
    
    recent_50_logic(page, sync)
    
    assert len(sync.synced) == 25 # Processed all available

def test_upcoming_7_days_logic():
    page = MockBookingsPage(num_bookings=15)
    sync = MockSyncService()
    
    upcoming_7_days_logic(page, sync)
    
    assert page.navigated
    assert page.filter_set
    assert len(sync.synced) == 15 # Processed all available in the filter

def test_sync_all_logic():
    page = MockBookingsPage(num_bookings=55)
    sync = MockSyncService()
    
    sync_all_logic(page, sync)
    
    assert page.navigated
    assert page.filter_set
    assert page.sort_set
    # Both phases ran
    assert len(sync.synced) == 55 + 50
