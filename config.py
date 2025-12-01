import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_mnm_secret_key():
    """
    Load configuration from MNM_SECRET_KEY JSON secret (for Cloud Run)
    or fall back to individual environment variables (for local development)
    """
    mnm_secret = os.environ.get('MNM_SECRET_KEY', '')
    if mnm_secret:
        try:
            # Parse JSON secret
            secret_data = json.loads(mnm_secret)
            print(f"DEBUG: Successfully parsed MNM_SECRET_KEY JSON")
            print(f"DEBUG: Found keys: {list(secret_data.keys())}")
            return {
                'SECRET_KEY': secret_data.get('SECRET_KEY', ''),
                'GOOGLE_CLIENT_ID': secret_data.get('GOOGLE_CLIENT_ID', ''),
                'GOOGLE_CLIENT_SECRET': secret_data.get('GOOGLE_CLIENT_SECRET', ''),
                'GOOGLE_REDIRECT_URI': secret_data.get('GOOGLE_REDIRECT_URI', '')
            }
        except (json.JSONDecodeError, TypeError) as e:
            # If JSON parsing fails, fall back to individual env vars
            print(f"ERROR: Failed to parse MNM_SECRET_KEY as JSON: {e}")
            print(f"DEBUG: MNM_SECRET_KEY value (first 100 chars): {mnm_secret[:100]}")
            return None
    else:
        print("DEBUG: MNM_SECRET_KEY environment variable not set, using individual env vars")
    return None

# Try to load from JSON secret first, then fall back to individual env vars
_secret_config = load_mnm_secret_key()

class Config:
    # Load from JSON secret if available, otherwise from individual env vars
    if _secret_config:
        SECRET_KEY = _secret_config['SECRET_KEY'] or 'dev-secret-key-change-in-production'
        GOOGLE_CLIENT_ID = _secret_config['GOOGLE_CLIENT_ID'] or ''
        GOOGLE_CLIENT_SECRET = _secret_config['GOOGLE_CLIENT_SECRET'] or ''
        # Use the redirect URI from secret, or try to detect Cloud Run URL
        default_redirect = os.environ.get('GOOGLE_REDIRECT_URI', '')
        if not default_redirect and os.environ.get('K_SERVICE'):
            # We're in Cloud Run, construct URL from environment
            service_url = os.environ.get('K_SERVICE_URL', '')
            if service_url:
                default_redirect = f"{service_url}/login/callback"
        GOOGLE_REDIRECT_URI = _secret_config['GOOGLE_REDIRECT_URI'] or default_redirect or 'http://localhost:5001/login/callback'
        print(f"DEBUG: Loaded config from MNM_SECRET_KEY - Client ID present: {bool(GOOGLE_CLIENT_ID)}, Redirect URI: {GOOGLE_REDIRECT_URI}")
    else:
        SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
        GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
        GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
        GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5001/login/callback')
        print(f"DEBUG: Loaded config from individual env vars - Client ID present: {bool(GOOGLE_CLIENT_ID)}")
    
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'session:'
    # Ensure session directory exists
    SESSION_FILE_DIR = os.path.join(os.path.dirname(__file__), 'flask_session')
    SESSION_FILE_THRESHOLD = 500
    
    # Allowed email domain
    ALLOWED_EMAIL_DOMAIN = '@cloudphysician.net'
    
    # Patient data file
    PATIENT_DATA_FILE = 'pat_jsons.json'
    
    # Gemini API settings
    # Set this in .env file
    # Get API key from: https://makersuite.google.com/app/apikey
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash-exp')  # Try gemini-2.0 first, fallback to 1.5
    
    # RADAR API settings
    # RADAR_URL comes from environment variable or .env file
    # For local development, it can be set in .env file
    RADAR_URL = os.environ.get('RADAR_URL', '')
    # RADAR_READ_SERVICE_ACCOUNT comes from environment variable or .env file
    # Can also be loaded from radar_service_account.json file using load_radar_read_service_account()
    # For local development, it can be set in .env file as a JSON string
    RADAR_READ_SERVICE_ACCOUNT = os.environ.get('RADAR_READ_SERVICE_ACCOUNT', '')

