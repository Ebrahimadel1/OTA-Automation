from src.booking_sync.field_mapping import map_booking_to_airtable

def test_map_booking_to_airtable():
    raw_data = {
        "booking_reference": "GYG123456",
        "product_title": "Cairo: Luxury Dinner Cruise",
        "activity_datetime": "2026-10-10T20:30:00Z",
        "lead_traveler_name": "John Doe",
        "lead_traveler_phone": "+1234567890",
        "customer_email": "customer-test@reply.getyourguide.com",
        "customer_country": "United States",
        "retail_price": "€250.00",
        "revenue": "€170.00",
        "commission_breakdown": 0.32,
        "option_text": "default | Including Transfer",
        "languages": "English",
        "participants_adults": 2,
        "participants_children": 1,
        "participants_infants": 0,
        "pickup_location": "Hilton Hotel",
        "total_price": 250.0,
        "status": "Active"
    }
    
    mapped = map_booking_to_airtable(raw_data)
    
    assert mapped["Agency"] == "GetYourGuide"
    assert mapped["Booking Nr."] == "GYG123456"
    assert mapped["trip Name"] == "Cairo: Luxury Dinner Cruise"
    assert mapped["Date Trip"] == "2026-10-10T20:30:00Z"
    assert mapped["Customer Name"] == "John Doe"
    assert mapped["Customer Phone"] == "+1234567890"
    assert mapped["Customer Email"] == "customer-test@reply.getyourguide.com"
    assert mapped["Customer Country"] == "United States"
    assert mapped["Retail Price"] == "€250.00"
    assert mapped["Revenue"] == "€170.00"
    assert mapped["Commission Breakdown"] == 0.32
    assert mapped["Option"] == "Including Transfer"
    assert mapped["Guide"] == "English"
    assert mapped["ADT"] == 2
    assert mapped["CHD"] == 1
    assert mapped["Inf"] == 0
    assert mapped["Hotel Name"] == "Hilton Hotel"
    assert mapped["Total price EUR"] == 250.0
    assert mapped["Booking Status"] == "Confirmed"

def test_map_booking_canceled():
    raw_data = {
        "booking_reference": "GYG999",
        "status": "Canceled"
    }
    mapped = map_booking_to_airtable(raw_data)
    assert mapped["Booking Status"] == "Canceled"
