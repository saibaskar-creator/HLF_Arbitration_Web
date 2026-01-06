import os
import json
import re
import vertexai
from vertexai.generative_models import GenerativeModel, Part, SafetySetting
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted
import sys


# --- PATH FIX: Add project root to system path ---
# This ensures we can import from 'src' regardless of where the script is run
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can safely import from src.utils
from src.utils import load_prompt

# --- CONFIGURATION ---
# --- ADC AUTHENTICATION (Cloud Run & Local) ---
import google.auth

# Get credentials from environment (Cloud Run) or local gcloud auth
credentials, project = google.auth.default()
PROJECT_ID = project  # Automatically detected
LOCATION = "us-central1"

LOCATION = "us-central1"
MODEL_ID = "gemini-2.0-flash-exp"

# --- UPDATED AGREEMENT SCHEMA ---
agreement_schema = {
    "type": "OBJECT",
    "properties": {
        "agreementInfo": {
            "type": "OBJECT",
            "properties": {
                "agreementNo": {"type": "STRING"},
                "agreementDate": {"type": "STRING"}
            }
        },
        "borrower": {
            "type": "OBJECT",
            "properties": {
                "name": {"type": "STRING"},
                "address": {"type": "STRING"}
            }
        },
        "coBorrower": {
            "type": "OBJECT",
            "properties": {
                "name": {"type": "STRING"},
                "address": {"type": "STRING"}
            },
            "nullable": True
        },
        "guarantor": {
            "type": "OBJECT",
            "properties": {
                "name": {"type": "STRING"},
                "address": {"type": "STRING"}
            }
        },
        "arbitration": {
            "type": "OBJECT",
            "properties": {
                "venue": {"type": "STRING", "description": "City of arbitration (e.g., Chennai)"},
                "clause": {"type": "STRING", "description": "Brief summary of the clause"}
            }
        },
        "vehicleProof": {
            "type": "OBJECT",
            "properties": {
                "documentName": {"type": "STRING", "description": "e.g., Tax Invoice, Insurance Covernote"},
                "documentDate": {"type": "STRING", "description": "Date found on the proof"}
            },
            "nullable": True
        }
    },
    "required": ["agreementInfo", "borrower", "guarantor", "arbitration"]
}

def clean_json_response(raw_text):
    """Cleans markdown, fixes JSON syntax, and removes dangerous newlines."""
    cleaned = raw_text.strip()
    # Remove Markdown code blocks
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(json)?", "", cleaned).strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    # Find the first '{' and last '}'
    start = cleaned.find('{')
    end = cleaned.rfind('}')
    
    if start != -1 and end != -1:
        cleaned = cleaned[start:end+1]
    
    # FORCE REMOVE NEWLINES to prevent "Unterminated string" errors
    cleaned = cleaned.replace('\n', ' ').replace('\r', ' ')
    cleaned = re.sub(' +', ' ', cleaned)
    return cleaned

@retry(
    retry=retry_if_exception_type(ResourceExhausted),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(5)
)
def generate_with_retry(model, pdf_bytes):
    print("   ... Contacting Gemini (Attempting generation)...")
    
    # Safety Armor
    safety_settings = [
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
        ),
    ]

    return model.generate_content(
        [Part.from_data(pdf_bytes, mime_type="application/pdf")],
        generation_config={
            "response_mime_type": "application/json", 
            "response_schema": agreement_schema,
            "temperature": 0.0,
            "max_output_tokens": 8192
        },
        safety_settings=safety_settings
    )

def extract_agreement_data(pdf_path):
    print(f"🚀 Initializing Vertex AI ({MODEL_ID}) for Agreement: {os.path.basename(pdf_path)}")
    print(f"🚀 Initializing Vertex AI ({MODEL_ID}) for Agreement: {os.path.basename(pdf_path)}")
    vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
    
    # Load prompt from external file
    system_instruction_text = load_prompt("agreement_prompt.txt")
    
    model = GenerativeModel(
        MODEL_ID,
        system_instruction=[system_instruction_text]
    )

    try:
        # OPTIMIZATION: We send the full file because Co-Borrower/Proofs 
        # can be anywhere (Pages 11, 33, 59, 61).
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
    except FileNotFoundError:
        msg = f"❌ Error: File not found at {pdf_path}"
        with open("extraction_error.log", "a", encoding="utf-8") as f: f.write(msg + "\n")
        print(msg)
        return None

    print("🧠 Sending PDF to Gemini...")
    
    try:
        response = generate_with_retry(model, pdf_bytes)
        
        if not response.text:
             msg = "❌ Error: Received empty response from Gemini."
             with open("extraction_error.log", "a", encoding="utf-8") as f: f.write(msg + "\n")
             print(msg)
             return None
             
        cleaned_output = clean_json_response(response.text)
        return json.loads(cleaned_output)

    except json.JSONDecodeError as e:
        msg = f"❌ JSON Parse Error: {e}"
        with open("extraction_error.log", "a", encoding="utf-8") as f: f.write(msg + "\n")
        print(msg)
        return None
    except Exception as e:
        with open("extraction_error.log", "a", encoding="utf-8") as f:
            f.write(f"Agreement API Error: {e}\n")
        print(f"❌ API Error: {e}")
        return None

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(__file__))
    test_file = os.path.join(base_dir, "input_docs", "Agreement_Test.pdf")
    
    if os.path.exists(test_file):
        data = extract_agreement_data(test_file)
        if data:
            print("\n✅ AGREEMENT EXTRACTION SUCCESSFUL!")
            print(f"Borrower:     {data.get('borrower', {}).get('name')}")
            print(f"Co-Borrower:  {data.get('coBorrower', {}).get('name', 'None')}")
            print(f"Guarantor:    {data.get('guarantor', {}).get('name')}")
            print(f"Arbitration:  {data.get('arbitration', {}).get('venue')}")
            print(f"Vehicle Proof:{data.get('vehicleProof', {}).get('documentName')} ({data.get('vehicleProof', {}).get('documentDate')})")
            print("-" * 30)
            print(json.dumps(data, indent=2))