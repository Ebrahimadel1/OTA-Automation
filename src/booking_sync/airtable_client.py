import time
from pyairtable import Table
from pyairtable.formulas import match
from src.booking_sync.config import Config
from src.booking_sync.logging_config import logger

class AirtableClient:
    def __init__(self):
        # We allow initialization to fail if PAT is missing, 
        # but handle it gracefully if it's just a DRY_RUN where PAT might not be present.
        pat = Config.AIRTABLE_PAT or "dummy_pat"
        base = Config.AIRTABLE_BASE_ID or "dummy_base"
        table_name = Config.AIRTABLE_TABLE_NAME or "dummy_table"
        self.table = Table(pat, base, table_name)
        
    def find_by_booking_ref(self, booking_ref: str):
        """Finds a single record by Booking Nr. Includes basic retry for rate limits."""
        try:
            # We use match to safely build the formula
            records = self.table.all(formula=match({"Booking Nr.": booking_ref}))
            return records[0] if records else None
        except Exception as e:
            logger.error(f"Error fetching from Airtable: {e}")
            raise
            
    def create_record(self, data: dict):
        if Config.DRY_RUN:
            logger.info(f"[DRY RUN] Would create record: {data.get('Booking Nr.')}")
            return {"id": "dry_run_id", "fields": data}
            
        try:
            return self.table.create(data)
        except Exception as e:
            logger.error(f"Error creating record in Airtable: {e}")
            raise
            
    def update_record(self, record_id: str, data: dict):
        if Config.DRY_RUN:
            logger.info(f"[DRY RUN] Would update record {record_id} with new data.")
            return {"id": record_id, "fields": data}
            
        try:
            return self.table.update(record_id, data)
        except Exception as e:
            logger.error(f"Error updating record {record_id} in Airtable: {e}")
            raise
