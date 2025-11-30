# M&M Review System

A Flask-based web application for reviewing patient EMR files in a chronological timeline format.

## Features

- **LLM-Powered Analysis**: 
  - Timeline summary of significant clinical events
  - Identification of unaddressed vitals and lab results
  - Uses Gemini 2.0 Flash (experimental) or falls back to Gemini 1.5 Flash
- **Gmail OAuth authentication** (restricted to @cloudphysician.net emails)
- **Patient lookup** by CPMRN and encounters
- **Chronological timeline display** of:
  - Notes
  - Orders
  - Lab Reports
  - Vitals
  - Input/Output

## Setup

1. Create a virtual environment (required on systems with externally-managed Python):
```bash
python3 -m venv venv
```

2. Activate the virtual environment:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up API credentials (see [CREDENTIALS_SETUP.md](CREDENTIALS_SETUP.md) for detailed instructions):
   - **Gemini API Key** (required for LLM analysis): Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - **Google OAuth Credentials** (optional, for authentication): Get from [Google Cloud Console](https://console.cloud.google.com/)

5. Set up environment variables:
```bash
# Required for LLM analysis
export GEMINI_API_KEY="your-gemini-api-key"

# Optional for OAuth authentication
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-client-secret"
export GOOGLE_REDIRECT_URI="http://localhost:5000/login/callback"
export SECRET_KEY="your-secret-key"
```

6. Run the application:
```bash
# Make sure virtual environment is activated
source venv/bin/activate
python app.py
```

7. Access the application at `http://localhost:5000`

**Note:** If you're not using a virtual environment, you can run the app directly with:
```bash
./venv/bin/python app.py
```

## Features

- **LLM-Powered Analysis**: 
  - Timeline summary of significant clinical events
  - Identification of unaddressed vitals and lab results
  - Uses Gemini 2.0 Flash (experimental) or falls back to Gemini 1.5 Flash
- **Chronological Timeline**: All events sorted by timestamp
- **Gmail OAuth**: Secure authentication for @cloudphysician.net users

## Development Mode

If OAuth is not configured, the application will run in development mode, allowing you to bypass authentication for testing purposes.

## Project Structure

```
mandmreview/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── data_processor.py     # Patient data processing logic
├── llm_analyzer.py       # LLM analysis functions
├── requirements.txt      # Python dependencies
├── CREDENTIALS_SETUP.md  # Credentials setup guide
├── pat_jsons.json        # Patient data file
├── templates/           # HTML templates
│   ├── login.html
│   ├── patient_lookup.html
│   └── timeline.html
└── static/              # Static files
    ├── css/
    │   └── style.css
    └── js/
        └── timeline.js
```

## Notes

- The patient data is currently loaded from `pat_jsons.json` regardless of the CPMRN/encounters entered (dummy implementation as specified)
- All events are sorted chronologically and displayed in a unified timeline
- The frontend design matches the React app design from `app.tsx`
