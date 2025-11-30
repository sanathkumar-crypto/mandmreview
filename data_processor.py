import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import re
from html import unescape

def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """Parse timestamp string to datetime object, handling various formats."""
    if not timestamp_str:
        return None
    try:
        # Try ISO format first
        if 'Z' in timestamp_str:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        elif '+' in timestamp_str or timestamp_str.count('-') >= 3:
            return datetime.fromisoformat(timestamp_str)
        else:
            # Try parsing without timezone
            return datetime.fromisoformat(timestamp_str)
    except (ValueError, AttributeError):
        try:
            # Try parsing as milliseconds timestamp
            if timestamp_str.isdigit():
                return datetime.fromtimestamp(int(timestamp_str) / 1000)
        except (ValueError, OSError):
            pass
    return None

def parse_html_content(html_content: str) -> str:
    """Extract text content from HTML, removing tags."""
    if not html_content:
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html_content)
    # Decode HTML entities
    text = unescape(text)
    # Clean up whitespace
    text = ' '.join(text.split())
    return text

def extract_notes(patient_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract notes from patient data."""
    events = []
    notes = patient_data.get('notes', {}).get('finalNotes', [])
    
    for note in notes:
        timestamp_str = note.get('createdTimestamp') or note.get('timestamp')
        if not timestamp_str:
            continue
            
        timestamp = parse_timestamp(timestamp_str)
        if not timestamp:
            continue
            
        # Extract all components
        content = note.get('content', [])
        note_text_parts = []
        author_name = 'Unknown'
        author_email = ''
        
        # Author can be in the note itself or in content items
        author = note.get('author', {})
        if isinstance(author, dict):
            author_name = author.get('name', 'Unknown')
            author_email = author.get('email', '')
        
        for item in content:
            # Check if author is in this content item
            if isinstance(item, dict):
                item_author = item.get('author', {})
                if isinstance(item_author, dict) and item_author.get('name'):
                    author_name = item_author.get('name', author_name)
                    author_email = item_author.get('email', author_email)
                
                # Extract components
                if 'components' in item:
                    components = item.get('components', [])
                    for component in components:
                        display_name = component.get('displayName', '')
                        value = component.get('value', '')
                        if value:
                            parsed_value = parse_html_content(value)
                            if parsed_value:
                                note_text_parts.append(f"{display_name}: {parsed_value}")
                else:
                    # Direct component
                    display_name = item.get('displayName', '')
                    value = item.get('value', '')
                    if value:
                        parsed_value = parse_html_content(value)
                        if parsed_value:
                            note_text_parts.append(f"{display_name}: {parsed_value}")
        
        if note_text_parts:
            note_text = ' | '.join(note_text_parts)
            
            events.append({
                'timestamp': timestamp,
                'type': 'note',
                'data': {
                    'author': author_name,
                    'email': author_email,
                    'content': note_text
                }
            })
    
    return events

def extract_orders(patient_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract orders from patient data."""
    events = []
    orders = patient_data.get('orders', {})
    
    # Process active labs
    active_labs = orders.get('active', {}).get('labs', [])
    for lab in active_labs:
        investigation = lab.get('investigation')
        if not investigation:
            continue
            
        created_at = lab.get('createdAt')
        if created_at:
            timestamp = parse_timestamp(created_at)
            if timestamp:
                created_by = lab.get('createdBy', '')
                signed = lab.get('signed', '')
                email = created_by if created_by else signed
                events.append({
                    'timestamp': timestamp,
                    'type': 'order',
                    'data': {
                        'investigation': investigation,
                        'action': 'created',
                        'email': email
                    }
                })
        
        updated_at = lab.get('updatedAt')
        if updated_at and updated_at != created_at:
            timestamp = parse_timestamp(updated_at)
            if timestamp:
                created_by = lab.get('createdBy', '')
                signed = lab.get('signed', '')
                email = created_by if created_by else signed
                events.append({
                    'timestamp': timestamp,
                    'type': 'order',
                    'data': {
                        'investigation': investigation,
                        'action': 'updated',
                        'email': email
                    }
                })
        
        discontinue_at = lab.get('discontinueAt')
        if discontinue_at:
            timestamp = parse_timestamp(discontinue_at)
            if timestamp:
                discontinue_by = lab.get('discontinueBy', '')
                created_by = lab.get('createdBy', '')
                signed = lab.get('signed', '')
                email = discontinue_by if discontinue_by else (created_by if created_by else signed)
                events.append({
                    'timestamp': timestamp,
                    'type': 'order',
                    'data': {
                        'investigation': investigation,
                        'action': 'discontinued',
                        'email': email
                    }
                })
    
    # Process inactive labs
    inactive_labs = orders.get('inactive', {}).get('labs', [])
    for lab in inactive_labs:
        investigation = lab.get('investigation')
        if not investigation:
            continue
            
        created_at = lab.get('createdAt')
        if created_at:
            timestamp = parse_timestamp(created_at)
            if timestamp:
                created_by = lab.get('createdBy', '')
                signed = lab.get('signed', '')
                email = created_by if created_by else signed
                events.append({
                    'timestamp': timestamp,
                    'type': 'order',
                    'data': {
                        'investigation': investigation,
                        'action': 'created',
                        'email': email
                    }
                })
        
        updated_at = lab.get('updatedAt')
        if updated_at and updated_at != created_at:
            timestamp = parse_timestamp(updated_at)
            if timestamp:
                created_by = lab.get('createdBy', '')
                signed = lab.get('signed', '')
                email = created_by if created_by else signed
                events.append({
                    'timestamp': timestamp,
                    'type': 'order',
                    'data': {
                        'investigation': investigation,
                        'action': 'updated',
                        'email': email
                    }
                })
        
        discontinue_at = lab.get('discontinueAt')
        if discontinue_at:
            timestamp = parse_timestamp(discontinue_at)
            if timestamp:
                discontinue_by = lab.get('discontinueBy', '')
                created_by = lab.get('createdBy', '')
                signed = lab.get('signed', '')
                email = discontinue_by if discontinue_by else (created_by if created_by else signed)
                events.append({
                    'timestamp': timestamp,
                    'type': 'order',
                    'data': {
                        'investigation': investigation,
                        'action': 'discontinued',
                        'email': email
                    }
                })
    
    return events

def extract_lab_reports(patient_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract lab reports (documents) from patient data."""
    events = []
    documents = patient_data.get('documents', [])
    
    for doc in documents:
        name = doc.get('name')
        if not name:
            continue
            
        updated_at = doc.get('updatedAt')
        if not updated_at:
            continue
            
        timestamp = parse_timestamp(updated_at)
        if not timestamp:
            continue
        
        # Extract attributes
        attributes = doc.get('attributes', {})
        attr_text = []
        for attr_name, attr_data in attributes.items():
            if isinstance(attr_data, dict):
                value = attr_data.get('value')
                if value is not None and value != '':
                    attr_text.append(f"{attr_name}: {value}")
        
        reported_at = doc.get('reportedAt')
        reported_at_str = ''
        if reported_at:
            reported_dt = parse_timestamp(reported_at)
            if reported_dt:
                reported_at_str = reported_dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                reported_at_str = str(reported_at)
        
        # Extract email from verified field
        verified = doc.get('verified', {})
        email = ''
        if isinstance(verified, dict):
            verified_by = verified.get('by', {})
            if isinstance(verified_by, dict):
                email = verified_by.get('email', '')
        
        events.append({
            'timestamp': timestamp,
            'type': 'lab',
            'data': {
                'test': name,
                'results': attr_text,
                'reportedAt': reported_at_str,
                'email': email
            }
        })
    
    return events

def extract_vitals(patient_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract vitals from patient data."""
    events = []
    vitals = patient_data.get('vitals', [])
    
    for vital in vitals:
        timestamp_str = vital.get('timestamp')
        if not timestamp_str:
            continue
            
        timestamp = parse_timestamp(timestamp_str)
        if not timestamp:
            continue
        
        # Extract non-null vital fields
        vital_data = {}
        vital_fields = [
            'daysTemperature', 'daysTemperatureUnit', 'daysHR', 'daysRR', 
            'daysBP', 'daysMAP', 'daysCVP', 'daysSpO2', 'daysFiO2',
            'daysGCS', 'daysAVPU', 'daysPatPosition'
        ]
        
        for field in vital_fields:
            value = vital.get(field)
            if value is not None and value != '':
                # Format field name (remove 'days' prefix and convert to readable)
                field_name = field.replace('days', '')
                if field_name == 'Temperature':
                    unit = vital.get('daysTemperatureUnit', '')
                    vital_data['temp'] = f"{value}{unit}" if unit else str(value)
                elif field_name == 'HR':
                    vital_data['hr'] = str(value)
                elif field_name == 'RR':
                    vital_data['rr'] = str(value)
                elif field_name == 'BP':
                    vital_data['bp'] = str(value)
                elif field_name == 'MAP':
                    vital_data['map'] = str(value)
                elif field_name == 'CVP':
                    vital_data['cvp'] = str(value)
                elif field_name == 'SpO2':
                    vital_data['spo2'] = str(value)
                elif field_name == 'FiO2':
                    vital_data['fio2'] = str(value)
                elif field_name == 'GCS':
                    vital_data['gcs'] = str(value)
                elif field_name == 'AVPU':
                    vital_data['avpu'] = str(value)
                elif field_name == 'PatPosition':
                    vital_data['position'] = str(value)
        
        if vital_data:
            # Extract email from verifiedBy field
            verified_by = vital.get('verifiedBy', {})
            email = ''
            if isinstance(verified_by, dict):
                email = verified_by.get('email', '')
            
            vital_data['email'] = email
            events.append({
                'timestamp': timestamp,
                'type': 'vital',
                'data': vital_data
            })
    
    return events

def extract_io(patient_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract input/output data from patient data."""
    events = []
    io_data = patient_data.get('io', {})
    days = io_data.get('days', [])
    
    for day in days:
        day_date_str = day.get('dayDate')
        if not day_date_str:
            continue
            
        day_date = parse_timestamp(day_date_str)
        if not day_date:
            continue
        
        hours = day.get('hours', [])
        for hour in hours:
            hour_name = hour.get('hourName')
            if hour_name is None:
                continue
            try:
                hour_name = int(hour_name)
            except (ValueError, TypeError):
                continue
                
            minutes = hour.get('minutes', [])
            for minute in minutes:
                minute_name = minute.get('minuteName')
                if minute_name is None:
                    continue
                try:
                    minute_name = int(minute_name)
                except (ValueError, TypeError):
                    continue
                
                # Calculate timestamp
                try:
                    timestamp = day_date.replace(hour=hour_name, minute=minute_name, second=0, microsecond=0)
                except (ValueError, TypeError):
                    continue
                
                # Extract intake
                intake = minute.get('intake', {})
                intake_parts = []
                
                # Feeds
                feeds = intake.get('feeds', {})
                tube = feeds.get('tube', {})
                if tube.get('amount'):
                    intake_parts.append(f"Tube feed: {tube['amount']}mL")
                
                # Medications
                meds = intake.get('meds', {})
                infusion = meds.get('infusion', [])
                for inf in infusion:
                    if inf.get('amount'):
                        name = inf.get('name', 'Medication')
                        amount = inf.get('amount')
                        intake_parts.append(f"{name}: {amount}mL")
                
                bolus = meds.get('bolus', [])
                for bol in bolus:
                    if bol.get('amount'):
                        name = bol.get('name', 'Medication')
                        amount = bol.get('amount')
                        intake_parts.append(f"{name}: {amount}mL")
                
                # Blood products
                blood_products = intake.get('bloodProducts', {})
                prbc = blood_products.get('prbc', {})
                if prbc.get('amount'):
                    intake_parts.append(f"PRBC: {prbc['amount']}mL")
                
                # Extract output
                output = minute.get('output', {})
                output_parts = []
                
                # Stool
                stool = output.get('stool', {})
                if stool.get('amount'):
                    note = stool.get('note', '')
                    output_parts.append(f"Stool: {stool['amount']} {note}".strip())
                
                # Drain
                drain = output.get('drain', [])
                for d in drain:
                    if d.get('amount'):
                        output_parts.append(f"Drain: {d['amount']}mL")
                
                # Procedure
                procedure = output.get('procedure', [])
                for p in procedure:
                    if p.get('amount'):
                        output_parts.append(f"Procedure: {p['amount']}mL")
                
                # Dialysis
                dialysis = output.get('dialysis', [])
                for d in dialysis:
                    if d.get('amount'):
                        output_parts.append(f"Dialysis: {d['amount']}mL")
                
                if intake_parts or output_parts:
                    io_data_dict = {}
                    if intake_parts:
                        io_data_dict['input'] = ', '.join(intake_parts)
                    if output_parts:
                        io_data_dict['output'] = ', '.join(output_parts)
                    
                    events.append({
                        'timestamp': timestamp,
                        'type': 'io',
                        'data': io_data_dict
                    })
    
    return events

def process_patient_data(patient_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Process patient data and create unified chronological timeline."""
    all_events = []
    
    # Extract all event types
    all_events.extend(extract_notes(patient_data))
    all_events.extend(extract_orders(patient_data))
    all_events.extend(extract_lab_reports(patient_data))
    all_events.extend(extract_vitals(patient_data))
    all_events.extend(extract_io(patient_data))
    
    # Sort by timestamp
    all_events.sort(key=lambda x: x['timestamp'])
    
    return all_events

def get_patient_info(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract patient information for display."""
    name = patient_data.get('name', '')
    last_name = patient_data.get('lastName', '')
    full_name = f"{name}, {last_name}" if last_name else name
    
    mrn = patient_data.get('MRN', '')
    cpmrn = patient_data.get('CPMRN', '')
    
    dob = patient_data.get('dob')
    age_data = patient_data.get('age', {})
    age = age_data.get('year') if isinstance(age_data, dict) else None
    
    gender = patient_data.get('sex', '')
    
    icu_admit_date = patient_data.get('ICUAdmitDate')
    admission = ''
    if icu_admit_date:
        dt = parse_timestamp(icu_admit_date)
        if dt:
            admission = dt.strftime('%m/%d/%Y %H:%M')
        else:
            admission = icu_admit_date
    
    diagnoses = patient_data.get('diagnoses', [])
    diagnosis_str = ', '.join(diagnoses) if diagnoses else 'N/A'
    
    return {
        'name': full_name,
        'mrn': mrn or cpmrn,
        'dob': dob or 'N/A',
        'age': age or 'N/A',
        'gender': gender or 'N/A',
        'admission': admission,
        'diagnosis': diagnosis_str
    }

