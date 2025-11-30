# OAuth Troubleshooting Guide

## Current Status
✅ OAuth credentials are present in `.env`
✅ Credentials format is valid
✅ OAuth flow can be created locally
❌ Getting "OAuth client was not found" from Google

## Most Common Causes

### 1. OAuth Consent Screen Not Configured
**Fix:**
1. Go to: https://console.cloud.google.com/apis/credentials/consent
2. Select your project
3. Configure the OAuth consent screen:
   - User Type: External (or Internal if using Google Workspace)
   - App name: "M&M Review System"
   - User support email: Your email
   - Developer contact: Your email
4. Add scopes:
   - `email`
   - `profile`
   - `openid`
5. Add test users (if in Testing mode): Add `@cloudphysician.net` email addresses
6. Click "Save and Continue" through all steps
7. **Publish the app** (or keep in Testing mode with test users added)

### 2. Redirect URI Not Authorized
**Fix:**
1. Go to: https://console.cloud.google.com/apis/credentials
2. Find your OAuth 2.0 Client ID
3. Click to edit it
4. Under "Authorized redirect URIs", make sure you have EXACTLY:
   ```
   http://localhost:5000/login/callback
   ```
   - No trailing slash
   - Must be `http://` not `https://` for localhost
   - Case sensitive
5. Click "Save"

### 3. Wrong Google Cloud Project
**Fix:**
1. Verify the Client ID `1032805148357-mpcss6fkq3b20gimd7dpen4aiemndfop` exists in your current project
2. Go to: https://console.cloud.google.com/apis/credentials
3. Check the project dropdown at the top
4. Make sure you're in the correct project
5. If the Client ID doesn't exist, create a new one or switch projects

### 4. Client ID Deleted or Disabled
**Fix:**
1. Check if the OAuth client still exists
2. If deleted, create a new one:
   - Go to: https://console.cloud.google.com/apis/credentials
   - Click "Create Credentials" > "OAuth 2.0 Client ID"
   - Application type: Web application
   - Name: "M&M Review Web Client"
   - Authorized redirect URIs: `http://localhost:5000/login/callback`
   - Copy the new Client ID and Secret to `.env`

### 5. Testing Mode Restrictions
**Fix:**
1. If OAuth consent screen is in "Testing" mode:
   - Add your test user email to the test users list
   - Or publish the app (if you have permission)
2. Go to: https://console.cloud.google.com/apis/credentials/consent
3. Add test users or click "Publish App"

## Quick Verification Steps

1. **Test the authorization URL:**
   ```bash
   ./venv/bin/python test_oauth.py
   ```
   This should generate a valid authorization URL.

2. **Check the exact error:**
   - Look at the Flask debug output in terminal
   - Check browser console for errors
   - The error message from Google will tell you exactly what's wrong

3. **Verify in Google Cloud Console:**
   - Client ID exists: https://console.cloud.google.com/apis/credentials
   - Consent screen configured: https://console.cloud.google.com/apis/credentials/consent
   - Redirect URI matches exactly

## Debug Mode

The app now has extensive debug logging. When you try to login:
1. Check the terminal where Flask is running
2. Look for lines starting with "DEBUG:"
3. These will show exactly where the OAuth flow is failing

## Temporary Workaround

If you need to test the app without OAuth:
1. Click "Continue as Development User" on the login page
2. This bypasses OAuth authentication
3. You can still test all other features

## Still Having Issues?

1. Check the Flask debug logs in terminal
2. Copy the exact error message from Google
3. Verify all steps above
4. Try creating a new OAuth client from scratch

