# CDS Policy Vision

A Flask web application that analyzes parking sign images and provides parking guidance using Google's Gemini AI.

## What It Does

1. **Upload a parking sign image**
2. **Enter vehicle details** (type, date, time)
3. **Get two AI-powered analyses:**
   - CDS (Curb Data Specification) output - structured parking rule data
   - Plain English parking guidance - "Can I park here?" answer

## Quick Start

### Local Development
```bash
# Install dependencies
pip install flask google-generativeai python-dotenv

# Set up environment
echo "API_KEY=your_gemini_api_key" > .env

# Run the app
python3 app.py
```

Visit `http://localhost:5000`

### Docker
```bash
# Build
docker build -t my-flask-app .

# Run
docker run -p 8080:8080 --env-file .env my-flask-app
```

Visit `http://localhost:8080`

## Required Files

- `system_instructions1.txt` - Instructions for CDS analysis
- `system_instructions2.txt` - Instructions for parking guidance
- `prompt1.txt` - Prompt for first API call
- `prompt2.txt` - Template for second API call (uses user variables)
- `.env` - Your Gemini API key

## How It Works

1. **First API Call**: Analyzes sign image → generates structured CDS data
2. **Second API Call**: Uses sign image + user input → provides parking advice

Built with Flask, Google Gemini AI, and Tailwind CSS.