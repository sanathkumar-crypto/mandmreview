#!/usr/bin/env python3
"""Test script to verify OAuth configuration"""
import os
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow

load_dotenv()

CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '').strip()
CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '').strip()
REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5001/login/callback').strip()

print("=" * 60)
print("OAuth Configuration Test")
print("=" * 60)
print(f"Client ID: {CLIENT_ID[:30]}...{CLIENT_ID[-20:] if len(CLIENT_ID) > 50 else CLIENT_ID}")
print(f"Client ID length: {len(CLIENT_ID)}")
print(f"Client ID format valid: {CLIENT_ID.endswith('.apps.googleusercontent.com')}")
print(f"Client Secret: {'SET' if CLIENT_SECRET else 'NOT SET'}")
print(f"Client Secret length: {len(CLIENT_SECRET) if CLIENT_SECRET else 0}")
print(f"Redirect URI: {REDIRECT_URI}")
print()

if not CLIENT_ID or not CLIENT_SECRET:
    print("ERROR: Missing credentials in .env file")
    exit(1)

try:
    print("Testing OAuth flow creation...")
    client_config = {
        "web": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']
    )
    flow.redirect_uri = REDIRECT_URI
    
    print("✓ OAuth flow created successfully")
    print()
    print("Generating authorization URL...")
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    print(f"✓ Authorization URL generated")
    print(f"  State: {state}")
    print(f"  URL (first 100 chars): {auth_url[:100]}...")
    print()
    print("=" * 60)
    print("SUCCESS: OAuth configuration appears valid!")
    print("=" * 60)
    print()
    print("If you're still getting 'OAuth client not found' error:")
    print("1. Verify the Client ID exists in Google Cloud Console")
    print("2. Check that the redirect URI matches exactly:")
    print(f"   {REDIRECT_URI}")
    print("3. Ensure OAuth consent screen is configured")
    print("4. Make sure you're using the correct Google Cloud project")
    
except Exception as e:
    print(f"✗ ERROR: {e}")
    print()
    import traceback
    traceback.print_exc()
    print()
    print("=" * 60)
    print("TROUBLESHOOTING:")
    print("=" * 60)
    print("1. Verify Client ID and Secret in Google Cloud Console:")
    print("   https://console.cloud.google.com/apis/credentials")
    print("2. Check that the redirect URI is authorized:")
    print(f"   {REDIRECT_URI}")
    print("3. Ensure OAuth consent screen is published or in testing mode")
    print("4. Verify you're using credentials from the correct project")

