#!/usr/bin/env python3
"""
Debug script to trace physician note date extraction step by step.
"""

import sys
import os
from dotenv import load_dotenv
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from radar_service import get_patient_json, load_radar_read_service_account
from data_processor import (
    extract_notes, 
    is_physician_note, 
    extract_note_content, 
    extract_content_after_date, 
    parse_timestamp,
    format_note_content
)

load_dotenv()
load_radar_read_service_account()
Config.RADAR_READ_SERVICE_ACCOUNT = os.environ.get('RADAR_READ_SERVICE_ACCOUNT', '')

def main():
    cpmrn = 'INUPVNSSNV1492'
    print("=" * 80)
    print("DEBUGGING PHYSICIAN NOTE DATE EXTRACTION")
    print("=" * 80)
    print(f"CPMRN: {cpmrn}")
    print()
    
    # Step 1: Load patient data
    print("STEP 1: Loading patient data from Radar API...")
    patient_data = get_patient_json(cpmrn, '1')
    if not patient_data:
        print("ERROR: Could not load patient data")
        return
    print("✓ Patient data loaded")
    print()
    
    # Step 2: Find the note with Babita and 03/10/2025
    print("STEP 2: Finding note with 'Babita' and '03/10/2025:' in summary...")
    notes = patient_data.get('notes', {}).get('finalNotes', [])
    print(f"Total notes: {len(notes)}")
    
    target_note = None
    for i, note in enumerate(notes):
        timestamp_str = note.get('createdTimestamp') or note.get('timestamp')
        if timestamp_str and '2025-10-03' in timestamp_str:
            # Check if this note has the summary we're looking for
            content = note.get('content', [])
            for item in content:
                if isinstance(item, dict) and 'components' in item:
                    for comp in item.get('components', []):
                        if comp.get('displayName') == 'Summary':
                            summary_value = comp.get('value', '')
                            if 'Babita' in summary_value and '03/10/2025:' in summary_value:
                                target_note = note
                                print(f"✓ Found target note at index {i}")
                                print(f"  Timestamp: {timestamp_str}")
                                break
                    if target_note:
                        break
                if target_note:
                    break
            if target_note:
                break
    
    if not target_note:
        print("ERROR: Could not find target note")
        return
    print()
    
    # Step 3: Check if it's detected as a physician note
    print("STEP 3: Checking if note is detected as physician note...")
    print(f"  Top-level author: {target_note.get('author', {})}")
    
    # Check content items for author
    content = target_note.get('content', [])
    print(f"  Content items: {len(content)}")
    for i, item in enumerate(content):
        if isinstance(item, dict):
            item_author = item.get('author', {})
            if item_author:
                print(f"  Content[{i}] author: {item_author}")
    
    is_physician = is_physician_note(target_note)
    print(f"  is_physician_note() result: {is_physician}")
    if not is_physician:
        print("  ✗ NOTE IS NOT DETECTED AS PHYSICIAN NOTE!")
        print("  This is the problem - date extraction won't run for non-physician notes")
        return
    print("  ✓ Note is detected as physician note")
    print()
    
    # Step 4: Extract note content
    print("STEP 4: Extracting note content...")
    current_content = extract_note_content(target_note)
    print(f"  Content keys: {list(current_content.keys())}")
    
    if 'Summary' not in current_content:
        print("  ✗ No Summary section found!")
        return
    
    summary_text = current_content['Summary']
    print(f"  Summary length: {len(summary_text)}")
    print(f"  Summary (first 200 chars): {summary_text[:200]}...")
    print(f"  Contains '03/10/2025:': {'03/10/2025:' in summary_text}")
    print()
    
    # Step 5: Parse timestamp
    print("STEP 5: Parsing note timestamp...")
    timestamp_str = target_note.get('createdTimestamp') or target_note.get('timestamp')
    timestamp = parse_timestamp(timestamp_str)
    print(f"  Timestamp string: {timestamp_str}")
    print(f"  Parsed timestamp: {timestamp}")
    print(f"  Date: {timestamp.date()}")
    print(f"  Looking for date: 03/10/2025")
    print()
    
    # Step 6: Test date extraction function
    print("STEP 6: Testing extract_content_after_date() function...")
    summary_after_date = extract_content_after_date(summary_text, timestamp)
    print(f"  Original summary length: {len(summary_text)}")
    print(f"  After extraction length: {len(summary_after_date)}")
    print(f"  Changed: {summary_after_date != summary_text}")
    
    if summary_after_date != summary_text:
        print("  ✓ Date extraction function works!")
        print(f"  Extracted content (first 150 chars): {summary_after_date[:150]}...")
    else:
        print("  ✗ Date extraction function did NOT find matching date")
        print("  This means the date pattern doesn't match")
    print()
    
    # Step 7: Simulate what happens in extract_notes
    print("STEP 7: Simulating extract_notes() processing...")
    print("  (This is what happens in the actual extract_notes function)")
    print()
    
    if is_physician:
        print("  → Note is physician note, checking Summary section...")
        if 'Summary' in current_content:
            print(f"  → Summary found in current_content")
            print(f"  → Calling extract_content_after_date()...")
            summary_after_date = extract_content_after_date(summary_text, timestamp)
            print(f"  → Result length: {len(summary_after_date)}")
            print(f"  → Changed: {summary_after_date != summary_text}")
            
            if summary_after_date != summary_text:
                print("  → Date found! Updating current_content['Summary']...")
                current_content['Summary'] = summary_after_date
                print(f"  → Updated summary length: {len(current_content['Summary'])}")
                print(f"  → Updated summary: {current_content['Summary'][:150]}...")
            else:
                print("  → Date NOT found, keeping original summary")
        else:
            print("  → No Summary in current_content")
    else:
        print("  → Note is NOT physician note, skipping date extraction")
    print()
    
    # Step 8: Format the content
    print("STEP 8: Formatting note content for display...")
    formatted_content = format_note_content(current_content)
    print(f"  Formatted content length: {len(formatted_content)}")
    print(f"  Formatted content (first 300 chars):")
    print(f"  {formatted_content[:300]}...")
    print()
    
    # Step 9: Compare with actual extract_notes output
    print("STEP 9: Comparing with actual extract_notes() output...")
    events = extract_notes(patient_data)
    print(f"  Total events extracted: {len(events)}")
    
    found_event = None
    for event in events:
        if event.get('type') == 'note':
            data = event.get('data', {})
            content_text = data.get('content', '')
            timestamp = event.get('timestamp', '')
            
            # Look for note from Oct 3, 2025
            if '2025-10-03' in str(timestamp):
                print(f"  Found note from Oct 3, 2025:")
                print(f"    Author: {data.get('author', 'Unknown')}")
                print(f"    Timestamp: {timestamp}")
                print(f"    Content length: {len(content_text)}")
                
                if 'Babita' in content_text:
                    found_event = event
                    print(f"    Contains 'Babita': True")
                    print(f"    Contains '03/10/2025:': {'03/10/2025:' in content_text}")
                    print(f"    Content (first 400 chars):")
                    print(f"    {content_text[:400]}...")
                    print()
                    
                    # Check if date extraction was applied
                    if 'The patient was fully conscious' in content_text:
                        if 'Babita, a 30-year-old' not in content_text:
                            print("  ✓ SUCCESS: Date extraction was applied!")
                            print("  Only new content after date is shown.")
                        else:
                            print("  ✗ FAILED: Date extraction was NOT applied!")
                            print("  Full content (including old text) is still shown.")
                    else:
                        print("  ? Note doesn't contain 'The patient was fully conscious'")
                    break
    
    if not found_event:
        print("  ✗ Could not find matching event in extract_notes() output")
        print("  Listing all note events from Oct 3:")
        for event in events:
            if event.get('type') == 'note':
                timestamp = event.get('timestamp', '')
                if '2025-10-03' in str(timestamp):
                    data = event.get('data', {})
                    print(f"    - Author: {data.get('author', 'Unknown')}, Content length: {len(data.get('content', ''))}")
    
    print("=" * 80)
    print("DEBUG COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()

