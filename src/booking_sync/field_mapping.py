def map_booking_to_airtable(booking_data: dict) -> dict:
    """
    Maps the raw booking data parsed from GetYourGuide to Airtable fields.
    """
    # Status: 'Canceled' if canceled on platform, otherwise 'Confirmed'
    raw_status = booking_data.get("status")
    booking_status = "Canceled" if raw_status == "Canceled" else "Confirmed"

    customer_email = booking_data.get("customer_email")
    if customer_email and (
        any(ign in customer_email.lower() for ign in ["support@", "customer.care@", "supplier-support@", "help@"])
        or (customer_email.lower().endswith("@getyourguide.com") and not customer_email.lower().endswith("@reply.getyourguide.com"))
    ):
        customer_email = None

    airtable_record = {
        "Agency": "GetYourGuide",  # Fixed as per the screenshots
        "Booking Nr.": booking_data.get("booking_reference"),
        "trip Name": booking_data.get("product_title"),
        "Date Trip": booking_data.get("activity_datetime"), # ISO 8601 string
        "Customer Name": booking_data.get("lead_traveler_name"),
        "Customer Phone": booking_data.get("lead_traveler_phone"),
        "Customer Email": customer_email,
        "Customer Country": booking_data.get("customer_country"),
        "Option": booking_data.get("option_text").split(" | ", 1)[-1].strip() if booking_data.get("option_text") else None,
        "Guide": booking_data.get("languages"),
        "ADT": booking_data.get("participants_adults", 0),
        "CHD": booking_data.get("participants_children", 0),
        "Inf": booking_data.get("participants_infants", 0),
        "Hotel Name": booking_data.get("pickup_location"),
        "Total price EUR": booking_data.get("total_price"),
        "Retail Price": booking_data.get("retail_price"),
        "Revenue": booking_data.get("revenue"),
        "Commission Breakdown": booking_data.get("commission_breakdown"),
        "Booking Status": booking_status,
    }
    
    # Remove None values so we don't overwrite Airtable with empty if not explicitly intended
    return {k: v for k, v in airtable_record.items() if v is not None}
