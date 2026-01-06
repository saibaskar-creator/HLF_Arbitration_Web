import sys
import os
import traceback

# Add project root to path (mimic main.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

print(f"DEBUG: PYTHONPATH set to: {BASE_DIR}")

try:
    # List models to see what is available
    import vertexai
    from vertexai.preview.generative_models import GenerativeModel
    
    PROJECT_ID = "hlf-arbitration" # Hardcoded based on prev files
    LOCATION = "us-central1"
    
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    
    print(f"DEBUG: Checking available models in {PROJECT_ID} @ {LOCATION}...")
    
    # Try 3.0 explicitly
    try:
        model = GenerativeModel("gemini-3-flash-preview")
        print("✅ gemini-3-flash-preview instantiated (Client side check only)")
        # Try a dummy generation to force server check
        resp = model.generate_content("Hello")
        print("✅ gemini-3-flash-preview is WORKING! Response received.")
    except Exception as e:
        print(f"❌ gemini-3-flash-preview FAILED: {e}")

    # Try 2.0
    try:
        model = GenerativeModel("gemini-2.0-flash-exp")
        print("✅ gemini-2.0-flash-exp instantiated")
    except Exception as e:
         print(f"❌ gemini-2.0-flash-exp FAILED: {e}")

except Exception as e:
    print(f"\nCRITICAL EXCEPTION: {e}")
    traceback.print_exc()
