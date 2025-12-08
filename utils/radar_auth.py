"""
RADAR API authentication utility using Google Service Account
"""

import json
import logging
import requests
from typing import Dict, Any
from google.auth.transport.requests import Request
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

def get_service_account_credentials(service_account_json: str) -> service_account.Credentials:
    """
    Parse service account JSON and return credentials object
    """
    try:
        if isinstance(service_account_json, str):
            service_account_info = json.loads(service_account_json)
        else:
            service_account_info = service_account_json
            
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info
        )
        return credentials
    except Exception as e:
        logger.error(f"Failed to create service account credentials: {e}")
        raise

def fetch_id_token(service_account_json: str, audience: str) -> str:
    """
    Use service account key to mint an ID token for the given audience
    """
    try:
        request = Request()
        target_creds = service_account.IDTokenCredentials.from_service_account_info(
            json.loads(service_account_json) if isinstance(service_account_json, str) else service_account_json,
            target_audience=audience
        )
        target_creds.refresh(request)
        return target_creds.token
    except Exception as e:
        logger.error(f"Failed to fetch ID token: {e}")
        raise

def call_radar_api_with_auth(
    url: str, 
    json_body: Dict[str, Any], 
    service_account_json: str,
    timeout: int = 30
) -> requests.Response:
    """
    Make authenticated call to RADAR API using service account ID token
    """
    try:
        # For Cloud Run/Functions, audience is the URL
        jwt = fetch_id_token(service_account_json, url)
        headers = {
            'Authorization': f'Bearer {jwt}', 
            'Content-Type': 'application/json'
        }
        
        logger.info(f"Making authenticated request to RADAR API: {url}")
        response = requests.post(url, json=json_body, headers=headers, timeout=timeout)
        
        logger.info(f"RADAR API response status: {response.status_code}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to call RADAR API with authentication: {e}")
        raise





