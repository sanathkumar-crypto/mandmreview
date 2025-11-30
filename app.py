from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_session import Session
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json
import os
from config import Config
from data_processor import process_patient_data, get_patient_info

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
    if not app.config.get('GOOGLE_CLIENT_ID') or not app.config.get('GOOGLE_CLIENT_SECRET'):
        # For development, allow bypass
        return render_template('login.html', oauth_configured=False)
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": app.config['GOOGLE_CLIENT_ID'],
                "client_secret": app.config['GOOGLE_CLIENT_SECRET'],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [app.config['GOOGLE_REDIRECT_URI']]
            }
        },
        scopes=SCOPES
    )
    flow.redirect_uri = app.config['GOOGLE_REDIRECT_URI']
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/login/callback')
def login_callback():
    """Handle OAuth callback."""
    # Check for development bypass
    if request.args.get('dev') == 'true':
        session['user_email'] = 'dev@cloudphysician.net'
        session['user_name'] = 'Development User'
        return redirect(url_for('patient_lookup'))
    
    if 'error' in request.args:
        return f"Error: {request.args.get('error')}", 400
    
    state = session.get('oauth_state')
    if not state or state != request.args.get('state'):
        return "Invalid state parameter", 400
    
    if not app.config.get('GOOGLE_CLIENT_ID') or not app.config.get('GOOGLE_CLIENT_SECRET'):
        return "OAuth not configured", 500
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": app.config['GOOGLE_CLIENT_ID'],
                "client_secret": app.config['GOOGLE_CLIENT_SECRET'],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [app.config['GOOGLE_REDIRECT_URI']]
            }
        },
        scopes=SCOPES,
        state=state
    )
    flow.redirect_uri = app.config['GOOGLE_REDIRECT_URI']
    
    flow.fetch_token(authorization_response=request.url)
    
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
    service = build('oauth2', 'v2', credentials=credentials)
    user_info = service.userinfo().get().execute()
    
    email = user_info.get('email', '')
    if not email.endswith('@cloudphysician.net'):
        session.clear()
        return "Access denied. Only @cloudphysician.net email addresses are allowed.", 403
    
    session['user_email'] = email
    session['user_name'] = user_info.get('name', email)
    session.pop('oauth_state', None)
    
    return redirect(url_for('patient_lookup'))

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
    
    return render_template('timeline.html', 
                         patient=patient_info, 
                         events=timeline_events,
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

