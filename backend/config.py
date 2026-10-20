# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Supabase Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_HEADERS = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    # SMS / USSD configuration
    SMS_MODE = os.getenv("SMS_MODE", "mock")  # mock | africastalking | other
    AFRICAS_TALKING_USERNAME = os.getenv("AFRICASTALKING_USERNAME")
    AFRICAS_TALKING_API_KEY = os.getenv("AFRICASTALKING_API_KEY")
    USSD_SHORTCODE = os.getenv("USSD_SHORTCODE", "*384#")

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

# Select the configuration based on environment
env = os.getenv("FLASK_ENV", "development")
config = DevelopmentConfig() if env == "development" else ProductionConfig()