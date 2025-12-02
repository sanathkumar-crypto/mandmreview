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

def is_abnormal_vital(vital_key: str, vital_value: str) -> bool:
    """Check if a vital sign value is abnormal."""
    if not vital_value:
        return False
    
    try:
        # Extract numeric value from string (handle units like "98.6°F", "120/80", etc.)
        numeric_value = None
        
        # Handle temperature with units
        if vital_key == 'temp':
            # Extract number from string like "98.6°F" or "37.2°C"
            temp_match = re.search(r'([\d.]+)', str(vital_value))
            if temp_match:
                temp_val = float(temp_match.group(1))
                # Check if Fahrenheit or Celsius
                if '°F' in str(vital_value) or 'F' in str(vital_value):
                    # Normal: 97-99°F
                    return temp_val < 97 or temp_val > 99
                elif '°C' in str(vital_value) or 'C' in str(vital_value):
                    # Normal: 36.1-37.2°C
                    return temp_val < 36.1 or temp_val > 37.2
                else:
                    # Assume Fahrenheit if no unit
                    return temp_val < 97 or temp_val > 99
        
        # Handle BP (format: "120/80" or "120")
        elif vital_key == 'bp':
            bp_match = re.search(r'(\d+)(?:/(\d+))?', str(vital_value))
            if bp_match:
                systolic = int(bp_match.group(1))
                diastolic = int(bp_match.group(2)) if bp_match.group(2) else None
                # Normal: Systolic 90-120, Diastolic 60-80
                if diastolic:
                    return systolic < 90 or systolic > 120 or diastolic < 60 or diastolic > 80
                else:
                    return systolic < 90 or systolic > 120
        
        # Handle numeric vitals
        else:
            # Extract first number from string
            num_match = re.search(r'([\d.]+)', str(vital_value))
            if num_match:
                numeric_value = float(num_match.group(1))
                
                if vital_key == 'hr':
                    # Normal: 60-100 bpm
                    return numeric_value < 60 or numeric_value > 100
                elif vital_key == 'rr':
                    # Normal: 12-20 breaths/min
                    return numeric_value < 12 or numeric_value > 20
                elif vital_key == 'map':
                    # Normal: 70-100 mmHg
                    return numeric_value < 70 or numeric_value > 100
                elif vital_key == 'cvp':
                    # Normal: 2-8 mmHg
                    return numeric_value < 2 or numeric_value > 8
                elif vital_key == 'spo2':
                    # Normal: >95%
                    return numeric_value < 95
                elif vital_key == 'gcs':
                    # Normal: 15, abnormal: <15
                    return numeric_value < 15
                elif vital_key == 'avpu':
                    # Normal: "A" (Alert), abnormal: others
                    return str(vital_value).upper() != 'A'
                # fio2 and position don't have normal/abnormal ranges
                elif vital_key in ['fio2', 'position']:
                    return False
        
        return False
    except (ValueError, AttributeError):
        # If we can't parse, assume it's not clearly abnormal
        return False

def is_abnormal_lab_result(lab_result: str) -> bool:
    """Check if a lab result string indicates an abnormal value."""
    if not lab_result:
        return False
    
    lab_lower = lab_result.lower()
    
    # Check for common abnormal indicators
    # Look for flags like "H" (high), "L" (low), "H*", "L*", "↑", "↓", "HIGH", "LOW"
    abnormal_flags = [' h ', ' h*', ' l ', ' l*', '↑', '↓', ' high', ' low', 
                      '(h)', '(l)', '[h]', '[l]', 'critical', 'abnormal']
    
    for flag in abnormal_flags:
        if flag in lab_lower:
            return True
    
    # Check for patterns like "value H" or "value L" at the end
    if re.search(r'[\d.]+[ \t]+[HL]\b', lab_lower):
        return True
    
    # Check for patterns like "value (H)" or "value (L)"
    if re.search(r'[\d.]+[ \t]*\([HL]\)', lab_lower):
        return True
    
    # If no clear abnormal indicator, assume normal
    return False

def extract_note_content(note: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract note content as a dictionary mapping displayName to parsed value.
    Returns a dict with component names as keys and their values.
    """
    content_dict = {}
    content = note.get('content', [])
    
    for item in content:
        if isinstance(item, dict):
            # Extract components
            if 'components' in item:
                components = item.get('components', [])
                for component in components:
                    display_name = component.get('displayName', '')
                    # Skip Assessment section
                    if display_name.lower() == 'assessment':
                        continue
                    value = component.get('value', '')
                    if value:
                        parsed_value = parse_html_content(value)
                        if parsed_value:
                            content_dict[display_name] = parsed_value
            else:
                # Direct component
                display_name = item.get('displayName', '')
                # Skip Assessment section
                if display_name.lower() == 'assessment':
                    continue
                value = item.get('value', '')
                if value:
                    parsed_value = parse_html_content(value)
                    if parsed_value:
                        content_dict[display_name] = parsed_value
    
    return content_dict

def find_new_content(current_content: Dict[str, str], previous_content: Dict[str, str]) -> Dict[str, str]:
    """
    Compare current note content with previous note content and return only new/changed content.
    Uses fuzzy matching - content is considered new if it's significantly different.
    Handles date-stamped updates and extensions of previous content.
    """
    new_content = {}
    
    for display_name, current_value in current_content.items():
        previous_value = previous_content.get(display_name, '')
        
        # If this component doesn't exist in previous note, it's new
        if not previous_value:
            new_content[display_name] = current_value
        else:
            # Normalize for comparison (remove extra whitespace)
            current_normalized = ' '.join(current_value.split())
            previous_normalized = ' '.join(previous_value.split())
            
            # If values are identical (after normalization), skip
            if current_normalized == previous_normalized:
                continue
            
            # Strategy 1: If current starts with previous content, extract what comes after
            current_lower = current_value.lower()
            previous_lower = previous_value.lower()
            
            # Check if previous content appears at the start of current (allowing for minor variations)
            if current_lower.startswith(previous_lower):
                # Previous is at the start - extract everything after it
                new_part = current_value[len(previous_value):].strip()
                if new_part:
                    new_content[display_name] = new_part
                    continue
            
            # Strategy 2: Find where previous content ends in current content
            # This handles cases where there might be minor formatting differences
            prev_idx = current_lower.find(previous_lower)
            if prev_idx >= 0:
                # Found previous content - get what comes after
                after_prev = current_value[prev_idx + len(previous_value):].strip()
                if after_prev:
                    # Check if what comes after looks like a date-stamped update
                    # Pattern: date pattern like "03/10/2025:" or "DD/MM/YYYY:" or similar
                    import re
                    date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s*:'
                    if re.search(date_pattern, after_prev, re.IGNORECASE):
                        # It's a date-stamped update, include it
                        new_content[display_name] = after_prev
                        continue
                    # Or if it's a significant amount of new text
                    elif len(after_prev) > 20:  # At least 20 characters of new content
                        new_content[display_name] = after_prev
                        continue
            
            # Strategy 3: Check if current is an extension (contains previous + more)
            # Calculate word overlap to determine if current extends previous
            current_words = current_normalized.lower().split()
            previous_words = previous_normalized.lower().split()
            
            if len(current_words) > len(previous_words):
                # Check if previous words appear in sequence at the start of current
                words_match = True
                for i, prev_word in enumerate(previous_words[:min(10, len(previous_words))]):  # Check first 10 words
                    if i < len(current_words) and current_words[i] != prev_word:
                        words_match = False
                        break
                
                if words_match:
                    # Previous content is at the start, extract the rest
                    # Find where previous normalized content ends
                    prev_normalized_len = len(previous_normalized)
                    if len(current_normalized) > prev_normalized_len:
                        # Try to find a good split point
                        # Look for sentence boundaries or date patterns after previous content
                        remaining = current_value
                        # Try to find where previous content ends in original (case-sensitive)
                        prev_end_pos = -1
                        for i in range(len(current_value) - len(previous_value) + 1):
                            if current_value[i:i+len(previous_value)].lower() == previous_lower:
                                prev_end_pos = i + len(previous_value)
                                break
                        
                        if prev_end_pos >= 0:
                            new_part = current_value[prev_end_pos:].strip()
                            if new_part:
                                new_content[display_name] = new_part
                                continue
            
            # Strategy 4: Calculate similarity for different content
            if current_words and previous_words:
                overlap = len(set(current_words) & set(previous_words))
                total_unique = len(set(current_words) | set(previous_words))
                similarity = overlap / total_unique if total_unique > 0 else 0
                
                # If similarity is low (< 0.3), it's mostly new content
                if similarity < 0.3:
                    new_content[display_name] = current_value
                # If similarity is moderate (0.3-0.7), it's partially new - show the whole thing
                elif similarity < 0.7:
                    new_content[display_name] = current_value
                # If high similarity but not identical, try to extract new parts
                else:
                    # For high similarity, show the whole value as it likely has important updates
                    new_content[display_name] = current_value
            else:
                # Fallback: if we can't determine, show the whole value
                new_content[display_name] = current_value
    
    return new_content

def format_note_content(content_dict: Dict[str, str]) -> str:
    """Format note content dictionary as a string."""
    note_text_parts = []
    for display_name, value in content_dict.items():
        note_text_parts.append(f"{display_name}: {value}")
    return ' | '.join(note_text_parts)

def extract_notes(patient_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract notes from patient data with role-based diffing."""
    events = []
    notes = patient_data.get('notes', {}).get('finalNotes', [])
    
    # Group notes by role and sort by timestamp
    notes_by_role = {}
    for note in notes:
        # Skip notes with role "Critical Care Registered Nurse"
        note_role = note.get('role', '')
        if note_role and note_role.lower() == 'critical care registered nurse':
            continue
        
        timestamp_str = note.get('createdTimestamp') or note.get('timestamp')
        if not timestamp_str:
            continue
            
        timestamp = parse_timestamp(timestamp_str)
        if not timestamp:
            continue
        
        # Use empty string as default role if not specified
        role_key = note_role if note_role else ''
        if role_key not in notes_by_role:
            notes_by_role[role_key] = []
        
        notes_by_role[role_key].append({
            'note': note,
            'timestamp': timestamp
        })
    
    # Sort notes within each role by timestamp
    for role_key in notes_by_role:
        notes_by_role[role_key].sort(key=lambda x: x['timestamp'])
    
    # Process notes by role
    for role_key, role_notes in notes_by_role.items():
        previous_content = {}
        
        for idx, note_data in enumerate(role_notes):
            note = note_data['note']
            timestamp = note_data['timestamp']
            
            # Extract author info
            author_name = 'Unknown'
            author_email = ''
            author = note.get('author', {})
            if isinstance(author, dict):
                author_name = author.get('name', 'Unknown')
                author_email = author.get('email', '')
            
            # Check for author in content items
            content = note.get('content', [])
            for item in content:
                if isinstance(item, dict):
                    item_author = item.get('author', {})
                    if isinstance(item_author, dict) and item_author.get('name'):
                        author_name = item_author.get('name', author_name)
                        author_email = item_author.get('email', author_email)
            
            # Extract current note content
            current_content = extract_note_content(note)
            
            if not current_content:
                continue
            
            # For first note of this role, show full content
            # For subsequent notes, show only new content
            if idx == 0:
                # First note - show everything
                display_content = current_content
                previous_content = current_content.copy()
            else:
                # Subsequent note - show only new content
                new_content = find_new_content(current_content, previous_content)
                if not new_content:
                    # No new content, skip this note
                    continue
                display_content = new_content
                # Update previous content for next comparison
                previous_content = current_content.copy()
            
            # Format and add event
            note_text = format_note_content(display_content)
            
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
        
        # Extract attributes, only keeping abnormal results
        attributes = doc.get('attributes', {})
        attr_text = []
        for attr_name, attr_data in attributes.items():
            if isinstance(attr_data, dict):
                value = attr_data.get('value')
                if value is not None and value != '':
                    result_str = f"{attr_name}: {value}"
                    # Only include if abnormal
                    if is_abnormal_lab_result(result_str):
                        attr_text.append(result_str)
        
        reported_at = doc.get('reportedAt')
        reported_at_str = ''
        if reported_at:
            reported_dt = parse_timestamp(reported_at)
            if reported_dt:
                reported_at_str = reported_dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                reported_at_str = str(reported_at)
        
        # Only add lab event if there are abnormal results
        if attr_text:
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
        
        # Extract non-null vital fields, only keeping abnormal ones
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
                vital_key = None
                vital_value_str = None
                
                if field_name == 'Temperature':
                    unit = vital.get('daysTemperatureUnit', '')
                    vital_value_str = f"{value}{unit}" if unit else str(value)
                    vital_key = 'temp'
                elif field_name == 'HR':
                    vital_value_str = str(value)
                    vital_key = 'hr'
                elif field_name == 'RR':
                    vital_value_str = str(value)
                    vital_key = 'rr'
                elif field_name == 'BP':
                    vital_value_str = str(value)
                    vital_key = 'bp'
                elif field_name == 'MAP':
                    vital_value_str = str(value)
                    vital_key = 'map'
                elif field_name == 'CVP':
                    vital_value_str = str(value)
                    vital_key = 'cvp'
                elif field_name == 'SpO2':
                    vital_value_str = str(value)
                    vital_key = 'spo2'
                elif field_name == 'FiO2':
                    vital_value_str = str(value)
                    vital_key = 'fio2'
                elif field_name == 'GCS':
                    vital_value_str = str(value)
                    vital_key = 'gcs'
                elif field_name == 'AVPU':
                    vital_value_str = str(value)
                    vital_key = 'avpu'
                elif field_name == 'PatPosition':
                    vital_value_str = str(value)
                    vital_key = 'position'
                
                # Only include if abnormal (exclude fio2 and position as they don't have normal/abnormal ranges)
                if vital_key and vital_value_str:
                    if vital_key not in ['fio2', 'position'] and is_abnormal_vital(vital_key, vital_value_str):
                        vital_data[vital_key] = vital_value_str
        
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

