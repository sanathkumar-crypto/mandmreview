# Credentials Setup Guide

This guide explains where to put your API credentials for the M&M Review application.

## Quick Setup (Recommended)

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your actual credentials:
   ```bash
   nano .env
   # or use your preferred editor
   ```

3. That's it! The application will automatically load credentials from `.env`

---

## 1. Gemini API Key (for LLM Analysis)

### Where to get it:
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey) or [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to "APIs & Services" > "Credentials"
3. Click "Create Credentials" > "API Key"
4. Copy your API key

### Where to put it:

**Recommended: `.env` file** (automatically loaded)
Create a file named `.env` in the project root (copy from `.env.example`):
```bash
cp .env.example .env
# Then edit .env and add:
GEMINI_API_KEY=your-api-key-here
```

**Alternative: Environment Variable**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### Model Selection:
The application will try to use the latest Gemini model available:
- First tries: `gemini-2.0-flash-exp` (experimental)
- Falls back to: `gemini-1.5-flash` (stable)
- Last resort: `gemini-1.5-pro`

You can override this in `config.py`:
```python
GEMINI_MODEL = 'gemini-1.5-flash'  # or 'gemini-1.5-pro'
```

---

## 2. Google OAuth Credentials (for User Authentication)

### Where to get them:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth 2.0 Client ID"
5. Configure OAuth consent screen (if not done):
   - User Type: Internal (for @cloudphysician.net) or External
   - Scopes: email, profile, openid
6. Application type: Web application
7. Authorized redirect URIs: 
   - `http://localhost:5001/login/callback` (for local development)
   - `https://yourdomain.com/login/callback` (for production)
8. Copy the **Client ID** and **Client Secret**

### Where to put them:

**Recommended: `.env` file** (automatically loaded)
Add to your `.env` file:
```
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5001/login/callback
```

**Alternative: Environment Variables**
```bash
export GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your-client-secret"
export GOOGLE_REDIRECT_URI="http://localhost:5001/login/callback"
```

### Important Notes:
- The application restricts login to `@cloudphysician.net` email addresses
- Make sure your OAuth consent screen is configured correctly
- For production, update the redirect URI to match your domain
- Never commit credentials to git (they're in `.gitignore`)

---

## 3. Flask Secret Key (for Session Management)

### Where to put it:

**Recommended: `.env` file**
Add to your `.env` file:
```
SECRET_KEY=your-random-secret-key-here
```

**Generate a secure secret key:**
```python
import secrets
print(secrets.token_hex(32))
```

Or use this one-liner:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## Complete `.env` File Example

Your `.env` file should look like this:

```bash
# Flask Configuration
SECRET_KEY=your-generated-secret-key-here

# Gemini API (Required for LLM Analysis)
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.0-flash-exp

# Google OAuth (Optional)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
GOOGLE_REDIRECT_URI=http://localhost:5001/login/callback
```

**Important:** The `.env` file is automatically ignored by git, so your credentials won't be committed.

---

## File Locations Summary

| Credential | Location in Code | Environment Variable |
|------------|------------------|---------------------|
| Gemini API Key | `config.py` → `GEMINI_API_KEY` | `GEMINI_API_KEY` |
| Google OAuth Client ID | `config.py` → `GOOGLE_CLIENT_ID` | `GOOGLE_CLIENT_ID` |
| Google OAuth Client Secret | `config.py` → `GOOGLE_CLIENT_SECRET` | `GOOGLE_CLIENT_SECRET` |
| OAuth Redirect URI | `config.py` → `GOOGLE_REDIRECT_URI` | `GOOGLE_REDIRECT_URI` |
| Flask Secret Key | `config.py` → `SECRET_KEY` | `SECRET_KEY` |

---

## Security Best Practices

1. **Never commit credentials to git** - They're already in `.gitignore`
2. **Use environment variables** for production deployments
3. **Rotate credentials** periodically
4. **Use different credentials** for development and production
5. **Restrict OAuth redirect URIs** to your actual domains only

