#!/bin/bash

# Script to create MNM_SECRET_KEY from .env file
# This reads the values from .env and creates:
# 1. A local JSON file (mnm_secret_key.json) for local development
# 2. Optionally uploads to GCP Secret Manager (if gcloud is configured)

set -e

PROJECT_ID=${PROJECT_ID:-"patientview-9uxml"}
LOCAL_JSON_FILE="mnm_secret_key.json"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found"
    exit 1
fi

# Load values from .env
source .env

# Create JSON structure
SECRET_JSON=$(cat <<EOF
{
  "SECRET_KEY": "${SECRET_KEY}",
  "GOOGLE_CLIENT_ID": "${GOOGLE_CLIENT_ID}",
  "GOOGLE_CLIENT_SECRET": "${GOOGLE_CLIENT_SECRET}",
  "GOOGLE_REDIRECT_URI": "${GOOGLE_REDIRECT_URI}",
  "GEMINI_API_KEY": "${GEMINI_API_KEY}"
}
EOF
)

# Save to local JSON file for local development
echo "$SECRET_JSON" > "$LOCAL_JSON_FILE"
echo "✅ Created local JSON file: $LOCAL_JSON_FILE"
echo ""
echo "JSON content:"
cat "$LOCAL_JSON_FILE"
echo ""
echo ""

# Optionally upload to GCP Secret Manager (if gcloud is available)
if command -v gcloud &> /dev/null; then
    echo "gcloud found. Uploading to GCP Secret Manager..."
    
    # Create temporary file for gcloud
    TEMP_FILE=$(mktemp)
    echo "$SECRET_JSON" > "$TEMP_FILE"
    
    # Create or update the secret
    if gcloud secrets describe MNM_SECRET_KEY --project="$PROJECT_ID" &>/dev/null 2>&1; then
        echo "Secret exists, updating..."
        echo -n "$SECRET_JSON" | gcloud secrets versions add MNM_SECRET_KEY --data-file=- --project="$PROJECT_ID"
    else
        echo "Creating new secret..."
        echo -n "$SECRET_JSON" | gcloud secrets create MNM_SECRET_KEY --data-file=- --project="$PROJECT_ID"
    fi
    
    # Clean up
    rm "$TEMP_FILE"
    echo "✅ Secret created/updated in GCP Secret Manager!"
else
    echo "⚠️  gcloud not found. Skipping GCP Secret Manager upload."
    echo "   Local JSON file created successfully for local development."
fi

echo ""
echo "✅ Done! Local JSON file is ready for use with 'python app.py'"
