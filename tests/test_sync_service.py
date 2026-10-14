import pytest
from src.booking_sync.sync_service import SyncService, compute_hash

class MockAirtableClient:
    def __init__(self):
        self.db = {} # booking_ref -> record
        self.fail_mode = False
        self.dry_run = False
        
    def find_by_booking_ref(self, ref):
        if self.fail_mode:
            raise Exception("API Error")
        return self.db.get(ref)
        
    def create_record(self, data):
        if self.dry_run:
            return {"id": "dry_run_id", "fields": data}
        if self.fail_mode:
            raise Exception("API Error")
        ref = data["Booking Nr."]
        self.db[ref] = {"id": f"rec_{ref}", "fields": data}
        return self.db[ref]
        
    def update_record(self, record_id, data):
        if self.dry_run:
            return {"id": record_id, "fields": data}
        if self.fail_mode:
            raise Exception("API Error")
        # Find ref by id
        for ref, rec in self.db.items():
            if rec["id"] == record_id:
                rec["fields"].update(data)
                return rec
        return None

def test_sync_scenarios():
    client = MockAirtableClient()
    service = SyncService(client)
    
    # 1. New Booking
    raw1 = {"booking_reference": "GYG1", "product_title": "Tour A", "total_price": 100.0}
    service.sync_booking(raw1)
    assert service.stats["created"] == 1
    assert "GYG1" in client.db
    
    # 2. Same Booking Again (No changes)
    service.sync_booking(raw1)
    assert service.stats["unchanged"] == 1
    
    # 3. Changed Booking (Update)
    raw1_changed = {"booking_reference": "GYG1", "product_title": "Tour A", "total_price": 120.0}
    service.sync_booking(raw1_changed)
    assert service.stats["updated"] == 1
    assert client.db["GYG1"]["fields"]["Total price EUR"] == 120.0
    
    # 4. Booking without Reference
    raw_invalid = {"product_title": "Invalid"}
    service.sync_booking(raw_invalid)
    assert service.stats["skipped_invalid"] == 1
    
    # 5. API Failure
    client.fail_mode = True
    raw2 = {"booking_reference": "GYG2", "product_title": "Tour B"}
    service.sync_booking(raw2)
    assert service.stats["failed"] == 1
    
    # 6. Dry Run mode
    client.fail_mode = False
    client.dry_run = True
    raw3 = {"booking_reference": "GYG3", "product_title": "Tour C"}
    service.sync_booking(raw3)
    # The service updates stats regardless, but the mock client doesn't store it
    assert service.stats["created"] == 2
    assert "GYG3" not in client.db

def test_datetime_and_changes():
    from src.booking_sync.sync_service import has_changes, is_same_datetime
    
    # Cairo UTC+2/UTC+3 test:
    # 18:00 local Cairo is 16:00 UTC (during standard time +2)
    cairo_local = "2026-11-09T18:00:00"
    airtable_utc = "2026-11-09T16:00:00.000Z"
    assert is_same_datetime(airtable_utc, cairo_local) is True
    
    existing = {"Date Trip": airtable_utc, "trip Name": "Sunset Cruise"}
    incoming = {"Date Trip": cairo_local, "trip Name": "Sunset Cruise"}
    assert has_changes(existing, incoming) is False
    
    # Changed date
    different_date = {"Date Trip": "2026-11-10T18:00:00", "trip Name": "Sunset Cruise"}
    assert has_changes(existing, different_date) is True
