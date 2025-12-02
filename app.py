from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_session import Session
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs, urlencode
import json
import os
import logging
from dotenv import load_dotenv
from config import Config
from data_processor import process_patient_data, get_patient_info
from llm_analyzer import analyze_timeline_summary, analyze_unaddressed_events
from radar_service import get_patient_json, load_radar_read_service_account, get_user_role

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Allow HTTP for localhost (required for local development)
# WARNING: Only use this for local development, never in production!
# In Cloud Run, we use HTTPS, so explicitly unset OAUTHLIB_INSECURE_TRANSPORT
if os.environ.get('K_SERVICE'):
    # We're in Cloud Run - ensure HTTPS is enforced
    os.environ.pop('OAUTHLIB_INSECURE_TRANSPORT', None)
elif os.environ.get('FLASK_ENV') == 'development' or 'localhost' in os.environ.get('GOOGLE_REDIRECT_URI', ''):
    # Local development - allow HTTP
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    print("DEBUG: OAUTHLIB_INSECURE_TRANSPORT set to 1 for localhost development")

app = Flask(__name__)
app.config.from_object(Config)
# Configure session cookie settings for OAuth flow
# In Cloud Run, use secure cookies (HTTPS)
is_cloud_run = bool(os.environ.get('K_SERVICE'))
app.config['SESSION_COOKIE_SECURE'] = is_cloud_run  # True in Cloud Run (HTTPS), False for localhost
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Log configuration on startup
logger.info(f"Running in Cloud Run: {is_cloud_run}")
logger.info(f"OAuth Client ID configured: {bool(app.config.get('GOOGLE_CLIENT_ID'))}")
logger.info(f"OAuth Redirect URI: {app.config.get('GOOGLE_REDIRECT_URI', 'Not set')}")
# Ensure session directory exists
session_dir = app.config.get('SESSION_FILE_DIR', 'flask_session')
os.makedirs(session_dir, exist_ok=True)
Session(app)

# OAuth 2.0 scopes
SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']

# Load Radar service account on startup
if not Config.RADAR_READ_SERVICE_ACCOUNT:
    logger.info("Attempting to load Radar service account from file...")
    if load_radar_read_service_account():
        # Update Config with the loaded service account from environment
        Config.RADAR_READ_SERVICE_ACCOUNT = os.environ.get('RADAR_READ_SERVICE_ACCOUNT', '')

def load_patient_data():
    """Load patient data from JSON file."""
    try:
        with open(Config.PATIENT_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # If it's a list, take the first item
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            return data
    except Exception as e:
        print(f"Error loading patient data: {e}")
        return None

def is_authenticated():
    """Check if user is authenticated."""
    # In local development (not Cloud Run), bypass OAuth
    if not is_cloud_run:
        return True
    return 'user_email' in session and session.get('user_email', '').endswith('@cloudphysician.net')

def require_auth(f):
    """Decorator to require authentication."""
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def index():
    """Home page - redirects to login or patient lookup."""
    if is_authenticated():
        return redirect(url_for('patient_lookup'))
    return redirect(url_for('login'))

@app.route('/login')
def login():
    """Initiate Google OAuth login."""
    if is_authenticated():
        return redirect(url_for('patient_lookup'))
    
    # In local development (not Cloud Run), bypass OAuth and auto-authenticate
    if not is_cloud_run:
        logger.info("Local development mode: bypassing OAuth")
        session['user_email'] = 'dev@cloudphysician.net'
        session['user_name'] = 'Development User'
        # Set default role for development (can be overridden via env var)
        session['user_role'] = os.environ.get('DEV_USER_ROLE', '')
        return redirect(url_for('patient_lookup'))
    
    # Ensure OAUTHLIB_INSECURE_TRANSPORT is set for localhost
    redirect_uri = app.config.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/login/callback').strip()
    if 'localhost' in redirect_uri or '127.0.0.1' in redirect_uri:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    # Check if we have OAuth credentials configured
    client_id = app.config.get('GOOGLE_CLIENT_ID', '').strip()
    client_secret = app.config.get('GOOGLE_CLIENT_SECRET', '').strip()
    
    # Debug logging
    print(f"DEBUG: Client ID present: {bool(client_id)}")
    print(f"DEBUG: Client ID length: {len(client_id) if client_id else 0}")
    print(f"DEBUG: Client ID starts with: {client_id[:20] if client_id else 'N/A'}...")
    print(f"DEBUG: Client Secret present: {bool(client_secret)}")
    print(f"DEBUG: Redirect URI: {redirect_uri}")
    
    if not client_id or not client_secret:
        # For development, allow bypass
        error_msg = "OAuth credentials not found in configuration"
        print(f"DEBUG: {error_msg}")
        return render_template('login.html', oauth_configured=False, oauth_error=error_msg)
    
    try:
        # Validate client ID format
        if not client_id.endswith('.apps.googleusercontent.com'):
            raise ValueError(f"Invalid Client ID format. Should end with .apps.googleusercontent.com")
        
        # Validate client secret format
        if not client_secret.startswith('GOCSPX-'):
            print("WARNING: Client Secret doesn't start with GOCSPX-, but continuing anyway...")
        
        client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        }
        
        print(f"DEBUG: Creating OAuth flow with redirect URI: {redirect_uri}")
        flow = Flow.from_client_config(client_config, scopes=SCOPES)
        flow.redirect_uri = redirect_uri
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        session['oauth_state'] = state
        print(f"DEBUG: OAuth flow created successfully, redirecting to: {authorization_url[:100]}...")
        return redirect(authorization_url)
    except ValueError as e:
        error_msg = f"Configuration error: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return render_template('login.html', 
                             oauth_configured=False, 
                             oauth_error=error_msg)
    except Exception as e:
        # If OAuth fails, show error and allow dev bypass
        error_msg = f"OAuth error: {str(e)}"
        print(f"DEBUG: {error_msg}")
        import traceback
        traceback.print_exc()
        return render_template('login.html', 
                             oauth_configured=False, 
                             oauth_error=error_msg)

@app.route('/login/callback')
def login_callback():
    """Handle OAuth callback."""
    # Check for development bypass
    if request.args.get('dev') == 'true':
        session['user_email'] = 'dev@cloudphysician.net'
        session['user_name'] = 'Development User'
        # Set default role for development (can be overridden via env var)
        session['user_role'] = os.environ.get('DEV_USER_ROLE', '')
        return redirect(url_for('patient_lookup'))
    
    # Ensure OAUTHLIB_INSECURE_TRANSPORT is set for localhost
    redirect_uri = app.config.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/login/callback').strip()
    if 'localhost' in redirect_uri or '127.0.0.1' in redirect_uri:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    if 'error' in request.args:
        error = request.args.get('error')
        error_description = request.args.get('error_description', '')
        print(f"DEBUG: OAuth error from Google: {error}")
        print(f"DEBUG: Error description: {error_description}")
        return render_template('login.html', 
                             oauth_configured=False, 
                             oauth_error=f"OAuth Error: {error}. {error_description}")
    
    state = session.get('oauth_state')
    received_state = request.args.get('state')
    
    # Debug session info
    print(f"DEBUG: Session ID: {session.get('_id', 'N/A')}")
    print(f"DEBUG: Session keys: {list(session.keys())}")
    print(f"DEBUG: OAuth state in session: {state}")
    print(f"DEBUG: Received state from callback: {received_state}")
    
    client_id = app.config.get('GOOGLE_CLIENT_ID', '').strip()
    client_secret = app.config.get('GOOGLE_CLIENT_SECRET', '').strip()
    
    if not client_id or not client_secret:
        return "OAuth not configured", 500
    
    # Validate state - if session state exists, it must match. Otherwise, proceed with received state
    if state and state != received_state:
        print(f"DEBUG: State mismatch. Expected: {state}, Received: {received_state}")
        return "Invalid state parameter", 400
    elif not state:
        # State was lost from session - this happens in development with Flask-Session issues
        # We can still proceed if we have a valid code and received_state
        print(f"DEBUG: WARNING - State lost from session but received: {received_state}")
        if not received_state or not request.args.get('code'):
            return "Session expired. Please try again.", 400
    
    try:
        print(f"DEBUG: Creating OAuth flow for callback with redirect URI: {redirect_uri}")
        client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        }
        
        # Create flow without state - we'll validate it separately
        # The Flow doesn't require state for token exchange, only for validation
        flow = Flow.from_client_config(client_config, scopes=SCOPES)
        flow.redirect_uri = redirect_uri
        
        # In Cloud Run, ensure we use HTTPS for the callback URL
        # request.url might be HTTP internally, but we need HTTPS for OAuth
        callback_url = request.url
        if os.environ.get('K_SERVICE'):
            # We're in Cloud Run - construct proper HTTPS URL
            if redirect_uri.startswith('https://'):
                # Use the redirect_uri as base and append query parameters
                parsed_request = urlparse(request.url)
                query_params = parse_qs(parsed_request.query)
                # Build the callback URL using the configured redirect_uri
                callback_url = f"{redirect_uri}?{urlencode(query_params, doseq=True)}"
            elif callback_url.startswith('http://'):
                # Fallback: just replace http with https
                callback_url = callback_url.replace('http://', 'https://', 1)
        
        print(f"DEBUG: Fetching token with URL: {callback_url[:200]}...")
        flow.fetch_token(authorization_response=callback_url)
        print("DEBUG: Token fetched successfully")
        
        credentials = flow.credentials
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        # Get user info
        print("DEBUG: Building OAuth2 service to get user info")
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        print(f"DEBUG: User info retrieved: {user_info.get('email', 'N/A')}")
        
        email = user_info.get('email', '')
        if not email.endswith('@cloudphysician.net'):
            session.clear()
            return "Access denied. Only @cloudphysician.net email addresses are allowed.", 403
        
        session['user_email'] = email
        session['user_name'] = user_info.get('name', email)
        session.pop('oauth_state', None)
        
        # Get user role from Radar API
        try:
            user_role = get_user_role(email)
            if user_role:
                session['user_role'] = user_role
                logger.info(f"User role retrieved: {user_role}")
            else:
                logger.warning(f"Could not retrieve user role for {email}")
        except Exception as e:
            logger.error(f"Error retrieving user role: {e}")
        
        return redirect(url_for('patient_lookup'))
    except Exception as e:
        error_msg = f"OAuth callback error: {str(e)}"
        print(f"DEBUG: {error_msg}")
        import traceback
        traceback.print_exc()
        return render_template('login.html', 
                             oauth_configured=False, 
                             oauth_error=error_msg)

@app.route('/logout')
def logout():
    """Logout user."""
    session.clear()
    return redirect(url_for('login'))

@app.route('/debug/oauth')
def debug_oauth():
    """Debug endpoint to check OAuth configuration."""
    import json
    debug_info = {
        'credentials_loaded': {
            'client_id': bool(app.config.get('GOOGLE_CLIENT_ID')),
            'client_secret': bool(app.config.get('GOOGLE_CLIENT_SECRET')),
            'redirect_uri': app.config.get('GOOGLE_REDIRECT_URI', 'NOT SET')
        },
        'client_id_format': {
            'ends_with_correct_suffix': app.config.get('GOOGLE_CLIENT_ID', '').endswith('.apps.googleusercontent.com') if app.config.get('GOOGLE_CLIENT_ID') else False,
            'length': len(app.config.get('GOOGLE_CLIENT_ID', ''))
        },
        'client_secret_format': {
            'starts_with_gocspx': app.config.get('GOOGLE_CLIENT_SECRET', '').startswith('GOCSPX-') if app.config.get('GOOGLE_CLIENT_SECRET') else False,
            'length': len(app.config.get('GOOGLE_CLIENT_SECRET', ''))
        },
        'environment': {
            'oauthlib_insecure_transport': os.environ.get('OAUTHLIB_INSECURE_TRANSPORT', 'NOT SET'),
            'redirect_uri_contains_localhost': 'localhost' in app.config.get('GOOGLE_REDIRECT_URI', '')
        },
        'checklist': {
            'redirect_uri_in_google_console': 'MANUAL CHECK REQUIRED: Go to https://console.cloud.google.com/apis/credentials and verify the redirect URI is added',
            'oauth_consent_screen_configured': 'MANUAL CHECK REQUIRED: Go to https://console.cloud.google.com/apis/credentials/consent and verify it\'s configured',
            'test_users_added': 'MANUAL CHECK REQUIRED: If using External user type, add test users in OAuth consent screen'
        }
    }
    return jsonify(debug_info)

@app.route('/patient-lookup', methods=['GET', 'POST'])
@require_auth
def patient_lookup():
    """Patient lookup form."""
    if request.method == 'POST':
        cpmrn = request.form.get('cpmrn', '').strip()
        encounters = request.form.get('encounters', '').strip()
        
        if not cpmrn or not encounters:
            flash('Please provide both CPMRN and Encounters', 'error')
            has_patient_data = bool(session.get('patient_data'))
            return render_template('patient_lookup.html', 
                                 user_email=session.get('user_email', ''),
                                 has_patient_data=has_patient_data)
        
        # Try to load service account if not already loaded
        if not Config.RADAR_READ_SERVICE_ACCOUNT:
            if load_radar_read_service_account():
                Config.RADAR_READ_SERVICE_ACCOUNT = os.environ.get('RADAR_READ_SERVICE_ACCOUNT', '')
        
        if not Config.RADAR_READ_SERVICE_ACCOUNT:
            flash('Radar service account not configured. Please check configuration.', 'error')
            has_patient_data = bool(session.get('patient_data'))
            return render_template('patient_lookup.html', 
                                 user_email=session.get('user_email', ''),
                                 has_patient_data=has_patient_data)
        
        if not Config.RADAR_URL:
            flash('Radar URL not configured. Please set RADAR_URL in environment variables.', 'error')
            has_patient_data = bool(session.get('patient_data'))
            return render_template('patient_lookup.html', 
                                 user_email=session.get('user_email', ''),
                                 has_patient_data=has_patient_data)
        
        # Get patient data from Radar API
        logger.info(f"Fetching patient data for CPMRN: {cpmrn}, Encounters: {encounters}")
        patient_data = get_patient_json(cpmrn, encounters)
        
        if not patient_data:
            flash(f'Patient not found for CPMRN: {cpmrn}, Encounters: {encounters}', 'error')
            has_patient_data = bool(session.get('patient_data'))
            return render_template('patient_lookup.html', 
                                 user_email=session.get('user_email', ''),
                                 has_patient_data=has_patient_data)
        
        # Store patient data in session for timeline view
        session['patient_data'] = patient_data
        session['cpmrn'] = cpmrn
        session['encounters'] = encounters
        
        return redirect(url_for('timeline'))
    
    # Check if patient data exists in session
    has_patient_data = bool(session.get('patient_data'))
    
    return render_template('patient_lookup.html', 
                         user_email=session.get('user_email', ''),
                         has_patient_data=has_patient_data)

@app.route('/timeline')
@require_auth
def timeline():
    """Main timeline view."""
    # Try to get patient data from session first (from Radar API lookup)
    patient_data = session.get('patient_data')
    
    # Fallback to loading from file if not in session
    if not patient_data:
        logger.info("No patient data in session, loading from file...")
        patient_data = load_patient_data()
    
    if not patient_data:
        flash('No patient data available. Please lookup a patient first.', 'error')
        return redirect(url_for('patient_lookup'))
    
    patient_info = get_patient_info(patient_data)
    timeline_events = process_patient_data(patient_data)
    
    # Convert datetime objects to strings for JSON serialization
    for event in timeline_events:
        if hasattr(event['timestamp'], 'isoformat'):
            event['timestamp'] = event['timestamp'].isoformat()
    
    # Generate LLM analyses (only if there are events to analyze)
    timeline_summary = None
    unaddressed_analysis = None
    if timeline_events:
        timeline_summary = analyze_timeline_summary(timeline_events)
        unaddressed_analysis = analyze_unaddressed_events(timeline_events)
    
    # Patient data exists if we got here (otherwise would have redirected)
    return render_template('timeline.html', 
                         patient=patient_info, 
                         events=timeline_events,
                         timeline_summary=timeline_summary,
                         unaddressed_analysis=unaddressed_analysis,
                         user_name=session.get('user_name', 'User'),
                         user_email=session.get('user_email', ''),
                         has_patient_data=True)

@app.route('/download-patient-json')
@require_auth
def download_patient_json():
    """Download patient JSON file - restricted to specific users."""
    user_email = session.get('user_email', '')
    allowed_users = ['dileep.unni@cloudphysician.net', 'sanath.kumar@cloudphysician.net']
    
    if user_email not in allowed_users:
        flash('Access denied. You do not have permission to download patient data.', 'error')
        return redirect(url_for('patient_lookup'))
    
    # Get patient data from session or file
    patient_data = session.get('patient_data') or load_patient_data()
    
    if not patient_data:
        flash('No patient data available to download.', 'error')
        return redirect(url_for('patient_lookup'))
    
    # Get patient identifier for filename
    cpmrn = session.get('cpmrn', 'patient')
    encounters = session.get('encounters', '')
    filename = f"patient_{cpmrn}_{encounters}.json" if encounters else f"patient_{cpmrn}.json"
    
    # Create response with JSON data
    response = jsonify(patient_data)
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    response.headers['Content-Type'] = 'application/json'
    
    return response

@app.route('/api/patient-data', methods=['POST'])
@require_auth
def api_patient_data():
    """API endpoint that returns patient JSON from Radar API or file."""
    data = request.get_json() or {}
    cpmrn = data.get('cpmrn', '').strip()
    encounters = data.get('encounters', '').strip()
    
    # If CPMRN and encounters provided, fetch from Radar API
    if cpmrn and encounters:
        # Try to load service account if not already loaded
        if not Config.RADAR_READ_SERVICE_ACCOUNT:
            if load_radar_read_service_account():
                Config.RADAR_READ_SERVICE_ACCOUNT = os.environ.get('RADAR_READ_SERVICE_ACCOUNT', '')
        
        if not Config.RADAR_READ_SERVICE_ACCOUNT or not Config.RADAR_URL:
            return jsonify({'error': 'Radar service not configured'}), 500
        
        patient_data = get_patient_json(cpmrn, encounters)
        if not patient_data:
            return jsonify({'error': f'Patient not found for CPMRN: {cpmrn}, Encounters: {encounters}'}), 404
        return jsonify(patient_data)
    
    # Otherwise, return from session or file
    patient_data = session.get('patient_data') or load_patient_data()
    if not patient_data:
        return jsonify({'error': 'Patient data not found'}), 404
    return jsonify(patient_data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)

