# OAuth Debugging Checklist

## Common OAuth Issues and Solutions

### 1. Redirect URI Mismatch (Most Common)
**Error**: "redirect_uri_mismatch" or "OAuth client was not found"

**Solution**: 
- Go to https://console.cloud.google.com/apis/credentials
- Click on your OAuth 2.0 Client ID
- Under "Authorized redirect URIs", make sure you have EXACTLY:
  ```
  http://localhost:5000/login/callback
  ```
- The URI must match EXACTLY (including http vs https, port number, path)
- Click "Save"

### 2. OAuth Consent Screen Not Configured
**Error**: "Access blocked: This app's request is invalid"

**Solution**:
- Go to https://console.cloud.google.com/apis/credentials/consent
- Configure the OAuth consent screen:
  - User Type: External (for testing) or Internal (if using Google Workspace)
  - App name, support email, developer contact
  - Add scopes: `openid`, `email`, `profile`
  - Add test users if using External user type

### 3. Client ID/Secret Not Matching
**Error**: "invalid_client" or "unauthorized_client"

**Solution**:
- Verify the Client ID and Secret in `.env` match what's in Google Cloud Console
- Make sure there are no extra spaces or quotes in `.env` file
- Format should be:
  ```
  GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
  GOOGLE_CLIENT_SECRET=GOCSPX-your-secret
  GOOGLE_REDIRECT_URI=http://localhost:5000/login/callback
  ```

### 4. App Not Restarted After .env Changes
**Solution**:
- Restart the Flask app after updating `.env` file
- The app loads `.env` only at startup

### 5. Testing the Configuration
Run the debug script:
```bash
./venv/bin/python debug_oauth.py
```

This will verify:
- Credentials are loaded from `.env`
- OAuth flow can be created
- Redirect URI is correct


