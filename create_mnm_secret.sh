#!/bin/bash

# Script to create MNM_SECRET_KEY from .env file
# This reads the values from .env and creates a JSON secret for GCP Secret Manager

set -e

PROJECT_ID=${PROJECT_ID:-"patientview-9uxml"}

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
  "GOOGLE_REDIRECT_URI": "${GOOGLE_REDIRECT_URI}"
}
EOF
)

# Create temporary file
TEMP_FILE=$(mktemp)
echo "$SECRET_JSON" > "$TEMP_FILE"

echo "Created JSON secret file:"
cat "$TEMP_FILE"
echo ""
echo "Creating secret in GCP Secret Manager..."

# Create or update the secret
if gcloud secrets describe MNM_SECRET_KEY --project="$PROJECT_ID" &>/dev/null; then
    echo "Secret exists, updating..."
    echo -n "$SECRET_JSON" | gcloud secrets versions add MNM_SECRET_KEY --data-file=- --project="$PROJECT_ID"
else
    echo "Creating new secret..."
    echo -n "$SECRET_JSON" | gcloud secrets create MNM_SECRET_KEY --data-file=- --project="$PROJECT_ID"
fi

# Clean up
rm "$TEMP_FILE"

echo "✅ Secret created/updated successfully!"
