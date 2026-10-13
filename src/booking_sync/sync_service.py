import hashlib
import json
from datetime import datetime, timezone
from src.booking_sync.config import Config
from src.booking_sync.logging_config import logger
from src.booking_sync.field_mapping import map_booking_to_airtable

def compute_hash(fields: dict) -> str:
    """Computes a deterministic hash of the synced fields."""
    excluded_fields = ["Last Synced At", "Data Hash", "Sync Status"]
    hashable_data = {k: v for k, v in fields.items() if k not in excluded_fields and v is not None}
    sorted_json = json.dumps(hashable_data, sort_keys=True, default=str)
    return hashlib.sha256(sorted_json.encode('utf-8')).hexdigest()

def has_changes(existing_fields: dict, new_fields: dict) -> bool:
    """Checks whether any synced field has meaningfully changed compared to existing Airtable fields."""
    for k, new_val in new_fields.items():
        if new_val is None:
            continue
        old_val = existing_fields.get(k)
        if old_val is None:
            return True
        # Compare numeric
        if isinstance(new_val, (int, float)) and isinstance(old_val, (int, float)):
            if float(new_val) != float(old_val):
                return True
        # Compare datetime/strings
        elif "date" in k.lower() or "trip" in k.lower():
            old_str = str(old_val).replace(".000Z", "").replace("Z", "")
            new_str = str(new_val).replace(".000Z", "").replace("Z", "")
            if old_str != new_str:
                return True
        else:
            if str(old_val).strip() != str(new_val).strip():
                return True

    return False

class SyncService:
    def __init__(self, airtable_client):
        self.client = airtable_client
        self.stats = {
            "created": 0,
            "updated": 0,
            "unchanged": 0,
            "failed": 0,
            "skipped_invalid": 0
        }

    def sync_booking(self, raw_booking: dict):
        """Syncs a single booking to Airtable idempotently."""
        if not raw_booking.get("booking_reference"):
            logger.error("Booking rejected: Missing booking reference.")
            self.stats["skipped_invalid"] += 1
            return
            
        booking_ref = raw_booking["booking_reference"]
        mapped_fields = map_booking_to_airtable(raw_booking)

        try:
            existing_record = self.client.find_by_booking_ref(booking_ref)
            
            if not existing_record:
                # Create new
                logger.info(f"Creating new record for {booking_ref}")
                self.client.create_record(mapped_fields)
                self.stats["created"] += 1
            else:
                existing_fields = existing_record.get("fields", {})
                
                if has_changes(existing_fields, mapped_fields):
                    # Update existing
                    logger.info(f"Updating existing record for {booking_ref}")
                    update_payload = {k: v for k, v in mapped_fields.items() if v is not None}
                    self.client.update_record(existing_record["id"], update_payload)
                    self.stats["updated"] += 1
                else:
                    # Unchanged
                    logger.info(f"Record {booking_ref} unchanged. Skipping.")
                    self.stats["unchanged"] += 1
                    
        except Exception as e:
            logger.error(f"Failed to sync {booking_ref}: {e}")
            self.stats["failed"] += 1

    def print_report(self):
        logger.info(f"--- Sync Report ---")
        logger.info(f"Created: {self.stats['created']}")
        logger.info(f"Updated: {self.stats['updated']}")
        logger.info(f"Unchanged: {self.stats['unchanged']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Skipped (Invalid): {self.stats['skipped_invalid']}")
        if Config.DRY_RUN:
            logger.info("NOTE: Ran in DRY_RUN mode. No actual Airtable writes occurred.")
