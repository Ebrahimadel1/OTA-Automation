import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Airtable
    AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
    AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
    AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
    
    # GetYourGuide
    GYG_LOGIN_EMAIL = os.getenv("GYG_LOGIN_EMAIL")
    GYG_LOGIN_PASSWORD = os.getenv("GYG_LOGIN_PASSWORD")
    GYG_TOTP_SECRET = os.getenv("GYG_TOTP_SECRET")
    PORTAL_TIMEZONE = os.getenv("PORTAL_TIMEZONE", "Africa/Cairo")
    
    # Operation modes
    HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
    DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Default URL
    GYG_BASE_URL = "https://supplier.getyourguide.com"
