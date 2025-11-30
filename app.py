from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_session import Session
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json
import os
from config import Config
from data_processor import process_patient_data, get_patient_info
from llm_analyzer import analyze_timeline_summary, analyze_unaddressed_events

# Allow HTTP for localhost (required for local development)
# WARNING: Only use this for local development, never in production!
if os.environ.get('FLASK_ENV') == 'development' or 'localhost' in os.environ.get('GOOGLE_REDIRECT_URI', ''):
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.config.from_object(Config)
Session(app)

# OAuth 2.0 scopes
SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']

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
    
    # Check if we have OAuth credentials configured
    client_id = app.config.get('GOOGLE_CLIENT_ID', '').strip()
    client_secret = app.config.get('GOOGLE_CLIENT_SECRET', '').strip()
    redirect_uri = app.config.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/login/callback').strip()
    
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
        return redirect(url_for('patient_lookup'))
    
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
    if not state or state != received_state:
        print(f"DEBUG: State mismatch. Expected: {state}, Received: {received_state}")
        return "Invalid state parameter", 400
    
    client_id = app.config.get('GOOGLE_CLIENT_ID', '').strip()
    client_secret = app.config.get('GOOGLE_CLIENT_SECRET', '').strip()
    redirect_uri = app.config.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/login/callback').strip()
    
    if not client_id or not client_secret:
        return "OAuth not configured", 500
    
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
        
        flow = Flow.from_client_config(client_config, scopes=SCOPES, state=state)
        flow.redirect_uri = redirect_uri
        
        print(f"DEBUG: Fetching token with URL: {request.url[:200]}...")
        flow.fetch_token(authorization_response=request.url)
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

@app.route('/patient-lookup', methods=['GET', 'POST'])
@require_auth
def patient_lookup():
    """Patient lookup form."""
    if request.method == 'POST':
        cpmrn = request.form.get('cpmrn', '')
        encounters = request.form.get('encounters', '')
        # For now, we'll just redirect to timeline with dummy data
        return redirect(url_for('timeline'))
    return render_template('patient_lookup.html')

@app.route('/timeline')
@require_auth
def timeline():
    """Main timeline view."""
    patient_data = load_patient_data()
    if not patient_data:
        return "Error loading patient data", 500
    
    patient_info = get_patient_info(patient_data)
    timeline_events = process_patient_data(patient_data)
    
    # Convert datetime objects to strings for JSON serialization
    for event in timeline_events:
        if hasattr(event['timestamp'], 'isoformat'):
            event['timestamp'] = event['timestamp'].isoformat()
    
    # Generate LLM analyses
    timeline_summary = analyze_timeline_summary(timeline_events)
    unaddressed_analysis = analyze_unaddressed_events(timeline_events)
    
    return render_template('timeline.html', 
                         patient=patient_info, 
                         events=timeline_events,
                         timeline_summary=timeline_summary,
                         unaddressed_analysis=unaddressed_analysis,
                         user_name=session.get('user_name', 'User'))

@app.route('/api/patient-data', methods=['POST'])
@require_auth
def api_patient_data():
    """Dummy API endpoint that returns patient JSON regardless of input."""
    patient_data = load_patient_data()
    if not patient_data:
        return jsonify({'error': 'Patient data not found'}), 404
    return jsonify(patient_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

