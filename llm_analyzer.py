import google.generativeai as genai
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os
from config import Config

def load_prompts():
    """Load prompts from prompts.json file with fallback to defaults."""
    prompts_file = os.path.join(os.path.dirname(__file__), 'prompts.json')
    
    # Default prompts (fallback if file doesn't exist)
    default_prompts = {
        "timeline_summary": {
            "name": "Timeline Summary",
            "description": "Prompt used to generate a concise summary of significant timeline events from patient EMR data.",
            "template": "You are a medical review assistant analyzing a patient's EMR timeline. Review the following chronological events and provide a concise summary focusing on:\n\n1. Significant clinical events (admissions, procedures, critical changes)\n2. Important diagnostic findings (abnormal labs, imaging results)\n3. Treatment decisions and their timing\n4. Critical vital sign changes\n5. Major interventions or changes in care\n\nFocus only on clinically significant events. Ignore routine measurements that are within normal limits.\n\nTimeline Events:\n{events_text}\n\nProvide a structured summary in 3-4 bullet points highlighting the most important clinical events and their progression. Be concise but specific."
        },
        "unaddressed_events": {
            "name": "Unaddressed Events Analysis",
            "description": "Prompt used to identify abnormal vital signs and lab results that are not mentioned or addressed in clinical notes.",
            "template": "You are a medical review assistant. Analyze the following patient data to identify:\n\n1. Abnormal vital signs that are NOT mentioned or addressed in clinical notes\n2. Abnormal lab results that are NOT mentioned or addressed in clinical notes\n3. Critical values that appear to be overlooked\n\nClinical Notes:\n{notes_text}\n\nVital Signs:\n{vitals_text}\n\nLab Results:\n{labs_text}\n\nFor each unaddressed finding, identify:\n- The specific abnormal value\n- When it occurred\n- Why it's significant (e.g., \"Elevated temperature of 101°F on 2025-07-15 not addressed in notes\")\n- Clinical significance\n\nIf all significant findings appear to be addressed, state that. Be specific and concise."
        }
    }
    
    try:
        if os.path.exists(prompts_file):
            with open(prompts_file, 'r', encoding='utf-8') as f:
                prompts_data = json.load(f)
                # Merge with defaults to ensure all keys exist
                result = default_prompts.copy()
                result.update(prompts_data)
                return result
        else:
            return default_prompts
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Failed to load prompts from {prompts_file}: {e}. Using defaults.")
        return default_prompts

def get_prompt_template(prompt_key: str) -> str:
    """Get a specific prompt template by key."""
    prompts = load_prompts()
    prompt_data = prompts.get(prompt_key, {})
    return prompt_data.get('template', '')

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
    
    # Load prompt template from JSON file
    prompt_template = get_prompt_template('timeline_summary')
    if not prompt_template:
        return "Error: Timeline summary prompt template not found"
    
    prompt = prompt_template.format(events_text=events_text)

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
    
    # Load prompt template from JSON file
    prompt_template = get_prompt_template('unaddressed_events')
    if not prompt_template:
        return "Error: Unaddressed events prompt template not found"
    
    prompt = prompt_template.format(
        notes_text=notes_text,
        vitals_text=vitals_text,
        labs_text=labs_text
    )

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error analyzing unaddressed events: {str(e)}"

