import os
import json
import re
import vertexai
from vertexai.generative_models import GenerativeModel, Part
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
MODEL_ID = "gemini-2.0-flash-exp"  # Using the fast, standard model

# --- CLAIM STATEMENT SCHEMA ---
claim_schema = {
    "type": "OBJECT",
    "properties": {
        "meta": {
            "type": "OBJECT",
            "properties": {
                "contractStatus": {"type": "STRING", "description": "G or L"},
                "claimDate": {"type": "STRING"},
                "repoDate": {"type": "STRING"},
                "saleDate": {"type": "STRING"}
            }
        },
        "entities": {
            "type": "OBJECT",
            "properties": {
                "borrower": {"type": "OBJECT", "properties": {"name": {"type": "STRING"}, "address": {"type": "STRING"}}},
                "coBorrower": {"type": "OBJECT", "properties": {"name": {"type": "STRING"}, "address": {"type": "STRING"}}},
                "guarantor": {"type": "OBJECT", "properties": {"name": {"type": "STRING"}, "address": {"type": "STRING"}}}
            }
        },
        "agreementValueCalculation": {
            "type": "OBJECT",
            "properties": {
                "amountFinanced": {"type": "STRING"},
                "financeCharges": {"type": "STRING"},
                "insuranceDeposit": {"type": "STRING"},
                "futureInterest": {"type": "STRING"},
                "totalReceivable": {"type": "STRING", "description": "The resulting Agreement Value"}
            }
        },
        "claimCalculation": {
            "type": "OBJECT",
            "properties": {
                "additionalInterest": {"type": "STRING"},
                "chequeReturnCharges": {"type": "STRING"},
                "repoCharges": {"type": "STRING"},
                "legalCharges": {"type": "STRING"},
                "otherExpenses": {"type": "STRING"},
                "paidByBorrower": {"type": "STRING", "description": "Amount received from borrower"},
                "saleAmount": {"type": "STRING", "description": "Amount received on sale of asset"},
                "finalClaimAmount": {"type": "STRING"}
            }
        }
    },
    "required": ["meta", "entities", "agreementValueCalculation", "claimCalculation"]
}

def clean_and_parse_json(text):
    """
    Cleans Gemini output to ensure valid JSON parsing.
    """
    # 1. Remove Markdown code blocks (```json ... ```)
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*$", "", text)
    
    # 2. Strip leading/trailing whitespace
    text = text.strip()
    
    # 3. Find the first '{' and last '}'
    try:
        start = text.index('{')
        end = text.rindex('}') + 1
        text = text[start:end]
    except ValueError:
        pass

    return json.loads(text)

@retry(
    retry=retry_if_exception_type(ResourceExhausted),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(5)
)
def generate_with_retry(model, pdf_bytes):
    print("   ... Contacting Gemini (Attempting generation)...")
    return model.generate_content(
        [Part.from_data(pdf_bytes, mime_type="application/pdf")],
        generation_config={
            "response_mime_type": "application/json", 
            "response_schema": claim_schema,
            "temperature": 0.0 
        }
    )

def extract_claim_data(pdf_path):
    print(f"🚀 Initializing Vertex AI ({MODEL_ID}) for Claim: {os.path.basename(pdf_path)}")
    print(f"🚀 Initializing Vertex AI ({MODEL_ID}) for Claim: {os.path.basename(pdf_path)}")
    vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
    
    # Load from external prompt file
    system_instruction_text = load_prompt("claim_prompt.txt")
    
    model = GenerativeModel(
        MODEL_ID,
        system_instruction=[system_instruction_text]
    )

    try:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
    except FileNotFoundError:
        print(f"❌ Error: File not found at {pdf_path}")
        return None

    print("🧠 Sending PDF to Gemini...")
    
    try:
        response = generate_with_retry(model, pdf_bytes)
        
        try:
            # Parse and return structured data using cleaner
            data = clean_and_parse_json(response.text)
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            print(f"📄 Raw Output was: {response.text}")
            raise e
        
        # Remap for the main pipeline to understand 'repoInfo' and 'saleInfo'
        # This keeps compatibility with your main_pipeline.py
        structured_output = {
            "meta": data.get("meta"),
            "entities": data.get("entities"),
            "agreementValueCalculation": data.get("agreementValueCalculation"),
            "claimCalculation": data.get("claimCalculation"),
            
            # Compatibility Mapping
            "repoInfo": {"repoDate": data["meta"].get("repoDate")},
            "saleInfo": {
                "saleDate": data["meta"].get("saleDate"),
                "saleAmount": data["claimCalculation"].get("saleAmount")
            },
            "claimInfo": {"totalClaimAmount": data["claimCalculation"].get("finalClaimAmount")}
        }
        
        return structured_output

    except Exception as e:
        with open("extraction_error.log", "a", encoding="utf-8") as f:
             f.write(f"Claim API Error: {e}\n")
        print(f"❌ API Error: {e}")
        return None

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(__file__))
    test_file = os.path.join(base_dir, "input_docs", "Claim Statement Test.pdf")
    
    if os.path.exists(test_file):
        data = extract_claim_data(test_file)
        if data:
            print("\n✅ CLAIM EXTRACTION SUCCESSFUL!")
            print(json.dumps(data, indent=2))