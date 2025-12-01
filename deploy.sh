#!/bin/bash

# M&M Review Microservice Deployment Script
# This script deploys the Flask application to Google Cloud Run

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
PROJECT_ID=${PROJECT_ID:-"patientview-9uxml"}
REGION=${REGION:-"asia-south1"}
SERVICE_NAME=${SERVICE_NAME:-"mnm"}

# Display configuration
print_status "Deployment Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service Name: $SERVICE_NAME"
echo "  Secrets:"
echo "    - GEMINI_API_KEY (from Secret Manager)"
echo "    - RADAR_URL (from RADAR_READ_URL secret)"
echo "    - RADAR_READ_SERVICE_ACCOUNT (from Secret Manager)"
echo "    - MNM_SECRET_KEY (JSON secret containing SECRET_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI)"

# Confirm deployment
echo
read -p "Do you want to proceed with deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelled"
    exit 0
fi

# Check if gcloud is installed and authenticated
print_status "Checking gcloud configuration..."
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    print_error "Not authenticated with gcloud. Please run: gcloud auth login"
    exit 1
fi

# Set the project
print_status "Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Check if required secrets exist
print_status "Checking required secrets..."
if ! gcloud secrets describe GEMINI_API_KEY --quiet 2>/dev/null; then
    print_error "Secret GEMINI_API_KEY not found. Please create it in Secret Manager."
    exit 1
fi

if ! gcloud secrets describe RADAR_READ_URL --quiet 2>/dev/null; then
    print_error "Secret RADAR_READ_URL not found. Please create it in Secret Manager."
    exit 1
fi

if ! gcloud secrets describe RADAR_READ_SERVICE_ACCOUNT --quiet 2>/dev/null; then
    print_error "Secret RADAR_READ_SERVICE_ACCOUNT not found. Please create it in Secret Manager."
    exit 1
fi

if ! gcloud secrets describe MNM_SECRET_KEY --quiet 2>/dev/null; then
    print_error "Secret MNM_SECRET_KEY not found. Please create it in Secret Manager."
    print_status "Create a JSON file with the following structure:"
    print_status "{"
    print_status "  \"SECRET_KEY\": \"your-secret-key\","
    print_status "  \"GOOGLE_CLIENT_ID\": \"your-client-id\","
    print_status "  \"GOOGLE_CLIENT_SECRET\": \"your-client-secret\","
    print_status "  \"GOOGLE_REDIRECT_URI\": \"https://your-cloud-run-url/login/callback\""
    print_status "}"
    print_status ""
    print_status "Then create the secret with:"
    print_status "  gcloud secrets create MNM_SECRET_KEY --data-file=secret.json --project=$PROJECT_ID"
    exit 1
fi

print_success "All required secrets found!"

# Enable required APIs
print_status "Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com --quiet
gcloud services enable run.googleapis.com --quiet
gcloud services enable containerregistry.googleapis.com --quiet
gcloud services enable secretmanager.googleapis.com --quiet

# Build and deploy using Cloud Build
print_status "Building and deploying using Cloud Build..."
gcloud builds submit \
    --config cloudbuild.yaml \
    --substitutions=_REGION="$REGION" \
    --project $PROJECT_ID

# Get the service URL
print_status "Getting service URL..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)" 2>/dev/null || echo "")

if [ -n "$SERVICE_URL" ]; then
    print_success "Deployment completed successfully!"
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  Frontend URL: $SERVICE_URL"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "Access your application at:"
    echo "  $SERVICE_URL"
    echo ""
    echo "Available routes:"
    echo "  - Login: $SERVICE_URL/login"
    echo "  - Patient Lookup: $SERVICE_URL/patient-lookup"
    echo "  - Timeline: $SERVICE_URL/timeline"
    echo ""
    
    # Test the root endpoint
    print_status "Testing service endpoint..."
    if curl -s -f "$SERVICE_URL" > /dev/null; then
        print_success "Service is responding!"
    else
        print_warning "Service might still be starting up. Please try accessing the URL in a few moments."
    fi
else
    print_error "Failed to get service URL. Please check the deployment logs."
    exit 1
fi

print_success "Deployment script completed!"
