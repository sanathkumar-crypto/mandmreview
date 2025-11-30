import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'session:'
    
    # Google OAuth settings
    # Set these in .env file
    # For OAuth: Go to https://console.cloud.google.com/apis/credentials
    # Create OAuth 2.0 Client ID credentials
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/login/callback')
    
    # Allowed email domain
    ALLOWED_EMAIL_DOMAIN = '@cloudphysician.net'
    
    # Patient data file
    PATIENT_DATA_FILE = 'pat_jsons.json'
    
    # Gemini API settings
    # Set this in .env file
    # Get API key from: https://makersuite.google.com/app/apikey
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash-exp')  # Try gemini-2.0 first, fallback to 1.5

