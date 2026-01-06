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
# We stick to the model that worked for you, but we add "Armor" to it below
MODEL_ID = "gemini-2.0-flash-exp"

# --- SOA SCHEMA ---
soa_schema = {
    "type": "OBJECT",
    "properties": {
        "contractDetails": {
            "type": "OBJECT",
            "properties": {
                "contractNumber": {"type": "STRING"},
                "contractDate": {"type": "STRING"},
                "contractStatus": {"type": "STRING"},
                "tenure": {"type": "STRING"},
                "expiryDate": {"type": "STRING"},
                "financeRate": {"type": "STRING"}
            }
        },
        "customerInfo": {
            "type": "OBJECT",
            "properties": {
                "name": {"type": "STRING"},
                "address": {"type": "STRING"},
                "communicationAddress": {"type": "STRING"}
            }
        },
        "productInfo": {
            "type": "OBJECT",
            "properties": {
                "chassisNo": {"type": "STRING"},
                "engineNo": {"type": "STRING"},
                "vehicleNo": {"type": "STRING"},
                "productModel": {"type": "STRING"}
            }
        },
        "financials": {
            "type": "OBJECT",
            "properties": {
                "financeAmount": {"type": "STRING"},
                "financeCharges": {"type": "STRING"},
                "agreementValue": {"type": "STRING"},
                "emiAmount": {"type": "STRING"}
            }
        },
        "agingAnalysis": {
            "type": "OBJECT",
            "properties": {
                "currentMonth": {"type": "STRING"},
                "lessThanOneMonth": {"type": "STRING"},
                "oneMonth": {"type": "STRING"},
                "twoMonth": {"type": "STRING"},
                "threeMonth": {"type": "STRING"},
                "fourMonth": {"type": "STRING"},
                "fiveMonth": {"type": "STRING"},
                "sixMonth": {"type": "STRING"},
                "aboveSixMonth": {"type": "STRING"},
                "futureMonth": {"type": "STRING"},
                "totalOverdue": {"type": "STRING"}
            }
        },
        "chequeBounces": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "bounceDate": {"type": "STRING"},
                    "chequeNo": {"type": "STRING"},
                    "amount": {"type": "STRING"},
                    "reason": {"type": "STRING"}
                }
            }
        }
    },
    "required": ["contractDetails", "customerInfo", "financials", "agingAnalysis"]
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

    # FORCE REMOVE NEWLINES inside the string to prevent "Unterminated string" errors
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
    
    # ✅ SAFETY ARMOR: Disable filters that might block legal text
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
            "response_schema": soa_schema,
            "temperature": 0.0,
            "max_output_tokens": 8192  # ✅ Increased to prevent cutoff
        },
        safety_settings=safety_settings
    )

def extract_soa_data(pdf_path):
    print(f"🚀 Initializing Vertex AI ({MODEL_ID}) for SOA: {os.path.basename(pdf_path)}")
    print(f"🚀 Initializing Vertex AI ({MODEL_ID}) for SOA: {os.path.basename(pdf_path)}")
    vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
    
    system_instruction_text = load_prompt("soa_prompt.txt")
    
    model = GenerativeModel(
        MODEL_ID,
        system_instruction=[system_instruction_text]
    )

    try:
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
        
        # Debugging: Print first 100 chars if it fails again
        # Debugging: Print first 100 chars if it fails again
        if not response.text:
             msg = "❌ Error: Received empty response from Gemini."
             with open("extraction_error.log", "a", encoding="utf-8") as f: f.write(msg + "\n")
             print(msg)
             return None
             
        cleaned_output = clean_json_response(response.text)
        
        # DEBUG: Write the cleaned output to see why it fails
        with open("debug_cleaned_soa.txt", "w", encoding="utf-8") as f:
            f.write(cleaned_output)
            
        return json.loads(cleaned_output)

    except json.JSONDecodeError as e:
        msg = f"❌ JSON Parse Error: {e}"
        with open("extraction_error.log", "a", encoding="utf-8") as f: f.write(msg + "\n")
        
        # DUMP BAD JSON for inspection
        with open("bad_json_soa.txt", "w", encoding="utf-8") as f:
            f.write(response.text)
            
        print(msg)
        return None
    except Exception as e:
        with open("extraction_error.log", "a", encoding="utf-8") as f:
             f.write(f"SOA API Error: {e}\n")
        print(f"❌ API Error: {e}")
        return None

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(__file__))
    test_file = os.path.join(base_dir, "input_docs", "SOA_Test.pdf")
    
    if os.path.exists(test_file):
        data = extract_soa_data(test_file)
        if data:
            print("\n✅ SOA EXTRACTION SUCCESSFUL!")
            print(f"Inferred EMI Amount: {data['financials'].get('emiAmount')}")
            print(json.dumps(data, indent=2))