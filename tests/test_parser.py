import pytest
from src.booking_sync.portal.parser import parse_participants, extract_price, parse_booking_card

SAMPLE_CARD_1 = """
Cairo: Turquoise Prestige Nile Sunset Dinner & Show Cruise

default | Including Transfer (Pickup & Drop-off)

Nov 21, 2026 6:00 PM

2 participants

GYG996RLBHLR
Oct 11, 2026
Hide details
Lead traveler

Lorraine Ramchandra

+61414762082

Participants
2 Adults (10-99)
Languages
Live guide: English
Guide
Select guide
Ticket codes
VOO55SE80YEIEYDRKELRORZ6EJ3QKLTD-NDWZ1
Pricing

€120.00 (32% commission)

Reserve Now Pay Later Booking

No

Payment status

Booking confirmed; payment will be included in the next invoice.

Message customer
Request cancellation
"""

SAMPLE_CARD_2 = """
Cairo: Nile Royal Topaz Night Dinner Cruise with Show

default | Excluding Transfer (Pickup & Drop-off)

Oct 19, 2026 8:30 PM

2 participants

GYGRFQBQ7AVB
Oct 11, 2026
Hide details
Lead traveler

Thaís de França Watanabe

+5519982223909

Participants
2 Adults (10-99)
Languages
Live guide: English
Guide
Select guide
Pricing

€90.00 (32% commission)

Message customer
Request cancellation
"""

def test_parse_participants_single():
    res = parse_participants("3 Adults (10-99)")
    assert res == {"ADT": 3, "CHD": 0, "Inf": 0}

def test_parse_participants_multiple():
    text = "2 Infants (0-4)\n3 Children (5-9)\n8 Adults (10-99)"
    res = parse_participants(text)
    assert res == {"ADT": 8, "CHD": 3, "Inf": 2}

def test_extract_price():
    assert extract_price("€210.00 (32% commission)") == 210.0
    assert extract_price("USD 1,250.50") == 1250.5
    assert extract_price("150") == 150.0

def test_parse_booking_card_sample_1():
    data = parse_booking_card(SAMPLE_CARD_1)
    assert data["booking_reference"] == "GYG996RLBHLR"
    assert data["status"] == "Active"
    assert data["product_title"] == "Cairo: Turquoise Prestige Nile Sunset Dinner & Show Cruise"
    assert data["option_text"] == "default | Including Transfer (Pickup & Drop-off)"
    assert data["activity_datetime"] == "2026-11-21T18:00:00"
    assert data["lead_traveler_name"] == "Lorraine Ramchandra"
    assert data["lead_traveler_phone"] == "+61414762082"
    assert data["participants_adults"] == 2
    assert data["participants_children"] == 0
    assert data["participants_infants"] == 0
    assert data["languages"] == "English"
    assert data["total_price"] == 120.0

def test_parse_booking_card_sample_2():
    data = parse_booking_card(SAMPLE_CARD_2)
    assert data["booking_reference"] == "GYGRFQBQ7AVB"
    assert data["status"] == "Active"
    assert data["product_title"] == "Cairo: Nile Royal Topaz Night Dinner Cruise with Show"
    assert data["option_text"] == "default | Excluding Transfer (Pickup & Drop-off)"
    assert data["activity_datetime"] == "2026-10-19T20:30:00"
    assert data["lead_traveler_name"] == "Thaís de França Watanabe"
    assert data["lead_traveler_phone"] == "+5519982223909"
    assert data["total_price"] == 90.0
