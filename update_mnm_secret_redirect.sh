#!/bin/bash

# Script to update MNM_SECRET_KEY with the correct Cloud Run redirect URI
# Usage: ./update_mnm_secret_redirect.sh <cloud-run-url>

set -e

PROJECT_ID=${PROJECT_ID:-"patientview-9uxml"}

if [ -z "$1" ]; then
    echo "Usage: $0 <cloud-run-url>"
    echo "Example: $0 https://mnm-xxxxx-xx.a.run.app"
    exit 1
fi

CLOUD_RUN_URL="$1"
REDIRECT_URI="${CLOUD_RUN_URL}/login/callback"

echo "Updating MNM_SECRET_KEY with redirect URI: $REDIRECT_URI"

# Get current secret value
CURRENT_SECRET=$(gcloud secrets versions access latest --secret=MNM_SECRET_KEY --project="$PROJECT_ID")

# Parse current JSON and update redirect URI
UPDATED_SECRET=$(echo "$CURRENT_SECRET" | python3 -c "
import json
import sys
data = json.load(sys.stdin)
data['GOOGLE_REDIRECT_URI'] = sys.argv[1]
print(json.dumps(data, indent=2))
" "$REDIRECT_URI")

# Create temporary file
TEMP_FILE=$(mktemp)
echo -n "$UPDATED_SECRET" > "$TEMP_FILE"

echo "Updated secret content:"
cat "$TEMP_FILE"
echo ""

# Update the secret
echo "Updating secret in GCP Secret Manager..."
echo -n "$UPDATED_SECRET" | gcloud secrets versions add MNM_SECRET_KEY --data-file=- --project="$PROJECT_ID"

# Clean up
rm "$TEMP_FILE"

echo "✅ Secret updated successfully!"
echo ""
echo "⚠️  IMPORTANT: Also update the redirect URI in Google Cloud Console OAuth credentials:"
echo "   https://console.cloud.google.com/apis/credentials?project=$PROJECT_ID"
echo "   Add this to 'Authorized redirect URIs': $REDIRECT_URI"




