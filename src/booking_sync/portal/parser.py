import re
from datetime import datetime
import phonenumbers
from phonenumbers import geocoder
import pycountry

def get_country_from_phone(phone_str: str):
    """Extracts the English country name from an international phone string."""
    if not phone_str:
        return None
    try:
        cleaned = phone_str.strip()
        if cleaned.startswith("-"):
            cleaned = "+" + cleaned.lstrip("-")
        elif not cleaned.startswith("+"):
            cleaned = "+" + cleaned
        parsed = phonenumbers.parse(cleaned)
        region = phonenumbers.region_code_for_number(parsed)
        if region:
            c = pycountry.countries.get(alpha_2=region)
            if c:
                return c.name
        desc = geocoder.description_for_number(parsed, "en")
        return desc if desc else None
    except Exception:
        return None

def parse_participants(participant_text: str) -> dict:
    """
    Parses strings like "2 Infants (0-4)\n3 Children (5-9)\n8 Adults (10-99)"
    and returns a dictionary with ADT, CHD, Inf counts.
    """
    result = {"ADT": 0, "CHD": 0, "Inf": 0}
    if not participant_text:
        return result
        
    adult_match = re.search(r'(\d+)\s*(?:Adult|adult)', participant_text)
    if adult_match:
        result["ADT"] = int(adult_match.group(1))
        
    child_match = re.search(r'(\d+)\s*(?:Child|child)', participant_text)
    if child_match:
        result["CHD"] = int(child_match.group(1))
        
    infant_match = re.search(r'(\d+)\s*(?:Infant|infant)', participant_text)
    if infant_match:
        result["Inf"] = int(infant_match.group(1))
        
    return result

def extract_price(price_text: str) -> float:
    """Extracts float value from strings like '€210.00 (32% commission)'"""
    if not price_text:
        return 0.0
    match = re.search(r'[\d,]+\.\d+|\d+', price_text)
    if match:
        return float(match.group(0).replace(',', ''))
    return 0.0

def parse_booking_card(card_text: str) -> dict:
    """
    Parses the full text of an expanded GetYourGuide booking card into a structured dictionary.
    """
    data = {}
    
    # 1. Booking Reference (e.g. GYG996RLBHLR)
    ref_match = re.search(r'\b(GYG[A-Z0-9]+)\b', card_text)
    if ref_match:
        data["booking_reference"] = ref_match.group(1)
        
    # 2. Status: "Canceled" if canceled, otherwise "Active"
    # Note: Avoid matching "Request cancellation" button
    if re.search(r'\b(?:Canceled|Cancelled)\b', card_text, re.IGNORECASE):
        data["status"] = "Canceled"
    else:
        data["status"] = "Active"
        
    # 3. Product Title and Option
    # The header portion before "Hide details" contains Title and Option
    pre_details = card_text.split("Hide details")[0].strip() if "Hide details" in card_text else card_text.split("Show details")[0].strip()
    lines = [l.strip() for l in pre_details.splitlines() if l.strip()]
    
    # Filter out badges if any appear at the top
    title_idx = 0
    while title_idx < len(lines) and lines[title_idx].lower() in ["urgent", "missing", "specify pickup time"]:
        title_idx += 1
        
    if title_idx < len(lines):
        data["product_title"] = lines[title_idx]
        if title_idx + 1 < len(lines) and not re.search(r'GYG|\d{4}', lines[title_idx + 1]):
            data["option_text"] = lines[title_idx + 1]

    # 4. Activity Datetime (e.g. Nov 21, 2026 6:00 PM)
    dt_match = re.search(r'([A-Za-z]{3}\s+\d{1,2},\s+\d{4}\s+\d{1,2}:\d{2}\s+(?:AM|PM))', card_text)
    if dt_match:
        try:
            dt = datetime.strptime(dt_match.group(1), "%b %d, %Y %I:%M %p")
            data["activity_datetime"] = dt.strftime("%Y-%m-%dT%H:%M:%S")
        except Exception:
            data["activity_datetime"] = dt_match.group(1)

    # 5. Lead Traveler Name, Phone, and Country
    if "Lead traveler" in card_text:
        after_lead = card_text.split("Lead traveler", 1)[1]
        lead_section = re.split(r'\n+(?:Participants|Pickup details|Languages|Guide|Ticket codes|Pricing)', after_lead)[0]
        lead_lines = [l.strip() for l in lead_section.splitlines() if l.strip()]
        if lead_lines:
            data["lead_traveler_name"] = lead_lines[0]
            for line in lead_lines[1:]:
                if re.search(r'[\d+]', line) and "lead_traveler_phone" not in data and "@" not in line:
                    data["lead_traveler_phone"] = line
                    data["customer_country"] = get_country_from_phone(line)
                elif "@" in line and "customer_email" not in data:
                    clean_email = line.strip()
                    if not any(ign in clean_email.lower() for ign in ["support@", "customer.care@", "supplier-support@"]):
                        data["customer_email"] = clean_email

        # Also fallback check for @reply.getyourguide.com anywhere in lead_section or card_text
        if "customer_email" not in data:
            reply_match = re.search(r'\b([a-zA-Z0-9_.+-]+@reply\.getyourguide\.com)\b', card_text)
            if reply_match:
                data["customer_email"] = reply_match.group(1)

    # 6. Participants
    participants_dict = parse_participants(card_text)
    data["participants_adults"] = participants_dict["ADT"]
    data["participants_children"] = participants_dict["CHD"]
    data["participants_infants"] = participants_dict["Inf"]

    # 7. Languages / Guide
    lang_match = re.search(r'(?:Live guide|Audio guide):\s*([^\n]+)', card_text, re.IGNORECASE)
    if lang_match:
        data["languages"] = lang_match.group(1).strip()

    # 8. Pricing & Breakdown
    pricing_match = re.search(r'Pricing\s*\n+([^\n]+)', card_text)
    if pricing_match:
        data["total_price"] = extract_price(pricing_match.group(1))
    else:
        price_fallback = re.search(r'[€$£]\s*([\d,]+(?:\.\d+)?)', card_text)
        if price_fallback:
            data["total_price"] = extract_price(price_fallback.group(0))

    # Pricing Breakdown details (Retail Price, Revenue, Commission Breakdown)
    total_row = re.search(r'Total:\s*([€$£\w,.]+)\s+([€$£\w,.]+)\s+(\d+(?:\.\d+)?)\s*%', card_text)
    if total_row:
        data["retail_price"] = total_row.group(1).strip()
        data["revenue"] = total_row.group(2).strip()
        try:
            data["commission_breakdown"] = float(total_row.group(3)) / 100.0
        except Exception:
            pass
    else:
        # Fallback to row under table headers
        table_match = re.search(r'(?:Retail Price\s+Revenue|Retail Price\tRevenue)[^\n]*\n+[^\t\n]+\s+([€$£\w,.]+)\s+([€$£\w,.]+)\s+(\d+(?:\.\d+)?)\s*%', card_text)
        if table_match:
            data["retail_price"] = table_match.group(1).strip()
            data["revenue"] = table_match.group(2).strip()
            try:
                data["commission_breakdown"] = float(table_match.group(3)) / 100.0
            except Exception:
                pass
        else:
            comm_match = re.search(r'\((\d+(?:\.\d+)?)\s*%\s*commission\)', card_text, re.IGNORECASE)
            if comm_match:
                try:
                    data["commission_breakdown"] = float(comm_match.group(1)) / 100.0
                except Exception:
                    pass

    # 9. Pickup Location
    if "Pickup details" in card_text:
        pickup_section = card_text.split("Pickup details", 1)[1]
        loc_match = re.search(r'Location\s*\n+([^\n]+)', pickup_section)
        if loc_match:
            loc_val = loc_match.group(1).strip()
            if loc_val.lower() not in ["specify time", "edit"]:
                data["pickup_location"] = loc_val

    return data
