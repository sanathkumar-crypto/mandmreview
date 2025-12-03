#!/usr/bin/env python3
"""Debug script to check OAuth configuration."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("OAuth Configuration Debug")
print("=" * 60)

# Check environment variables
client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')
redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/login/callback')

print(f"\n1. Environment Variables:")
print(f"   GOOGLE_CLIENT_ID: {'SET' if client_id else 'NOT SET'} (length: {len(client_id)})")
if client_id:
    print(f"      First 30 chars: {client_id[:30]}...")
    print(f"      Last 30 chars: ...{client_id[-30:]}")
    print(f"      Ends with .apps.googleusercontent.com: {client_id.endswith('.apps.googleusercontent.com')}")

print(f"\n   GOOGLE_CLIENT_SECRET: {'SET' if client_secret else 'NOT SET'} (length: {len(client_secret)})")
if client_secret:
    print(f"      First 20 chars: {client_secret[:20]}...")
    print(f"      Starts with GOCSPX-: {client_secret.startswith('GOCSPX-')}")

print(f"\n   GOOGLE_REDIRECT_URI: {redirect_uri}")

# Check config.py
print(f"\n2. Config.py Loading:")
from config import Config
config_client_id = Config.GOOGLE_CLIENT_ID
config_client_secret = Config.GOOGLE_CLIENT_SECRET
config_redirect_uri = Config.GOOGLE_REDIRECT_URI

print(f"   Config.GOOGLE_CLIENT_ID: {'SET' if config_client_id else 'NOT SET'} (length: {len(config_client_id) if config_client_id else 0})")
print(f"   Config.GOOGLE_CLIENT_SECRET: {'SET' if config_client_secret else 'NOT SET'} (length: {len(config_client_secret) if config_client_secret else 0})")
print(f"   Config.GOOGLE_REDIRECT_URI: {config_redirect_uri}")

# Test OAuth flow creation
print(f"\n3. Testing OAuth Flow Creation:")
if config_client_id and config_client_secret:
    try:
        from google_auth_oauthlib.flow import Flow
        
        # Set insecure transport for localhost
        if 'localhost' in config_redirect_uri or '127.0.0.1' in config_redirect_uri:
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
            print(f"   ✓ OAUTHLIB_INSECURE_TRANSPORT set to 1")
        
        client_config = {
            "web": {
                "client_id": config_client_id,
                "client_secret": config_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [config_redirect_uri]
            }
        }
        
        SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']
        flow = Flow.from_client_config(client_config, scopes=SCOPES)
        flow.redirect_uri = config_redirect_uri
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        print(f"   ✓ OAuth flow created successfully!")
        print(f"   ✓ Authorization URL generated: {authorization_url[:80]}...")
        print(f"   ✓ State parameter: {state[:20]}...")
    except Exception as e:
        print(f"   ✗ ERROR creating OAuth flow: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"   ✗ Cannot test - credentials not configured")

print("\n" + "=" * 60)

