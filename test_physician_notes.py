#!/usr/bin/env python3
"""
Test script to demonstrate physician note analysis with date-based content extraction.
Tests with CPMRN: INASSILCAC4163
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_processor import (
    extract_notes, 
    extract_note_content, 
    extract_content_after_date,
    is_physician_note,
    parse_timestamp,
    process_patient_data
)
from radar_service import get_patient_json, load_radar_read_service_account
from config import Config

# Load environment variables
load_dotenv()

def print_separator(title=""):
    """Print a visual separator."""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)
    print()

def test_physician_note_analysis(cpmrn: str, encounters: str = "1"):
    """Test physician note analysis for a given CPMRN."""
    
    print_separator("PHYSICIAN NOTE ANALYSIS TEST")
    print(f"CPMRN: {cpmrn}")
    print(f"Encounters: {encounters}")
    print()
    
    # Step 1: Load patient data
    print_separator("STEP 1: Loading Patient Data")
    
    patient_data = None
    
    # Try to load from Radar API first
    print("Attempting to load from Radar API...")
    try:
        # Load service account if needed
        if not Config.RADAR_READ_SERVICE_ACCOUNT:
            print("Loading Radar service account from file...")
            if load_radar_read_service_account():
                # Update Config with the loaded service account
                Config.RADAR_READ_SERVICE_ACCOUNT = os.environ.get('RADAR_READ_SERVICE_ACCOUNT', '')
                print("✓ Successfully loaded Radar service account from file")
            else:
                print("✗ Failed to load Radar service account from file")
        
        if Config.RADAR_READ_SERVICE_ACCOUNT and Config.RADAR_URL:
            print(f"Radar URL: {Config.RADAR_URL}")
            print("Fetching patient data from Radar API...")
            patient_data = get_patient_json(cpmrn, encounters)
            if patient_data:
                print("✓ Successfully loaded patient data from Radar API")
            else:
                print("✗ Failed to load from Radar API, trying local file...")
        else:
            print("Radar API not configured, trying local file...")
    except Exception as e:
        print(f"✗ Error loading from Radar API: {e}")
        print("Trying local file...")
    
    # Fallback to local file
    if not patient_data:
        print("Loading from local file (pat_jsons.json)...")
        try:
            with open('pat_jsons.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    patient_data = data[0]
                else:
                    patient_data = data
            print("✓ Successfully loaded patient data from local file")
        except Exception as e:
            print(f"✗ Error loading from local file: {e}")
            return
    
    if not patient_data:
        print("✗ No patient data available")
        return
    
    print(f"Patient Name: {patient_data.get('name', 'N/A')} {patient_data.get('lastName', '')}")
    print()
    
    # Step 2: Extract notes
    print_separator("STEP 2: Extracting Notes")
    
    notes = patient_data.get('notes', {}).get('finalNotes', [])
    print(f"Total notes found: {len(notes)}")
    print()
    
    # Filter physician notes
    physician_notes = []
    print("Analyzing each note to identify physician notes...")
    for idx, note in enumerate(notes, 1):
        # Extract author from note level (not from content items)
        author = note.get('author', {})
        if not author and note.get('content'):
            # Sometimes author might be in content items
            for item in note.get('content', []):
                if isinstance(item, dict) and 'author' in item:
                    author = item.get('author', {})
                    break
        
        author_name = author.get('name', '') if isinstance(author, dict) else ''
        author_role = author.get('role', '') if isinstance(author, dict) else ''
        note_type = note.get('noteType', '')
        
        # Check manually if it looks like a physician note
        is_physician = is_physician_note(note)
        
        # Also check if author name starts with "Dr." as fallback
        if not is_physician and author_name and ('Dr.' in author_name or 'MD' in author_name or 'physician' in author_name.lower()):
            print(f"  Note #{idx}: Author='{author_name}' (contains Dr./MD) -> Treating as Physician")
            is_physician = True
        
        print(f"  Note #{idx}: Author='{author_name}', Role='{author_role}', Type='{note_type}' -> Physician: {is_physician}")
        
        if is_physician:
            physician_notes.append(note)
    
    print(f"\nPhysician notes found: {len(physician_notes)}")
    print()
    
    # Step 3: Analyze each physician note
    print_separator("STEP 3: Analyzing Physician Notes")
    
    if len(physician_notes) == 0:
        print("No physician notes found by role/type. Checking author names...")
        # Show first note that looks like it might be a physician note
        for idx, note in enumerate(notes, 1):
            author = note.get('author', {})
            author_name = author.get('name', '') if isinstance(author, dict) else ''
            if author_name and ('Dr.' in author_name or 'MD' in author_name or 'physician' in author_name.lower()):
                print(f"\nFound note #{idx} by {author_name} - treating as physician note for demonstration")
                physician_notes = [note]
                break
    
    for idx, note in enumerate(physician_notes, 1):
        print(f"\n--- Physician Note #{idx} ---")
        
        # Get note metadata - author can be at note level or in content
        author = note.get('author', {})
        if not author or not isinstance(author, dict) or not author.get('name'):
            # Try to get from content items
            for item in note.get('content', []):
                if isinstance(item, dict) and 'author' in item:
                    item_author = item.get('author', {})
                    if isinstance(item_author, dict) and item_author.get('name'):
                        author = item_author
                        break
        
        author_name = author.get('name', 'Unknown') if isinstance(author, dict) else 'Unknown'
        author_email = author.get('email', '') if isinstance(author, dict) else ''
        author_role = author.get('role', '') if isinstance(author, dict) else ''
        
        timestamp_str = note.get('createdTimestamp') or note.get('timestamp')
        timestamp = parse_timestamp(timestamp_str) if timestamp_str else None
        
        print(f"Author: {author_name} ({author_email})")
        print(f"Role: {author_role}")
        print(f"Note Type: {note.get('noteType', 'N/A')}")
        print(f"Created: {timestamp_str}")
        if timestamp:
            print(f"Parsed Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Date formats to search: {timestamp.day:02d}/{timestamp.month:02d}/{timestamp.year}, "
                  f"{timestamp.day}/{timestamp.month}/{timestamp.year}, etc.")
        print()
        
        # Extract note content
        print("Extracting note content...")
        current_content = extract_note_content(note)
        print(f"Found {len(current_content)} content sections: {list(current_content.keys())}")
        print()
        
        # Check Summary section
        if 'Summary' in current_content:
            summary_text = current_content['Summary']
            print("--- Summary Section (BEFORE date extraction) ---")
            print(f"Length: {len(summary_text)} characters")
            print(f"Preview (first 200 chars): {summary_text[:200]}...")
            print()
            
            if timestamp:
                print(f"Searching for date matching note timestamp: {timestamp.strftime('%Y-%m-%d')}")
                print("Trying date formats:")
                day = timestamp.day
                month = timestamp.month
                year = timestamp.year
                
                date_formats = [
                    f"{day:02d}/{month:02d}/{year}",
                    f"{day}/{month}/{year}",
                    f"{month:02d}/{day:02d}/{year}",  # US format
                    f"{day:02d}/{month:02d}-",  # Partial format: 22/11-
                    f"{day}/{month}-",  # Partial format: 22/11-
                ]
                
                for date_fmt in date_formats:
                    print(f"  - {date_fmt}:")
                    pattern_with_colon = f"{date_fmt}:"
                    pattern_with_dash = f"{date_fmt}-"
                    pattern_with_space = f"{date_fmt} "
                    
                    idx_colon = summary_text.find(pattern_with_colon)
                    idx_dash = summary_text.find(pattern_with_dash)
                    idx_space = summary_text.find(pattern_with_space)
                    
                    if idx_colon >= 0:
                        print(f"    ✓ Found with colon at position {idx_colon}")
                        content_after = summary_text[idx_colon + len(pattern_with_colon):].strip()
                        print(f"    Content after date ({len(content_after)} chars): {content_after[:150]}...")
                        break
                    elif idx_dash >= 0:
                        print(f"    ✓ Found with dash at position {idx_dash}")
                        content_after = summary_text[idx_dash + len(pattern_with_dash):].strip()
                        print(f"    Content after date ({len(content_after)} chars): {content_after[:150]}...")
                        break
                    elif idx_space >= 0:
                        print(f"    ✓ Found with space at position {idx_space}")
                        content_after = summary_text[idx_space + len(pattern_with_space):].strip()
                        print(f"    Content after date ({len(content_after)} chars): {content_after[:150]}...")
                        break
                    else:
                        print(f"    ✗ Not found")
                
                print()
                print("Applying date extraction...")
                summary_after_date = extract_content_after_date(summary_text, timestamp)
                
                if summary_after_date != summary_text:
                    print("✓ Date found! Extracted content after date:")
                    print("--- Summary Section (AFTER date extraction) ---")
                    print(f"Length: {len(summary_after_date)} characters")
                    print(f"Content: {summary_after_date}")
                    print()
                else:
                    print("✗ No matching date found in summary. Showing full content.")
                    print("--- Summary Section (FULL CONTENT) ---")
                    print(f"Content: {summary_text}")
                    print()
            else:
                print("✗ No timestamp available for date matching")
                print("--- Summary Section (FULL CONTENT) ---")
                print(f"Content: {summary_text}")
                print()
        else:
            print("✗ No Summary section found in this note")
            print()
        
        # Show other sections
        print("--- Other Sections ---")
        for section_name, section_content in current_content.items():
            if section_name != 'Summary':
                print(f"{section_name}: {section_content[:100]}..." if len(section_content) > 100 else f"{section_name}: {section_content}")
        print()
    
    # Step 4: Process all notes using extract_notes function
    print_separator("STEP 4: Processing with extract_notes (Internal)")
    
    print("Processing all notes with role-based diffing and date extraction...")
    note_events_raw = extract_notes(patient_data)
    
    print(f"\nTotal note events from extract_notes: {len(note_events_raw)}")
    print()
    
    # Step 5: Process with process_patient_data (what frontend receives)
    print_separator("STEP 5: Processing with process_patient_data (Frontend Format)")
    
    print("Processing all events (notes, orders, labs, vitals, I/O)...")
    all_events = process_patient_data(patient_data)
    
    # Convert timestamps to ISO format strings (as done in app.py)
    for event in all_events:
        if hasattr(event.get('timestamp'), 'isoformat'):
            event['timestamp'] = event['timestamp'].isoformat()
    
    print(f"\nTotal events (all types): {len(all_events)}")
    
    # Filter note events
    note_events = [e for e in all_events if e.get('type') == 'note']
    print(f"Note events: {len(note_events)}")
    print()
    
    # Display final output for physician notes (exact format sent to frontend)
    print_separator("STEP 6: Final Output - EXACT FORMAT SENT TO FRONTEND")
    print("(This is what the frontend receives and displays)")
    print()
    
    for idx, event in enumerate(note_events, 1):
        timestamp = event.get('timestamp', '')
        event_type = event.get('type', '')
        data = event.get('data', {})
        author = data.get('author', 'Unknown')
        email = data.get('email', '')
        content = data.get('content', '')
        
        print(f"\n--- Note Event #{idx} (Frontend Format) ---")
        print(f"Type: {event_type}")
        print(f"Timestamp: {timestamp}")
        print(f"Author: {author}")
        print(f"Email: {email}")
        print(f"Content (what frontend displays):")
        print("-" * 60)
        print(content)
        print("-" * 60)
        print()
        
        # Also show the full event structure for debugging
        if idx <= 3:  # Show structure for first 3 notes only
            print(f"Full event structure (JSON):")
            event_json = json.dumps(event, indent=2, default=str)
            print(event_json[:500] + "..." if len(event_json) > 500 else event_json)
            print()
    
    # Summary of physician notes
    print_separator("STEP 7: Physician Note Summary")
    
    physician_note_count = 0
    physician_notes_with_date_extraction = 0
    
    for event in note_events:
        author = event.get('data', {}).get('author', '')
        email = event.get('data', {}).get('email', '')
        content = event.get('data', {}).get('content', '')
        
        # Check if this looks like a physician note
        is_physician = False
        if author:
            author_lower = author.lower()
            if 'dr.' in author_lower or ' md' in author_lower or ', md' in author_lower or 'physician' in author_lower:
                is_physician = True
        
        if is_physician:
            physician_note_count += 1
            # Check if content looks like it was date-extracted (shorter, starts with new content)
            # This is a heuristic - date-extracted content is typically shorter and doesn't start with "Summary: Summary:"
            if content and not content.startswith('Summary: Summary:') and len(content) < 500:
                physician_notes_with_date_extraction += 1
                print(f"✓ Physician note by {author} - Date extraction appears to be applied")
                print(f"  Content preview: {content[:150]}...")
            else:
                print(f"  Physician note by {author} - Full content shown (no date match found)")
    
    print(f"\nTotal physician notes: {physician_note_count}")
    print(f"Notes with date extraction applied: {physician_notes_with_date_extraction}")
    print()
    
    print_separator("TEST COMPLETE")

if __name__ == '__main__':
    # Test with the specified CPMRN
    cpmrn = "INASSILCAC4163"
    encounters = "1"  # Default to 1, can be changed if needed
    
    # Allow command line override
    if len(sys.argv) > 1:
        cpmrn = sys.argv[1]
    if len(sys.argv) > 2:
        encounters = sys.argv[2]
    
    try:
        test_physician_note_analysis(cpmrn, encounters)
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

