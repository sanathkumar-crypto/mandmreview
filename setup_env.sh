#!/bin/bash
# Setup script for M&M Review Application
# Run this script with: source setup_env.sh

echo "Setting up environment variables for M&M Review Application"
echo ""
echo "Please enter your credentials (or press Enter to skip):"
echo ""

# Gemini API Key
read -p "Enter your Gemini API Key (get from https://makersuite.google.com/app/apikey): " GEMINI_KEY
if [ ! -z "$GEMINI_KEY" ]; then
    export GEMINI_API_KEY="$GEMINI_KEY"
    echo "✓ Gemini API Key set"
else
    echo "⚠ Gemini API Key not set (LLM analysis will not work)"
fi

echo ""

# Google OAuth (optional)
read -p "Enter your Google OAuth Client ID (optional, press Enter to skip): " CLIENT_ID
if [ ! -z "$CLIENT_ID" ]; then
    export GOOGLE_CLIENT_ID="$CLIENT_ID"
    echo "✓ Google OAuth Client ID set"
fi

read -p "Enter your Google OAuth Client Secret (optional, press Enter to skip): " CLIENT_SECRET
if [ ! -z "$CLIENT_SECRET" ]; then
    export GOOGLE_CLIENT_SECRET="$CLIENT_SECRET"
    echo "✓ Google OAuth Client Secret set"
fi

read -p "Enter your OAuth Redirect URI (default: http://localhost:5001/login/callback): " REDIRECT_URI
if [ ! -z "$REDIRECT_URI" ]; then
    export GOOGLE_REDIRECT_URI="$REDIRECT_URI"
else
    export GOOGLE_REDIRECT_URI="http://localhost:5001/login/callback"
fi

# Secret Key
read -p "Enter a secret key for Flask sessions (or press Enter to use default): " SECRET_KEY
if [ ! -z "$SECRET_KEY" ]; then
    export SECRET_KEY="$SECRET_KEY"
    echo "✓ Secret Key set"
else
    export SECRET_KEY="dev-secret-key-change-in-production"
    echo "⚠ Using default secret key (not recommended for production)"
fi

echo ""
echo "=========================================="
echo "Environment variables set for this session"
echo "=========================================="
echo ""
echo "To make these permanent, add them to your ~/.bashrc or ~/.bash_profile"
echo ""
echo "To run the application now, use:"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""

