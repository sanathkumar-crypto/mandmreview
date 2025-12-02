import google.generativeai as genai
from typing import List, Dict, Any, Optional
from datetime import datetime
from config import Config

def initialize_gemini():
    """Initialize Gemini API client."""
    if not Config.GEMINI_API_KEY:
        return None
    
    genai.configure(api_key=Config.GEMINI_API_KEY)
    
    # Try to use gemini-3.0 first, fallback to gemini-2.0-flash-exp or gemini-1.5-flash
    models_to_try = [
        'gemini-2.0-flash-exp',  # Latest experimental
        'gemini-1.5-flash',      # Stable flash model
        'gemini-1.5-pro'         # Pro model as last resort
    ]
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            # Test if model is accessible with a simple query
            try:
                model.generate_content("test")
            except:
                # If test fails, still try to use the model (might work for actual queries)
                pass
            return model
        except Exception as e:
            print(f"Model {model_name} not available: {e}")
            continue
    
    return None

def format_event_for_llm(event: Dict[str, Any]) -> str:
    """Format a single event for LLM analysis."""
    timestamp = event.get('timestamp', '')
    if isinstance(timestamp, datetime):
        timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(timestamp, str):
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
    
    event_type = event.get('type', '')
    data = event.get('data', {})
    
    if event_type == 'note':
        return f"[{timestamp}] NOTE by {data.get('author', 'Unknown')}: {data.get('content', '')[:200]}"
    elif event_type == 'order':
        action = data.get('action', 'created')
        return f"[{timestamp}] ORDER {action.upper()}: {data.get('investigation', '')}"
    elif event_type == 'lab':
        # Lab results are already filtered to only abnormal values in data_processor
        results = ', '.join(data.get('results', [])[:3])
        return f"[{timestamp}] LAB: {data.get('test', '')} - {results}"
    elif event_type == 'vital':
        # Vitals are already filtered to only abnormal values in data_processor
        # Exclude email from display
        vital_str = ', '.join([f"{k}: {v}" for k, v in data.items() if v and k != 'email'])
        return f"[{timestamp}] VITALS: {vital_str}"
    elif event_type == 'io':
        io_str = []
        if data.get('input'):
            io_str.append(f"Input: {data['input']}")
        if data.get('output'):
            io_str.append(f"Output: {data['output']}")
        return f"[{timestamp}] I/O: {', '.join(io_str)}"
    
    return f"[{timestamp}] {event_type}: {str(data)[:100]}"

def analyze_timeline_summary(events: List[Dict[str, Any]]) -> Optional[str]:
    """Generate LLM-based summary of significant timeline events."""
    if not events:
        return None
    
    model = initialize_gemini()
    if not model:
        return "LLM analysis not available (API key not configured)"
    
    # Format events for analysis
    formatted_events = []
    for event in events[:50]:  # Limit to first 50 events to avoid token limits
        formatted_events.append(format_event_for_llm(event))
    
    events_text = "\n".join(formatted_events)
    
    prompt = f"""You are a medical review assistant analyzing a patient's EMR timeline. Review the following chronological events and provide a concise summary focusing on:

1. Significant clinical events (admissions, procedures, critical changes)
2. Important diagnostic findings (abnormal labs, imaging results)
3. Treatment decisions and their timing
4. Critical vital sign changes
5. Major interventions or changes in care

Focus only on clinically significant events. Ignore routine measurements that are within normal limits.

Timeline Events:
{events_text}

Provide a structured summary in 3-4 bullet points highlighting the most important clinical events and their progression. Be concise but specific."""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def analyze_unaddressed_events(events: List[Dict[str, Any]]) -> Optional[str]:
    """Analyze which vitals or lab results are not addressed in notes."""
    if not events:
        return None
    
    model = initialize_gemini()
    if not model:
        return "LLM analysis not available (API key not configured)"
    
    # Separate notes from vitals and labs
    notes = []
    vitals = []
    labs = []
    
    for event in events:
        if event.get('type') == 'note':
            notes.append(event)
        elif event.get('type') == 'vital':
            vitals.append(event)
        elif event.get('type') == 'lab':
            labs.append(event)
    
    # Format for analysis
    notes_text = "\n".join([format_event_for_llm(n) for n in notes[:20]])
    vitals_text = "\n".join([format_event_for_llm(v) for v in vitals[:30]])
    labs_text = "\n".join([format_event_for_llm(l) for l in labs[:30]])
    
    prompt = f"""You are a medical review assistant. Analyze the following patient data to identify:

1. Abnormal vital signs that are NOT mentioned or addressed in clinical notes
2. Abnormal lab results that are NOT mentioned or addressed in clinical notes
3. Critical values that appear to be overlooked

Clinical Notes:
{notes_text}

Vital Signs:
{vitals_text}

Lab Results:
{labs_text}

For each unaddressed finding, identify:
- The specific abnormal value
- When it occurred
- Why it's significant (e.g., "Elevated temperature of 101°F on 2025-07-15 not addressed in notes")
- Clinical significance

If all significant findings appear to be addressed, state that. Be specific and concise."""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error analyzing unaddressed events: {str(e)}"

