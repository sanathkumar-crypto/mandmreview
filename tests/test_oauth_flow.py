#!/usr/bin/env python3
"""Test the OAuth flow end-to-end."""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Set insecure transport
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from flask import Flask
from flask_session import Session
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
Session(app)

print("Testing OAuth configuration in Flask app context...")
print(f"Client ID from config: {'SET' if app.config.get('GOOGLE_CLIENT_ID') else 'NOT SET'}")
print(f"Client Secret from config: {'SET' if app.config.get('GOOGLE_CLIENT_SECRET') else 'NOT SET'}")
print(f"Redirect URI from config: {app.config.get('GOOGLE_REDIRECT_URI')}")

# Test the login route logic
with app.app_context():
    client_id = app.config.get('GOOGLE_CLIENT_ID', '').strip()
    client_secret = app.config.get('GOOGLE_CLIENT_SECRET', '').strip()
    redirect_uri = app.config.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/login/callback').strip()
    
    if not client_id or not client_secret:
        print("ERROR: Credentials not found in Flask config!")
        sys.exit(1)
    
    print(f"\n✓ Credentials found in Flask config")
    print(f"  Client ID: {client_id[:30]}...{client_id[-20:]}")
    print(f"  Redirect URI: {redirect_uri}")
    
    # Check redirect URI format
    print(f"\nImportant: Make sure this redirect URI is added in Google Cloud Console:")
    print(f"  {redirect_uri}")
    print(f"\nTo add it:")
    print(f"  1. Go to https://console.cloud.google.com/apis/credentials")
    print(f"  2. Click on your OAuth 2.0 Client ID")
    print(f"  3. Under 'Authorized redirect URIs', add: {redirect_uri}")
    print(f"  4. Click 'Save'")


