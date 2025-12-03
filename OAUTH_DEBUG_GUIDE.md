# OAuth Debugging Guide

## Quick Diagnostic

Visit this URL in your browser to check OAuth configuration:
```
http://localhost:5000/debug/oauth
```

## Most Common Issues

### 1. **Redirect URI Not Added in Google Cloud Console** (90% of issues)

**Symptoms:**
- Error: "redirect_uri_mismatch"
- Error: "OAuth client was not found"
- Login redirects but shows error page

**Fix:**
1. Go to https://console.cloud.google.com/apis/credentials
2. Click on your OAuth 2.0 Client ID
3. Scroll to "Authorized redirect URIs"
4. Click "+ ADD URI"
5. Add EXACTLY: `http://localhost:5000/login/callback`
6. Click "Save"
7. Wait 1-2 minutes for changes to propagate

**Important:** The URI must match EXACTLY:
- Must be `http://` (not `https://`) for localhost
- Must include the port `:5000`
- Must include the full path `/login/callback`
- No trailing slashes

### 2. **OAuth Consent Screen Not Configured**

**Symptoms:**
- Error: "Access blocked: This app's request is invalid"
- Error: "Error 400: invalid_request"

**Fix:**
1. Go to https://console.cloud.google.com/apis/credentials/consent
2. If not configured, click "CONFIGURE CONSENT SCREEN"
3. Select "External" (for testing) or "Internal" (if using Google Workspace)
4. Fill in required fields:
   - App name: "M&M Review System" (or any name)
   - User support email: Your email
   - Developer contact: Your email
5. Click "Save and Continue"
6. On Scopes page, click "Add or Remove Scopes"
7. Add these scopes:
   - `openid`
   - `email`
   - `profile`
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`
8. Click "Save and Continue"
9. If using "External" user type, add test users:
   - Click "Add Users"
   - Add your @cloudphysician.net email address
   - Click "Add"
10. Click "Save and Continue" through remaining steps

### 3. **Credentials Not Loading from .env File**

**Symptoms:**
- Error: "OAuth credentials not found in configuration"
- Login page shows "OAuth not configured"

**Fix:**
1. Check that `.env` file exists in project root
2. Verify format (no quotes, no spaces around `=`):
   ```
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=GOCSPX-your-secret
   GOOGLE_REDIRECT_URI=http://localhost:5000/login/callback
   ```
3. Restart Flask app after changing `.env`:
   ```bash
   pkill -f "python app.py"
   ./venv/bin/python app.py
   ```

### 4. **Client ID/Secret Mismatch**

**Symptoms:**
- Error: "invalid_client"
- Error: "unauthorized_client"

**Fix:**
1. Verify Client ID ends with `.apps.googleusercontent.com`
2. Verify Client Secret starts with `GOCSPX-`
3. Make sure you're using the correct credentials from Google Cloud Console
4. Check for extra spaces or hidden characters in `.env` file

### 5. **Test User Not Added (External User Type)**

**Symptoms:**
- Error: "Access blocked: This app's request is invalid"
- Error: "User is not authorized"

**Fix:**
1. Go to https://console.cloud.google.com/apis/credentials/consent
2. Scroll to "Test users"
3. Click "+ ADD USERS"
4. Add your @cloudphysician.net email address
5. Click "Add"

## Testing Steps

1. **Verify credentials are loaded:**
   ```bash
   ./venv/bin/python debug_oauth.py
   ```
   Should show: ✓ OAuth flow created successfully!

2. **Check Flask app configuration:**
   Visit: http://localhost:5000/debug/oauth
   Should show credentials are loaded

3. **Test login flow:**
   - Visit: http://localhost:5000
   - Click "Sign in with Google"
   - Should redirect to Google login page
   - After login, should redirect back to app

## Still Not Working?

1. **Check Flask logs:**
   ```bash
   tail -f /tmp/flask_debug.log
   ```
   Look for DEBUG messages starting with "DEBUG:"

2. **Check browser console:**
   - Open browser developer tools (F12)
   - Check Console tab for errors
   - Check Network tab for failed requests

3. **Verify Google Cloud Console:**
   - Make sure OAuth 2.0 Client ID is enabled
   - Check that redirect URI is exactly: `http://localhost:5000/login/callback`
   - Verify OAuth consent screen is published (or in testing mode with your email added)

4. **Common mistakes:**
   - Using `https://localhost` instead of `http://localhost`
   - Missing port number `:5000`
   - Wrong path (should be `/login/callback`)
   - Extra spaces in `.env` file
   - Forgot to restart Flask app after changing `.env`


