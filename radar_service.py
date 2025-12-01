"""
RADAR service module for patient data operations
"""

import logging
import os
import requests
from typing import Dict, Any, Optional
from config import Config
from utils.radar_auth import call_radar_api_with_auth

logger = logging.getLogger(__name__)

def load_radar_read_service_account():
    """
    Load the radar read service account from the JSON file
    """
    try:
        service_account_path = 'radar_service_account.json'
        if os.path.exists(service_account_path):
            with open(service_account_path, 'r') as f:
                service_account_json = f.read()
            
            # Set the environment variable
            os.environ['RADAR_READ_SERVICE_ACCOUNT'] = service_account_json
            logger.info("✅ Successfully loaded RADAR_READ_SERVICE_ACCOUNT from radar_service_account.json")
            return True
        else:
            logger.warning(f"⚠️  Service account file not found: {service_account_path}")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to load radar read service account: {e}")
        return False

def get_patient_json(cpmrn: str, encounters: str) -> Optional[Dict[str, Any]]:
    """
    Get patient JSON from RADAR API using CPMRN and encounters.
    
    Args:
        cpmrn: Patient CPMRN identifier
        encounters: Patient encounters identifier
        
    Returns:
        Patient data dictionary or None if not found/error
    """
    radar_url = Config.RADAR_URL or os.environ.get('RADAR_URL', '')
    service_account_json = Config.RADAR_READ_SERVICE_ACCOUNT or os.environ.get('RADAR_READ_SERVICE_ACCOUNT', '')
    
    if not radar_url:
        logger.error("RADAR_URL not configured")
        return None
    
    if not service_account_json:
        logger.error("RADAR_READ_SERVICE_ACCOUNT not configured")
        return None
    
    payload = {
        "function": "get_patient_json",
        "filter_using": {
            "CPMRN": cpmrn,
            "encounters": int(encounters)
        },
        "return_fields": {}
    }
    print("Sending payload to RADAR API: ", payload)
    
    try:
        # Use service account authentication
        response = call_radar_api_with_auth(
            radar_url, 
            payload, 
            service_account_json
        )
        
        if not response.ok:
            logger.warning(f"RADAR API returned {response.status_code}: {response.text}")
            return None
        
        patient_data = response.json()
        
        # If it's a list, take the first item
        if isinstance(patient_data, list) and len(patient_data) > 0:
            return patient_data[0]
        elif isinstance(patient_data, dict):
            return patient_data
        else:
            logger.warning(f"Unexpected response format from RADAR API: {type(patient_data)}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"RADAR API request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in get_patient_json: {e}")
        return None

