# M&M Review System

A Flask-based web application for reviewing patient EMR files in a chronological timeline format.

## Features

- Gmail OAuth authentication (restricted to @cloudphysician.net emails)
- Patient lookup by CPMRN and encounters
- Chronological timeline display of:
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

4. Set up environment variables (optional, for OAuth):
```bash
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-client-secret"
export GOOGLE_REDIRECT_URI="http://localhost:5000/login/callback"
export SECRET_KEY="your-secret-key"
```

5. Run the application:
```bash
# Make sure virtual environment is activated
source venv/bin/activate
python app.py
```

6. Access the application at `http://localhost:5000`

**Note:** If you're not using a virtual environment, you can run the app directly with:
```bash
./venv/bin/python app.py
```

## Development Mode

If OAuth is not configured, the application will run in development mode, allowing you to bypass authentication for testing purposes.

## Project Structure

```
mandmreview/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── data_processor.py     # Patient data processing logic
├── requirements.txt      # Python dependencies
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
