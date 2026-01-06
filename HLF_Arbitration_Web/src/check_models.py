import os
import json
import vertexai
from vertexai.generative_models import GenerativeModel

# --- SETUP ---
# --- ADC AUTHENTICATION ---
import google.auth

credentials, project = google.auth.default()
PROJECT_ID = project
LOCATION = "us-central1"

vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)

# --- THE LIST OF SUSPECTS ---
# Common model names likely to exist in 2025-2026
candidates = [
    "gemini-2.0-flash-exp",   # Likely the new standard
    "gemini-1.5-flash-002",   # The specific stable version
    "gemini-1.5-flash",       # The generic alias
    "gemini-1.5-pro",         # The powerful version
    "gemini-1.0-pro",         # The old reliable
    "gemini-pro"              # The generic fallback
]

print(f"🔍 Scanning for available models in {LOCATION}...\n")

for model_name in candidates:
    print(f"Testing: {model_name.ljust(25)}", end=" ... ")
    try:
        model = GenerativeModel(model_name)
        # Try a tiny ping
        response = model.generate_content("Hi", generation_config={"max_output_tokens": 1})
        print("✅ AVAILABLE!")
    except Exception as e:
        if "404" in str(e):
            print("❌ Not Found")
        elif "429" in str(e):
            print("⚠️ Quota Exceeded (But Exists)")
        else:
            print(f"⚠️ Error: {str(e)[:50]}")